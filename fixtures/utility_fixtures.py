"""Utility fixtures — screenshots, video paths and other common helpers.

The ``screenshot`` fixture exposes a callable so tests can capture named
screenshots on demand; automatic on-failure capture is handled in ``conftest.py``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from playwright.sync_api import Page

from utils import screenshot_helper
from utils.logger import get_logger

log = get_logger("utility_fixtures")


@pytest.fixture
def screenshot(app_page: Page) -> Callable[[str], Path]:
    """Return a callable that captures a named full-page screenshot."""

    def _capture(name: str, full_page: bool = True) -> Path:
        return screenshot_helper.capture(app_page, name, full_page=full_page)

    return _capture


@pytest.fixture
def logger():
    """Expose a test-scoped logger."""
    return get_logger("test")
