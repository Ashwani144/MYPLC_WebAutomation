"""Application launch smoke tests for the IAPMO PLC portal."""
from __future__ import annotations

import os
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.login_page import LoginPage
from utils.logger import get_logger

log = get_logger("test_launch")

EXPECTED_TITLE = "IAPMO Product Listing & Certification | PLC"


@allure.feature("Launch")
@allure.story("TC01 - Launch portal and verify page title")
@pytest.mark.ui
@pytest.mark.smoke
def test_tc01_launch_url_and_assert_title(app_page: Page) -> None:
    """TC01: Launch the IAPMO PLC URL and assert the page title."""
    app_page.goto(settings.base_url, wait_until="commit")

    log.info("Launched %s, page title: '%s'", settings.base_url, app_page.title())
    expect(app_page).to_have_title(EXPECTED_TITLE)


@allure.feature("Authentication")
@allure.story("TC02 - Login to home page with R&TAdmin")
@pytest.mark.ui
@pytest.mark.smoke
def test_tc02_login_with_excel_credentials(app_page: Page, login_data) -> None:
    """TC02: Log in using username/password parameterized in the Excel testdata file."""
    username = login_data["username"]
    password = os.environ["MYPLC_PASSWORD"]

    login = LoginPage(app_page).open()
    login.login(username, password)

    log.info("Post-login URL: %s", app_page.url)
    expect(app_page).to_have_url(re.compile(r"admin/home"))
