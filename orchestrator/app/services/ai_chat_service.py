"""
AI Chat Service with context-aware responses
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.user import User
from app.models.ai_context import AIConversation, AIMessage, AIActionLog
from app.services.ai_context_service import AIContextService


# Action handlers
class AIActionHandler:
    """Handles AI-requested actions"""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    async def execute_action(self, action_type: str, params: Dict) -> Dict:
        """Execute an action based on AI request"""
        handlers = {
            "list_servers": self._list_servers,
            "get_server_status": self._get_server_status,
            "list_deployments": self._list_deployments,
            "create_backup": self._create_backup,
            "restart_server": self._restart_server,
        }

        handler = handlers.get(action_type)
        if not handler:
            return {"error": f"Unknown action: {action_type}"}

        try:
            result = await handler(params)

            # Log action
            log = AIActionLog(
                user_id=self.user_id,
                action_type=action_type,
                action_params=params,
                status="success",
                result=result,
            )
            self.db.add(log)
            self.db.commit()

            return result
        except Exception as e:
            # Log failed action
            log = AIActionLog(
                user_id=self.user_id,
                action_type=action_type,
                action_params=params,
                status="failed",
                result={"error": str(e)},
            )
            self.db.add(log)
            self.db.commit()

            return {"error": str(e)}

    async def _list_servers(self, params: Dict) -> Dict:
        """List all user's servers"""
        from app.models.server import Server

        stmt = select(Server).where(Server.user_id == self.user_id)
        servers = self.db.execute(stmt).scalars().all()

        return {
            "count": len(servers),
            "servers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "host": s.host,
                    "port": s.port,
                }
                for s in servers
            ],
        }

    async def _get_server_status(self, params: Dict) -> Dict:
        """Get status of a specific server"""
        from app.models.server import Server

        server_id = params.get("server_id")
        stmt = select(Server).where(
            Server.id == server_id, Server.user_id == self.user_id
        )
        server = self.db.execute(stmt).scalar_one_or_none()

        if not server:
            return {"error": "Server not found"}

        return {
            "id": server.id,
            "name": server.name,
            "host": server.host,
            "status": "online",  # Would check actual status
        }

    async def _list_deployments(self, params: Dict) -> Dict:
        """List recent deployments"""
        from app.models.deployment import Deployment

        limit = params.get("limit", 10)
        stmt = (
            select(Deployment)
            .where(Deployment.user_id == self.user_id)
            .order_by(desc(Deployment.created_at))
            .limit(limit)
        )
        deployments = self.db.execute(stmt).scalars().all()

        return {
            "count": len(deployments),
            "deployments": [
                {
                    "id": d.id,
                    "environment": d.environment,
                    "status": d.status,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in deployments
            ],
        }

    async def _create_backup(self, params: Dict) -> Dict:
        """Create a backup"""
        # Placeholder - would integrate with actual backup service
        return {
            "status": "initiated",
            "backup_id": str(uuid.uuid4()),
            "message": "Backup creation initiated",
        }

    async def _restart_server(self, params: Dict) -> Dict:
        """Restart a server"""
        # Placeholder - would integrate with actual server management
        return {
            "status": "initiated",
            "message": "Server restart initiated",
        }


class AIChatService:
    """AI Chat Service with context awareness"""

    def __init__(self, db: Session):
        self.db = db
        self.context_service = AIContextService(db)

    async def chat(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        Process chat message with context awareness
        """
        # Get or create session
        if not session_id:
            session_id = str(uuid.uuid4())

        conversation = await self._get_or_create_conversation(user_id, session_id)

        # Get user context
        await self.context_service.update_user_context(user_id)
        context_data = await self.context_service.get_context_for_query(
            user_id, message
        )

        # Store user message
        user_message = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
            context_snapshot=context_data,
        )
        self.db.add(user_message)
        self.db.commit()

        # Generate AI response
        response_data = await self._generate_response(
            user_id, message, context_data, conversation
        )

        # Store assistant message
        assistant_message = AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response_data["response"],
            action_taken=response_data.get("action"),
            action_result=response_data.get("action_result"),
            model_used="gpt-4",  # or Claude
        )
        self.db.add(assistant_message)

        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        if not conversation.title:
            # Generate title from first message
            conversation.title = message[:50] + ("..." if len(message) > 50 else "")

        self.db.commit()

        return {
            "response": response_data["response"],
            "action": response_data.get("action"),
            "action_result": response_data.get("action_result"),
            "session_id": session_id,
            "context_used": {
                "servers": context_data["user_summary"]["total_servers"],
                "deployments": context_data["user_summary"]["total_deployments"],
            },
        }

    async def _get_or_create_conversation(
        self, user_id: int, session_id: str
    ) -> AIConversation:
        """Get or create conversation"""
        stmt = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.session_id == session_id,
        )
        conversation = self.db.execute(stmt).scalar_one_or_none()

        if not conversation:
            # Get user context
            context = await self.context_service.get_or_create_context(user_id)

            conversation = AIConversation(
                user_id=user_id,
                session_id=session_id,
                context_id=context.id,
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

        return conversation

    async def _generate_response(
        self,
        user_id: int,
        message: str,
        context: Dict,
        conversation: AIConversation,
    ) -> Dict:
        """
        Generate AI response using context
        This is a simplified version - in production would use OpenAI/Claude API
        """
        # Get conversation history
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at)
            .limit(10)
        )
        history = self.db.execute(stmt).scalars().all()

        # Build context string
        context_str = self._build_context_string(context)

        # Build conversation history
        history_str = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in history[-5:]]
        )

        # Detect if action is needed
        action_info = self._detect_action(message)

        if action_info:
            # Execute action
            action_handler = AIActionHandler(self.db, user_id)
            action_result = await action_handler.execute_action(
                action_info["type"], action_info["params"]
            )

            # Generate response with action result
            response = self._generate_action_response(
                message, action_info["type"], action_result
            )

            return {
                "response": response,
                "action": action_info["type"],
                "action_result": action_result,
            }

        # Generate regular response
        response = self._generate_contextual_response(message, context, history_str)

        return {"response": response}

    def _build_context_string(self, context: Dict) -> str:
        """Build context string for AI"""
        summary = context["user_summary"]
        knowledge = context["relevant_knowledge"]

        context_parts = [
            f"User has {summary['total_servers']} server(s) and {summary['total_deployments']} deployment(s).",
        ]

        if knowledge:
            context_parts.append("\nRelevant information:")
            for entry in knowledge[:3]:
                context_parts.append(f"- {entry['title']}: {entry['content'][:100]}...")

        return "\n".join(context_parts)

    def _detect_action(self, message: str) -> Optional[Dict]:
        """Detect if message requires an action"""
        message_lower = message.lower()

        # Simple keyword-based action detection
        if any(word in message_lower for word in ["list", "show", "get"]):
            if "server" in message_lower:
                return {"type": "list_servers", "params": {}}
            elif "deployment" in message_lower:
                return {"type": "list_deployments", "params": {"limit": 10}}

        if "status" in message_lower and "server" in message_lower:
            return {"type": "get_server_status", "params": {}}

        if "backup" in message_lower and "create" in message_lower:
            return {"type": "create_backup", "params": {}}

        if "restart" in message_lower and "server" in message_lower:
            return {"type": "restart_server", "params": {}}

        return None

    def _generate_action_response(
        self, message: str, action_type: str, result: Dict
    ) -> str:
        """Generate response for action execution"""
        if "error" in result:
            return f"I tried to {action_type.replace('_', ' ')}, but encountered an error: {result['error']}"

        # Format response based on action type
        if action_type == "list_servers":
            servers = result.get("servers", [])
            if not servers:
                return "You don't have any servers configured yet."
            response = f"You have {result['count']} server(s):\n"
            for server in servers:
                response += f"- {server['name']} ({server['host']}:{server['port']})\n"
            return response

        elif action_type == "list_deployments":
            deployments = result.get("deployments", [])
            if not deployments:
                return "You don't have any deployments yet."
            response = f"Here are your recent deployments ({result['count']}):\n"
            for dep in deployments[:5]:
                response += f"- Deployment {dep['id']}: {dep['environment']} - {dep['status']}\n"
            return response

        elif action_type == "create_backup":
            return f"✓ Backup creation initiated successfully. Backup ID: {result.get('backup_id')}"

        elif action_type == "restart_server":
            return "✓ Server restart initiated successfully."

        return f"Action {action_type} completed: {json.dumps(result)}"

    def _generate_contextual_response(
        self, message: str, context: Dict, history: str
    ) -> str:
        """
        Generate contextual response
        Simplified version - would use OpenAI/Claude API
        """
        summary = context["user_summary"]
        message_lower = message.lower()

        # Simple rule-based responses
        if any(word in message_lower for word in ["hello", "hi", "hey"]):
            return f"Hello! I'm your infrastructure assistant. You have {summary['total_servers']} server(s) and {summary['total_deployments']} deployment(s). How can I help you today?"

        if "help" in message_lower:
            return """I can help you with:
- View your servers: "show me my servers"
- Check deployments: "list my deployments"
- Create backups: "create a backup"
- Server status: "check server status"
- And answer questions about your infrastructure!

What would you like to do?"""

        if any(word in message_lower for word in ["how many", "count"]):
            return f"You currently have {summary['total_servers']} server(s) and {summary['total_deployments']} deployment(s) in your infrastructure."

        # Default response
        return f"I understand you're asking about: '{message}'. Based on your infrastructure ({summary['total_servers']} servers, {summary['total_deployments']} deployments), I can help you manage your resources. Try asking 'help' to see what I can do!"

    async def get_conversation_history(
        self, user_id: int, session_id: str
    ) -> List[Dict]:
        """Get conversation history"""
        stmt = select(AIConversation).where(
            AIConversation.user_id == user_id,
            AIConversation.session_id == session_id,
        )
        conversation = self.db.execute(stmt).scalar_one_or_none()

        if not conversation:
            return []

        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.id)
            .order_by(AIMessage.created_at)
        )
        messages = self.db.execute(stmt).scalars().all()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "action": msg.action_taken,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
