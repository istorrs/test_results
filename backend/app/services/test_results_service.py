"""
Test results service for database operations.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..models import (
    TestRun,
    TestRunCreate,
    TestRunResponse,
    TestRunListResponse,
    TestSuite,
    TestSummary,
    IndexedFields,
)


class TestResultsService:
    """Service for managing test results."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["test_runs"]

    async def create_test_run(
        self,
        test_run_data: TestRunCreate,
        test_suites: List[TestSuite],
        project_name: Optional[str] = None,
    ) -> TestRun:
        """Create a new test run."""
        run_id = str(uuid.uuid4())

        # Calculate summary statistics
        summary = self._calculate_summary(test_suites)

        # Determine overall status
        status = "success"
        if summary.failed > 0 or summary.errors > 0:
            status = "failure"
        elif summary.passed == 0 and summary.total_tests > 0:
            status = "unknown"

        # Create indexed fields
        indexed_fields = IndexedFields(
            project_name=project_name,
            status=status,
        )

        # Create test run
        test_run = TestRun(
            run_id=run_id,
            source=test_run_data.source,
            versions=test_run_data.versions or {},
            execution=test_run_data.execution or {},
            summary=summary,
            test_suites=test_suites,
            custom_metadata=test_run_data.custom_metadata or {},
            tags=test_run_data.tags or [],
            indexed_fields=indexed_fields,
        )

        await self.collection.insert_one(test_run.model_dump())
        return test_run

    def _calculate_summary(self, test_suites: List[TestSuite]) -> TestSummary:
        """Calculate summary statistics from test suites."""
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for suite in test_suites:
            for test_case in suite.test_cases:
                total_tests += 1
                if test_case.status == "passed":
                    passed += 1
                elif test_case.status == "failed":
                    failed += 1
                elif test_case.status == "skipped":
                    skipped += 1
                elif test_case.status == "error":
                    errors += 1

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0.0

        return TestSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            success_rate=round(success_rate, 2),
        )

    async def get_test_run(self, run_id: str) -> Optional[TestRun]:
        """Get a test run by ID."""
        run_dict = await self.collection.find_one({"run_id": run_id})
        if not run_dict:
            return None
        return TestRun(**run_dict)

    async def list_test_runs(
        self,
        project_name: Optional[str] = None,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 50,
    ) -> TestRunListResponse:
        """List test runs with filtering."""
        query: Dict[str, Any] = {}

        if project_name:
            query["indexed_fields.project_name"] = project_name
        if branch:
            query["source.branch"] = branch
        if status:
            query["indexed_fields.status"] = status
        if tags:
            query["tags"] = {"$all": tags}

        if start_date or end_date:
            date_query: Dict[str, Any] = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["created_at"] = date_query

        # Get total count
        total = await self.collection.count_documents(query)

        # Get paginated results
        skip = (page - 1) * limit
        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        results = []
        async for run_dict in cursor:
            test_run = TestRun(**run_dict)
            results.append(
                TestRunResponse(
                    run_id=test_run.run_id,
                    created_at=test_run.created_at,
                    source=test_run.source,
                    versions=test_run.versions,
                    summary=test_run.summary,
                    test_suites=test_run.test_suites,
                    tags=test_run.tags,
                    indexed_fields=test_run.indexed_fields,
                )
            )

        return TestRunListResponse(
            total=total,
            page=page,
            limit=limit,
            results=results,
        )

    async def get_test_case_history(
        self, test_name: str, project_name: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get history for a specific test case."""
        query: Dict[str, Any] = {"test_suites.test_cases.name": test_name}

        if project_name:
            query["indexed_fields.project_name"] = project_name

        cursor = (
            self.collection.find(query)
            .sort("created_at", -1)
            .limit(limit)
        )

        history = []
        async for run_dict in cursor:
            test_run = TestRun(**run_dict)

            # Find the specific test case in this run
            for suite in test_run.test_suites:
                for test_case in suite.test_cases:
                    if test_case.name == test_name:
                        history.append(
                            {
                                "run_id": test_run.run_id,
                                "created_at": test_run.created_at,
                                "branch": test_run.source.branch,
                                "commit_sha": test_run.source.commit_sha,
                                "status": test_case.status,
                                "time": test_case.time,
                                "failure": test_case.failure,
                                "error": test_case.error,
                            }
                        )
                        break

        return history

    async def delete_test_run(self, run_id: str) -> bool:
        """Delete a test run."""
        result = await self.collection.delete_one({"run_id": run_id})
        return result.deleted_count > 0
