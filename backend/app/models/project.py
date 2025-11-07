"""
Project data models.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectSettings(BaseModel):
    """Project settings."""
    retention_days: int = 90
    notify_on_failure: bool = False
    notification_channels: List[str] = []


class APIKey(BaseModel):
    """API key model."""
    key_id: str
    key_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    permissions: List[str] = ["read", "write"]


class APIKeyCreate(BaseModel):
    """API key creation model."""
    name: str
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API key response model (includes plain key only on creation)."""
    key_id: str
    api_key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class ProjectMember(BaseModel):
    """Project member model."""
    user_email: str
    role: str = "viewer"  # "admin", "contributor", "viewer"
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    """Project model."""
    project_name: str
    display_name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    api_keys: List[APIKey] = []
    members: List[ProjectMember] = []


class ProjectCreate(BaseModel):
    """Project creation model."""
    project_name: str
    display_name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response model."""
    project_name: str
    display_name: str
    description: Optional[str] = None
    created_at: datetime
    settings: ProjectSettings
    members: List[ProjectMember]
