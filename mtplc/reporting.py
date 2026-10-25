"""
PyTest configuration and professional Playwright test reporting for MTPLC.
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
from datetime import datetime
from html import escape
from pathlib import Path

import pytest


# ============================================================
# Project Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORTS_DIR = PROJECT_ROOT / "reports"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
FAILURE_SCREENSHOTS_DIR = SCREENSHOTS_DIR / "failures"

HTML_REPORT = REPORTS_DIR / "MTPLC_Automation_Report.html"
PDF_REPORT = REPORTS_DIR / "IAPMO_MYPLC_Automation_Report.pdf"

PDF_SOURCE_HTML = (
    REPORTS_DIR
    / "IAPMO_MYPLC_Automation_PDF_Source.html"
)


# ============================================================
# Create Required Directories
# ============================================================

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

SCREENSHOTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

FAILURE_SCREENSHOTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Allow an application-specific target for the upload smoke test."""
    parser.addoption(
        "--application-number",
        dest="application_number",
        default=None,
        help="Target UI application number, for example P-254482.",
    )
    parser.addoption(
        "--model-workbook-application-number",
        dest="model_workbook_application_number",
        default=None,
        help=(
            "Application number in the populated model workbook when it "
            "differs from the target UI application."
        ),
    )
    parser.addoption(
        "--phase2-only",
        action="store_true",
        default=False,
        help="Run Vanessa's complete Phase 2 workflow for the selected application.",
    )
    parser.addoption(
        "--phase2-resume-from-list",
        action="store_true",
        default=False,
        help=(
            "Resume Vanessa's Phase 2 after the application is already List; "
            "run the hamburger List and Complete Application actions."
        ),
    )


# ============================================================
# Execution Data
# ============================================================

TEST_RESULTS: list[dict] = []

EXECUTION_START: datetime | None = None
EXECUTION_END: datetime | None = None


# ============================================================
# Scenario Information
# ============================================================

SCENARIO_NAME = "Application Status Incomplete to List to Complete"
APPLICATION_NAME = "MYPLC"
APPLICATION_NUMBER = "Auto-detected from application workbook"
MODEL_NUMBER = "Workbook-derived model set"
SCENARIO_STEPS = [
    "R&T Engineer: log in successfully",
    "R&T Engineer: open the target application and verify Incomplete status",
    "R&T Engineer: verify model upload or upload the populated template",
    "R&T Engineer: list and verify every workbook model as Recommendable",
    "R&T Engineer: select the application-level Staff Recommendation List",
    "R&T Engineer: validate Additional Companies and their model rows",
    "R&T Engineer: log out successfully",
    "Vanessa: log in successfully",
    "Vanessa: open the application and verify its expected starting status",
    "Vanessa: create/verify the Write Up Action Item after reload",
    "Vanessa: change application status from Incomplete to List",
    "Vanessa: run the enabled hamburger List action and confirm List",
    "Vanessa: complete the application, save its PDF, and verify redirect",
    "Vanessa: log out successfully",
    "R&T Admin: log in successfully",
    "R&T Admin: open the application and verify final status Complete",
    "R&T Admin: log out successfully",
]


# ============================================================
# Browser Configuration
# ============================================================

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Launch Chromium in maximized mode."""

    return {
        **browser_type_launch_args,
        "args": [
            *browser_type_launch_args.get("args", []),
            "--start-maximized",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Use the full browser window instead of a fixed viewport."""

    return {
        **browser_context_args,
        "no_viewport": True,
    }


# ============================================================
# PyTest Configuration
# ============================================================

def pytest_configure(config: pytest.Config) -> None:
    """Configure professional report metadata."""

    global APPLICATION_NUMBER, EXECUTION_START

    EXECUTION_START = datetime.now()
    APPLICATION_NUMBER = (
        config.getoption("application_number")
        or os.getenv("MTPLC_APPLICATION_NUMBER")
        or "Auto-detected from application workbook"
    )

    config._mtplc_start_time = EXECUTION_START

    if hasattr(config, "_metadata"):

        config._metadata["MTPLC Project"] = (
            "MTPLC Automation"
        )

        config._metadata["MTPLC Application"] = (
            APPLICATION_NAME
        )

        config._metadata["MTPLC Framework"] = (
            "Playwright + PyTest"
        )

        config._metadata["MTPLC Browser"] = (
            "Chromium"
        )

        config._metadata["MTPLC Operating System"] = (
            "Windows"
        )

        config._metadata["MTPLC Test Type"] = (
            "UI Automation"
        )

        config._metadata["MTPLC Execution Type"] = (
            "Smoke / Regression"
        )

        config._metadata["MTPLC Scenario"] = (
            SCENARIO_NAME
        )

        config._metadata["MTPLC Application Number"] = (
            APPLICATION_NUMBER
        )

        config._metadata["MTPLC Model Number"] = (
            MODEL_NUMBER
        )

        config._metadata["MTPLC Report Generated"] = (
            EXECUTION_START.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )


