"""End-to-end Main Models CRUD and application completion workflow."""

import secrets
from pathlib import Path

import pytest

from mtplc.config.settings import settings
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.clients_page import ClientsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.logout_page import LogoutPage
from mtplc.pages.models_add_section_page import ModelsAddSectionPage
from mtplc.pages.models_section_crud_page import ModelsSectionCrudPage


SCENARIO_NAME = "Main Models CRUD and Complete Application"
SCENARIO_STEPS = [
    "Vanessa: log in successfully",
    "Vanessa: create a new cUPC application and complete initial setup",
    "Vanessa: add the first model section and model",
    "Vanessa: add the second model section and model",
    "Vanessa: capture the initial section order",
    "Vanessa: move the first section down and verify the new order",
    "Vanessa: move the first section back up and verify the original order",
    "Vanessa: add a temporary section and model before the first section",
    "Vanessa: edit the temporary section brand name",
    "Vanessa: delete the temporary section and verify cleanup",
    "Vanessa: log out successfully",
    "Anish.Desai: log in successfully",
    "Anish.Desai: reopen the generated application and verify its details",
    "Anish.Desai: list both retained models and verify their recommendation state",
    "Anish.Desai: create and verify the Write Up Action Item",
    "Anish.Desai: change the application status to List",
    "Anish.Desai: reload and verify the List action is enabled",
    "Anish.Desai: confirm List and accept confirmation dialogs",
    "Anish.Desai: verify both retained models in Certificate Preview",
    "Anish.Desai: complete the application and verify the saved PDF",
]


def _start_workflow_step(
    request: pytest.FixtureRequest,
    step_number: int,
) -> None:
    request.node.user_properties.append(
        ("workflow_step_started", step_number)
    )


def _record_workflow_step(
    request: pytest.FixtureRequest,
    step_number: int,
) -> None:
    request.node.user_properties.append(
        ("workflow_step_completed", step_number)
    )


def _capture_screenshot(
    page,
    request: pytest.FixtureRequest,
    application_id: str,
    step_number: int,
    screenshot_name: str,
) -> Path:
    """Capture and associate a screenshot with its report step."""
    screenshot_dir = Path("reports/screenshots/model_section_crud")
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = (
        screenshot_dir
        / f"{application_id}_{screenshot_name}.png"
    ).resolve()
    page.screenshot(path=str(screenshot_path), full_page=True)
    request.node.user_properties.append(
        (
            "workflow_step_screenshot",
            f"{step_number}::{screenshot_path}",
        )
    )
    return screenshot_path


