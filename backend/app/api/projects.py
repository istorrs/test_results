"""
Project management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..core.database import get_database
from ..services.project_service import ProjectService
from ..models import (
    ProjectCreate,
    ProjectResponse,
    APIKeyCreate,
    APIKeyResponse,
    User,
)
from .dependencies import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new project."""
    db = get_database()
    project_service = ProjectService(db)

    try:
        project = await project_service.create_project(project_data, current_user.email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ProjectResponse(
        project_name=project.project_name,
        display_name=project.display_name,
        description=project.description,
        created_at=project.created_at,
        settings=project.settings,
        members=project.members,
    )


@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user: User = Depends(get_current_user)):
    """List all projects for the current user."""
    db = get_database()
    project_service = ProjectService(db)

    projects = await project_service.list_projects(current_user.email)

    return [
        ProjectResponse(
            project_name=p.project_name,
            display_name=p.display_name,
            description=p.description,
            created_at=p.created_at,
            settings=p.settings,
            members=p.members,
        )
        for p in projects
    ]


@router.get("/{project_name}", response_model=ProjectResponse)
async def get_project(
    project_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get project details."""
    db = get_database()
    project_service = ProjectService(db)

    project = await project_service.get_project(project_name)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user has access
    if not any(m.user_email == current_user.email for m in project.members):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ProjectResponse(
        project_name=project.project_name,
        display_name=project.display_name,
        description=project.description,
        created_at=project.created_at,
        settings=project.settings,
        members=project.members,
    )


@router.post("/{project_name}/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    project_name: str,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
):
    """Generate a new API key for a project."""
    db = get_database()
    project_service = ProjectService(db)

    project = await project_service.get_project(project_name)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is admin
    user_member = next(
        (m for m in project.members if m.user_email == current_user.email), None
    )

    if user_member is None or user_member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    api_key = await project_service.generate_api_key(project_name, key_data)
    return api_key


@router.delete("/{project_name}/api-keys/{key_id}")
async def revoke_api_key(
    project_name: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
):
    """Revoke an API key."""
    db = get_database()
    project_service = ProjectService(db)

    project = await project_service.get_project(project_name)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if user is admin
    user_member = next(
        (m for m in project.members if m.user_email == current_user.email), None
    )

    if user_member is None or user_member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    success = await project_service.revoke_api_key(project_name, key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"message": "API key revoked successfully"}
