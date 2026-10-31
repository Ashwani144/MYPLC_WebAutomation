import secrets
from pathlib import Path

import pytest

from mtplc.config.settings import settings
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.clients_page import ClientsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.models_add_section_page import ModelsAddSectionPage


SCENARIO_NAME = "Add Section via Models Tab to Complete Application"
SCENARIO_STEPS = [
    "Vanessa: log in successfully",
    "Vanessa: create a cUPC application and complete initial setup",
    "Vanessa: add the first model section and verify the model",
    "Vanessa: add the second model section and verify the model",
    "Vanessa: log out successfully",
    "Anish.Desai: log in successfully",
    "Anish.Desai: reopen the same application and verify its details",
    "Anish.Desai: list both models and verify their recommendation state",
    "Anish.Desai: create and verify the Write Up Action Item",
    "Anish.Desai: change application status to List and save",
    "Anish.Desai: reload and wait until the List action is enabled",
    "Anish.Desai: confirm List and accept confirmation dialogs",
    "Anish.Desai: verify both models in Certificate Preview",
    "Anish.Desai: complete the application and verify the PDF and redirect",
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


@pytest.mark.regression
def test_create_application_add_sections_list_and_complete(
    page,
    request: pytest.FixtureRequest,
) -> None:
    """Create an application, add models, list it, verify Preview, and complete it."""
    request.node.user_properties.append(
        ("workflow_scenario_name", SCENARIO_NAME)
    )
    request.node.user_properties.append(
        ("workflow_scenario_steps", SCENARIO_STEPS)
    )

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    clients_page = ClientsPage(page)

    # Sign in as Vanessa and create the application.
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

    # Add the first section and model.
    _start_workflow_step(request, 3)
    model_number = f"ModelTest_{secrets.randbelow(9000) + 1000}"

    models_page = ModelsAddSectionPage(page)
    models_page.add_section_with_first_model(
        brand_name="Automated Brand Name",
        section_header="Automated section header",
        section_footer="Automated section footer",
        model_number=model_number,
        description="Testing",
    )
    _record_workflow_step(request, 3)

    # Add the second section and model.
    _start_workflow_step(request, 4)
    model_number_after = (
        f"Automate_Model_Number_{secrets.randbelow(9000) + 1000}"
    )

    models_page.add_section_after_with_model(
        brand_name="Automation Add Section After Brand Name",
        section_header="Automation Add Section After Section Header",
        section_footer="Automation Add Section After Section Footer",
        model_number=model_number_after,
        description="Testing After add",
    )
    request.node.user_properties.append(
        (
            "model_number_summary",
            f"{model_number}, {model_number_after}",
        )
    )
    _record_workflow_step(request, 4)

    # Log out Vanessa and sign in as Anish.
    _start_workflow_step(request, 5)
    page.get_by_text("Log out", exact=True).click(timeout=15000)
    _record_workflow_step(request, 5)

    _start_workflow_step(request, 6)
    launch_page.open()
    login_page.validate_login_page()

    # Use Anish.Desai's configured engineer credentials for the review steps.
    username, password = settings.credentials_for("engineer")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()
    _record_workflow_step(request, 6)

    # Reopen the same application using its numeric ID, without a "P-" prefix.
    _start_workflow_step(request, 7)
    page.goto(
        f"{settings.base_url.rstrip('/')}/admin/applications"
        f"#/details/{application_id}/details/",
        wait_until="domcontentloaded",
    )

    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    _record_workflow_step(request, 7)

    # List the models.
    _start_workflow_step(request, 8)
    details_page.click_models_tab()
    details_page.list_all_unrecommended_models(
        (model_number, model_number_after)
    )
    _record_workflow_step(request, 8)

    # Create and verify the Write Up action item.
    _start_workflow_step(request, 9)
    details_page.click_action_items_tab()
    details_page.create_write_up_action_item()
    details_page.validate_write_up_action_item()
    _record_workflow_step(request, 9)

    # Save the status, reload the application, and wait for List to be enabled.
    _start_workflow_step(request, 10)
    details_page.change_application_status("List")
    _record_workflow_step(request, 10)

    _start_workflow_step(request, 11)
    details_page.reload_application_details()
    details_page.wait_until_list_action_enabled()
    _record_workflow_step(request, 11)

    # Handles the List confirmation and any optional Yes popup.
    _start_workflow_step(request, 12)
    details_page.list_application()
    _record_workflow_step(request, 12)

    # Validate both models in Certificate Preview before completing.
    _start_workflow_step(request, 13)
    details_page.open_certificate_preview(application_id)
    details_page.validate_models_in_certificate_preview(
        (model_number, model_number_after)
    )
    _record_workflow_step(request, 13)

    # Complete the application and wait for the redirect.
    _start_workflow_step(request, 14)
    pdf_path = details_page.complete_application(
        download_directory=Path("reports/downloads"),
        application_id=application_id,
    )
    details_page.wait_for_application_completion()

    assert pdf_path.is_file(), f"Completion PDF was not saved: {pdf_path}"
    _record_workflow_step(request, 14)