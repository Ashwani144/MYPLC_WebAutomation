from __future__ import annotations

import pytest
from playwright.sync_api import Page

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

