from __future__ import annotations

import pytest
from playwright.sync_api import Page

from mtplc.pages.application_details_page import ApplicationDetailsPage
from mtplc.pages.clients_page import ClientsPage


def test_open_client_applications_uses_requested_client_id(page: Page) -> None:
    page.route(
        "https://qa-myplc.iapmo.org/admin/clients",
        lambda route: route.fulfill(
            body=(
                '<a ng-click="dc.selectTab(\'applications\')">'
                "Applications</a>"
                '<a class="btn btn-edit btn-primary">'
                "New File Application</a>"
            )
        ),
    )

    ClientsPage(page).open_client_applications("6265")

    assert page.url == (
        "https://qa-myplc.iapmo.org/admin/clients"
        "#/details/6265/applications/"
    )


@pytest.mark.parametrize("certificate_label", ["cUPC", "UPC"])
def test_start_new_file_application_selects_cupc_and_submits(
    page: Page,
    certificate_label: str,
) -> None:
    page.route(
        "https://qa-myplc.iapmo.org/admin/applications**",
        lambda route: route.fulfill(
            body=f"""
        <a class="btn btn-edit btn-primary">New File Application</a>
        <label><input type="checkbox"> {certificate_label}</label>
        <button class="btn btn-primary btn-block"
                onclick="this.dataset.started = 'true';
                         window.location.hash = '/details/12345/details/'">
          Start Application
        </button>
        """
        ),
    )
    page.goto(
        "https://qa-myplc.iapmo.org/admin/applications"
        "#/details/54321/details/"
    )

    clients_page = ClientsPage(page)
    application_id = clients_page.start_new_file_application()

    checkbox_locator = (
        clients_page.CUPC
        if certificate_label == "cUPC"
        else clients_page.UPC_ALIAS
    )
    assert page.locator(checkbox_locator).is_checked()
    assert page.locator(clients_page.START_APPLICATION).get_attribute(
        "data-started"
    ) == "true"
    assert application_id == "12345"


def test_validate_additional_company_model_without_models_tab(
    page: Page,
) -> None:
    model_number = "Additional-Company-Model-123"
    page.route(
        "https://qa-myplc.iapmo.org/admin/applications**",
        lambda route: route.fulfill(
            body=f"""
        <a ng-click="aadc.selectTab('additional-companies')">
          Additional Companies
        </a>
        <a ng-click="aadc.getselectedAddCoTab(0)">Test Company</a>
        <table>
          <thead>
            <tr><th>Additional Company Model Number</th></tr>
          </thead>
          <tbody><tr><td>{model_number}</td></tr></tbody>
        </table>
        """
        ),
    )
    page.goto(
        "https://qa-myplc.iapmo.org/admin/applications"
        "#/details/54321/details/"
    )

    details_page = ApplicationDetailsPage(page)
    details_page.click_additional_companies_tab()
    details_page.validate_additional_companies(
        expected_model_number=model_number,
    )


def test_list_additional_company_models_confirms_before_action(
    page: Page,
) -> None:
    model_number = "Additional-Company-Model-123"
    page.route(
        "https://qa-myplc.iapmo.org/admin/applications**",
        lambda route: route.fulfill(
            body=f"""
        <button onclick="
          document.getElementById('confirmation').hidden = false
        ">List</button>
        <div id="confirmation" role="dialog" hidden>
          <p>Are you sure you want to List all the un-recommended models
             for this Additional Company?</p>
          <button onclick="
            document.getElementById('confirmation').hidden = true
          ">Confirm</button>
        </div>
        <table>
          <thead>
            <tr><th>Additional Company Model Number</th></tr>
          </thead>
          <tbody><tr><td>{model_number}</td></tr></tbody>
        </table>
        """
        ),
    )
    page.goto(
        "https://qa-myplc.iapmo.org/admin/applications"
        "#/details/54321/details/"
    )

    ApplicationDetailsPage(page).list_additional_company_models(
        model_number,
    )
