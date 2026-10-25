"""Applications module tests for MTPLC."""

import pytest

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage


@pytest.mark.smoke
@pytest.mark.regression
def test_open_incomplete_application(page) -> None:
    """Validate Applications > Incomplete navigation."""

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    applications_page = ApplicationsPage(page)

    # 1. Launch application
    launch_page.open()
    launch_page.validate_login_page()

    # 2. Login
    login_page.login()
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    # 3. Open Applications
    applications_page.click_applications()

    # 4. Open Incomplete
    applications_page.click_incomplete()

    # 5. Screenshot
    applications_page.take_screenshot(
        "06_incomplete_page.png"
    )
