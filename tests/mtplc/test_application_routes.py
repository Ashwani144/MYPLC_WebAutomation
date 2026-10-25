from __future__ import annotations

import pytest
from playwright.sync_api import Page

from mtplc.config.settings import settings
from mtplc.pages.applications_page import ApplicationsPage


@pytest.mark.parametrize(
    ("method_name", "expected_path"),
    [
        (
            "open_incomplete_applications",
            "/Admin/applications/incomplete#/incomplete",
        ),
        (
            "open_all_applications",
            "/Admin/applications#/all-applications",
        ),
    ],
)
def test_open_application_listing_directly(
    page: Page,
    method_name: str,
    expected_path: str,
) -> None:
    page.route(
        "**/Admin/applications**",
        lambda route: route.fulfill(
            content_type="text/html",
            body=(
                '<label for="entries">Show entries</label>'
                '<select id="entries" aria-label="Show entries">'
                "<option>10</option></select>"
            )
        ),
    )

    method = getattr(ApplicationsPage(page), method_name)
    method()

    assert page.url == f"{settings.base_url.rstrip('/')}{expected_path}"

