"""
MTPLC - Upload Model Template Test.

Flow:

Launch
    ->
Login
    ->
Applications
    ->
Incomplete
    ->
P-254402
    ->
Models
    ->
Manage Models
    ->
Upload Model Template
    ->
Select FEBCO-P-254402.xlsx
    ->
Upload Models
    ->
Yes
    ->
Validate uploaded model
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage


LOGGER = logging.getLogger(__name__)


# ================================================================
# TEST DATA
# ================================================================

APPLICATION_NUMBER = "P-254402"

APPLICATION_ID = "254402"

MODEL_TEMPLATE_PATH = (
    r"C:\Users\hp\Downloads\FEBCO-P-254402.xlsx"
)


# ================================================================
# TEST
# ================================================================

@pytest.mark.skip(
    reason=(
        "Superseded by test_application_validation.py, which includes upload "
        "and Recommendable-status verification without uploading twice."
    )
)
@pytest.mark.smoke
def test_upload_model_template(page) -> None:
    """
    Verify Model Template upload for P-254402.
    """

    # ============================================================
    # PAGE OBJECTS
    # ============================================================

    launch_page = LaunchPage(
        page
    )

    login_page = LoginPage(
        page
    )

    applications_page = ApplicationsPage(
        page
    )

    application_details_page = ApplicationDetailsPage(
        page
    )

    # ============================================================
    # TEST DATA
    # ============================================================

    LOGGER.info(
        "Application Number: %s",
        APPLICATION_NUMBER,
    )

    LOGGER.info(
        "Application ID: %s",
        APPLICATION_ID,
    )

    LOGGER.info(
        "Model Template: %s",
        MODEL_TEMPLATE_PATH,
    )

    # ============================================================
    # VALIDATE EXCEL FILE
    # ============================================================

    template_path = Path(
        MODEL_TEMPLATE_PATH
    ).resolve()

    if not template_path.exists():

        raise FileNotFoundError(
            f"Model Template file does not exist: "
            f"{template_path}"
        )

    if not template_path.is_file():

        raise ValueError(
            f"Model Template path is not a file: "
            f"{template_path}"
        )

    LOGGER.info(
        "Local Model Template file validated successfully"
    )

    # ============================================================
    # 1. LAUNCH
    # ============================================================

    LOGGER.info(
        "Starting MTPLC application"
    )

    launch_page.open()

    # ============================================================
    # 2. LOGIN
    # ============================================================

    LOGGER.info(
        "Validating Login page"
    )

    login_page.validate_login_page()

    LOGGER.info(
        "Performing Login"
    )

    login_page.login()

    login_page.wait_for_login_navigation()

    login_page.validate_successful_login()

    # ============================================================
    # 3. APPLICATIONS
    # ============================================================

    LOGGER.info(
        "Opening Applications module"
    )

    applications_page.click_applications()

    # ============================================================
    # 4. INCOMPLETE
    # ============================================================

    LOGGER.info(
        "Opening Incomplete applications"
    )

    applications_page.click_incomplete()

    # ============================================================
    # 5. OPEN APPLICATION
    # ============================================================

    LOGGER.info(
        "Opening application: %s",
        APPLICATION_NUMBER,
    )

    applications_page.open_application(
        APPLICATION_NUMBER
    )

    # ============================================================
    # 6. APPLICATION DETAILS
    # ============================================================

    application_details_page.validate_application_details(
        APPLICATION_ID
    )

    # ============================================================
    # 7. OPEN MODELS TAB
    # ============================================================

    LOGGER.info(
        "Opening Models tab"
    )

    application_details_page.click_models_tab()

    # ============================================================
    # 8-11. UPLOAD MODEL TEMPLATE
    # ============================================================

    LOGGER.info(
        "Starting Model Template upload flow"
    )

    application_details_page.upload_model_template_flow(
        file_path=str(template_path),
    )

    # ============================================================
    # FINAL
    # ============================================================

    LOGGER.info(
        "Upload Model Template test completed successfully"
    )
