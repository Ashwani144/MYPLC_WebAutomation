import pytest

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.launch_page import LaunchPage
from mtplc.pages.login_page import LoginPage


@pytest.mark.smoke
def test_add_model_after(page):
    """
    Launch
    -> Login
    -> Applications
    -> Incomplete
    -> P-252956
    -> Models
    -> All Models
    -> Select Model
    -> Add Row
    -> After
    -> Enter Draft Row Data
    -> Save
    -> Confirm Save
    -> Validate Success
    """

    launch_page = LaunchPage(page)
    login_page = LoginPage(page)
    applications_page = ApplicationsPage(page)

    # 1. Launch
    launch_page.open()

    # 2. Login
    login_page.validate_login_page()
    login_page.login()
    login_page.wait_for_login_navigation()
    login_page.validate_successful_login()

    # 3. Applications
    applications_page.click_applications()

    # 4. Incomplete
    applications_page.click_incomplete()

    # 5. Application
    applications_page.open_application(
        "P-252956"
    )

    # 6. Models
    applications_page.click_models()

    # 7. All Models
    applications_page.click_all_models()

    # 8. Select Model
    applications_page.select_model(
        "430940"
    )

    # 9. Add Row
    applications_page.click_add_row()

    # 10. After
    applications_page.click_after()

    # 11. Draft Row Data
    applications_page.enter_draft_row_data(
        model_number="100101",
        description="By Automation Test",
        iapmo_westand="Test",
        cal_green="Test",
        leed="Test",
    )

    # 12. Save
    applications_page.click_save()

    # 13. Confirm
    applications_page.confirm_save()

    # 14. Success
    applications_page.validate_models_update_success()
