"""AI assistant API endpoints."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.deepseek import DeepseekAI
from app.models.ai_conversation import AIConversation, AIFeedback, AIMessage, AIPromptTemplate
from app.models.ai_file_modification import AIFileModification, ModificationAction, ModificationStatus
from app.models.server import Server
from app.models.user import User
import re
from app.schemas.ai import (
    AIActionExecuteRequest,
    AIActionExecuteResponse,
    AIAnalysisRequest,
    AIAnalysisResponse,
    AIAutomationRequest,
    AIAutomationResponse,
    AIChatRequest,
    AIChatResponse,
    AIConversationCreate,
    AIConversationResponse,
    AIConversationUpdate,
    AIContextRequest,
    AIContextResponse,
    AIFeedbackCreate,
    AIFeedbackResponse,
    AIMessageResponse,
    AIPromptTemplateCreate,
    AIPromptTemplateResponse,
    AITroubleshootRequest,
    AITroubleshootResponse,
)
from app.utils.logging import log_integration_event

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


# Conversation endpoints
@router.post("/conversations", response_model=AIConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: AIConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI conversation."""
    try:
        conversation = AIConversation(
            user_id=current_user.id,
            title=data.title,
            server_id=data.server_id,
            deployment_id=data.deployment_id,
            context_type=data.context_type,
            model=data.model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        log_integration_event(
            "AI",
            "conversation_created",
            True,
            {"conversation_id": conversation.id, "user_id": current_user.id},
        )

        return conversation
    except Exception as e:
        logger.exception(f"Failed to create conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation",
        )


@router.get("/conversations", response_model=List[AIConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's conversations."""
    try:
        query = select(AIConversation).where(AIConversation.user_id == current_user.id)

        if active_only:
            query = query.where(AIConversation.is_active == True)

        query = query.order_by(AIConversation.last_message_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        conversations = list(result.scalars().all())

        return conversations
    except Exception as e:
        logger.exception(f"Failed to list conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        )


@router.get("/conversations/{conversation_id}", response_model=AIConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation by ID."""
    try:
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get conversation",
        )


@router.patch("/conversations/{conversation_id}", response_model=AIConversationResponse)
async def update_conversation(
    conversation_id: int,
    data: AIConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update conversation."""
    try:
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)

        await db.commit()
        await db.refresh(conversation)

        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation",
        )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete conversation (soft delete)."""
    try:
        result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        conversation.is_active = False
        await db.commit()

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )


# Message endpoints
@router.get("/conversations/{conversation_id}/messages", response_model=List[AIMessageResponse])
async def list_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List conversation messages."""
    try:
        # Verify conversation ownership
        conv_result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        if not conv_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Get messages
        result = await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at)
            .offset(skip)
            .limit(limit)
        )
        messages = list(result.scalars().all())

        return messages
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list messages",
        )


def parse_file_modifications(ai_response: str) -> List[Dict]:
    """
    Parse AI response for file modification proposals.

    Format expected:
    FILE_MODIFICATION:
    file_path: /path/to/file.yaml
    action: update
    summary: Brief description
    explanation: Detailed explanation
    ---CONTENT---
    [file content]
    ---END---
    """
    modifications = []

    # Find all FILE_MODIFICATION blocks
    pattern = r'FILE_MODIFICATION:\s*\nfile_path:\s*(.+?)\s*\naction:\s*(\w+)\s*\nsummary:\s*(.+?)\s*\nexplanation:\s*(.+?)\s*\n---CONTENT---\s*\n(.*?)\n---END---'

    matches = re.finditer(pattern, ai_response, re.DOTALL | re.MULTILINE)

    for match in matches:
        file_path = match.group(1).strip()
        action = match.group(2).strip().lower()
        summary = match.group(3).strip()
        explanation = match.group(4).strip()
        content = match.group(5).strip()

        # Validate action
        valid_actions = ['create', 'update', 'delete']
        if action not in valid_actions:
            action = 'update'

        modifications.append({
            'file_path': file_path,
            'action': action,
            'summary': summary,
            'explanation': explanation,
            'content': content,
        })

    return modifications


# Chat endpoint
@router.post("/conversations/{conversation_id}/chat", response_model=AIChatResponse)
async def chat(
    conversation_id: int,
    data: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and get AI response."""
    try:
        # Verify conversation ownership
        conv_result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Initialize AI service
        ai_service = DeepseekAI(db)

        # Send message and get response
        message = await ai_service.chat(
            conversation_id=conversation_id,
            user_message=data.message,
            include_context=data.include_context,
        )

        if not message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get AI response",
            )

        # Parse AI response for file modifications
        file_modifications = parse_file_modifications(message.content)
        created_modifications = []

        if file_modifications:
            # Get the first server from conversation or user's servers
            server_id = conversation.server_id

            if not server_id:
                # Get user's first server as default
                servers_result = await db.execute(
                    select(Server).where(Server.id.in_(
                        select(Server.id).where(Server.id.isnot(None)).limit(1)
                    ))
                )
                first_server = servers_result.scalar_one_or_none()
                if first_server:
                    server_id = first_server.id

            if server_id:
                # Get server for reading original content
                server_result = await db.execute(select(Server).where(Server.id == server_id))
                server = server_result.scalar_one_or_none()

                for mod_data in file_modifications:
                    try:
                        # Try to read original content
                        content_before = None
                        if server and mod_data['action'] == 'update':
                            from app.utils.ssh import read_remote_file
                            try:
                                content_before = await read_remote_file(server, mod_data['file_path'])
                            except Exception:
                                pass  # File might not exist yet

                        # Create file modification record
                        modification = AIFileModification(
                            user_id=current_user.id,
                            server_id=server_id,
                            conversation_id=conversation_id,
                            message_id=message.id,
                            file_path=mod_data['file_path'],
                            action=ModificationAction[mod_data['action'].upper()],
                            content_before=content_before,
                            content_after=mod_data['content'],
                            ai_explanation=mod_data['explanation'],
                            ai_summary=mod_data['summary'],
                            status=ModificationStatus.PENDING,
                        )

                        db.add(modification)
                        await db.commit()
                        await db.refresh(modification)

                        created_modifications.append({
                            'action_type': 'file_modification',
                            'action_params': {
                                'modification_id': str(modification.id),
                                'file_path': modification.file_path,
                                'action': modification.action,
                            },
                            'description': modification.ai_summary or f"Modify {modification.file_path}",
                            'requires_confirmation': True,
                            'reversible': True,
                        })

                        logger.info(f"Created file modification {modification.id} for {modification.file_path}")

                    except Exception as e:
                        logger.error(f"Failed to create file modification: {e}")

        # Return response with created modifications
        return AIChatResponse(
            message=message,
            suggested_actions=created_modifications if created_modifications else None,
            executed_actions=None,
            requires_confirmation=len(created_modifications) > 0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}",
        )


# Action execution endpoint
@router.post("/actions/execute", response_model=AIActionExecuteResponse)
async def execute_action(
    data: AIActionExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an AI-suggested action."""
    try:
        # Verify conversation ownership
        conv_result = await db.execute(
            select(AIConversation).where(
                AIConversation.id == data.conversation_id,
                AIConversation.user_id == current_user.id,
            )
        )
        if not conv_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        # Verify confirmation for actions that require it
        if data.action.requires_confirmation and not data.confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This action requires user confirmation",
            )

        # TODO: Implement action execution logic
        # This will call the appropriate backend services based on action_type
        # For now, return placeholder response

        log_integration_event(
            "AI",
            "action_executed",
            True,
            {
                "action_type": data.action.action_type,
                "user_id": current_user.id,
                "conversation_id": data.conversation_id,
            },
        )

        return AIActionExecuteResponse(
            success=True,
            action_type=data.action.action_type,
            result={"message": "Action execution not yet implemented"},
            error=None,
            rollback_available=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to execute action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute action",
        )


# Automation generation endpoint
@router.post("/generate-automation", response_model=AIAutomationResponse)
async def generate_automation(
    data: AIAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate Home Assistant automation from description."""
    try:
        ai_service = DeepseekAI(db)

        automation_yaml = await ai_service.generate_automation_suggestion(
            description=data.description,
            context=data.context,
        )

        if not automation_yaml:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate automation",
            )

        log_integration_event(
            "AI",
            "automation_generated",
            True,
            {"user_id": current_user.id, "server_id": data.server_id},
        )

        return AIAutomationResponse(
            automation_yaml=automation_yaml,
            explanation="Generated automation based on your description",
            suggested_filename="automation.yaml",
            entities_used=[],
            can_deploy=False,
            deployment_instructions="Review the automation and manually add it to your Home Assistant configuration",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate automation",
        )


# Configuration analysis endpoint
@router.post("/analyze-config", response_model=AIAnalysisResponse)
async def analyze_config(
    data: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze Home Assistant configuration."""
    try:
        ai_service = DeepseekAI(db)

        analysis = await ai_service.analyze_configuration(
            config_content=data.config_content,
            focus=data.focus,
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze configuration",
            )

        log_integration_event(
            "AI",
            "config_analyzed",
            True,
            {"user_id": current_user.id, "server_id": data.server_id},
        )

        # Parse analysis response into structured format
        # For now, return basic response
        return AIAnalysisResponse(
            summary=analysis,
            issues=[],
            score=None,
            recommendations=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to analyze configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze configuration",
        )


# Troubleshooting endpoint
@router.post("/troubleshoot", response_model=AITroubleshootResponse)
async def troubleshoot(
    data: AITroubleshootRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Troubleshoot Home Assistant error."""
    try:
        ai_service = DeepseekAI(db)

        solution = await ai_service.troubleshoot_error(
            error_message=data.error_message,
            context=data.context,
        )

        if not solution:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to troubleshoot error",
            )

        log_integration_event(
            "AI",
            "error_troubleshot",
            True,
            {"user_id": current_user.id, "server_id": data.server_id},
        )

        # Parse solution into structured format
        # For now, return basic response
        return AITroubleshootResponse(
            root_cause="Analysis provided by AI",
            solution_steps=[solution],
            prevention_tips=[],
            related_docs=[],
            confidence="medium",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to troubleshoot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to troubleshoot error",
        )


# Prompt template endpoints
@router.post("/templates", response_model=AIPromptTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: AIPromptTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create AI prompt template."""
    try:
        template = AIPromptTemplate(**data.model_dump())
        db.add(template)
        await db.commit()
        await db.refresh(template)

        return template
    except Exception as e:
        logger.exception(f"Failed to create template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template",
        )


@router.get("/templates", response_model=List[AIPromptTemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List AI prompt templates."""
    try:
        query = select(AIPromptTemplate)

        if category:
            query = query.where(AIPromptTemplate.category == category)

        if active_only:
            query = query.where(AIPromptTemplate.is_active == True)

        query = query.order_by(AIPromptTemplate.use_count.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        templates = list(result.scalars().all())

        return templates
    except Exception as e:
        logger.exception(f"Failed to list templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list templates",
        )


# Feedback endpoints
@router.post("/feedback", response_model=AIFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    data: AIFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for AI message."""
    try:
        # Verify message exists and user has access
        msg_result = await db.execute(
            select(AIMessage)
            .join(AIConversation)
            .where(
                AIMessage.id == data.message_id,
                AIConversation.user_id == current_user.id,
            )
        )
        if not msg_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )

        feedback = AIFeedback(
            **data.model_dump(),
            user_id=current_user.id,
        )
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)

        return feedback
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feedback",
        )


# Context endpoint
@router.post("/context", response_model=AIContextResponse)
async def build_context(
    data: AIContextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Build AI context from system data."""
    try:
        from app.services.ai_context_service import AIContextService

        context_service = AIContextService(db)
        await context_service.update_user_context(current_user.id)
        context_data = await context_service.get_context_for_query(current_user.id, data.query or "")

        return AIContextResponse(
            context_summary=f"User has {context_data['user_summary']['total_servers']} servers and {context_data['user_summary']['total_deployments']} deployments",
            server_info=context_data['user_summary']['servers'],
            deployment_info=context_data['user_summary']['projects'],
            integrations=None,
            recent_activity=context_data['recent_activities'][:5],
        )

    except Exception as e:
        logger.exception(f"Failed to build context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build context",
        )


@router.get("/user-context")
async def get_user_full_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive user context for AI assistant"""
    try:
        from app.services.ai_context_service import AIContextService

        context_service = AIContextService(db)
        context = await context_service.update_user_context(current_user.id)

        return {
            "total_servers": context.total_servers,
            "total_deployments": context.total_deployments,
            "total_backups": context.total_backups,
            "servers": context.servers_summary,
            "projects": context.projects_summary,
            "recent_activities": context.recent_activities[:20],
        }
    except Exception as e:
        logger.exception(f"Failed to get user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user context",
        )


@router.post("/context/refresh")
async def refresh_user_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Force refresh of user context"""
    try:
        from app.services.ai_context_service import AIContextService

        context_service = AIContextService(db)
        context = await context_service.update_user_context(current_user.id)

        return {
            "status": "refreshed",
            "total_servers": context.total_servers,
            "total_deployments": context.total_deployments,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.exception(f"Failed to refresh context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh context",
        )
