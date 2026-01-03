"""GitHub API schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class GitHubStatusResponse(BaseModel):
    """GitHub connection status response."""

    connected: bool = Field(..., description="Whether GitHub is connected")
    username: Optional[str] = Field(None, description="GitHub username")
    email: Optional[str] = Field(None, description="GitHub email")


class GitHubRepoResponse(BaseModel):
    """GitHub repository response."""

    id: str = Field(..., description="Repository ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: str = Field("", description="Repository description")
    private: bool = Field(..., description="Whether repository is private")
    clone_url: str = Field(..., description="Clone URL")
    default_branch: str = Field(..., description="Default branch name")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class GitHubBranchResponse(BaseModel):
    """GitHub branch response."""

    name: str = Field(..., description="Branch name")
    commit: str = Field(..., description="Commit SHA (short)")
    protected: bool = Field(..., description="Whether branch is protected")


class GitHubWebhookResponse(BaseModel):
    """GitHub webhook configuration response."""

    enabled: bool = Field(..., description="Whether webhook is enabled")
    url: str = Field(..., description="Webhook URL")
    secret: str = Field("", description="Webhook secret")
    events: List[str] = Field(default_factory=list, description="Webhook events")


class LinkRepoRequest(BaseModel):
    """Request to link repository to server."""

    repo_url: str = Field(..., description="Repository URL or full name (owner/repo)")
    branch: str = Field(..., description="Branch name")
