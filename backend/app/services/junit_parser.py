"""
JUnit XML parser service.
"""
import xml.etree.ElementTree as ET
from typing import List
from datetime import datetime
from ..models import TestSuite, TestCase, TestFailure, TestError, TestSkipped


class JUnitParser:
    """Parser for JUnit XML test reports."""

    @staticmethod
    def parse(xml_content: bytes) -> List[TestSuite]:
        """
        Parse JUnit XML and return list of test suites.

        Args:
            xml_content: Raw XML content as bytes

        Returns:
            List of TestSuite objects
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid JUnit XML: {str(e)}")

        test_suites = []

        # Handle both <testsuites> and <testsuite> root elements
        if root.tag == "testsuites":
            suite_elements = root.findall("testsuite")
        elif root.tag == "testsuite":
            suite_elements = [root]
        else:
            raise ValueError(f"Unknown root element: {root.tag}")

        for suite_elem in suite_elements:
            test_suite = JUnitParser._parse_test_suite(suite_elem)
            test_suites.append(test_suite)

        return test_suites

    @staticmethod
    def _parse_test_suite(suite_elem: ET.Element) -> TestSuite:
        """Parse a single test suite element."""
        name = suite_elem.get("name", "Unknown Suite")
        tests = int(suite_elem.get("tests", "0"))
        failures = int(suite_elem.get("failures", "0"))
        errors = int(suite_elem.get("errors", "0"))
        skipped = int(suite_elem.get("skipped", "0"))
        time = float(suite_elem.get("time", "0"))

        timestamp_str = suite_elem.get("timestamp")
        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        test_cases = []
        for case_elem in suite_elem.findall("testcase"):
            test_case = JUnitParser._parse_test_case(case_elem)
            test_cases.append(test_case)

        return TestSuite(
            name=name,
            tests=tests,
            failures=failures,
            errors=errors,
            skipped=skipped,
            time=time,
            timestamp=timestamp,
            test_cases=test_cases,
        )

    @staticmethod
    def _parse_test_case(case_elem: ET.Element) -> TestCase:
        """Parse a single test case element."""
        name = case_elem.get("name", "Unknown Test")
        classname = case_elem.get("classname")
        time = float(case_elem.get("time", "0"))

        # Determine status and parse failure/error/skipped
        failure_elem = case_elem.find("failure")
        error_elem = case_elem.find("error")
        skipped_elem = case_elem.find("skipped")

        failure = None
        error = None
        skipped = None
        status = "passed"

        if failure_elem is not None:
            status = "failed"
            failure = TestFailure(
                message=failure_elem.get("message"),
                type=failure_elem.get("type"),
                stacktrace=failure_elem.text,
            )
        elif error_elem is not None:
            status = "error"
            error = TestError(
                message=error_elem.get("message"),
                type=error_elem.get("type"),
                stacktrace=error_elem.text,
            )
        elif skipped_elem is not None:
            status = "skipped"
            skipped = TestSkipped(
                message=skipped_elem.get("message") or skipped_elem.text,
            )

        # Parse system-out and system-err
        system_out_elem = case_elem.find("system-out")
        system_err_elem = case_elem.find("system-err")

        system_out = system_out_elem.text if system_out_elem is not None else None
        system_err = system_err_elem.text if system_err_elem is not None else None

        return TestCase(
            name=name,
            classname=classname,
            time=time,
            status=status,
            failure=failure,
            error=error,
            skipped=skipped,
            system_out=system_out,
            system_err=system_err,
        )
