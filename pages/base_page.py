"""BasePage — shared behaviour for every page object.

Encapsulates common interactions (navigation, waiting, clicking, typing) and
utility methods (collecting links/images) so concrete page objects stay small
and focused on element locators.
"""
from __future__ import annotations

from typing import List

from playwright.sync_api import Locator, Page, expect

from config.settings import settings
from utils.logger import get_logger

log = get_logger("base_page")


class BasePage:
    """Root of the page-object hierarchy."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.page.set_default_timeout(settings.default_timeout)
        self.page.set_default_navigation_timeout(settings.navigation_timeout)

    # ---- navigation --------------------------------------------------------
    def navigate(self, url: str = "") -> None:
        target = url or settings.base_url
        log.info("Navigating to %s", target)
        self.page.goto(target, wait_until="domcontentloaded")

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded")

    def title(self) -> str:
        return self.page.title()

    def current_url(self) -> str:
        return self.page.url

    # ---- interactions ------------------------------------------------------
    def click(self, selector: str) -> None:
        log.debug("Click %s", selector)
        self.page.click(selector)

    def type_text(self, selector: str, text: str) -> None:
        log.debug("Type %r into %s", text, selector)
        self.page.fill(selector, text)

    def press(self, selector: str, key: str) -> None:
        self.page.press(selector, key)

    def wait_for(self, selector: str, state: str = "visible") -> Locator:
        locator = self.page.locator(selector)
        locator.wait_for(state=state)  # type: ignore[arg-type]
        return locator

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).first.is_visible()

    def text_of(self, selector: str) -> str:
        return self.page.locator(selector).first.inner_text()

    # ---- page-wide helpers -------------------------------------------------
    def get_all_links(self) -> List[str]:
        """Return every non-empty, non-anchor href on the page."""
        hrefs = self.page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href)",
        )
        return [h for h in hrefs if h and not h.startswith("javascript:") and "#" not in h[-1:]]

    def get_image_count(self) -> int:
        return self.page.locator("img").count()

    def get_all_image_sources(self) -> List[str]:
        return self.page.eval_on_selector_all("img", "els => els.map(e => e.src)")
