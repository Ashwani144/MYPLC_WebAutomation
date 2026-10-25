"""MTPLC scoped reporting and viewport behavior."""
from __future__ import annotations

import pytest

from mtplc.reporting import (
    pytest_configure,
    pytest_runtest_makereport,
    pytest_sessionfinish,
)


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Keep the MTPLC suite's maximized Chromium launch behavior."""
    return {
        **browser_type_launch_args,
        "args": [*browser_type_launch_args.get("args", []), "--start-maximized"],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Use the full maximized window for MTPLC UI workflows."""
    return {**browser_context_args, "no_viewport": True}
