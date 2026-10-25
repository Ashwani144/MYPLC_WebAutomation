"""API testing fixtures.

Provide a Playwright APIRequestContext-backed :class:`APIClient` for REST tests,
independent of the UI browser lifecycle.
"""
from __future__ import annotations

from typing import Generator

import pytest
from playwright.sync_api import Playwright

from config.settings import settings
from utils.api_client import APIClient
from utils.logger import get_logger

log = get_logger("api_fixtures")


@pytest.fixture(scope="session")
def api_request_context(playwright: Playwright):
    """Session-scoped API request context pointed at the configured API base URL."""
    context = playwright.request.new_context(
        base_url=settings.api_base_url,
        extra_http_headers={"Accept": "application/json"},
        timeout=settings.default_timeout,
    )
    log.info("API request context created for %s", settings.api_base_url)
    yield context
    context.dispose()


@pytest.fixture
def api_client(api_request_context) -> APIClient:
    """Fluent API client fixture for REST tests."""
    return APIClient(api_request_context, base_url=settings.api_base_url)


# --------------------------------------------------------------------------- #
# MYPLC (IAPMO) REST API fixtures                                              #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def myplc_api_context(playwright: Playwright):
    """Session-scoped API request context pointed at the MYPLC API base URL."""
    context = playwright.request.new_context(
        base_url=settings.myplc_api_base_url,
        extra_http_headers={"Accept": "application/json"},
        timeout=settings.default_timeout,
    )
    log.info("MYPLC API request context created for %s", settings.myplc_api_base_url)
    yield context
    context.dispose()


@pytest.fixture
def myplc_client(myplc_api_context) -> APIClient:
    """Fluent API client fixture for the MYPLC REST API."""
    return APIClient(myplc_api_context, base_url=settings.myplc_api_base_url)


@pytest.fixture
def myplc_auth_token(myplc_client: APIClient) -> str:
    """Authenticate against the MYPLC API and return a bearer token.

    Skips the test when ``MYPLC_PASSWORD`` is not configured so the suite does
    not fail hard in environments without the secret provisioned.
    """
    if not settings.myplc_password:
        pytest.skip("MYPLC_PASSWORD not configured; set the env var to run MYPLC API tests")

    response = myplc_client.post(
        "/auth/login",
        data={
            "UserUserName": settings.myplc_username,
            "UserLogInPassword": settings.myplc_password,
            "UserSource": settings.myplc_user_source,
        },
    )
    response.assert_status(200)
    token = response.json().get("token")
    assert token, "Login succeeded but no token was returned"
    log.info("MYPLC login successful; token acquired")
    return token
