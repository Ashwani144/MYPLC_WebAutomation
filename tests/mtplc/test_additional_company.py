"""End-to-end test for an Additional Company application."""

import secrets
from pathlib import Path

import pytest

from mtplc.config.settings import settings
from mtplc.pages.additional_company_page import AdditionalCompanyPage
from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.clients_page import ClientsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.regression
def test_create_application_additional_company_and_complete(page):
    """Create an application, add an Additional Company model, and complete it."""
    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    clients_page = ClientsPage(page)

    # Phase 1: Vanessa creates the application and adds its company/model.
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("vanessa")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    clients_page.open_client_applications(ClientsPage.CLIENT_ID)
    application_id = clients_page.start_new_file_application()

    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)
    details_page.complete_initial_application_setup()

    company_number = f"{secrets.randbelow(10000):04d}"
    brand_number = f"{secrets.randbelow(10000):04d}"
    company_name = f"Additional Company Testing {company_number}"
    brand_name = f"Additional Brand Testing {brand_number}"

    main_model_number = f"AddCompany_Main_{secrets.randbelow(9000) + 1000}"
    additional_company_model_number = (
        f"AddCompany_Model_{secrets.randbelow(9000) + 1000}"
    )

    additional_company_page = AdditionalCompanyPage(page)
    additional_company_page.add_additional_company_with_model(
        company_name=company_name,
        brand_name=brand_name,
        section_header="Additional Section Header Testing",
        section_footer="Additional Section Footer Testing",
        main_model_number=main_model_number,
        additional_company_model_number=additional_company_model_number,
        additional_company_description="Testing Additional Company",
    )

    # Log out Vanessa.
    page.get_by_text("Log out", exact=True).click(timeout=15000)

    # Phase 2: Anish.Desai verifies the Additional Company model and completes it.
    launch_page.open()
    login_page.validate_login_page()

    # In this project, the "engineer" credentials are Anish.Desai's.
    username, password = settings.credentials_for("engineer")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    page.goto(
        f"{settings.base_url.rstrip('/')}/admin/applications"
        f"#/details/{application_id}/details/",
        wait_until="domcontentloaded",
    )

    details_page = ApplicationDetailsPage(page)
    details_page.validate_application_details(application_id)

    details_page.click_additional_companies_tab()
    details_page.validate_additional_companies(
        expected_model_number=additional_company_model_number,
    )
    details_page.list_additional_company_models(
        additional_company_model_number,
    )

    details_page.click_action_items_tab()
    details_page.create_write_up_action_item()
    details_page.validate_write_up_action_item()

    details_page.change_application_status("List")
    details_page.reload_application_details()
    details_page.wait_until_list_action_enabled()
    details_page.list_application()

    details_page.open_certificate_preview(application_id)
    details_page.validate_models_in_certificate_preview(
        (
            main_model_number,
            additional_company_model_number,
        )
    )

    pdf_path = details_page.complete_application(
        download_directory=Path("reports/downloads"),
        application_id=application_id,
    )
    details_page.wait_for_application_completion()
    assert pdf_path.is_file(), f"Completion PDF was not saved: {pdf_path}"

    # Log out Anish after completion.
    page.get_by_text("Log out", exact=True).click(timeout=15000)

    # Phase 3: R&TPlumbingCertificationAdmin signs in after completion.
    launch_page.open()
    login_page.validate_login_page()

    username, password = settings.credentials_for("admin")
    login_page.login(username=username, password=password)
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()