@pytest.mark.regression
def test_create_application_model_section_crud_and_complete(
    page,
    request: pytest.FixtureRequest,
) -> None:
    """Create a fresh application, exercise section CRUD, and complete it."""
    request.node.user_properties.append(
        ("workflow_scenario_name", SCENARIO_NAME)
    )
    request.node.user_properties.append(
        ("workflow_scenario_steps", SCENARIO_STEPS)
    )

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    clients_page = ClientsPage(page)
    logout_page = LogoutPage(page)

    _start_workflow_step(request, 1)
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("vanessa")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()
    _record_workflow_step(request, 1)

    _start_workflow_step(request, 2)
    clients_page.open_client_applications(ClientsPage.CLIENT_ID)
    application_id = clients_page.start_new_file_application()
    request.node.user_properties.append(
        ("application_number", f"P-{application_id}")
    )

    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    details_page.complete_initial_application_setup()
    _record_workflow_step(request, 2)

    token = secrets.token_hex(3).upper()
    first_brand_name = f"CRUD Base Brand {token}"
    first_model_number = f"CRUD_BASE_{token}"

    _start_workflow_step(request, 3)
    models_page = ModelsAddSectionPage(page)
    models_page.add_section_with_first_model(
        brand_name=first_brand_name,
        section_header="CRUD base section header",
        section_footer="CRUD base section footer",
        model_number=first_model_number,
        description="CRUD base model",
    )
    _record_workflow_step(request, 3)

    second_brand_name = f"CRUD Second Brand {token}"
    second_model_number = f"CRUD_SECOND_{token}"

    _start_workflow_step(request, 4)
    models_page.add_section_after_with_model(
        brand_name=second_brand_name,
        section_header="CRUD second section header",
        section_footer="CRUD second section footer",
        model_number=second_model_number,
        description="CRUD second model",
    )
    request.node.user_properties.append(
        (
            "model_number_summary",
            f"{first_model_number}, {second_model_number}",
        )
    )
    _record_workflow_step(request, 4)

    crud_page = ModelsSectionCrudPage(page)
    _start_workflow_step(request, 5)
    page.reload(wait_until="domcontentloaded")
    details_page.click_models_tab()
    ApplicationsPage(page).click_all_models()
    page.locator(ModelsSectionCrudPage.SECTION_CARDS).first.wait_for(
        state="visible",
        timeout=30000,
    )
    original_order = crud_page.section_order()
    assert len(original_order) == 2, (
        "Expected exactly two retained model sections before CRUD."
    )
    _capture_screenshot(
        page,
        request,
        application_id,
        5,
        "05_models_before_crud",
    )
    _record_workflow_step(request, 5)

    _start_workflow_step(request, 6)
    crud_page.move_section_after(first_brand_name)
    _capture_screenshot(
        page,
        request,
        application_id,
        6,
        "06_first_section_moved_down",
    )
    _record_workflow_step(request, 6)

    _start_workflow_step(request, 7)
    crud_page.move_section_before(first_brand_name)
    _capture_screenshot(
        page,
        request,
        application_id,
        7,
        "07_first_section_moved_back_up",
    )
    _record_workflow_step(request, 7)

    temporary_token = secrets.token_hex(4)
    temporary_brand_name = f"CRUD Temporary Brand {temporary_token}"
    edited_brand_name = f"{temporary_brand_name} Edited"

    _start_workflow_step(request, 8)
    crud_page.add_section_before(
        anchor_brand_name=first_brand_name,
        new_brand_name=temporary_brand_name,
        section_header="Temporary CRUD section header",
        section_footer="Temporary CRUD section footer",
        model_number=f"CRUD_TEMP_{temporary_token.upper()}",
        description=f"Temporary CRUD model {temporary_token}",
    )
    _capture_screenshot(
        page,
        request,
        application_id,
        8,
        "08_temporary_section_created",
    )
    _record_workflow_step(request, 8)

    _start_workflow_step(request, 9)
    crud_page.edit_section_brand(
        old_brand_name=temporary_brand_name,
        edited_brand_name=edited_brand_name,
    )
    _capture_screenshot(
        page,
        request,
        application_id,
        9,
        "09_temporary_section_edited",
    )
    _record_workflow_step(request, 9)

    _start_workflow_step(request, 10)
    crud_page.delete_section(edited_brand_name)
    assert crud_page.section_order() == original_order
    _capture_screenshot(
        page,
        request,
        application_id,
        10,
        "10_temporary_section_deleted",
    )
    _record_workflow_step(request, 10)

    _start_workflow_step(request, 11)
    logout_page.click_logout()
    page.locator(LoginPage.USERNAME).wait_for(
        state="visible",
        timeout=30000,
    )
    _record_workflow_step(request, 11)

    _start_workflow_step(request, 12)
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("engineer")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()
    _record_workflow_step(request, 12)

    _start_workflow_step(request, 13)
    page.goto(
        f"{settings.base_url}/admin/applications"
        f"#/details/{application_id}/details/",
        wait_until="domcontentloaded",
        timeout=60000,
    )
    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    _record_workflow_step(request, 13)

    _start_workflow_step(request, 14)
    details_page.click_models_tab()
    details_page.list_all_unrecommended_models(
        (first_model_number, second_model_number)
    )
    _record_workflow_step(request, 14)

    _start_workflow_step(request, 15)
    details_page.click_action_items_tab()
    details_page.create_write_up_action_item()
    details_page.validate_write_up_action_item()
    _record_workflow_step(request, 15)

    _start_workflow_step(request, 16)
    details_page.change_application_status("List")
    _record_workflow_step(request, 16)

    _start_workflow_step(request, 17)
    details_page.reload_application_details()
    details_page.wait_until_list_action_enabled()
    _record_workflow_step(request, 17)

    _start_workflow_step(request, 18)
    details_page.list_application()
    _record_workflow_step(request, 18)

    _start_workflow_step(request, 19)
    details_page.open_certificate_preview(application_id)
    details_page.validate_models_in_certificate_preview(
        (first_model_number, second_model_number)
    )
    _record_workflow_step(request, 19)

    _start_workflow_step(request, 20)
    pdf_path = details_page.complete_application(
        download_directory=Path("reports/downloads"),
        application_id=application_id,
    )
    details_page.wait_for_application_completion()
    assert pdf_path.is_file(), f"Completion PDF was not saved: {pdf_path}"
    _record_workflow_step(request, 20)