# ============================================================
# Determine Actual Failed Step
# ============================================================

def _get_failed_step_index() -> int | None:
    """Return the workflow step that was active when the test failed."""
    workflow_results = [
        result for result in TEST_RESULTS
        if result["status"] == "FAILED"
    ]
    if workflow_results:
        failed_result = workflow_results[-1]
        completed = set(failed_result.get("completed_steps", []))
        started = failed_result.get("started_steps", [])
        for step in reversed(started):
            if step not in completed:
                return step
    return None


# ============================================================
# Scenario Step Status
# ============================================================

def _get_scenario_step_statuses() -> list[str]:
    """
    Return an individual status for every scenario step.

    PASSED:
        Steps completed before the failure.

    FAILED:
        The step where the failure occurred.

    NOT EXECUTED:
        Steps after the failure.

    If the complete test passes:
        Every step is PASSED.
    """

    total_steps = len(SCENARIO_STEPS)

    # --------------------------------------------------------
    # No execution result
    # --------------------------------------------------------

    if not TEST_RESULTS:

        return [
            "NOT EXECUTED"
            for _ in range(total_steps)
        ]

    # --------------------------------------------------------
    completed = {
        step
        for result in TEST_RESULTS
        for step in result.get("completed_steps", [])
    }
    failed_step = _get_failed_step_index()

    statuses = []
    for index in range(1, total_steps + 1):
        if index in completed:
            statuses.append("PASSED")
        elif index == failed_step:
            statuses.append("FAILED")
        else:
            statuses.append("NOT EXECUTED")
    return statuses


# ============================================================
# Scenario Overall Status
# ============================================================

def _get_scenario_step_status() -> str:
    """Determine overall scenario status."""

    if not TEST_RESULTS:

        return "NOT EXECUTED"

    if any(
        result["status"] == "FAILED"
        for result in TEST_RESULTS
    ):

        return "FAILED"

    if any(
        result["status"] == "SKIPPED"
        for result in TEST_RESULTS
    ):

        return "SKIPPED"

    if all(
        result["status"] == "PASSED"
        for result in TEST_RESULTS
    ):
        return (
            "PASSED"
            if all(
                status == "PASSED"
                for status in _get_scenario_step_statuses()
            )
            else "PARTIAL"
        )

    return "UNKNOWN"


