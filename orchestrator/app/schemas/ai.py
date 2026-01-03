"""AI assistant schemas."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# Conversation schemas
class AIConversationBase(BaseModel):
    """Base conversation schema."""

    title: str = Field(..., min_length=1, max_length=255)
    server_id: Optional[int] = None
    deployment_id: Optional[int] = None
    context_type: Optional[str] = Field(
        None, description="Context type: server, deployment, general, wled, fpp, tailscale, automation, etc."
    )
    model: str = Field(default="deepseek-chat", max_length=100)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2000, gt=0, le=8000)


class AIConversationCreate(AIConversationBase):
    """Create conversation request."""

    pass


class AIConversationUpdate(BaseModel):
    """Update conversation request."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    summary: Optional[str] = None
    meta_data: Optional[Dict] = Field(None, serialization_alias="metadata")


class AIConversationResponse(AIConversationBase):
    """Conversation response."""

    id: int
    user_id: int
    summary: Optional[str] = None
    is_active: bool
    is_pinned: bool
    is_archived: bool
    last_message_at: Optional[datetime] = None
    message_count: int
    meta_data: Optional[Dict] = Field(None, serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message schemas
class AIMessageBase(BaseModel):
    """Base message schema."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


class AIMessageCreate(AIMessageBase):
    """Create message request."""

    context_data: Optional[Dict] = None


class AIMessageResponse(AIMessageBase):
    """Message response."""

    id: int
    conversation_id: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    context_data: Optional[Dict] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    meta_data: Optional[Dict] = Field(None, serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Chat schemas
class AIChatRequest(BaseModel):
    """Chat request."""

    message: str = Field(..., min_length=1, max_length=10000)
    include_context: bool = Field(
        default=True, description="Include server/deployment context in prompt"
    )
    execute_actions: bool = Field(
        default=True, description="Allow AI to execute actions on backend (create servers, modify configs, etc.)"
    )
    require_confirmation: bool = Field(
        default=True, description="Require user confirmation before executing destructive actions"
    )


class AIAction(BaseModel):
    """AI action that can be executed."""

    action_type: str = Field(..., description="Type of action: create_server, update_automation, deploy_config, etc.")
    action_params: Dict = Field(..., description="Parameters for the action")
    description: str = Field(..., description="Human-readable description of what this action does")
    requires_confirmation: bool = Field(default=True, description="Whether this action needs user confirmation")
    reversible: bool = Field(default=True, description="Whether this action can be rolled back")


class AIChatResponse(BaseModel):
    """Chat response."""

    message: AIMessageResponse
    suggested_actions: Optional[List[AIAction]] = Field(
        None, description="Actions the AI suggests executing"
    )
    executed_actions: Optional[List[Dict]] = Field(
        None, description="Actions that were executed and their results"
    )
    requires_confirmation: bool = Field(
        default=False, description="Whether user confirmation is needed for suggested actions"
    )


# Action execution schemas
class AIActionExecuteRequest(BaseModel):
    """Execute AI action request."""

    conversation_id: int
    action: AIAction
    confirmation: bool = Field(default=False, description="User confirmed the action")


class AIActionExecuteResponse(BaseModel):
    """Action execution response."""

    success: bool
    action_type: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    rollback_available: bool = False
    audit_log_id: Optional[int] = None


# Automation generation schemas
class AIAutomationRequest(BaseModel):
    """Generate automation request."""

    description: str = Field(..., min_length=10, max_length=2000)
    context: Optional[Dict] = Field(
        None, description="Optional context like available entities, devices, etc."
    )
    server_id: Optional[int] = None


class AIAutomationResponse(BaseModel):
    """Automation response."""

    automation_yaml: str
    explanation: str
    suggested_filename: str
    entities_used: List[str] = []
    can_deploy: bool = False
    deployment_instructions: Optional[str] = None


# Configuration analysis schemas
class AIAnalysisRequest(BaseModel):
    """Analyze configuration request."""

    config_content: str = Field(..., min_length=1)
    focus: Optional[str] = Field(
        None, description="Focus area: performance, security, best_practices, syntax, etc."
    )
    server_id: Optional[int] = None


class AIIssue(BaseModel):
    """Configuration issue."""

    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    category: str = Field(..., description="Category: security, performance, syntax, best_practice, etc.")
    title: str
    description: str
    line_number: Optional[int] = None
    suggestion: str
    auto_fixable: bool = False


class AIAnalysisResponse(BaseModel):
    """Analysis response."""

    summary: str
    issues: List[AIIssue]
    score: Optional[int] = Field(None, ge=0, le=100, description="Overall config score")
    recommendations: List[str]


# Troubleshooting schemas
class AITroubleshootRequest(BaseModel):
    """Troubleshoot error request."""

    error_message: str = Field(..., min_length=1)
    context: Optional[Dict] = Field(
        None, description="Additional context like logs, config snippets, etc."
    )
    server_id: Optional[int] = None
    deployment_id: Optional[int] = None


class AITroubleshootResponse(BaseModel):
    """Troubleshoot response."""

    root_cause: str
    solution_steps: List[str]
    prevention_tips: List[str]
    related_docs: List[str] = []
    confidence: Optional[str] = Field(None, pattern="^(high|medium|low)$")


# Prompt template schemas
class AIPromptTemplateBase(BaseModel):
    """Base prompt template schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    system_prompt: str = Field(..., min_length=1)
    user_prompt_template: Optional[str] = None
    variables: Optional[List[str]] = None
    recommended_model: Optional[str] = None
    recommended_temperature: Optional[float] = Field(None, ge=0, le=2)


class AIPromptTemplateCreate(AIPromptTemplateBase):
    """Create prompt template request."""

    pass


class AIPromptTemplateResponse(AIPromptTemplateBase):
    """Prompt template response."""

    id: int
    is_active: bool
    use_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Feedback schemas
class AIFeedbackCreate(BaseModel):
    """Create feedback request."""

    message_id: int
    rating: int = Field(..., ge=1, le=5)
    helpful: bool
    feedback_text: Optional[str] = None
    accuracy: Optional[int] = Field(None, ge=1, le=5)
    relevance: Optional[int] = Field(None, ge=1, le=5)
    clarity: Optional[int] = Field(None, ge=1, le=5)


class AIFeedbackResponse(AIFeedbackCreate):
    """Feedback response."""

    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Context schemas
class AIContextRequest(BaseModel):
    """Request to build AI context."""

    server_id: Optional[int] = None
    deployment_id: Optional[int] = None
    include_wled: bool = False
    include_fpp: bool = False
    include_tailscale: bool = False
    include_recent_logs: bool = False


class AIContextResponse(BaseModel):
    """AI context response."""

    context_summary: str
    server_info: Optional[Dict] = None
    deployment_info: Optional[Dict] = None
    integrations: Optional[Dict] = None
    recent_activity: Optional[List[Dict]] = None
