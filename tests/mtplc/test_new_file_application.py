import re

import pytest

from mtplc.config.settings import settings
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.clients_page import ClientsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.models_add_section_page import ModelsAddSectionPage


CLIENT_ID = "6265"


@pytest.mark.smoke
def test_phase_zero_create_new_file_application(page, request):
    """Create and set up an application, then open Models → Add Section."""
    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    clients_page = ClientsPage(page)

    # Launch and log in as Vanessa.
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("vanessa")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    # Resume a specified application, or create a new one for this run.
    application_number = request.config.getoption("application_number")

    if application_number:
        match = re.fullmatch(
            r"P-(\d+)",
            application_number.strip(),
            re.IGNORECASE,
        )
        if match is None:
            pytest.fail(
                "--application-number must use the format P-<digits> "
                "when resuming Phase 0."
            )

        application_id = match.group(1)
        page.goto(
            f"{settings.base_url.rstrip('/')}/admin/applications"
            f"#/details/{application_id}/details/",
            wait_until="commit",
        )
    else:
        clients_page.open_client_applications(CLIENT_ID)
        application_id = clients_page.start_new_file_application()

    # Create the page object only after the application page is open.
    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    details_page.complete_initial_application_setup()

    # Continue with the Models scenario.
    models_page = ModelsAddSectionPage(page)
    models_page.open_add_section()