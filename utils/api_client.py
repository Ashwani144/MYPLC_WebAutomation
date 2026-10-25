"""Lightweight REST API client built on Playwright's APIRequestContext.

Wraps common HTTP verbs with logging, response-time capture, and convenient
assertions. This is the Python/Playwright equivalent of a RestAssured-style
fluent API client and is used by the API test suite.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from playwright.sync_api import APIRequestContext, APIResponse

from utils.logger import get_logger

log = get_logger("api_client")


class APIResponseWrapper:
    """Convenience wrapper exposing status, timing, body and fluent asserts."""

    def __init__(self, response: APIResponse, elapsed_ms: float) -> None:
        self._response = response
        self.elapsed_ms = elapsed_ms

    @property
    def status(self) -> int:
        return self._response.status

    @property
    def ok(self) -> bool:
        return self._response.ok

    @property
    def headers(self) -> Dict[str, str]:
        return self._response.headers

    def json(self) -> Any:
        return self._response.json()

    def text(self) -> str:
        return self._response.text()

    # ---- fluent assertions -------------------------------------------------
    def assert_status(self, expected: int) -> "APIResponseWrapper":
        assert self.status == expected, (
            f"Expected status {expected} but got {self.status}"
        )
        return self

    def assert_ok(self) -> "APIResponseWrapper":
        assert self.ok, f"Expected 2xx response but got {self.status}"
        return self

    def assert_response_time_under(self, max_ms: float) -> "APIResponseWrapper":
        assert self.elapsed_ms <= max_ms, (
            f"Response time {self.elapsed_ms:.0f}ms exceeded limit {max_ms:.0f}ms"
        )
        return self

    def assert_json_has(self, key: str) -> "APIResponseWrapper":
        body = self.json()
        assert isinstance(body, dict) and key in body, (
            f"Expected key '{key}' in JSON response"
        )
        return self


class APIClient:
    """Thin wrapper over Playwright's APIRequestContext."""

    def __init__(self, request_context: APIRequestContext, base_url: str = "") -> None:
        self._ctx = request_context
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _timed(self, method: str, url: str, **kwargs: Any) -> APIResponseWrapper:
        log.info("API %s %s", method.upper(), url)
        start = time.perf_counter()
        response = getattr(self._ctx, method)(url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.info("API %s %s -> %s (%.0f ms)", method.upper(), url, response.status, elapsed_ms)
        return APIResponseWrapper(response, elapsed_ms)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> APIResponseWrapper:
        return self._timed("get", self._url(path), params=params, **kwargs)

    def post(self, path: str, data: Any = None, **kwargs: Any) -> APIResponseWrapper:
        return self._timed("post", self._url(path), data=data, **kwargs)

    def put(self, path: str, data: Any = None, **kwargs: Any) -> APIResponseWrapper:
        return self._timed("put", self._url(path), data=data, **kwargs)

    def patch(self, path: str, data: Any = None, **kwargs: Any) -> APIResponseWrapper:
        return self._timed("patch", self._url(path), data=data, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> APIResponseWrapper:
        return self._timed("delete", self._url(path), **kwargs)
