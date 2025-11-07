"""
Project management service.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from ..models import Project, ProjectCreate, APIKey, APIKeyCreate, APIKeyResponse, ProjectMember
from ..core.security import generate_api_key, hash_api_key


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["projects"]

    async def create_project(self, project_data: ProjectCreate, creator_email: str) -> Project:
        """Create a new project."""
        # Check if project already exists
        existing = await self.collection.find_one({"project_name": project_data.project_name})
        if existing:
            raise ValueError("Project with this name already exists")

        # Create project with creator as admin
        project = Project(
            **project_data.model_dump(),
            members=[ProjectMember(user_email=creator_email, role="admin")]
        )

        await self.collection.insert_one(project.model_dump())
        return project

    async def get_project(self, project_name: str) -> Optional[Project]:
        """Get project by name."""
        project_dict = await self.collection.find_one({"project_name": project_name})
        if not project_dict:
            return None
        return Project(**project_dict)

    async def list_projects(self, user_email: str) -> List[Project]:
        """List all projects for a user."""
        cursor = self.collection.find({"members.user_email": user_email})
        projects = []
        async for project_dict in cursor:
            projects.append(Project(**project_dict))
        return projects

    async def generate_api_key(
        self, project_name: str, key_data: APIKeyCreate
    ) -> APIKeyResponse:
        """Generate a new API key for a project."""
        # Generate API key
        plain_key = generate_api_key()
        key_hash = hash_api_key(plain_key)
        key_id = str(uuid.uuid4())

        # Calculate expiration
        expires_at = None
        if key_data.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)

        # Create API key
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=key_data.name,
            expires_at=expires_at,
        )

        # Add to project
        await self.collection.update_one(
            {"project_name": project_name},
            {"$push": {"api_keys": api_key.model_dump()}},
        )

        return APIKeyResponse(
            key_id=key_id,
            api_key=plain_key,  # Return plain key only on creation
            name=key_data.name,
            created_at=api_key.created_at,
            expires_at=expires_at,
        )

    async def verify_api_key(self, plain_key: str) -> Optional[str]:
        """
        Verify an API key and return the project name if valid.
        Also updates last_used timestamp.
        """
        key_hash = hash_api_key(plain_key)

        # Find project with matching API key
        project_dict = await self.collection.find_one({"api_keys.key_hash": key_hash})

        if not project_dict:
            return None

        project = Project(**project_dict)

        # Find the specific key and check expiration
        for api_key in project.api_keys:
            if api_key.key_hash == key_hash:
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return None  # Key expired

                # Update last_used
                await self.collection.update_one(
                    {
                        "project_name": project.project_name,
                        "api_keys.key_hash": key_hash,
                    },
                    {"$set": {"api_keys.$.last_used": datetime.utcnow()}},
                )

                return project.project_name

        return None

    async def revoke_api_key(self, project_name: str, key_id: str) -> bool:
        """Revoke an API key."""
        result = await self.collection.update_one(
            {"project_name": project_name},
            {"$pull": {"api_keys": {"key_id": key_id}}},
        )
        return result.modified_count > 0
