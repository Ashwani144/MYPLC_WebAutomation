"""Test-data fixtures — load externalized JSON / YAML data for data-driven tests."""
from __future__ import annotations

from typing import Any

import pytest

from utils.data_loader import DataLoader


@pytest.fixture(scope="session")
def data_loader() -> DataLoader:
    """Shared data loader instance."""
    return DataLoader()


@pytest.fixture
def users_data(data_loader: DataLoader) -> Any:
    """User test data loaded from testdata/users.yaml."""
    return data_loader.load("users.yaml")


@pytest.fixture
def api_data(data_loader: DataLoader) -> Any:
    """API test data loaded from testdata/api_data.json."""
    return data_loader.load("api_data.json")


@pytest.fixture
def client_flow_data(data_loader: DataLoader) -> Any:
    """MYPLC client-flow test data loaded from testdata/client_flow.json."""
    return data_loader.load("client_flow.json")


@pytest.fixture
def login_data(data_loader: DataLoader) -> dict[str, Any]:
    """Login credentials loaded from the Excel test data file.

    Returns the first data row of ``testdata/login_data.xlsx`` as a dict with
    ``username`` and ``password`` keys.
    """
    rows = data_loader.load_excel("login_data.xlsx", sheet="login")
    assert rows, "login_data.xlsx contains no credential rows"
    return rows[0]

