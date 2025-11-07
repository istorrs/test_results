"""
MongoDB database connection and utilities.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from .config import settings


class Database:
    """MongoDB database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB."""
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]

    # Create indexes
    await create_indexes()

    print("Successfully connected to MongoDB")


async def close_mongo_connection():
    """Close MongoDB connection."""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create database indexes for optimal query performance."""
    if db.db is None:
        return

    # Test runs indexes
    test_runs = db.db["test_runs"]
    await test_runs.create_index("run_id", unique=True)
    await test_runs.create_index([("created_at", -1)])
    await test_runs.create_index([("indexed_fields.project_name", 1), ("created_at", -1)])
    await test_runs.create_index([("source.branch", 1), ("created_at", -1)])
    await test_runs.create_index([("indexed_fields.status", 1)])
    await test_runs.create_index([("source.commit_sha", 1)])
    await test_runs.create_index([("test_suites.test_cases.name", 1)])

    # Projects indexes
    projects = db.db["projects"]
    await projects.create_index("project_name", unique=True)

    # Users indexes
    users = db.db["users"]
    await users.create_index("email", unique=True)


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    if db.db is None:
        raise RuntimeError("Database not initialized")
    return db.db