# ============================================================
# Failure Screenshot + Test Result
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
):
    """
    Capture test result and failure screenshot.

    Only the actual test execution phase is recorded.
    """

    outcome = yield

    global APPLICATION_NUMBER
    discovered_application = next(
        (
            value
            for key, value in item.user_properties
            if key == "application_number"
        ),
        None,
    )
    if discovered_application:
        APPLICATION_NUMBER = str(discovered_application)

    report = outcome.get_result()
    if not item.nodeid.startswith("tests/mtplc/"):
        return

    if report.when != "call":
        return

    page = item.funcargs.get("page")

    screenshot_path = None
    current_url = None

    # --------------------------------------------------------
    # Failure Screenshot
    # --------------------------------------------------------

    if report.failed and page is not None:
        current_url = page.url
        LOGGER.error("Test failed at URL: %s", current_url)
        report.sections.append(("Current URL", current_url))

        screenshot_name = (
            f"{item.name}.png"
            .replace("[", "_")
            .replace("]", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("<", "_")
            .replace(">", "_")
        )

        screenshot_path = (
            FAILURE_SCREENSHOTS_DIR
            / screenshot_name
        )

        try:

            page.screenshot(
                path=str(screenshot_path),
                full_page=True,
            )

            LOGGER.error(
                "Failure screenshot saved: %s",
                screenshot_path,
            )

            report.mtplc_screenshot = (
                screenshot_path
            )

        except Exception as exc:

            LOGGER.exception(
                "Unable to capture failure screenshot: %s",
                exc,
            )

    # --------------------------------------------------------
    # Determine Status
    # --------------------------------------------------------

    if report.passed:

        status = "PASSED"

    elif report.failed:

        status = "FAILED"

    elif report.skipped:

        status = "SKIPPED"

    else:

        status = "UNKNOWN"

    # --------------------------------------------------------
    # Store Result
    # --------------------------------------------------------

    TEST_RESULTS.append(
        {
            "nodeid": item.nodeid,
            "name": item.name,
            "status": status,
            "duration": getattr(
                report,
                "duration",
                0.0,
            ),
            "longrepr": (
                str(report.longrepr)
                if report.failed
                else ""
            ),
            "screenshot": screenshot_path,
            "url": current_url,
            "completed_steps": [
                int(value)
                for key, value in item.user_properties
                if key == "workflow_step_completed"
            ],
            "started_steps": [
                int(value)
                for key, value in item.user_properties
                if key == "workflow_step_started"
            ],
        }
    )


# ============================================================
# HTML Report Title
# ============================================================

def pytest_html_report_title(report) -> None:
    """Set HTML report title."""

    report.title = (
        "IAPMO - MYPLC Automation Test Report"
    )


# ============================================================
# HTML Report Header
# ============================================================

def pytest_html_results_summary(
    prefix,
    summary,
    postfix,
) -> None:
    """Add professional information to HTML report."""

    prefix.extend(
        [
            f"""
            <div class="mtplc-header">

                <div class="mtplc-title">
                    IAPMO - MYPLC Automation Test Report
                </div>

                <div class="mtplc-subtitle">
                    UI Automation Execution Summary
                </div>

                <div class="mtplc-info">

                    <div>
                        <strong>Application</strong>
                        <span>{APPLICATION_NAME}</span>
                    </div>

                    <div>
                        <strong>Scenario</strong>
                        <span>{SCENARIO_NAME}</span>
                    </div>

                    <div>
                        <strong>Application Number</strong>
                        <span>{APPLICATION_NUMBER}</span>
                    </div>

                    <div>
                        <strong>Model</strong>
                        <span>{MODEL_NUMBER}</span>
                    </div>

                    <div>
                        <strong>Framework</strong>
                        <span>Playwright + PyTest</span>
                    </div>

                    <div>
                        <strong>Browser</strong>
                        <span>Chromium</span>
                    </div>

                    <div>
                        <strong>Test Type</strong>
                        <span>UI Automation</span>
                    </div>

                    <div>
                        <strong>Generated</strong>
                        <span>
                            {
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                            }
                        </span>
                    </div>

                </div>

            </div>

            <div class="mtplc-section-title">
                Test Execution Results
            </div>
            <div class="mtplc-section-title">
                Workflow Steps
            </div>
            {_generate_scenario_table()}
            """
        ]
    )


# ============================================================
# HTML Table Header
# ============================================================

def pytest_html_results_table_header(cells) -> None:
    """Customize HTML result table headers."""

    cells.insert(
        1,
        "<th>Test Case</th>",
    )

    cells.insert(
        2,
        "<th>Status</th>",
    )

    cells.insert(
        3,
        "<th>Duration</th>",
    )

    cells.insert(
        4,
        "<th>Details</th>",
    )


# ============================================================
# HTML Table Row
# ============================================================

def pytest_html_results_table_row(
    report,
    cells,
) -> None:
    """Customize HTML result rows."""

    if getattr(
        report,
        "when",
        None,
    ) != "call":

        return

    cells.insert(
        1,
        f"<td>{escape(report.nodeid)}</td>",
    )

    if report.passed:

        status = (
            "<span class='status-pass'>"
            "PASS"
            "</span>"
        )

    elif report.failed:

        status = (
            "<span class='status-fail'>"
            "FAIL"
            "</span>"
        )

    elif report.skipped:

        status = (
            "<span class='status-skip'>"
            "SKIP"
            "</span>"
        )

    else:

        status = "UNKNOWN"

    cells.insert(
        2,
        f"<td>{status}</td>",
    )

    duration = getattr(
        report,
        "duration",
        0.0,
    )

    cells.insert(
        3,
        f"<td>{duration:.2f} sec</td>",
    )

    details = ""

    screenshot = getattr(
        report,
        "mtplc_screenshot",
        None,
    )

    if screenshot and screenshot.exists():

        relative_path = os.path.relpath(
            screenshot,
            REPORTS_DIR,
        ).replace(
            "\\",
            "/",
        )

        details = f"""
            <a href="../{relative_path}"
               target="_blank"
               class="screenshot-link">
               View Failure Screenshot
            </a>
        """

    cells.insert(
        4,
        f"<td>{details}</td>",
    )


# ============================================================
# Browser Detection
# ============================================================

def _find_browser() -> str | None:
    """Find Microsoft Edge or Google Chrome."""

    possible_browsers = [

        os.path.join(
            os.environ.get(
                "PROGRAMFILES(X86)",
                r"C:\Program Files (x86)",
            ),
            r"Microsoft\Edge\Application\msedge.exe",
        ),

        os.path.join(
            os.environ.get(
                "PROGRAMFILES",
                r"C:\Program Files",
            ),
            r"Microsoft\Edge\Application\msedge.exe",
        ),

        os.path.join(
            os.environ.get(
                "PROGRAMFILES",
                r"C:\Program Files",
            ),
            r"Google\Chrome\Application\chrome.exe",
        ),

        os.path.join(
            os.environ.get(
                "PROGRAMFILES(X86)",
                r"C:\Program Files (x86)",
            ),
            r"Google\Chrome\Application\chrome.exe",
        ),
    ]

    for browser in possible_browsers:

        if Path(browser).exists():

            return browser

    return None


# ============================================================
# Convert Screenshot to Base64
# ============================================================

def _image_to_base64(
    image_path: Path,
) -> str:
    """Convert screenshot into embedded Base64 image."""

    try:

        encoded = base64.b64encode(
            image_path.read_bytes()
        ).decode(
            "utf-8"
        )

        return (
            "data:image/png;base64,"
            f"{encoded}"
        )

    except Exception as exc:

        LOGGER.warning(
            "Unable to embed screenshot: %s",
            exc,
        )

        return ""


# ============================================================
# Generate Scenario Step Table
# ============================================================

def _generate_scenario_table() -> str:
    """Generate the three-column scenario step table."""

    statuses = (
        _get_scenario_step_statuses()
    )

    rows = ""

    for index, step in enumerate(
        SCENARIO_STEPS,
        start=1,
    ):

        status = statuses[index - 1]

        if status == "PASSED":

            status_class = (
                "step-passed"
            )

        elif status == "FAILED":

            status_class = (
                "step-failed"
            )

        elif status == "NOT EXECUTED":

            status_class = (
                "step-not-executed"
            )

        elif status == "SKIPPED":

            status_class = (
                "step-skipped"
            )

        else:

            status_class = (
                "step-unknown"
            )

        rows += f"""
        <tr>

            <td class="step-number">
                {index}
            </td>

            <td class="step-description">
                {escape(step)}
            </td>

            <td class="step-status {status_class}">
                {status}
            </td>

        </tr>
        """

    return f"""
    <table class="scenario-table">

        <thead>

            <tr>

                <th class="step-number-header">
                    S. No.
                </th>

                <th>
                    Test Step
                </th>

                <th class="step-status-header">
                    Status
                </th>

            </tr>

        </thead>

        <tbody>

            {rows}

        </tbody>

    </table>
    """


# ============================================================
# Generate Static PDF HTML
# ============================================================

def _generate_pdf_source_html() -> None:
    """Generate static HTML report for PDF conversion."""

    global EXECUTION_END

    EXECUTION_END = datetime.now()

    total = len(
        TEST_RESULTS
    )

    passed = sum(
        1
        for result in TEST_RESULTS
        if result["status"] == "PASSED"
    )

    failed = sum(
        1
        for result in TEST_RESULTS
        if result["status"] == "FAILED"
    )

    skipped = sum(
        1
        for result in TEST_RESULTS
        if result["status"] == "SKIPPED"
    )

    total_duration = sum(
        result["duration"]
        for result in TEST_RESULTS
    )

    if total > 0:

        pass_percentage = (
            passed / total
        ) * 100

    else:

        pass_percentage = 0

    start_time = (
        EXECUTION_START.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if EXECUTION_START
        else "-"
    )

    end_time = (
        EXECUTION_END.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if EXECUTION_END
        else "-"
    )

    overall_status = (
        _get_scenario_step_status()
    )

    # ========================================================
    # Test Result Cards
    # ========================================================

    rows = ""

    for index, result in enumerate(
        TEST_RESULTS,
        start=1,
    ):

        status = result["status"]

        if status == "PASSED":

            status_class = "passed"
            status_text = "PASSED"

        elif status == "FAILED":

            status_class = "failed"
            status_text = "FAILED"

        else:

            status_class = "skipped"
            status_text = "SKIPPED"

        screenshot_html = ""

        screenshot = result.get(
            "screenshot"
        )

        if (
            screenshot
            and screenshot.exists()
        ):

            image_data = (
                _image_to_base64(
                    screenshot
                )
            )

            if image_data:

                screenshot_html = f"""
                    <div class="screenshot-box">

                        <div class="screenshot-title">
                            Failure Screenshot
                        </div>

                        <img
                            src="{image_data}"
                            class="failure-image"
                        />

                    </div>
                """

        error_html = ""

        if result["longrepr"]:

            error_text = escape(
                result["longrepr"]
            )

            error_html = f"""
                <div class="error-box">

                    <strong>
                        Failure Details
                    </strong>

                    <pre>
{error_text}
                    </pre>

                </div>
            """

        rows += f"""
            <div class="test-card">

                <div class="test-header">

                    <div class="test-number">
                        #{index}
                    </div>

                    <div class="test-name">
                        {escape(result["nodeid"])}
                    </div>

                    <div class="status {status_class}">
                        {status_text}
                    </div>

                </div>

                <div class="test-info">

                    <div>

                        <span class="label">
                            Duration
                        </span>

                        <span class="value">
                            {result["duration"]:.2f} sec
                        </span>

                    </div>

                    <div>

                        <span class="label">
                            Test Name
                        </span>

                        <span class="value">
                            {escape(result["name"])}
                        </span>

                    </div>

                </div>

                {error_html}

                {screenshot_html}

            </div>
        """

    if not rows:

        rows = """
            <div class="no-results">
                No test execution results were recorded.
            </div>
        """

    # ========================================================
    # Scenario Table
    # ========================================================

    scenario_table = (
        _generate_scenario_table()
    )

    scenario_statuses = (
        _get_scenario_step_statuses()
    )

    scenario_total = len(
        SCENARIO_STEPS
    )

    scenario_passed = sum(
        1
        for status in scenario_statuses
        if status == "PASSED"
    )

    scenario_failed = sum(
        1
        for status in scenario_statuses
        if status == "FAILED"
    )

    scenario_not_executed = sum(
        1
        for status in scenario_statuses
        if status == "NOT EXECUTED"
    )

    # ========================================================
    # Complete PDF HTML
    # ========================================================

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<title>
IAPMO - MYPLC Automation Test Report
</title>

<style>

@page {{
    size: A4;
    margin: 12mm;
}}

* {{
    box-sizing: border-box;
}}

body {{

    font-family:
        "Segoe UI",
        Arial,
        sans-serif;

    margin: 0;
    padding: 0;

    color: #243447;
    background: #ffffff;

    font-size: 11px;
}}


/* =========================================================
   Report Header
   ========================================================= */

.report-header {{

    background: #173f5f;
    color: white;

    padding: 22px 25px;

    border-radius: 7px;

    margin-bottom: 18px;
}}

.report-title {{

    font-size: 24px;
    font-weight: 700;

    margin-bottom: 5px;
}}

.report-subtitle {{

    font-size: 12px;

    opacity: 0.9;
}}

.report-date {{

    margin-top: 10px;

    font-size: 10px;

    opacity: 0.85;
}}


/* =========================================================
   Section Titles
   ========================================================= */

.section-title {{

    font-size: 16px;

    font-weight: 700;

    margin-top: 18px;
    margin-bottom: 10px;

    color: #173f5f;

    border-bottom: 2px solid #173f5f;

    padding-bottom: 5px;
}}


/* =========================================================
   Scenario Metadata
   ========================================================= */

.scenario-info-table {{

    width: 100%;

    border-collapse: collapse;

    margin-bottom: 15px;
}}

.scenario-info-table td {{

    border: 1px solid #d9e1e8;

    padding: 7px 9px;
}}

.scenario-info-table td:nth-child(odd) {{

    width: 18%;

    font-weight: 600;

    background: #f3f6f8;
}}


/* =========================================================
   Overall Status
   ========================================================= */

.overall-status-box {{

    width: 100%;

    border: 1px solid #d9e1e8;

    padding: 10px;

    margin-bottom: 15px;

    text-align: center;
}}

.overall-status-title {{

    font-size: 10px;

    color: #64748b;

    margin-bottom: 4px;
}}

.overall-status {{

    font-size: 18px;

    font-weight: 700;
}}

.overall-passed {{
    color: #198754;
}}

.overall-failed {{
    color: #dc3545;
}}

.overall-skipped {{
    color: #d97706;
}}


/* =========================================================
   Summary Grid
   ========================================================= */

.summary-grid {{

    display: table;

    width: 100%;

    table-layout: fixed;

    margin-bottom: 18px;
}}

.summary-card {{

    display: table-cell;

    text-align: center;

    border: 1px solid #d9e1e8;

    padding: 10px 6px;

    vertical-align: middle;
}}

.summary-number {{

    font-size: 20px;

    font-weight: 700;

    margin-bottom: 3px;
}}

.summary-label {{

    font-size: 9px;

    color: #64748b;
}}

.total-number {{
    color: #173f5f;
}}

.pass-number {{
    color: #198754;
}}

.fail-number {{
    color: #dc3545;
}}

.skip-number {{
    color: #d97706;
}}

.not-executed-number {{
    color: #64748b;
}}


/* =========================================================
   Scenario Steps Table
   ========================================================= */

.scenario-table {{

    width: 100%;

    border-collapse: collapse;

    margin-top: 5px;

    page-break-inside: auto;
}}

.scenario-table thead {{

    display: table-header-group;
}}

.scenario-table tr {{

    page-break-inside: avoid;

    page-break-after: auto;
}}

.scenario-table th {{

    background: #173f5f;

    color: white;

    border: 1px solid #173f5f;

    padding: 7px 8px;

    text-align: left;

    font-size: 10px;
}}

.scenario-table td {{

    border: 1px solid #d9e1e8;

    padding: 6px 8px;

    vertical-align: middle;

    font-size: 10px;
}}

.scenario-table tbody tr:nth-child(even) {{

    background: #f8fafc;
}}

.step-number-header {{

    width: 12%;

    text-align: center !important;
}}

.step-number {{

    width: 12%;

    text-align: center;

    font-weight: 600;
}}

.step-description {{

    width: 68%;

    text-align: left;
}}

.step-status-header {{

    width: 20%;

    text-align: center !important;
}}

.step-status {{

    width: 20%;

    text-align: center;

    font-weight: 700;
}}

.step-passed {{
    color: #198754;
}}

.step-failed {{
    color: #dc3545;
}}

.step-skipped {{
    color: #d97706;
}}

.step-not-executed {{
    color: #64748b;
}}

.step-unknown {{
    color: #64748b;
}}


/* =========================================================
   Environment Table
   ========================================================= */

.environment-table {{

    width: 100%;

    border-collapse: collapse;

    margin-bottom: 18px;
}}

.environment-table td {{

    border: 1px solid #d9e1e8;

    padding: 7px;
}}

.environment-table td:first-child {{

    width: 25%;

    font-weight: 600;

    background: #f3f6f8;
}}


/* =========================================================
   Existing Test Case Cards
   ========================================================= */

.test-card {{

    border: 1px solid #d8dee5;

    border-radius: 7px;

    margin-bottom: 12px;

    page-break-inside: avoid;

    overflow: hidden;
}}

.test-header {{

    display: table;

    width: 100%;

    background: #f5f7f9;

    border-bottom: 1px solid #d8dee5;
}}

.test-number {{

    display: table-cell;

    width: 45px;

    text-align: center;

    padding: 10px 5px;

    font-weight: 700;

    color: #173f5f;
}}

.test-name {{

    display: table-cell;

    padding: 10px 8px;

    font-weight: 600;

    word-break: break-word;
}}

.status {{

    display: table-cell;

    width: 80px;

    text-align: center;

    vertical-align: middle;

    font-weight: 700;

    font-size: 9px;
}}

.status.passed {{
    color: #198754;
}}

.status.failed {{
    color: #dc3545;
}}

.status.skipped {{
    color: #d97706;
}}

.test-info {{

    display: table;

    width: 100%;

    padding: 8px 12px;
}}

.test-info > div {{

    display: table-cell;

    width: 50%;
}}

.label {{

    display: block;

    font-size: 9px;

    color: #6b7280;

    margin-bottom: 2px;
}}

.value {{

    display: block;

    font-weight: 600;
}}


/* =========================================================
   Failure Details
   ========================================================= */

.error-box {{

    margin: 8px 12px;

    padding: 9px;

    background: #fff4f4;

    border-left: 4px solid #dc3545;

    page-break-inside: avoid;
}}

.error-box strong {{
    color: #dc3545;
}}

.error-box pre {{

    white-space: pre-wrap;

    font-size: 8px;

    margin-top: 6px;

    color: #5a1a1a;
}}


/* =========================================================
   Failure Screenshot
   ========================================================= */

.screenshot-box {{

    margin: 10px 12px 12px 12px;

    text-align: center;

    page-break-inside: avoid;
}}

.screenshot-title {{

    text-align: left;

    font-weight: 600;

    margin-bottom: 6px;

    color: #173f5f;
}}

.failure-image {{

    width: 100%;

    max-height: 330px;

    object-fit: contain;

    border: 1px solid #d8dee5;

    border-radius: 5px;
}}


/* =========================================================
   No Results
   ========================================================= */

.no-results {{

    text-align: center;

    padding: 25px;

    border: 1px solid #ddd;

    color: #777;
}}


/* =========================================================
   Footer
   ========================================================= */

.footer {{

    margin-top: 20px;

    padding-top: 8px;

    border-top: 1px solid #d9e1e8;

    text-align: center;

    color: #777;

    font-size: 8px;
}}

</style>

</head>


<body>


<!-- =======================================================
     REPORT HEADER
     ======================================================= -->

<div class="report-header">

    <div class="report-title">
        IAPMO - MYPLC Automation Test Report
    </div>

    <div class="report-subtitle">
        UI Automation Execution Report
    </div>

    <div class="report-date">
        Generated: {end_time}
    </div>

</div>


<!-- =======================================================
     SCENARIO INFORMATION
     ======================================================= -->

<div class="section-title">
    Scenario
</div>


<table class="scenario-info-table">

    <tr>

        <td>Scenario</td>
        <td>{SCENARIO_NAME}</td>

        <td>Application</td>
        <td>{APPLICATION_NAME}</td>

    </tr>


    <tr>

        <td>Application Number</td>
        <td>{APPLICATION_NUMBER}</td>

        <td>Model</td>
        <td>{MODEL_NUMBER}</td>

    </tr>


    <tr>

        <td>Overall Status</td>

        <td colspan="3">

            <strong>
                {overall_status}
            </strong>

        </td>

    </tr>

</table>


<!-- =======================================================
     EXECUTION SUMMARY
     ======================================================= -->

<div class="section-title">
    Execution Summary
</div>


<div class="summary-grid">


    <div class="summary-card">

        <div class="summary-number total-number">
            {scenario_total}
        </div>

        <div class="summary-label">
            TOTAL STEPS
        </div>

    </div>


    <div class="summary-card">

        <div class="summary-number pass-number">
            {scenario_passed}
        </div>

        <div class="summary-label">
            PASSED
        </div>

    </div>


    <div class="summary-card">

        <div class="summary-number fail-number">
            {scenario_failed}
        </div>

        <div class="summary-label">
            FAILED
        </div>

    </div>


    <div class="summary-card">

        <div class="summary-number not-executed-number">
            {scenario_not_executed}
        </div>

        <div class="summary-label">
            NOT EXECUTED
        </div>

    </div>


    <div class="summary-card">

        <div class="summary-number total-number">
            {pass_percentage:.1f}%
        </div>

        <div class="summary-label">
            TEST PASS RATE
        </div>

    </div>


</div>


<!-- =======================================================
     SCENARIO STEPS
     ======================================================= -->

<div class="section-title">

    Scenarios - {SCENARIO_NAME}

</div>


{scenario_table}


<!-- =======================================================
     EXECUTION DETAILS
     ======================================================= -->

<div class="section-title">

    Execution Details

</div>


<table class="environment-table">

    <tr>

        <td>Project</td>

        <td>
            MTPLC Automation
        </td>

    </tr>


    <tr>

        <td>Application</td>

        <td>
            {APPLICATION_NAME}
        </td>

    </tr>


    <tr>

        <td>Scenario</td>

        <td>
            {SCENARIO_NAME}
        </td>

    </tr>


    <tr>

        <td>Application Number</td>

        <td>
            {APPLICATION_NUMBER}
        </td>

    </tr>


    <tr>

        <td>Model Number</td>

        <td>
            {MODEL_NUMBER}
        </td>

    </tr>


    <tr>

        <td>Framework</td>

        <td>
            Playwright + PyTest
        </td>

    </tr>


    <tr>

        <td>Browser</td>

        <td>
            Chromium
        </td>

    </tr>


    <tr>

        <td>Operating System</td>

        <td>
            Windows
        </td>

    </tr>


    <tr>

        <td>Execution Type</td>

        <td>
            Smoke / Regression
        </td>

    </tr>


    <tr>

        <td>Execution Start</td>

        <td>
            {start_time}
        </td>

    </tr>


    <tr>

        <td>Execution End</td>

        <td>
            {end_time}
        </td>

    </tr>


    <tr>

        <td>Total Execution Time</td>

        <td>
            {total_duration:.2f} seconds
        </td>

    </tr>

</table>


<!-- =======================================================
     PYTEST TEST CASE DETAILS
     ======================================================= -->

<div class="section-title">

    Test Case Details

</div>


{rows}


<!-- =======================================================
     FOOTER
     ======================================================= -->

<div class="footer">

    MTPLC Automation | Playwright + PyTest

    <br>

    This report was automatically generated by the automation framework.

</div>


</body>

</html>
"""


    # ========================================================
    # Write Static HTML
    # ========================================================

    PDF_SOURCE_HTML.write_text(
        html,
        encoding="utf-8",
    )

    LOGGER.info(
        "Static PDF source generated: %s",
        PDF_SOURCE_HTML,
    )


# ============================================================
# Generate PDF
# ============================================================

def _generate_pdf_report() -> None:
    """
    Generate PDF from static HTML.

    Microsoft Edge or Google Chrome is used for PDF conversion.
    """

    if not PDF_SOURCE_HTML.exists():

        LOGGER.warning(
            "PDF source HTML not found: %s",
            PDF_SOURCE_HTML,
        )

        return

    browser = _find_browser()

    if not browser:

        LOGGER.warning(
            "Microsoft Edge or Google Chrome was not found. "
            "PDF report was not generated."
        )

        return

    LOGGER.info(
        "Generating PDF report using browser: %s",
        browser,
    )

    try:

        command = [

            browser,

            "--headless",

            "--disable-gpu",

            "--no-sandbox",

            "--allow-file-access-from-files",

            "--run-all-compositor-stages-before-draw",

            "--virtual-time-budget=3000",

            f"--print-to-pdf={PDF_REPORT}",

            PDF_SOURCE_HTML.as_uri(),
        ]

        result = subprocess.run(

            command,

            capture_output=True,

            text=True,

            timeout=90,

            check=False,
        )

        if (
            result.returncode == 0
            and PDF_REPORT.exists()
        ):

            LOGGER.info(
                "PDF report generated successfully: %s",
                PDF_REPORT,
            )

        else:

            LOGGER.error(
                "PDF generation failed."
            )

            if result.stderr:

                LOGGER.error(
                    "Browser output: %s",
                    result.stderr,
                )

    except subprocess.TimeoutExpired:

        LOGGER.error(
            "PDF report generation timed out."
        )

    except Exception as exc:

        LOGGER.exception(
            "Unexpected error while generating PDF: %s",
            exc,
        )


# ============================================================
# Session Finish
# ============================================================

def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
) -> None:
    """
    Generate static PDF after all tests finish.
    """

    LOGGER.info(
        "PyTest execution completed."
    )

    _generate_pdf_source_html()

    _generate_pdf_report()



