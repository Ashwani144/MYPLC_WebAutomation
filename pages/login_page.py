"""Login page object for the IAPMO MyPLC portal."""
from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.logger import get_logger

log = get_logger("login_page")


class LoginPage(BasePage):
    """Encapsulates the MyPLC login screen."""

    URL = "https://qa-myplc.iapmo.org/"
    USERNAME = "#userUserName"
    PASSWORD = "#userLogInPassword"
    SIGN_IN = "button:has-text('Sign in')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open(self) -> "LoginPage":
        self.navigate(self.URL)
        return self

    def login(self, username: str, password: str) -> None:
        log.info("Logging in as %r", username)
        self.page.fill(self.USERNAME, username)
        self.page.fill(self.PASSWORD, password)
        self.page.click(self.SIGN_IN)
        self.page.wait_for_load_state("networkidle")
