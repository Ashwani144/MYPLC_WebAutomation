"""REST API tests demonstrating end-to-end API capabilities.

Covers:
- Basic GET with status + response-time assertions
- JSON schema validation
- Data-driven parametrized requests
- POST/create workflow
- A combined UI + API end-to-end style check

Uses jsonplaceholder.typicode.com as a stable public API sandbox.
"""
from __future__ import annotations

import json
from pathlib import Path

import allure
import pytest

from utils.api_client import APIClient
from utils.logger import get_logger
from utils.schema_validator import validate_schema

log = get_logger("test_api")

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "testdata" / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))


# @allure.feature("API")
# @allure.story("GET post with status and timing assertions")
# @pytest.mark.api
# def test_get_post_status_and_timing(api_client: APIClient, api_data) -> None:
#     case = api_data["get_post"]
#     response = api_client.get(case["endpoint"])
#     (
#         response
#         .assert_status(case["expected_status"])
#         .assert_response_time_under(case["max_response_time_ms"])
#         .assert_json_has("id")
#     )


# @allure.feature("API")
# @allure.story("Response body matches JSON schema")
# @pytest.mark.api
# def test_get_post_schema_validation(api_client: APIClient) -> None:
#     response = api_client.get("/posts/1").assert_ok()
#     validate_schema(response.json(), _load_schema("post_schema.json"))


# @allure.feature("API")
# @allure.story("Data-driven GET requests")
# @pytest.mark.api
# @pytest.mark.parametrize("post_id", [1, 2, 3, 10, 42])
# def test_get_posts_data_driven(api_client: APIClient, post_id: int) -> None:
#     response = api_client.get(f"/posts/{post_id}").assert_status(200)
#     assert response.json()["id"] == post_id


# @allure.feature("API")
# @allure.story("Create post (POST)")
# @pytest.mark.api
# def test_create_post(api_client: APIClient, api_data) -> None:
#     case = api_data["create_post"]
#     response = api_client.post(case["endpoint"], data=case["payload"])
#     response.assert_status(case["expected_status"]).assert_json_has("id")
#     body = response.json()
#     assert body["title"] == case["payload"]["title"]


# @allure.feature("API")
# @allure.story("List users returns a non-empty collection")
# @pytest.mark.api
# def test_list_users(api_client: APIClient, api_data) -> None:
#     case = api_data["list_users"]
#     response = api_client.get(case["endpoint"]).assert_status(case["expected_status"])
#     users = response.json()
#     assert isinstance(users, list) and len(users) >= case["min_count"]
