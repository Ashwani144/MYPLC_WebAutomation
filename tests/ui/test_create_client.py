"""Create Client UI test — generated from a recorded Playwright MCP session.

Flow:
1. Log in as the Certification Admin.
2. Open the Clients list from the left navigation.
3. Open the "Create New Client" dialog.
4. Fill the form (name, address, phone, website, tax type/id, note) and submit.
5. Assert the new client appears in the Clients list.

A unique client name is generated per run so repeated executions do not collide.
The password is read from the ``MYPLC_PASSWORD`` environment variable.
"""
from __future__ import annotations

import os
import re
import time

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.client_page import ClientPage
from pages.login_page import LoginPage
from utils.logger import get_logger

log = get_logger("test_create_client")


@allure.feature("Clients")
@allure.story("TC03 - Create a new client via the Admin UI")
@pytest.mark.ui
@pytest.mark.regression
def test_create_new_client(app_page: Page, login_data) -> None:
    """Create a client through the UI and verify it is listed."""
    username = login_data["username"]
    password = os.environ["MYPLC_PASSWORD"]

    # 1. Login
    LoginPage(app_page).open().login(username, password)
    expect(app_page).to_have_url(re.compile(r"admin/home"))

    # 2-4. Navigate + create
    client_name = f"Automation_Client_{int(time.time())}"
    clients = ClientPage(app_page)
    clients.open_clients_list().open_create_form()
    clients.create_client(
        name=client_name,
        address="4502 S Steele St, Tacoma, WA 98409, USA",
        phone="3563656550",
        website="https://google.com",
        tax_type="VAT",
        tax_id="121212",
        note="Created by automation",
    )

    # 5. Search for the client using the grid search box and assert it is found
    clients.search_client(client_name)
    expect(
        clients.client_cell(client_name),
        f"Newly created client '{client_name}' was not found in the Clients list",
    ).to_be_visible()
