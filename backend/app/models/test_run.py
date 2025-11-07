"""
Test run data models.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TestFailure(BaseModel):
    """Test failure details."""
    message: Optional[str] = None
    type: Optional[str] = None
    stacktrace: Optional[str] = None


class TestError(BaseModel):
    """Test error details."""
    message: Optional[str] = None
    type: Optional[str] = None
    stacktrace: Optional[str] = None


class TestSkipped(BaseModel):
    """Test skipped details."""
    message: Optional[str] = None


class TestCase(BaseModel):
    """Individual test case."""
    name: str
    classname: Optional[str] = None
    time: float = 0.0
    status: str  # "passed" | "failed" | "skipped" | "error"
    failure: Optional[TestFailure] = None
    error: Optional[TestError] = None
    skipped: Optional[TestSkipped] = None
    system_out: Optional[str] = None
    system_err: Optional[str] = None


class TestSuite(BaseModel):
    """Test suite containing multiple test cases."""
    name: str
    tests: int
    failures: int = 0
    errors: int = 0
    skipped: int = 0
    time: float = 0.0
    timestamp: Optional[datetime] = None
    test_cases: List[TestCase] = []


class TestSource(BaseModel):
    """Source information (Jenkins, GitHub Actions, etc.)."""
    type: str  # "jenkins" | "github_actions" | "gitlab_ci" | "manual"
    system_url: Optional[str] = None
    job_name: Optional[str] = None
    job_url: Optional[str] = None
    build_number: Optional[int] = None
    build_id: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    author: Optional[str] = None
    pr_number: Optional[int] = None


class TestVersions(BaseModel):
    """Version information."""
    testware_version: Optional[str] = None
    sut_version: Optional[str] = None  # Software Under Test
    sut_commit: Optional[str] = None
    environment: Optional[str] = None  # "dev", "staging", "production"
    dependencies: Dict[str, str] = {}


class TestExecution(BaseModel):
    """Test execution information."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    executor: Optional[str] = None  # Runner/agent name
    executor_os: Optional[str] = None
    executor_architecture: Optional[str] = None


class TestSummary(BaseModel):
    """Summary statistics."""
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    success_rate: float = 0.0


class IndexedFields(BaseModel):
    """Fields used for indexing and querying."""
    project_name: Optional[str] = None
    test_type: Optional[str] = None  # "unit", "integration", "e2e", "performance"
    status: str = "unknown"  # "success", "failure", "partial"


class Artifact(BaseModel):
    """Test artifacts (screenshots, logs, etc.)."""
    name: str
    type: str  # "screenshot", "log", "video", "report"
    url: str
    size_bytes: Optional[int] = None


class TestRun(BaseModel):
    """Complete test run model."""
    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: TestSource
    versions: TestVersions = Field(default_factory=TestVersions)
    execution: TestExecution = Field(default_factory=TestExecution)
    summary: TestSummary = Field(default_factory=TestSummary)
    test_suites: List[TestSuite] = []
    artifacts: List[Artifact] = []
    custom_metadata: Dict[str, Any] = {}
    tags: List[str] = []
    indexed_fields: IndexedFields = Field(default_factory=IndexedFields)


class TestRunCreate(BaseModel):
    """Test run creation model (from API)."""
    source: TestSource
    versions: Optional[TestVersions] = None
    execution: Optional[TestExecution] = None
    custom_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TestRunResponse(BaseModel):
    """Test run response model."""
    run_id: str
    created_at: datetime
    source: TestSource
    versions: TestVersions
    summary: TestSummary
    test_suites: List[TestSuite]
    tags: List[str]
    indexed_fields: IndexedFields


class TestRunListResponse(BaseModel):
    """Test run list response."""
    total: int
    page: int
    limit: int
    results: List[TestRunResponse]
