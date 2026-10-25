"""Page fixtures — build on the browser/context fixtures to provide ready pages
and initialized page objects for dependency injection into tests.
"""
from __future__ import annotations

from typing import Generator

import pytest
from playwright.sync_api import BrowserContext, Page

from utils.logger import get_logger

log = get_logger("page_fixtures")


@pytest.fixture
def app_page(app_context: BrowserContext) -> Generator[Page, None, None]:
    """A fresh page for each test, derived from the configured context."""
    page = app_context.new_page()
    log.debug("New page created")
    yield page
    if not page.is_closed():
        page.close()
