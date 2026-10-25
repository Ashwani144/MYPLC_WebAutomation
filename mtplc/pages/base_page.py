"""Shared Page Object functionality."""

from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Page

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def take_screenshot(self, filename: str) -> Path:
        """Save a full-page screenshot and return its path."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOTS_DIR / filename
        self.page.screenshot(path=str(path), full_page=True)
        LOGGER.info("Screenshot saved: %s", path)
        return path

