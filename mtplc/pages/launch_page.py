
import logging
from pathlib import Path

from playwright.sync_api import expect

from mtplc.config.settings import settings

LOGGER = logging.getLogger(__name__)


class LaunchPage:
    """Open the application and capture launch diagnostics."""

    def __init__(self, page):
        self.page = page

    def open(self) -> None:
        """Navigate to the application and inspect the login page."""

        LOGGER.info("Launching application: %s", settings.base_url)

        self.page.on(
            "requestfailed",
            lambda request: LOGGER.error(
                "Request failed: %s | %s",
                request.url,
                request.failure,
            ),
        )

        self.page.on(
            "pageerror",
            lambda error: LOGGER.error(
                "Browser JavaScript error: %s",
                error,
            ),
        )

        self.page.on(
            "console",
            lambda message: LOGGER.error(
                "Browser console error: %s",
                message.text,
            )
            if message.type == "error"
            else None,
        )

        try:
            self.page.set_default_navigation_timeout(60000)

            response = self.page.goto(
                settings.base_url,
                wait_until="commit",
                timeout=60000,
            )

            LOGGER.info(
                "HTTP status: %s",
                response.status if response else "No response",
            )
            LOGGER.info("Current URL: %s", self.page.url)

            LOGGER.info("Page title: %s", self.page.title())

            # Save diagnostics before checking the login selector.
            diagnostic_dir = Path("reports") / "diagnostics"
            diagnostic_dir.mkdir(parents=True, exist_ok=True)

            # Wait for the expected username field to appear.
            username = self.page.locator("#userUserName")

            try:
                username.wait_for(
                    state="visible",
                    timeout=60000,
                )
            except Exception:
                LOGGER.warning(
                    "Username selector #userUserName was not visible. "
                    "Inspecting the current page."
                )

            self.page.screenshot(
                path=str(diagnostic_dir / "launch_page.png"),
                full_page=True,
            )

            html = self.page.content()
            (diagnostic_dir / "launch_page.html").write_text(
                html,
                encoding="utf-8",
            )

            LOGGER.info(
                "Saved page HTML and screenshot to %s",
                diagnostic_dir.resolve(),
            )

            if username.count() == 0:
                LOGGER.error(
                    "Username selector #userUserName was not found."
                )
                LOGGER.error("Current URL: %s", self.page.url)

                raise AssertionError(
                    "Login username field is missing from the page. "
                    "Check reports/diagnostics/launch_page.html "
                    "and launch_page.png."
                )

            LOGGER.info("Login username field found successfully.")

        except Exception:
            LOGGER.exception("Application launch failed")
            raise

    def validate_login_page(self) -> None:
        """Validate that the login controls are available."""
        expect(self.page.locator("#userUserName")).to_be_visible()
        expect(self.page.locator("#userLogInPassword")).to_be_visible()
        expect(self.page.locator("button[type='submit']")).to_be_visible()
        LOGGER.info("Login page validation passed")
