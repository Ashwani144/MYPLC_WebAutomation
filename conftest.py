"""Root conftest — wires fixtures, custom reporter hooks, on-failure artifacts,
Allure environment metadata and end-of-session notifications.
"""
from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

# Re-export all custom fixtures so tests can request them directly.
from fixtures import *  # noqa: F401,F403
# pytest_addoption lives in browser_fixtures; import it so options register.
from fixtures.browser_fixtures import pytest_addoption  # noqa: F401

from config.settings import settings
from utils import screenshot_helper
from utils.logger import get_logger
from utils.notifier import notify_slack, notify_teams

# Register the local custom reporter as a plugin here (instead of via the
# ``-p`` flag in pytest.ini) so it loads after the project root is on sys.path.
# This lets ``pytest`` work the same as ``python -m pytest``.
pytest_plugins = ["reporters.custom_reporter"]

log = get_logger("conftest")


def _remap_legacy_test_paths(config: pytest.Config) -> None:
    """Let ``pytest tests/test_x.py`` resolve to ``tests/mtplc/test_x.py``.

    Keeps the legacy MTPLCAutomation commands working after the merge.
    """
    rewritten = []
    for arg in config.args:
        path_part, sep, rest = arg.partition("::")
        p = Path(path_part)
        if p.parent.name == "tests" and p.suffix == ".py" and not p.exists():
            alt = p.parent / "mtplc" / p.name
            if alt.exists():
                arg = f"{alt}{sep}{rest}"
        rewritten.append(arg)
    config.args[:] = rewritten

_REPORTS = Path("reports")
for sub in ("screenshots", "videos", "traces", "logs", "allure-results"):
    (_REPORTS / sub).mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Test result plumbing: expose call outcome to fixtures for on-failure logic.  #
# --------------------------------------------------------------------------- #
import html as _html


def _suite_of(item: pytest.Item) -> str:
    """Classify a test into a report suite based on its markers."""
    markers = {m.name for m in item.iter_markers()}
    if "ui" in markers:
        return "UI"
    if "api" in markers:
        return "API"
    if "visual" in markers:
        return "Visual"
    return "Other"


def _story_of(item: pytest.Item) -> str:
    """Return the @allure.story text for a test, if one is set.

    ``@allure.story("...")`` is recorded as an ``allure_label`` marker with
    ``label_type='story'``; fall back to the test function name otherwise.
    """
    for marker in item.iter_markers(name="allure_label"):
        if marker.kwargs.get("label_type") == "story" and marker.args:
            return str(marker.args[0])
    return item.name


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    # Stash values on the report so the pytest-html table hooks can render them.
    report.suite = _suite_of(item)
    report.story = _story_of(item)


# --------------------------------------------------------------------------- #
# pytest-html: add a sortable "Suite" column (group UI vs API) and a "Title"   #
# column showing the @allure.story text for each test.                         #
# --------------------------------------------------------------------------- #
def pytest_html_results_table_header(cells) -> None:
    cells.insert(1, '<th class="sortable suite" data-column-type="suite">Suite</th>')
    cells.insert(2, '<th class="sortable" data-column-type="story">Title</th>')


def pytest_html_results_table_row(report, cells) -> None:
    cells.insert(1, f'<td class="col-suite">{getattr(report, "suite", "Other")}</td>')
    story = _html.escape(getattr(report, "story", "") or "")
    cells.insert(2, f'<td class="col-story">{story}</td>')




@pytest.fixture(autouse=True)
def _capture_on_failure(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Automatically capture a screenshot when a UI test fails."""
    yield
    if not settings.screenshot_on_failure:
        return
    report = getattr(request.node, "rep_call", None)
    if report is None or not report.failed:
        return
    page = request.node.funcargs.get("app_page")
    if page is None or page.is_closed():
        return
    try:
        screenshot_helper.capture(page, f"FAILURE_{request.node.name}")
    except Exception as exc:  # best-effort
        log.warning("Failed to capture failure screenshot: %s", exc)


# --------------------------------------------------------------------------- #
# Allure environment metadata                                                 #
# --------------------------------------------------------------------------- #
def pytest_configure(config: pytest.Config) -> None:
    _remap_legacy_test_paths(config)
    config.addinivalue_line("markers", "smoke: quick sanity checks")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "ui: browser UI tests")
    config.addinivalue_line("markers", "api: REST API tests")
    config.addinivalue_line("markers", "visual: visual regression tests")

    env_file = _REPORTS / "allure-results" / "environment.properties"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(
        "\n".join(
            [
                f"Environment={settings.environment}",
                f"BaseURL={settings.base_url}",
                f"Browser={settings.browser}",
                f"Headless={settings.headless}",
                f"Workers={settings.workers}",
            ]
        ),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# End-of-session summary + notifications                                       #
# --------------------------------------------------------------------------- #
def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    summary = f"Playwright run on '{settings.environment}': {passed} passed, {failed} failed, {skipped} skipped"
    log.info(summary)

    if settings.slack_webhook_url:
        notify_slack(summary, passed, failed, skipped)
    if settings.teams_webhook_url:
        notify_teams(summary, passed, failed, skipped)
