"""Login Page Object for MTPLC."""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Page, expect

from mtplc.config.settings import settings
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Encapsulates MTPLC login interactions and validations."""

    USERNAME = "#userUserName"
    PASSWORD = "#userLogInPassword"

    # Confirmed MTPLC Sign in button XPath
    LOGIN_BUTTON = '//button[@type="submit"]'
    AUTHENTICATED_NAVIGATION = "span[data-i18n='nav.clients']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

        self.username = page.locator(self.USERNAME)
        self.password = page.locator(self.PASSWORD)
        self.login_button = page.locator(self.LOGIN_BUTTON)

    def validate_login_page(self) -> None:
        """Validate that the login page is displayed correctly."""
        expect(self.username).to_be_visible()
        expect(self.password).to_be_visible()
        expect(self.login_button).to_be_visible()
        expect(self.login_button).to_be_enabled()

        LOGGER.info("Login page validation passed")

    def enter_username(self, username: str | None = None) -> None:
        """Enter the MTPLC username."""
        LOGGER.info("Entering username")
        self.username.fill(username or settings.username)

    def enter_password(self, password: str | None = None) -> None:
        """Enter the MTPLC password."""
        LOGGER.info("Entering MTPLC password")
        self.password.fill(password or settings.password)

    def click_login(self) -> None:
        """Click the standard Sign in button."""
        LOGGER.info("Clicking Login")
        self.login_button.click()

    def login(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Perform the complete login operation."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def wait_for_login_navigation(self) -> None:
        """Wait until the authenticated home route and app navigation are ready."""
        expect(self.page).to_have_url(re.compile(r".*/admin/home.*"))
        expect(
            self.page.locator(self.AUTHENTICATED_NAVIGATION)
        ).to_be_visible(timeout=60000)

    def validate_successful_login(self) -> None:
        """Validate successful login using the authenticated home URL."""
        LOGGER.info("Login validation")

        expect(self.page).to_have_url(
            re.compile(r".*/admin/home.*")
        )

        LOGGER.info("Successful login validated")
