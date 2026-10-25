"""Browser & context fixtures for cross-browser + remote/cloud execution.

These fixtures override / extend the defaults from ``pytest-playwright`` so the
browser, launch args, viewport, video, tracing and remote endpoints are all
driven by the central :mod:`config.settings` module.

Supported execution targets (mutually exclusive, resolved from settings):
- Local Chromium / Firefox / WebKit (default)
- Selenium Grid (via ``connect_over_cdp`` when a CDP endpoint is exposed)
- BrowserStack (``connect`` over the BrowserStack Playwright endpoint)
- LambdaTest (``connect`` over the LambdaTest Playwright endpoint)
"""
from __future__ import annotations

import json
import urllib.parse
from typing import Any, Dict, Generator

import pytest
from playwright.sync_api import Browser, BrowserContext, Playwright

from config.settings import settings
from utils.logger import get_logger

log = get_logger("browser_fixtures")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI options for browser selection."""
    group = parser.getgroup("framework")
    group.addoption("--app-browser", action="store", default=None,
                    help="Override browser: chromium | firefox | webkit")
    group.addoption("--app-headed", action="store_true", default=False,
                    help="Run in headed mode regardless of config")
    parser.addoption(
        "--application-number", dest="application_number", default=None,
        help="MTPLC target UI application number, for example P-254482.",
    )
    parser.addoption(
        "--model-workbook-application-number",
        dest="model_workbook_application_number", default=None,
        help="MTPLC populated model workbook application number when different from the UI target.",
    )
    parser.addoption(
        "--phase2-only", action="store_true", default=False,
        help="Run only the MTPLC Vanessa Phase 2 workflow.",
    )
    parser.addoption(
        "--phase2-resume-from-list", action="store_true", default=False,
        help="Resume the MTPLC Phase 2 workflow from List status.",
    )


@pytest.fixture(scope="session")
def framework_settings():
    """Expose the resolved settings object to tests and other fixtures."""
    return settings


@pytest.fixture(scope="session")
def browser_name_resolved(request: pytest.FixtureRequest) -> str:
    cli = request.config.getoption("--app-browser")
    return (cli or settings.browser or "chromium").lower()


def _launch_args(headed: bool) -> Dict[str, Any]:
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    if headed:
        # Open the browser window maximized so it fits the screen.
        args.append("--start-maximized")
    return {
        "headless": not headed,
        "slow_mo": settings.slow_mo,
        "args": args,
    }


def _browserstack_endpoint() -> str:
    caps = {
        "browser": "chrome",
        "os": "Windows",
        "os_version": "11",
        "name": "Playwright BrowserStack Run",
        "build": "playwright-python-build",
        "browserstack.username": settings.browserstack_username,
        "browserstack.accessKey": settings.browserstack_access_key,
    }
    return f"{settings.browserstack_url}?caps={urllib.parse.quote(json.dumps(caps))}"


def _lambdatest_endpoint() -> str:
    caps = {
        "browserName": "Chrome",
        "browserVersion": "latest",
        "LT:Options": {
            "platform": "Windows 11",
            "build": "playwright-python-build",
            "name": "Playwright LambdaTest Run",
            "user": settings.lambdatest_username,
            "accessKey": settings.lambdatest_access_key,
        },
    }
    return f"{settings.lambdatest_url}?capabilities={urllib.parse.quote(json.dumps(caps))}"


@pytest.fixture(scope="session")
def app_browser(
    playwright: Playwright,
    browser_name_resolved: str,
    request: pytest.FixtureRequest,
) -> Generator[Browser, None, None]:
    """Session-scoped browser fixture supporting local, grid and cloud targets."""
    headed = request.config.getoption("--app-headed") or not settings.headless

    if settings.use_browserstack:
        log.info("Connecting to BrowserStack")
        browser = playwright.chromium.connect(_browserstack_endpoint())
    elif settings.use_lambdatest:
        log.info("Connecting to LambdaTest")
        browser = playwright.chromium.connect(_lambdatest_endpoint())
    elif settings.use_selenium_grid:
        log.info("Connecting to Selenium Grid via CDP: %s", settings.selenium_grid_url)
        browser = playwright.chromium.connect_over_cdp(settings.selenium_grid_url)
    else:
        engine = getattr(playwright, browser_name_resolved)
        log.info("Launching local browser: %s (headed=%s)", browser_name_resolved, headed)
        browser = engine.launch(**_launch_args(headed))

    yield browser
    browser.close()


@pytest.fixture
def app_context(
    app_browser: Browser,
    request: pytest.FixtureRequest,
) -> Generator[BrowserContext, None, None]:
    """Function-scoped browser context with viewport, locale, video & tracing."""
    headed = request.config.getoption("--app-headed") or not settings.headless

    context_args: Dict[str, Any] = {
        "locale": settings.locale,
        "timezone_id": settings.timezone,
        "ignore_https_errors": True,
    }
    if headed:
        # Fit the page to the maximized browser window instead of a fixed size.
        context_args["no_viewport"] = True
    else:
        context_args["viewport"] = {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        }
    if settings.record_video:
        context_args["record_video_dir"] = "reports/videos"
        context_args["record_video_size"] = {
            "width": settings.viewport_width,
            "height": settings.viewport_height,
        }

    context = app_browser.new_context(**context_args)

    if settings.record_trace:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    if settings.record_trace:
        context.tracing.stop(path="reports/traces/trace.zip")
    context.close()



