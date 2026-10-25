"""Three-role end-to-end validation for one MTPLC application."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from mtplc.config.application_config import discover_application_config
from mtplc.config.settings import settings
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.logout_page import LogoutPage

LOGGER = logging.getLogger(__name__)


def _record_workflow_step(
    request: pytest.FixtureRequest,
    step_number: int,
) -> None:
    request.node.user_properties.append(
        ("workflow_step_completed", step_number)
    )


def _start_workflow_step(
    request: pytest.FixtureRequest,
    step_number: int,
) -> None:
    request.node.user_properties.append(
        ("workflow_step_started", step_number)
    )


def _login_as_role(launch_page: LaunchPage, login_page: LoginPage, role: str) -> None:
    username, password = settings.credentials_for(role)
    launch_page.open()
    login_page.validate_login_page()
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()
    LOGGER.info("Authenticated using configured %s role credentials", role)


def _logout(logout_page: LogoutPage) -> None:
    logout_page.click_logout()
    logout_page.wait_for_logout_completion()
    logout_page.validate_successful_logout()


@pytest.mark.smoke
def test_application_model_template_upload(page, request: pytest.FixtureRequest) -> None:
    application_number = (
        request.config.getoption("application_number")
        or os.getenv("MTPLC_APPLICATION_NUMBER")
    )
    model_workbook_application_number = request.config.getoption(
        "model_workbook_application_number"
    )
    phase2_only = request.config.getoption("phase2_only")
    phase2_resume_from_list = request.config.getoption(
        "phase2_resume_from_list"
    )
    application = discover_application_config(
        application_number=application_number,
        model_workbook_application_number=model_workbook_application_number,
    )
    request.node.user_properties.append(
        ("application_number", application.application_number)
    )
    metadata = getattr(request.config, "_metadata", None)
    if metadata is not None:
        metadata["Application Number"] = application.application_number
    settings.credentials_for("vanessa")
    if not phase2_only and not phase2_resume_from_list:
        settings.credentials_for("engineer")
    if not phase2_only:
        settings.credentials_for("admin")

    LOGGER.info("Starting three-role workflow for %s (application ID %s)", application.application_number, application.application_id)
    LOGGER.info(
        "Using model data from %s",
        application.model_template_path.name,
    )
    LOGGER.info("Workbook contains %d distinct model numbers", len(application.expected_model_numbers))

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    applications_page = ApplicationsPage(page)
    details_page = ApplicationDetailsPage(page)
    logout_page = LogoutPage(page)

    if not phase2_only and not phase2_resume_from_list:
        # ==================== PHASE 1 ====================
        _start_workflow_step(request, 1)
        _login_as_role(launch_page, login_page, "engineer")
        _record_workflow_step(request, 1)

        _start_workflow_step(request, 2)
        applications_page.open_incomplete_applications()
        applications_page.open_application(application.application_number)
        details_page.validate_application_details(application.application_id)
        expect(details_page.application_status_value()).to_have_text("Incomplete", timeout=30000)
        _record_workflow_step(request, 2)

        _start_workflow_step(request, 3)
        details_page.click_models_tab()
        missing_models = [
            model_number for model_number in application.expected_model_numbers
            if not details_page.is_model_uploaded(model_number)
        ]
        if missing_models and len(missing_models) != len(application.expected_model_numbers):
            raise AssertionError(
                "The model table contains only part of the target workbook. "
                "Refusing to upload a duplicate template. Missing model numbers: "
                f"{', '.join(missing_models[:10])}"
            )
        if missing_models:
            details_page.upload_model_template_flow(
                file_path=str(application.model_template_path),
                expected_model_number=application.expected_model_numbers[0],
            )
        _record_workflow_step(request, 3)

        _start_workflow_step(request, 4)
        if not details_page.models_are_recommendable(application.expected_model_numbers):
            details_page.list_all_unrecommended_models(application.expected_model_numbers)
        else:
            for model_number in application.expected_model_numbers:
                details_page.validate_model_recommendable(model_number)
        _record_workflow_step(request, 4)

        _start_workflow_step(request, 5)
        details_page.click_details_tab()
        details_page.set_application_recommendation_list()
        _record_workflow_step(request, 5)

        _start_workflow_step(request, 6)
        details_page.click_additional_companies_tab()
        details_page.validate_additional_companies()
        _record_workflow_step(request, 6)

        _start_workflow_step(request, 7)
        _logout(logout_page)
        _record_workflow_step(request, 7)

    # ==================== PHASE 2 ====================
    _start_workflow_step(request, 8)
    _login_as_role(launch_page, login_page, "vanessa")
    _record_workflow_step(request, 8)

    _start_workflow_step(request, 9)
    if phase2_resume_from_list:
        applications_page.open_application_from_all(application.application_number)
    else:
        applications_page.open_incomplete_applications()
        applications_page.open_application(application.application_number)
    details_page.validate_application_details(application.application_id)

    if phase2_resume_from_list:
        try:
            expect(details_page.application_status_value()).to_have_text(
                "List",
                timeout=30000,
            )
        except AssertionError as exc:
            raise AssertionError(
                f"Cannot resume Phase 2: application "
                f"{application.application_number} must already be List."
            ) from exc
    else:
        expect(details_page.application_status_value()).to_have_text(
            "Incomplete",
            timeout=30000,
        )
    _record_workflow_step(request, 9)

    if not phase2_resume_from_list:
        _start_workflow_step(request, 10)
        details_page.click_action_items_tab()
        details_page.create_write_up_action_item()

        # One reload after creation lets the server-persisted Action Item appear.
        details_page.reload_application_details()
        details_page.click_action_items_tab()
        details_page.validate_write_up_action_item()
        _record_workflow_step(request, 10)

        # Incomplete -> List
        _start_workflow_step(request, 11)
        details_page.click_details_tab()
        details_page.change_application_status("List")
        expect(details_page.application_status_value()).to_have_text(
            "List",
            timeout=60000,
        )
        _record_workflow_step(request, 11)

    if phase2_resume_from_list:
        LOGGER.info(
            "Application is already List; continuing with the hamburger "
            "List action and completion flow"
        )

    # Wait for the hamburger List action to become enabled before using it.
    _start_workflow_step(request, 12)
    details_page.wait_until_list_action_enabled()
    details_page.list_application()
    expect(details_page.application_status_value()).to_have_text(
        "List",
        timeout=60000,
    )
    _record_workflow_step(request, 12)

    _start_workflow_step(request, 13)
    details_page.return_to_application_details(application.application_id)
    expect(details_page.application_status_value()).to_have_text(
        "List",
        timeout=30000,
    )

    # Complete the application from the resulting link and page button.
    pdf_path = details_page.complete_application(
        Path(__file__).resolve().parent.parent
        / "reports"
        / "application-completion",
        application.application_id,
    )
    LOGGER.info("Completion PDF for %s saved at %s", application.application_number, pdf_path)
    details_page.wait_for_application_completion(timeout=120000)
    _record_workflow_step(request, 13)

    _start_workflow_step(request, 14)
    _logout(logout_page)
    _record_workflow_step(request, 14)

    if not phase2_only:
        # ==================== PHASE 3 ====================
        _start_workflow_step(request, 15)
        _login_as_role(launch_page, login_page, "admin")
        _record_workflow_step(request, 15)

        _start_workflow_step(request, 16)
        applications_page.open_application_from_all(application.application_number)
        details_page.validate_application_details(application.application_id)

        expect(details_page.application_status_value()).to_have_text("Complete", timeout=60000)
        expect(page.locator(".alert-danger:visible")).to_have_count(0)
        _record_workflow_step(request, 16)

        _start_workflow_step(request, 17)
        _logout(logout_page)
        _record_workflow_step(request, 17)

    if phase2_resume_from_list:
        LOGGER.info(
            "PHASE 2/3 CONTINUATION PASSED: %s redirected, its completion PDF "
            "was saved, and Admin verified Complete",
            application.application_number,
        )
    elif phase2_only:
        LOGGER.info(
            "PHASE 2 WORKFLOW PASSED: %s redirected and its completion PDF "
            "was saved",
            application.application_number,
        )
    else:
        LOGGER.info(
            "END-TO-END WORKFLOW PASSED: %s is Complete",
            application.application_number,
        )

