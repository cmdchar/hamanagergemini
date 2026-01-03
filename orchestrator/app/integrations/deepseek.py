"""Deepseek AI integration service."""

import logging
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_conversation import AIConversation, AIMessage
from app.models.server import Server
from app.models.deployment import Deployment
from app.utils.logging import log_integration_event

settings = get_settings()
logger = logging.getLogger(__name__)


class DeepseekAI:
    """Service for Deepseek AI integration."""

    API_BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, db: AsyncSession, api_key: Optional[str] = None):
        """
        Initialize Deepseek AI service.

        Args:
            db: Database session
            api_key: Deepseek API key (optional, uses settings if not provided)
        """
        self.db = db
        self.api_key = api_key or settings.deepseek_api_key

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
    ) -> Dict:
        """
        Create a chat completion with Deepseek API.

        Args:
            messages: List of message dictionaries with role and content
            model: Model to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Dict: API response
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                }

                async with session.post(
                    f"{self.API_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        log_integration_event(
                            "Deepseek",
                            "chat_completion",
                            True,
                            {
                                "model": model,
                                "tokens": result.get("usage", {}).get("total_tokens", 0),
                            },
                        )
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Deepseek API error: {response.status} - {error_text}")
                        log_integration_event(
                            "Deepseek",
                            "chat_completion",
                            False,
                            {"error": f"HTTP {response.status}"},
                        )
                        return None

        except Exception as e:
            logger.exception(f"Failed to create chat completion: {e}")
            log_integration_event("Deepseek", "chat_completion", False, {"error": str(e)})
            return None

    async def chat(
        self,
        conversation_id: int,
        user_message: str,
        include_context: bool = True,
    ) -> Optional[AIMessage]:
        """
        Send a chat message and get AI response.

        Args:
            conversation_id: Conversation ID
            user_message: User's message
            include_context: Whether to include HA context

        Returns:
            Optional[AIMessage]: AI response message
        """
        try:
            # Get conversation
            result = await self.db.execute(
                select(AIConversation).where(AIConversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            # Get conversation history
            messages_result = await self.db.execute(
                select(AIMessage)
                .where(AIMessage.conversation_id == conversation_id)
                .order_by(AIMessage.created_at)
            )
            history = list(messages_result.scalars().all())

            # Build messages for API
            api_messages = []

            # Add system prompt
            system_prompt = await self._build_system_prompt(conversation, include_context)
            api_messages.append({"role": "system", "content": system_prompt})

            # Add conversation history (last 10 messages to stay within context)
            for msg in history[-10:]:
                api_messages.append({"role": msg.role, "content": msg.content})

            # Add user message
            api_messages.append({"role": "user", "content": user_message})

            # Save user message
            user_msg = AIMessage(
                conversation_id=conversation_id,
                role="user",
                content=user_message,
            )
            self.db.add(user_msg)
            await self.db.commit()

            # Get AI response
            response = await self.create_chat_completion(
                messages=api_messages,
                model=conversation.model,
                temperature=conversation.temperature,
                max_tokens=conversation.max_tokens,
            )

            if not response:
                return None

            # Extract response data
            choice = response.get("choices", [{}])[0]
            assistant_content = choice.get("message", {}).get("content", "")
            usage = response.get("usage", {})

            # Save assistant message
            assistant_msg = AIMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
                model=response.get("model"),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                finish_reason=choice.get("finish_reason"),
            )
            self.db.add(assistant_msg)

            # Update conversation
            conversation.last_message_at = assistant_msg.created_at
            conversation.message_count += 2  # User + assistant

            await self.db.commit()
            await self.db.refresh(assistant_msg)

            return assistant_msg

        except Exception as e:
            logger.exception(f"Failed to send chat message: {e}")
            return None

    async def _build_system_prompt(
        self, conversation: AIConversation, include_context: bool = True
    ) -> str:
        """
        Build system prompt with context.

        Args:
            conversation: Conversation object
            include_context: Whether to include HA context

        Returns:
            str: System prompt
        """
        base_prompt = """You are a Home Assistant configuration assistant. Help with HA config, YAML, automations, integrations, WLED, FPP, Tailscale.

IMPORTANT - File Modification Workflow:
When you need to modify a file, you MUST explain the changes you would make and provide the modified content in this format:

FILE_MODIFICATION:
file_path: /path/to/file.yaml
action: update
summary: Brief description of changes
explanation: Detailed explanation of why these changes are needed
---CONTENT---
[full modified file content here]
---END---

The user will review your proposed changes before they are applied to the server. DO NOT tell the user to manually edit files - always use this format to propose changes.

CONVERSATION MANAGEMENT:
You have access to conversation management features:
- Users can PIN important conversations to keep them at the top of the list
- Users can ARCHIVE conversations to hide them but keep the history
- Users can DELETE conversations permanently
- Pinned conversations always appear first in the sidebar
- All conversations have full message history that persists across sessions

If a user asks about managing conversations OR asks what you can do regarding the interface, explain these features clearly. You are aware of the UI elements (Pin icon, Archive icon, Delete option) in the sidebar.

However, if the user explicitly asks you to perform one of these actions on the CURRENT conversation, you can execute it by including the corresponding block in your response:

To DELETE the current conversation:
CONVERSATION_ACTION:
action: delete_current_conversation
reason: User requested deletion
---END---

To ARCHIVE the current conversation:
CONVERSATION_ACTION:
action: archive_current_conversation
reason: User requested archiving
---END---

To PIN the current conversation:
CONVERSATION_ACTION:
action: pin_current_conversation
reason: User requested pinning
---END---

AI TOOLS AND SCRIPTS:
You have access to tools and custom scripts. You can use them to gather information or perform actions that you cannot do directly.
To execute a tool or script, use the following block format:

