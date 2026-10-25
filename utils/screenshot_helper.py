"""Helpers for screenshots, video attachment and Allure integration."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from utils.logger import get_logger

log = get_logger("screenshot")

_ROOT = Path(__file__).resolve().parent.parent
_SCREENSHOT_DIR = _ROOT / "reports" / "screenshots"
_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def capture(page: Page, name: str, full_page: bool = True) -> Path:
    """Capture a screenshot and return its path."""
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    path = _SCREENSHOT_DIR / f"{safe_name}_{_timestamp()}.png"
    page.screenshot(path=str(path), full_page=full_page)
    log.info("Screenshot saved: %s", path)
    _attach_to_allure(path, name)
    return path


def _attach_to_allure(path: Path, name: str) -> None:
    try:
        import allure

        allure.attach.file(
            str(path),
            name=name,
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:  # allure optional
        pass


def attach_text(name: str, content: str) -> None:
    try:
        import allure

        allure.attach(content, name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass
