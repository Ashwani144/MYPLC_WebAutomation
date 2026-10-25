"""MYPLC (IAPMO) client-flow REST API tests.

Python/Playwright translation of the Postman collection
``testdata/Client Flow.postman_collection.json`` ("MYPLC Client Flow").

The collection is a stateful end-to-end journey run by an authenticated
Certification Admin:

1. Log in and obtain a bearer token.
2. Create a new client.
3. Create a primary contact for that client.
4. Create a billing contact for that client.
5. Create an application discount rule.
6. Create a file-level client alert.
7. Read the client back and verify the persisted details.
8. Delete the client (teardown).

Credentials are never hardcoded: the login password is read from the
``MYPLC_PASSWORD`` environment variable (see ``config/settings.py``). When it is
absent the whole suite is skipped rather than failing hard.
"""
from __future__ import annotations

import copy
import json
import random
import string
from datetime import date
from pathlib import Path
from typing import Any, Dict, Generator, List

import allure
import pytest

from config.settings import settings
from utils.api_client import APIClient
from utils.logger import get_logger
from utils.schema_validator import validate_schema

log = get_logger("test_client_flow")

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "testdata" / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _rand_suffix(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _rand_name() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=1)) + "".join(
        random.choices(string.ascii_lowercase, k=7)
    )


def _rand_phone() -> str:
    return str(random.randint(1_000_000_000, 9_999_999_999))


def _auth(token: str) -> Dict[str, str]:
    return {"Authorization": token}


def _assert_json_content_type(response) -> None:
    content_type = (response.headers.get("content-type") or "").lower()
    assert "application/json" in content_type, (
        f"Expected an application/json Content-Type but got '{content_type}'"
    )


# --------------------------------------------------------------------------- #
# Teardown safety net: delete any clients created during a test.              #
# --------------------------------------------------------------------------- #
@pytest.fixture
def created_clients(
    myplc_client: APIClient, myplc_auth_token: str
) -> Generator[List[Any], None, None]:
    """Track created client ids and guarantee their deletion after the test."""
    ids: List[Any] = []
    yield ids
    for client_id in ids:
        try:
           myplc_client.delete(f"/clients/{client_id}", headers=_auth(myplc_auth_token))
           log.info("Cleaned up leftover client %s", client_id)
        except Exception as exc:  # best-effort cleanup
            log.warning("Failed to clean up client %s: %s", client_id, exc)


# --------------------------------------------------------------------------- #
# 1. Login                                                                    #
# --------------------------------------------------------------------------- #
@allure.feature("MYPLC API")
@allure.story("Authentication")
@pytest.mark.api
def test_login_returns_valid_token(
    myplc_client: APIClient, myplc_auth_token: str, client_flow_data
) -> None:
    """Re-authenticate and assert the login contract (status, timing, schema)."""
    response = myplc_client.post(
        "/auth/login",
        data={
            "UserUserName": settings.myplc_username,
            "UserLogInPassword": settings.myplc_password,
            "UserSource": settings.myplc_user_source,
        },
    )

    response.assert_status(200).assert_response_time_under(
        client_flow_data["thresholds_ms"]["login"]
    )
    _assert_json_content_type(response)

    body = response.json()
    validate_schema(body, _load_schema("login_schema.json"))
    assert body["token"], "Token should not be empty"
    assert isinstance(body["user"], dict)
    for field in ("userName", "email", "firstName", "lastName"):
        assert field in body["user"], f"Login user object missing '{field}'"