SCRIPT_EXECUTION:
script: <tool_name>
arguments: <arg1> <arg2>
reason: <why you are running this>
---END---

Available Tools:
"""

        # Load and list tools
        try:
            from app.ai_tools.registry import ToolRegistry
            ToolRegistry.load_tools()
            tools = ToolRegistry.get_all_tools()
            
            for tool in tools:
                base_prompt += f"\n- {tool.name}: {tool.description}"
                # Simplified parameter description for prompt token efficiency
                params = [k for k in tool.parameters.get("properties", {}).keys()]
                if params:
                    base_prompt += f" (Args: {', '.join(params)})"
        except Exception as e:
            logger.error(f"Failed to load AI tools for prompt: {e}")

        base_prompt += "\n\nBe concise and helpful."

        if not include_context:
            return base_prompt

        # Add context based on conversation type
        context_parts = [base_prompt]

        # Add user infrastructure context
        try:
            from app.services.ai_context_service import AIContextService
            context_service = AIContextService(self.db)
            user_context = await context_service.update_user_context(conversation.user_id)

            # Minimal context
            context_parts.append(f"\n\nUser has {user_context.total_servers} server(s).")

            if user_context.servers_summary:
                for server_id, server_info in user_context.servers_summary.items():
                    context_parts.append(f"Server {server_id}: {server_info['name']}")

            # Add live file list from servers
            servers_with_files = await context_service.get_user_servers(conversation.user_id)
            for server_data in servers_with_files:
                try:
                    # List files directly from server
                    from app.models.server import Server
                    server_stmt = select(Server).where(Server.id == server_data['id'])
                    server_result = await self.db.execute(server_stmt)
                    server = server_result.scalar_one_or_none()

                    if server:
                        from app.utils.ssh import list_remote_files
                        files = await list_remote_files(server, server.config_path or '/config')

                        context_parts.append(f"\nFiles on {server.name}:")
                        for file in files[:20]:  # Limit to 20 files
                            file_type = "dir" if file.get("is_dir") else "file"
                            context_parts.append(f"  - {file.get('name')} ({file_type})")
                except Exception as e:
                    logger.debug(f"Could not list files from server {server_data['id']}: {e}")

        except Exception as e:
            logger.warning(f"Failed to load user context: {e}")

        # Add server context
        if conversation.server_id:
            server_result = await self.db.execute(
                select(Server).where(Server.id == conversation.server_id)
            )
            server = server_result.scalar_one_or_none()
            if server:
                context_parts.append(f"\n\nFOCUS: User is asking about server '{server.name}' (Host: {server.host})")
                if server.ha_version:
                    context_parts.append(f"Home Assistant Version: {server.ha_version}")

        # Add deployment context
        if conversation.deployment_id:
            deployment_result = await self.db.execute(
                select(Deployment).where(Deployment.id == conversation.deployment_id)
            )
            deployment = deployment_result.scalar_one_or_none()
            if deployment:
                context_parts.append(
                    f"\n\nFOCUS: User is asking about deployment #{deployment.id} (Status: {deployment.status})"
                )
                if deployment.error_message:
                    context_parts.append(f"Error: {deployment.error_message}")

        return "\n".join(context_parts)

    async def generate_automation_suggestion(
        self,
        description: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Generate HA automation based on description.

        Args:
            description: What the automation should do
            context: Optional context (entities, devices, etc.)

        Returns:
            Optional[str]: Generated YAML automation
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert at creating Home Assistant automations.
Generate complete, working YAML automations based on user descriptions.
Include proper triggers, conditions, and actions.
Use best practices and modern HA syntax.""",
            },
            {
                "role": "user",
                "content": f"Create a Home Assistant automation: {description}"
                + (f"\n\nContext: {context}" if context else ""),
            },
        ]

        response = await self.create_chat_completion(
            messages=messages,
            temperature=0.3,  # Lower for more deterministic output
            max_tokens=1500,
        )

        if response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return None

    async def analyze_configuration(
        self,
        config_content: str,
        focus: Optional[str] = None,
    ) -> Optional[str]:
        """
        Analyze HA configuration for issues.

        Args:
            config_content: Configuration YAML content
            focus: Optional focus area (performance, security, etc.)

        Returns:
            Optional[str]: Analysis and recommendations
        """
        focus_text = f" Focus on: {focus}." if focus else ""

        messages = [
            {
                "role": "system",
                "content": """You are an expert Home Assistant configuration auditor.
Analyze configurations for:
- Syntax errors
- Performance issues
- Security vulnerabilities
- Best practice violations
- Optimization opportunities

Provide specific, actionable recommendations.""",
            },
            {
                "role": "user",
                "content": f"Analyze this Home Assistant configuration:{focus_text}\n\n```yaml\n{config_content}\n```",
            },
        ]

        response = await self.create_chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=2000,
        )

        if response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return None

    async def troubleshoot_error(
        self,
        error_message: str,
        context: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Troubleshoot HA error message.

        Args:
            error_message: Error message to troubleshoot
            context: Optional context (logs, config, etc.)

        Returns:
            Optional[str]: Troubleshooting advice
        """
        messages = [
            {
                "role": "system",
                "content": """You are an expert Home Assistant troubleshooter.
Analyze error messages and provide:
- Root cause explanation
- Step-by-step solution
- Prevention tips

Be specific and practical.""",
            },
            {
                "role": "user",
                "content": f"Help me troubleshoot this Home Assistant error:\n\n{error_message}"
                + (f"\n\nAdditional context: {context}" if context else ""),
            },
        ]

        response = await self.create_chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=1500,
        )

        if response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return None
