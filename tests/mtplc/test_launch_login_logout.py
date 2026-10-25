"""Launch, login, Applications navigation and logout tests."""

import pytest

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage
from mtplc.pages.logout_page import LogoutPage


@pytest.mark.smoke
@pytest.mark.regression
def test_launch_login_logout(page) -> None:
    """Launch, login, navigate to Applications > Incomplete, and logout."""

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    applications_page = ApplicationsPage(page)
    logout_page = LogoutPage(page)

    # ============================================================
    # 1-2. Launch and validate login page
    # ============================================================

    launch_page.open()
    launch_page.validate_login_page()
    login_page.validate_login_page()

    login_page.take_screenshot("02_login.png")

    # ============================================================
    # 3-5. Login
    # ============================================================

    login_page.enter_username()
    login_page.enter_password()
    login_page.click_login()

    # ============================================================
    # 6. Validate successful login
    # ============================================================

    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    login_page.take_screenshot("03_after_login.png")

    # ============================================================
    # 7-8. Applications > Incomplete
    # ============================================================

    applications_page.click_applications()
    applications_page.click_incomplete()

    applications_page.take_screenshot("06_incomplete_page.png")

    # ============================================================
    # 9-10. Logout
    # ============================================================

    logout_page.click_logout()
    logout_page.wait_for_logout_completion()
    logout_page.validate_successful_logout()