# --------------------------------------------------------------------------- #
# 2-8. End-to-end client lifecycle                                            #
# --------------------------------------------------------------------------- #
@allure.feature("MYPLC API")
@allure.story("Client lifecycle end-to-end")
@pytest.mark.api
@pytest.mark.regression
def test_client_lifecycle_flow(
    myplc_client: APIClient,
    myplc_auth_token: str,
    client_flow_data: Dict[str, Any],
    created_clients: List[Any],
) -> None:
    """Full create -> contacts -> discount -> alert -> read -> delete journey."""
    token = myplc_auth_token
    headers = _auth(token)
    thresholds = client_flow_data["thresholds_ms"]

    # --- 2. Create new client ------------------------------------------------
    client_name = f"API_Client_{_rand_suffix()}"
    with allure.step("Create new client"):
        client_payload = copy.deepcopy(client_flow_data["client"])
        client_payload["name"] = client_name
        client_payload["phoneNumber"] = _rand_phone()

        response = myplc_client.post("/clients", data=client_payload, headers=headers)
        response.assert_status(201).assert_response_time_under(thresholds["create"])
        assert response.text().strip(), "Create-client response body should not be empty"

        client_id = response.json()
        created_clients.append(client_id)
        log.info("Created client %s (%s)", client_id, client_name)

    contact_url = f"/clients/{client_id}/create-contact/{client_id}"

    # --- 3. Create primary contact ------------------------------------------
    primary = {
        "firstName": _rand_name(),
        "lastName": _rand_name(),
        "phoneOne": _rand_phone(),
    }
    primary["email"] = f"{primary['firstName']}{primary['lastName']}@gmail.com"
    with allure.step("Create primary contact"):
        payload = copy.deepcopy(client_flow_data["contact"])
        payload.update(
            {
                "relationships": [],
                "firstName": primary["firstName"],
                "lastName": primary["lastName"],
                "email": primary["email"],
                "phoneOne": primary["phoneOne"],
                "contactType": "Primary",
            }
        )
        response = myplc_client.post(contact_url, data=payload, headers=headers)
        response.assert_status(201).assert_response_time_under(thresholds["create"])
        assert response.text().strip(), "Primary-contact response body should not be empty"

    # --- 4. Create billing contact ------------------------------------------
    billing = {
        "firstName": _rand_name(),
        "lastName": _rand_name(),
        "phoneOne": _rand_phone(),
    }
    billing["email"] = f"{billing['firstName']}{billing['lastName']}@gmail.com"
    with allure.step("Create billing contact"):
        payload = copy.deepcopy(client_flow_data["contact"])
        payload.update(
            {
                "relationships": [],
                "firstName": billing["firstName"],
                "lastName": billing["lastName"],
                "email": billing["email"],
                "phoneOne": billing["phoneOne"],
                "contactType": "Billing",
            }
        )
        response = myplc_client.post(contact_url, data=payload, headers=headers)
        response.assert_status(201).assert_response_time_under(thresholds["create"])
        assert response.text().strip(), "Billing-contact response body should not be empty"

    # --- 5. Create application discount rule ---------------------------------
    # NOTE: Disabled — the QA API returns 409 Conflict for this step.
    with allure.step("Create application discount rule"):
        today = date.today().isoformat()
        rule = copy.deepcopy(client_flow_data["discount_rule"])
        rule["clientId"] = client_id
        rule["name"] = f"Application Discount Rule{_rand_suffix()}"
        rule["startDate"] = f"{today}T18:30:00.000Z"
        rule["endDate"] = f"{today}T23:30:00.000Z"
        response = myplc_client.post("/discount-rules", data=rule, headers=headers)
        response.assert_status(201).assert_response_time_under(thresholds["create"])
        assert response.text().strip(), "Discount-rule response body should not be empty"

    # --- 6. Create file-level client alert -----------------------------------
    with allure.step("Create file-level client alert"):
        alert_cfg = client_flow_data["alert"]
        alert_payload = {
            "isFile": alert_cfg["isFile"],
            "alert": {"message": alert_cfg["message"]},
            "clientId": client_id,
        }
        response = myplc_client.post("/client-alerts", data=alert_payload, headers=headers)
        response.assert_status(201).assert_response_time_under(thresholds["create"])
        assert response.text().strip(), "Client-alert response body should not be empty"

    # --- 7. Read client details and verify persistence -----------------------
    with allure.step("Read client details and verify"):
        response = myplc_client.get(f"/clients/{client_id}", headers=headers)
        response.assert_status(200).assert_response_time_under(thresholds["read"])
        _assert_json_content_type(response)

        body = response.json()
        validate_schema(body, _load_schema("client_schema.json"))

        assert body["id"] == client_id, "Returned client id does not match created id"
        assert body["name"] == client_name, "Returned client name does not match"

        assert body["primaryContact"]["firstName"] == primary["firstName"]
        assert body["primaryContact"]["lastName"] == primary["lastName"]
        assert body["primaryContact"]["email"] == primary["email"]
        assert str(body["primaryContact"]["phoneOne"]) == primary["phoneOne"]

        assert body["billingContact"]["firstName"] == billing["firstName"]
        assert body["billingContact"]["lastName"] == billing["lastName"]
        assert body["billingContact"]["email"] == billing["email"]
        assert str(body["billingContact"]["phoneOne"]) == billing["phoneOne"]

    # --- 8. Delete client (teardown) -----------------------------------------
    with allure.step("Delete client"):
        response = myplc_client.delete(f"/clients/{client_id}", headers=headers)
        response.assert_status(204).assert_response_time_under(thresholds["delete"])
        # Deleted here explicitly; drop it so the safety-net fixture is a no-op.
        created_clients.remove(client_id)
