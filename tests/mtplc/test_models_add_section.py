import secrets

import pytest

from mtplc.config.settings import settings
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.clients_page import ClientsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.models_add_section_page import ModelsAddSectionPage


@pytest.mark.regression
def test_create_application_add_section_with_first_model(page):
    """Create an application, add a section, and save its first model."""
    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    clients_page = ClientsPage(page)

    # Launch the application and log in as Vanessa.
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("vanessa")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    # Open the configured client's Applications page and create an application.
    clients_page.open_client_applications(ClientsPage.CLIENT_ID)
    application_id = clients_page.start_new_file_application()

    # Use the ID returned by ClientsPage; no application number is hardcoded.
    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    details_page.complete_initial_application_setup()

    # Add the section and its first model.
    model_number = f"ModelTest_{secrets.randbelow(9000) + 1000}"

    models_page = ModelsAddSectionPage(page)
    models_page.add_section_with_first_model(
        brand_name="Automated Brand Name",
        section_header="Automated section header",
        section_footer="Automated section footer",
        model_number=model_number,
        description="Testing",
    )
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