"""AI assistant API endpoints."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.integrations.deepseek import DeepseekAI
from app.models.ai_conversation import AIConversation, AIFeedback, AIMessage, AIPromptTemplate
from app.models.user import User
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

        # TODO: Parse AI response for suggested actions
        # For now, return basic response
        return AIChatResponse(
            message=message,
            suggested_actions=None,
            executed_actions=None,
            requires_confirmation=False,
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
        # TODO: Implement context building from servers, deployments, integrations
        # This will gather relevant data to provide to the AI

        return AIContextResponse(
            context_summary="Context building not yet implemented",
            server_info=None,
            deployment_info=None,
            integrations=None,
            recent_activity=None,
        )

    except Exception as e:
        logger.exception(f"Failed to build context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to build context",
        )
