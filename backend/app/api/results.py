"""
Test results API endpoints.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
import json
from ..core.database import get_database
from ..services.test_results_service import TestResultsService
from ..services.junit_parser import JUnitParser
from ..models import (
    TestRun,
    TestRunCreate,
    TestRunResponse,
    TestRunListResponse,
)
from .dependencies import get_api_key_project, get_current_user
from ..models import User

router = APIRouter(prefix="/results", tags=["test-results"])


@router.post("", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def submit_test_results(
    junit_xml: UploadFile = File(...),
    metadata: str = Form(...),
    project_name: str = Depends(get_api_key_project),
):
    """
    Submit test results from CI/CD.
    Requires API key authentication.
    """
    # Parse metadata
    try:
        metadata_dict = json.loads(metadata)
        test_run_data = TestRunCreate(**metadata_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metadata: {str(e)}",
        )

    # Parse JUnit XML
    try:
        xml_content = await junit_xml.read()
        test_suites = JUnitParser.parse(xml_content)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JUnit XML: {str(e)}",
        )

    # Create test run
    db = get_database()
    service = TestResultsService(db)
    test_run = await service.create_test_run(test_run_data, test_suites, project_name)

    return TestRunResponse(
        run_id=test_run.run_id,
        created_at=test_run.created_at,
        source=test_run.source,
        versions=test_run.versions,
        summary=test_run.summary,
        test_suites=test_run.test_suites,
        tags=test_run.tags,
        indexed_fields=test_run.indexed_fields,
    )


@router.get("", response_model=TestRunListResponse)
async def list_test_results(
    project_name: Optional[str] = None,
    branch: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """
    List test results with filtering.
    Requires user authentication.
    """
    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO 8601 format.",
            )

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO 8601 format.",
            )

    # Parse tags
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",")]

    db = get_database()
    service = TestResultsService(db)

    results = await service.list_test_runs(
        project_name=project_name,
        branch=branch,
        status=status,
        start_date=start_dt,
        end_date=end_dt,
        tags=tags_list,
        page=page,
        limit=limit,
    )

    return results


@router.get("/{run_id}", response_model=TestRunResponse)
async def get_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get specific test run details.
    Requires user authentication.
    """
    db = get_database()
    service = TestResultsService(db)

    test_run = await service.get_test_run(run_id)

    if test_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found",
        )

    return TestRunResponse(
        run_id=test_run.run_id,
        created_at=test_run.created_at,
        source=test_run.source,
        versions=test_run.versions,
        summary=test_run.summary,
        test_suites=test_run.test_suites,
        tags=test_run.tags,
        indexed_fields=test_run.indexed_fields,
    )


@router.get("/test-cases/{test_name}/history")
async def get_test_case_history(
    test_name: str,
    project_name: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """
    Get history for a specific test case.
    Requires user authentication.
    """
    db = get_database()
    service = TestResultsService(db)

    history = await service.get_test_case_history(test_name, project_name, limit)

    return {
        "test_name": test_name,
        "total_runs": len(history),
        "history": history,
    }


@router.delete("/{run_id}")
async def delete_test_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a test run.
    Requires user authentication (admin only in production).
    """
    db = get_database()
    service = TestResultsService(db)

    success = await service.delete_test_run(run_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run not found",
        )

    return {"message": "Test run deleted successfully"}
