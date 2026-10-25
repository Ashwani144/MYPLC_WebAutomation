"""Application launch page object."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, expect

from mtplc.config.settings import settings
from mtplc.pages.base_page import BasePage

LOGGER = logging.getLogger(__name__)


class LaunchPage(BasePage):
    """Responsible for opening and validating application availability."""

    def open(self) -> None:
        LOGGER.info("Launching application")
        self.page.goto(settings.base_url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        self.take_screenshot("01_launch.png")

    def validate_login_page(self) -> None:
        """Validate that the supplied login controls are available."""
        expect(self.page.locator("#userUserName")).to_be_visible()
        expect(self.page.locator("#userLogInPassword")).to_be_visible()
        expect(self.page.locator('xpath=//*[@id="signin"]/div/div[3]/button')).to_be_visible()
        LOGGER.info("Login page validation passed")

