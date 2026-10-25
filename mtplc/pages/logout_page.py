"""Logout Page Object for MTPLC."""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Page, expect

from mtplc.config.settings import settings
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class LogoutPage(BasePage):
    """Encapsulates logout interaction and validation."""

    # Confirmed MTPLC logout locator
    LOGOUT_LOCATOR = "xpath=//a[normalize-space()='Log out']"

    def locate_logout(self):
        """Locate the Logout control."""
        return self.page.locator(self.LOGOUT_LOCATOR)

    def click_logout(self) -> None:
        """Click the Logout control."""
        LOGGER.info("Clicking Logout")

        logout_control = self.locate_logout()

        expect(logout_control).to_be_visible()
        expect(logout_control).to_be_enabled()

        logout_control.click()

    def wait_for_logout_completion(self) -> None:
        """Wait for logout processing to complete."""
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_load_state("networkidle")

    def validate_successful_logout(self) -> None:
        """Validate successful logout by checking the login page URL."""
        LOGGER.info("Logout validation")

        expect(self.page).to_have_url(
            re.compile(rf"{re.escape(settings.base_url.rstrip('/'))}/?$")
        )

        LOGGER.info("Successful logout validated")

        self.take_screenshot("04_after_logout.png")

