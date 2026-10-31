"""

MTPLC Application Details Page Object.



Handles:

    - Application Details validation

    - Models tab

    - Manage Models

    - Upload Model Template

    - Upload confirmation popup

"""



from __future__ import annotations



from datetime import date, timedelta
import logging
from pathlib import Path
import random
import re



from playwright.sync_api import (
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    expect,
)



from mtplc.pages.base_page import BasePage





LOGGER = logging.getLogger(__name__)





class ApplicationDetailsPage(BasePage):

    """MTPLC Application Details page object."""



    # ------------------------------------------------------------------

    # Models tab

    # ------------------------------------------------------------------



    MODELS_TAB = (

        "xpath=//a[@ng-click=\"aadc.selectTab('products')\"]"

    )



    DETAILS_TAB = (

        "xpath=//a[@ng-click=\"aadc.selectTab('details')\"]"

    )



    ACTION_ITEMS_TAB = (

        "xpath=//a[@ng-click=\"aadc.selectTab('action-items')\"]"

    )



    ADDITIONAL_COMPANIES_TAB = (

        "xpath=//a[@ng-click=\"aadc.selectTab('additional-companies')\"]"

    )



    APPLICATION_STATUS_HEADING = "h4"

    APPLICATION_STATUS_VALUE = (

        "span[ng-click*='editApplicationStatusClick']"

    )



    CREATE_NEW_ACTION_ITEM = (

        "xpath=//a[@class='btn btn-edit btn-primary']"

    )



    APPLICATION_ACTIONS_MENU = (

        "xpath=//button[@type='button'][.//i[@class='fa fa-bars']]"

    )



    LIST_APPLICATION_ACTION = (

        "xpath=//a[@class='btn'][normalize-space()='List']"

    )



    # ------------------------------------------------------------------

    # Manage Models

    # ------------------------------------------------------------------



    MANAGE_MODELS = (

        "xpath=//button[@class='btn btn-primary dropdown-toggle']"

    )



    # ------------------------------------------------------------------

    # Upload Model Template

    # ------------------------------------------------------------------



    UPLOAD_MODEL_TEMPLATE = (

        "xpath=//a[@ng-show=\""

        "aadc.userCanCreateModels && "

        "!aadc.readOnly && "

        "!aadc.applicationData.splitProjectSourceId && "

        "aadc.applicationData.applicationStatus.status != 'Complete' && "

        "aadc.projectTypes[aadc.applicationData.targetProject.projectType] "

        "!= 'AmazonResellers'"

        "\"]"

    )



    # ------------------------------------------------------------------

    # Upload Models confirmation popup

    # ------------------------------------------------------------------



    UPLOAD_MODELS_TITLE = "Upload Models"

    LIST_ALL_MODELS_BUTTON = (

        "xpath=//button[@class='btn-sm text-white multi-set-btn "

        "ng-binding ng-scope btn btn-primary']"

    )



    # ------------------------------------------------------------------

    # Constructor

    # ------------------------------------------------------------------



    def __init__(self, page: Page) -> None:

        super().__init__(page)



    # ==================================================================

    # Application Details

    # ==================================================================



    def validate_application_details(
        self,
        application_id: str,

    ) -> None:



        LOGGER.info(

            "Validating Application Details page for application ID: %s",

            application_id,

        )



        expected_url = re.compile(

            rf".*/admin/applications#/details/"

            rf"{re.escape(application_id)}/details/?.*"

        )



        expect(self.page).to_have_url(
            expected_url,
            timeout=30000,
        )

        expect(
            self.page.get_by_role(
                "heading",
                name=re.compile(r"^Application Status:\s*"),
            )
        ).to_be_visible(timeout=60000)
        self._wait_for_application_update()

        LOGGER.info(
            "Application Details URL validated: %s",
            self.page.url,
        )

    def _click_save_button(self, selector: str) -> None:
        save_button = self.page.locator(selector)
        expect(save_button).to_have_count(1, timeout=15000)
        expect(save_button).to_be_visible(timeout=15000)
        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)

    def _wait_for_application_update(self) -> None:
        loading_overlay = self.page.locator("div.loading-screen:visible")
        expect(loading_overlay).to_have_count(0, timeout=60000)
        self.page.wait_for_timeout(500)
        expect(loading_overlay).to_have_count(0, timeout=60000)

    def _choose_random_suggestion(
        self,
        search_input: Locator,
        search_values: tuple[str, ...] = ("1", "2"),
    ) -> str:
        suggestions = self.page.locator(
            "[role='option']:visible, "
            ".dropdown-menu:visible li:visible, "
            ".ui-select-choices-row:visible, "
            ".angucomplete-row:visible"
        )
        randomized_search_values = random.sample(
            list(search_values),
            k=len(search_values),
        )
        for index, search_text in enumerate(randomized_search_values):
            search_input.fill(search_text)
            try:
                suggestions.first.wait_for(state="visible", timeout=5000)
                break
            except PlaywrightTimeoutError:
                if index == len(randomized_search_values) - 1:
                    dialog = self.page.get_by_role("dialog")
                    dialog_text = (
                        dialog.inner_text()
                        if dialog.count() and dialog.is_visible()
                        else "<no visible dialog>"
                    )
                    raise AssertionError(
                        "The search field returned no selectable options "
                        f"for search values {search_values!r}. "
                        f"Visible dialog content: {dialog_text!r}"
                    ) from None

        count = suggestions.count()

        suggestion = suggestions.nth(random.randrange(count))
        selected_text = suggestion.inner_text().strip()
        if not selected_text:
            raise AssertionError(
                "The randomly selected search result has no visible text."
            )
        suggestion.click(timeout=15000)
        LOGGER.info("Selected random option: %s", selected_text)
        return selected_text

    def _assign_random_product_code_and_received_date(self) -> None:
        assign_product_code = self.page.locator(
            "xpath=//span[@class='ng-binding']"
            "[normalize-space()='Assign Product Code']"
        )
        if assign_product_code.count():
            expect(assign_product_code).to_be_visible(timeout=30000)
            assign_product_code.click(timeout=15000)

            product_code_input = self.page.get_by_placeholder(
                "Enter Product Code",
                exact=True,
            )
            expect(product_code_input).to_be_visible(timeout=15000)
            product_code = self._choose_random_suggestion(product_code_input)
            self._click_save_button(
                "xpath=//button[@ng-click='afc.updateProductCode()']"
            )
            self._wait_for_application_update()
            LOGGER.info("Product Code %s assigned", product_code)
        else:
            LOGGER.info(
                "Product Code is already assigned; keeping the existing value"
            )

        self._wait_for_application_update()
        not_set_value = self.page.get_by_text("Not Set", exact=True)
        if not_set_value.is_visible():
            expect(not_set_value).to_have_count(1, timeout=15000)
            not_set_value.click(timeout=15000)
            received_date_input = self.page.locator(
                "input[type='date']:visible"
            )
            expect(received_date_input).to_have_count(1, timeout=15000)
            expect(received_date_input).to_be_visible(timeout=15000)
            future_received_date = (
                date.today() + timedelta(days=random.randint(1, 30))
            )
            received_date_input.fill(future_received_date.isoformat())

            self._click_save_button(
                "xpath=//button[@ng-click='afc.updateReceivedDate()']"
            )
            self._wait_for_application_update()
            expect(not_set_value).to_be_hidden(timeout=30000)
            LOGGER.info(
                "Saved Received Date %s",
                future_received_date.isoformat(),
            )
        else:
            LOGGER.info("Received Date is already set; keeping its existing value")

    def _assign_random_engineer(self) -> None:
        assign_engineer = self.page.locator(
            "xpath=//span[@class='text-info']"
        )
        if assign_engineer.count() == 0:
            LOGGER.info("Engineer is already assigned; keeping the existing value")
            return
        expect(assign_engineer).to_have_count(1, timeout=30000)
        expect(assign_engineer).to_be_visible(timeout=30000)
        assign_engineer.click(timeout=15000)

        engineer_input = self.page.get_by_placeholder(
            "Enter Engineer Name",
            exact=True,
        )
        expect(engineer_input).to_be_visible(timeout=15000)
        engineer_input.click()
        engineer_input.fill("")
        preferred_engineer = self.page.locator(
            "xpath=//a[@title='Adnan Yousuf']"
        )
        try:
            engineer_input.press_sequentially("Adnan", delay=100)
            preferred_engineer.wait_for(state="visible", timeout=5000)
            selected_engineer = preferred_engineer.get_attribute("title")
            preferred_engineer.click(timeout=15000)
        except PlaywrightTimeoutError:
            suggestions = self.page.locator(
                "[role='option']:visible, "
                ".dropdown-menu:visible li:visible, "
                ".ui-select-choices-row:visible, "
                ".angucomplete-row:visible, "
                "a[title]:visible"
            )
            engineer_input.fill("")
            engineer_input.press_sequentially("a", delay=100)
            try:
                suggestions.first.wait_for(state="visible", timeout=15000)
            except PlaywrightTimeoutError:
                dialog = self.page.get_by_role("dialog")
                dialog_text = (
                    dialog.inner_text()
                    if dialog.count() and dialog.is_visible()
                    else "<no visible dialog>"
                )
                raise AssertionError(
                    "No engineer suggestions appeared after searching for "
                    "'Adnan' or 'a'. "
                    f"Visible dialog content: {dialog_text!r}"
                ) from None
            engineer = suggestions.nth(
                random.randrange(suggestions.count())
            )
            selected_engineer = (
                engineer.get_attribute("title")
                or engineer.inner_text().strip()
            )
            if not selected_engineer:
                raise AssertionError(
                    "The randomly selected engineer suggestion has no text."
                )
            engineer.click(timeout=15000)
        if not selected_engineer:
            raise AssertionError(
                "The preferred engineer suggestion did not expose a title."
            )
        self._click_save_button(
            "xpath=//span[normalize-space()='Save']"
        )
        self._wait_for_application_update()
        LOGGER.info("Engineer %s assignment saved", selected_engineer)

    def _assign_random_testing_lab(self) -> None:
        assign_lab = self.page.locator(
            "xpath=//span[normalize-space()='Assign Testing Lab']"
        )
        if assign_lab.count() == 0:
            LOGGER.info("Testing Lab is already assigned; keeping the existing value")
            return
        expect(assign_lab).to_be_visible(timeout=30000)
        assign_lab.click(timeout=15000)

        lab_input = self.page.get_by_placeholder(
            re.compile(r"Testing Lab|Lab", re.IGNORECASE)
        )
        if lab_input.count() == 0:
            lab_input = self.page.get_by_role(
                "textbox",
                name="Please select Laboratory",
                exact=True,
            )
        expect(lab_input).to_have_count(1, timeout=15000)
        expect(lab_input).to_be_visible(timeout=15000)

        selected_lab = self._choose_random_suggestion(
            lab_input,
            search_values=("1",),
        )
        self._wait_for_application_update()
        LOGGER.info("Testing Lab %s assignment saved", selected_lab)

    def complete_initial_application_setup(self) -> None:
        """Set product code, received date, engineer, and testing lab."""
        self._assign_random_product_code_and_received_date()
        self._assign_random_engineer()
        self._assign_random_testing_lab()
        LOGGER.info("Initial application setup is complete")
    
    # ==================================================================

    # Models Tab

    # ==================================================================



    def click_models_tab(self) -> None:



        LOGGER.info(

            "Clicking Models tab"

        )



        models_tab = self.page.locator(

            self.MODELS_TAB

        )



        expect(models_tab).to_have_count(

            1,

            timeout=30000,

        )



        expect(models_tab).to_be_visible(

            timeout=30000,

        )



        models_tab.scroll_into_view_if_needed(

            timeout=10000,

        )



        models_tab.click(

            timeout=15000,

        )

        expect(

            self.page.get_by_role("button", name="All Models")

        ).to_be_visible(timeout=30000)



        LOGGER.info(

            "Models tab clicked"

        )



    def click_action_items_tab(self) -> None:

        LOGGER.info("Clicking Action Items tab")



        action_items_tab = self.page.locator(self.ACTION_ITEMS_TAB)

        expect(action_items_tab).to_have_count(1, timeout=30000)

        expect(action_items_tab).to_be_visible(timeout=30000)

        action_items_tab.click(timeout=15000)



        LOGGER.info("Action Items tab clicked")



    def click_details_tab(self) -> None:

        LOGGER.info("Clicking Details tab")

        details_tab = self.page.locator(self.DETAILS_TAB)

        expect(details_tab).to_have_count(1, timeout=30000)

        expect(details_tab).to_be_visible(timeout=15000)

        details_tab.click(timeout=15000)

        LOGGER.info("Details tab clicked")



    def application_status_heading(self) -> Locator:

        heading = self.page.locator(

            self.APPLICATION_STATUS_HEADING

        ).filter(has_text="Application Status:")

        expect(heading).to_have_count(1, timeout=30000)

        return heading



    def application_status_value(self) -> Locator:

        value = self.application_status_heading().locator(

            self.APPLICATION_STATUS_VALUE

        )

        expect(value).to_have_count(1, timeout=15000)

        return value



    def change_application_status(self, status: str) -> None:
        """Choose and save a status from the observed inline status editor."""

        heading = self.application_status_heading()

        current_value = self.application_status_value()

        current_value.click(timeout=15000)



        dropdown = self.page.locator("application-statuses-drop-down")

        expect(dropdown).to_be_visible(timeout=15000)

        dropdown_button = dropdown.get_by_role("button")

        expect(dropdown_button).to_have_count(1, timeout=15000)

        dropdown_button.click(timeout=15000)



        option = dropdown.locator(
            "a.dropdown-item.ng-binding.ng-scope"
        ).filter(
            has_text=re.compile(rf"^\s*{re.escape(status)}\s*$")
        )
        expect(option).to_have_count(1, timeout=15000)
        expect(option).to_be_visible(timeout=15000)
        option.click(timeout=15000)
        expect(dropdown_button).to_contain_text(status, timeout=15000)



        save_button = self.page.locator(
            "xpath=//button[@ng-click="
            "'afc.updateStatus(afc.selectedApplicationStatus)']"
        )

        expect(save_button).to_be_visible(timeout=15000)

        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)
        self.accept_optional_yes_confirmation()
        expect(self.application_status_value()).to_have_text(
            status,
            timeout=60000,
        )
        LOGGER.info("Application Status saved as %s", status)

    def accept_optional_yes_confirmation(self) -> bool:
        """Accept a visible Yes button in an optional application dialog."""
        yes_button = (
            self.page.get_by_role("dialog")
            .get_by_role("button", name="Yes", exact=True)
        )
        try:
            expect(yes_button).to_be_visible(timeout=3000)
        except AssertionError:
            LOGGER.info("No optional Yes confirmation dialog was displayed")
            return False

        expect(yes_button).to_be_enabled(timeout=10000)
        yes_button.click(timeout=10000)
        expect(self.page.get_by_role("dialog")).to_have_count(0, timeout=30000)
        LOGGER.info("Accepted optional Yes confirmation")
        return True



    def click_additional_companies_tab(self) -> None:

        tab = self.page.locator(self.ADDITIONAL_COMPANIES_TAB)

        expect(tab).to_have_count(1, timeout=30000)

        expect(tab).to_be_visible(timeout=15000)

        tab.click(timeout=15000)

        expect(

            self.page.locator(

                'a[ng-click*="getselectedAddCoTab"]'

            ).first

        ).to_be_visible(timeout=30000)



    def validate_additional_companies(
        self,
        expected_model_number: str | None = None,
    ) -> None:
        empty_state = self.page.get_by_text(
            "No additional companies for review.",
            exact=True,
        )

        if empty_state.is_visible():
            if expected_model_number is not None:
                raise AssertionError(
                    "Expected Additional Company model "
                    f"{expected_model_number!r}, but the Additional Companies "
                    "tab is empty."
                )
            LOGGER.info("Additional Companies is empty, as expected")
            return



        company_tabs = self.page.locator(

            'a[ng-click*="getselectedAddCoTab"]'

        )

        expect(company_tabs.first).to_be_visible(timeout=15000)

        company_count = company_tabs.count()

        if company_count == 0:

            raise AssertionError(

                "Additional Companies has neither its verified empty-state "

                "message nor any visible company entries."

            )



        company_model_table = self.page.locator("table").filter(

            has_text="Additional Company Model Number"

        )

        expect(company_model_table).to_have_count(1, timeout=15000)

        expected_model_found = expected_model_number is None
        for index in range(company_count):
            company_tab = company_tabs.nth(index)
            company_name = company_tab.inner_text().strip()
            expect(company_tab).to_be_visible(timeout=15000)
            company_tab.click(timeout=15000)
            rows = company_model_table.get_by_role("row")
            expect(rows.nth(1)).to_be_visible(timeout=30000)
            LOGGER.info(
                "Additional Company %s displays model rows",
                company_name,
            )

            if expected_model_number is not None:
                expected_model = company_model_table.get_by_text(
                    expected_model_number,
                    exact=True,
                )
                try:
                    expect(expected_model).to_be_visible(timeout=3000)
                except PlaywrightTimeoutError:
                    continue
                expected_model_found = True
                break

        if not expected_model_found:
            raise AssertionError(
                "Additional Company model "
                f"{expected_model_number!r} was not found in any company."
            )

    def list_additional_company_models(self, model_number: str) -> None:
        """List un-recommended models for the selected Additional Company."""
        company_model_table = self.page.locator("table").filter(
            has_text="Additional Company Model Number"
        )
        model = company_model_table.get_by_text(model_number, exact=True)
        expect(model).to_be_visible(timeout=15000)

        list_button = self.page.get_by_role(
            "button",
            name="List",
            exact=True,
        )
        expect(list_button).to_have_count(1, timeout=15000)
        expect(list_button).to_be_enabled(timeout=15000)
        list_button.click(timeout=15000)

        confirmation = self.page.get_by_role("dialog").filter(
            has_text=re.compile(
                r"Are you sure you want to List all the un-recommended "
                r"models for this Additional Company\?",
                re.IGNORECASE,
            )
        )
        expect(confirmation).to_be_visible(timeout=15000)

        confirm_button = confirmation.get_by_role(
            "button",
            name="Confirm",
            exact=True,
        )
        expect(confirm_button).to_be_enabled(timeout=15000)
        confirm_button.click(timeout=15000)
        expect(confirmation).to_have_count(0, timeout=60000)
        expect(model).to_be_visible(timeout=30000)
        LOGGER.info(
            "Listed Additional Company models; model %s remains visible",
            model_number,
        )

    def _write_up_option(self) -> Locator:
        return self.page.get_by_role("listbox").get_by_role(
            "option",
            name="Write Up",
            exact=True,
        )

    def _configure_write_up_action_item(self, dialog: Locator) -> None:
        priority_button = dialog.get_by_role(
            "button",
            name="Select Priority",
            exact=True,
        )
        expect(priority_button).to_be_visible(timeout=15000)
        priority_button.click(timeout=15000)

        high_priority = dialog.get_by_text("High", exact=True)
        expect(high_priority).to_be_visible(timeout=15000)
        high_priority.click(timeout=15000)
        expect(
            dialog.get_by_role("button", name="High", exact=True)
        ).to_be_visible(timeout=15000)

        reminder_date = dialog.get_by_role(
            "textbox",
            name=re.compile(r"^Reminder Date"),
        )
        due_date = dialog.get_by_role(
            "textbox",
            name=re.compile(r"^Due Date"),
        )
        expect(reminder_date).to_be_visible(timeout=15000)
        expect(due_date).to_be_visible(timeout=15000)
        today = date.today().isoformat()
        reminder_date.fill(today)
        due_date.fill(today)

    def create_write_up_action_item(self) -> None:

        LOGGER.info("Creating a Write Up Action Item")



        action_items_grid = self.page.get_by_role("grid")
        expect(action_items_grid).to_have_count(1, timeout=30000)
        expect(action_items_grid).to_be_visible(timeout=15000)
        expect(
            self.page.get_by_text(
                re.compile(
                    r"Showing\s+\d+\s+to\s+\d+\s+of\s+\d+\s+entries"
                )
            )
        ).to_be_visible(timeout=30000)
        grid_text = action_items_grid.inner_text()

        if not all(

            heading in grid_text

            for heading in ("Description", "Type", "Priority")

        ):

            raise AssertionError(

                "The Action Items table does not contain its expected "

                "Description, Type, and Priority columns."

            )

        existing_write_up_count = len(
            re.findall(r"\bWrite Up\b", action_items_grid.inner_text())
        )
        existing_write_up = existing_write_up_count > 0

        if existing_write_up:

            LOGGER.info(

                "Found %d existing Write Up Action Item row(s); "
                "skipping duplicate creation",
                existing_write_up_count,

            )

            self.validate_write_up_action_item()

            return



        create_link = self.page.locator(self.CREATE_NEW_ACTION_ITEM)

        expect(create_link).to_have_count(1, timeout=30000)

        expect(create_link).to_be_visible(timeout=15000)

        with self.page.expect_response(

            lambda response: (

                "/api/action-item-types/by-user-department" in response.url

                and response.request.method == "GET"

            ),

            timeout=30000,

        ) as action_types_response:

            create_link.click(timeout=15000)

        if action_types_response.value.status != 200:

            raise AssertionError(

                "The Action Item type list failed to load "

                f"(HTTP {action_types_response.value.status})."

            )



        dialog = self.page.get_by_role("dialog")

        expect(dialog).to_be_visible(timeout=15000)

        self._configure_write_up_action_item(dialog)

        action_type = dialog.locator('input[name="typeId"]')

        expect(action_type).to_be_visible(timeout=15000)

        action_type.fill("Write")



        write_up_option = self._write_up_option()

        expect(write_up_option).to_have_count(1, timeout=30000)

        expect(write_up_option).to_be_visible(timeout=30000)

        with self.page.expect_response(

            lambda response: (

                "/api/action-item-statuses/by-action-item-type/" in response.url

                and response.request.method == "GET"

            ),

            timeout=30000,

        ) as action_statuses_response:

            write_up_option.click(timeout=15000)

        if action_statuses_response.value.status != 200:

            raise AssertionError(

                "The Write Up Action Item statuses failed to load "

                f"(HTTP {action_statuses_response.value.status})."

            )

        expect(action_type).to_have_value("Write Up", timeout=10000)



        status_value = dialog.locator('input[name="statusId"]')

        expect(status_value).to_have_class(

            re.compile(r"\bng-valid-required\b"),

            timeout=30000,

        )

        status_button = status_value.locator(

            "xpath=following-sibling::button[1]"

        )

        expect(status_button).not_to_have_text(

            "Select Status",

            timeout=30000,

        )



        create_button = dialog.get_by_role(

            "button",

            name=re.compile(r"Create Action Item", re.IGNORECASE),

        )

        expect(create_button).to_have_count(1, timeout=15000)

        expect(create_button).to_be_visible(timeout=15000)

        expect(create_button).to_be_enabled(timeout=15000)

        create_button.scroll_into_view_if_needed(timeout=10000)
        create_button.click(timeout=15000)

        self.accept_optional_yes_confirmation()
        expect(dialog).to_have_count(0, timeout=60000)

        LOGGER.info("Write Up Action Item submitted; refresh before validating")



    def validate_write_up_action_item(self) -> None:

        """Verify the Write Up type is visible in the Action Items table."""

        action_items_grid = self.page.get_by_role("grid")

        expect(action_items_grid).to_contain_text("Write Up", timeout=60000)
        LOGGER.info(
            "Verified persisted Write Up Action Item data after reload"
        )



    def wait_until_list_action_enabled(
        self,
        max_wait_seconds: int = 60,
    ) -> None:
        """Wait until the Actions menu exposes an enabled List action."""
        LOGGER.info("Waiting for List action to become enabled")
        actions_menu = self.page.locator(self.APPLICATION_ACTIONS_MENU)
        list_action = self.page.locator(self.LIST_APPLICATION_ACTION)
        timeout_ms = max_wait_seconds * 1000

        expect(actions_menu).to_be_visible(timeout=15000)
        expect(actions_menu).to_be_enabled(timeout=15000)
        if not list_action.is_visible():
            actions_menu.click(timeout=15000)

        try:
            expect(list_action).to_be_visible(timeout=timeout_ms)
            expect(list_action).to_be_enabled(timeout=timeout_ms)
        except AssertionError as exc:
            raise AssertionError(
                "The hamburger List action did not become visible and enabled "
                f"within {max_wait_seconds} seconds after saving the application "
                f"status. Current status: "
                f"{self.application_status_value().inner_text().strip()!r}."
            ) from exc

        LOGGER.info("List action is now visible and enabled")

    def wait_for_application_list_action(self) -> None:
        """Backward-compatible wrapper for List-action polling."""
        self.wait_until_list_action_enabled()

    def return_to_application_details(self, application_id: str) -> None:
        """Open the base Details route to dismiss workflow overlays."""
        current_url = self.page.url
        application_route = "/admin/applications#"
        if application_route not in current_url:
            raise AssertionError(
                "Cannot restore the application Details route from "
                f"unexpected URL: {current_url}"
            )

        origin = current_url.split(application_route, maxsplit=1)[0]
        details_url = (
            f"{origin}{application_route}/details/{application_id}/details/"
        )
        LOGGER.info(
            "Returning to application %s Details view before completion",
            application_id,
        )
        self.page.goto(details_url, wait_until="domcontentloaded")
        expect(self.page).to_have_url(
            re.compile(
                rf".*/admin/applications#/details/"
                rf"{re.escape(application_id)}/details/?$"
            ),
            timeout=30000,
        )
        expect(self.application_status_value()).to_be_visible(timeout=30000)

    def list_application(self) -> None:
        """Click List and handle the application confirmation."""
        LOGGER.info("Starting application List action")
        actions_menu = self.page.locator(self.APPLICATION_ACTIONS_MENU)
        list_action = self.page.locator(self.LIST_APPLICATION_ACTION)
        if not list_action.is_visible():
            expect(actions_menu).to_be_visible(timeout=15000)
            actions_menu.click(timeout=15000)
        expect(list_action).to_be_visible(timeout=15000)
        expect(list_action).to_be_enabled(timeout=15000)
        list_action.scroll_into_view_if_needed(timeout=10000)

        browser_dialog_messages: list[str] = []

        def accept_browser_confirmation(dialog) -> None:
            browser_dialog_messages.append(dialog.message)
            LOGGER.info(
                "Accepting browser confirmation for List action: %s",
                dialog.message,
            )
            dialog.accept()

        self.page.on("dialog", accept_browser_confirmation)
        try:
            list_action.click(timeout=15000)
        finally:
            self.page.remove_listener("dialog", accept_browser_confirmation)

        confirmation = self.page.get_by_role("dialog")
        if confirmation.is_visible():
            confirm_button = confirmation.get_by_role(
                "button",
                name=re.compile(r"^(Confirm|Yes)$", re.IGNORECASE),
            )
            expect(confirm_button).to_be_visible(timeout=15000)
            expect(confirm_button).to_be_enabled(timeout=15000)
            confirm_button.click(timeout=15000)
            expect(confirm_button).to_be_hidden(timeout=60000)

            second_yes = self.page.get_by_role(
                "button",
                name="Yes",
                exact=True,
            )
            try:
                expect(second_yes).to_be_visible(timeout=5000)
            except AssertionError:
                LOGGER.info("No second Yes confirmation displayed")
            else:
                expect(second_yes).to_be_enabled(timeout=15000)
                second_yes.click(timeout=15000)
        elif browser_dialog_messages:
            LOGGER.info(
                "List action browser confirmation accepted (%d dialog(s))",
                len(browser_dialog_messages),
            )
        else:
            success_toast = self.page.get_by_text(
                "Status Successfully Updated",
                exact=False,
            )
            try:
                expect(success_toast).to_be_visible(timeout=10000)
            except AssertionError as exc:
                raise AssertionError(
                    "Clicking the hamburger List action produced no Confirm/"
                    "Yes popup, browser confirmation, or observed "
                    "'Status Successfully Updated' notification."
                ) from exc
            LOGGER.info(
                "List action completed through the observed status update "
                "notification (no confirmation popup was displayed)"
            )

        expect(self.application_status_value()).to_have_text("List", timeout=60000)
        LOGGER.info("Application List action completed")

    def validate_models_in_certificate_preview(
        self,
        model_numbers: tuple[str, ...],
    ) -> None:
        """Check that each model appears in Certificate Preview."""
        preview = self._certificate_preview_dialog()
        expect(preview).to_be_visible(timeout=30000)

        self._wait_for_certificate_preview_animation()

        for model_number in model_numbers:
            expect(preview).to_contain_text(
                model_number,
                timeout=30000,
            )
            LOGGER.info(
                "Verified model %s in Certificate Preview",
                model_number,
            )


    def open_certificate_preview(self, application_id: str) -> None:
        """Open the observed Certificate Preview overlay for this application."""
        preview = self._certificate_preview_dialog()
        if preview.count() and preview.is_visible():
            LOGGER.info("Certificate Preview is already open")
            self._wait_for_certificate_preview_animation()
            return

        current_url = self.page.url
        application_route = "/admin/applications#"
        if application_route not in current_url:
            raise AssertionError(
                "Cannot open Certificate Preview from unexpected URL: "
                f"{current_url}"
            )

        origin = current_url.split(application_route, maxsplit=1)[0]
        preview_url = (
            f"{origin}{application_route}/details/{application_id}/details/"
            "null/certificate-overlay/true/false/false/false#actionItems"
        )
        LOGGER.info(
            "Opening Certificate Preview for application %s",
            application_id,
        )
        self.page.goto(preview_url, wait_until="domcontentloaded")
        preview = self._certificate_preview_dialog()
        expect(preview).to_be_visible(timeout=30000)

    def _certificate_preview_dialog(self) -> Locator:
        return self.page.locator(
            'div[role="dialog"].modal.in:visible'
        ).filter(
            has=self.page.get_by_role(
                "heading",
                name="Certificate Preview",
                exact=True,
            )
        ).last

    def _wait_for_modal_animations(self) -> None:
        self.page.wait_for_function(
            """() => {
                const dialogs = [...document.querySelectorAll(
                    'div[role="dialog"].modal'
                )].filter(element => element.getClientRects().length);
                const transitionClasses =
                    /\\b(?:ng-animate|ng-enter|ng-leave|ng-enter-active|ng-leave-active|in-add-active)\\b/;
                return dialogs.length > 0 && dialogs.every(element =>
                    !element.hasAttribute('data-ng-animate')
                    && !transitionClasses.test(element.className)
                );
            }""",
            timeout=30000,
        )

    def _wait_for_certificate_preview_animation(self) -> None:
        self._wait_for_modal_animations()
        self.page.wait_for_function(
            """() => {
                const previews = [...document.querySelectorAll(
                    'div[role="dialog"].modal.in'
                )].filter(element =>
                    element.getClientRects().length
                    && [...element.querySelectorAll(
                        'h1, h2, h3, .modal-title'
                    )].some(heading =>
                        heading.textContent.trim() === 'Certificate Preview'
                    )
                );
                return previews.length > 0;
            }""",
            timeout=15000,
        )

    def _certificate_preview_completion_action(self) -> Locator:
        return self._certificate_preview_dialog().locator(
            "xpath=.//a[@class='ml-2 btn btn-primary ng-scope']"
        ).first

    def _certificate_preview_closing_email_tab(self) -> Locator:
        return self._certificate_preview_dialog().get_by_text(
            "Closing Email",
            exact=True,
        )

    def _certificate_preview_complete_button(self) -> Locator:
        return self._certificate_preview_dialog().get_by_role(
            "button",
            name="Complete Application",
            exact=True,
        )

    def _scroll_certificate_completion_into_view(
        self,
        complete_button: Locator,
    ) -> None:
        complete_button.scroll_into_view_if_needed(timeout=10000)
        for _ in range(8):
            scroll_target = complete_button.evaluate(
                """element => {
                let parent = element.parentElement;
                while (parent && parent !== document.body) {
                    const style = getComputedStyle(parent);
                    const scrollable = /auto|scroll/.test(style.overflowY)
                        && parent.scrollHeight > parent.clientHeight + 1;
                    if (scrollable) {
                        const rect = parent.getBoundingClientRect();
                        return {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            scrollTop: parent.scrollTop
                        };
                    }
                    parent = parent.parentElement;
                }
                return null;
            }"""
            )
            if scroll_target is None:
                button_position = complete_button.evaluate(
                    """element => {
                        const rect = element.getBoundingClientRect();
                        return {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            viewportWidth: window.innerWidth,
                            viewportHeight: window.innerHeight
                        };
                    }"""
                )
                click_y = (
                    button_position["y"] + button_position["height"] / 2
                )
                delta = max(
                    75,
                    click_y - button_position["viewportHeight"] + 32,
                )
                previous_scroll_y = self.page.evaluate("window.scrollY")
                self.page.evaluate(
                    "(scrollDelta) => window.scrollBy(0, scrollDelta)",
                    delta,
                )
                self.page.wait_for_timeout(150)
                current_scroll_y = self.page.evaluate("window.scrollY")
                LOGGER.info(
                    "Scrolled the outer page to bring the Certificate Preview "
                    "footer into view (window scrollY: %s -> %s)",
                    previous_scroll_y,
                    current_scroll_y,
                )
                continue

            button_position = complete_button.evaluate(
                """element => {
                const rect = element.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight
                };
            }"""
            )
            click_x = button_position["x"] + button_position["width"] / 2
            click_y = button_position["y"] + button_position["height"] / 2
            if (
                0 <= click_x <= button_position["viewportWidth"]
                and 0 <= click_y <= button_position["viewportHeight"]
            ):
                break

            mouse_x = min(
                max(
                    scroll_target["x"] + scroll_target["width"] / 2,
                    1,
                ),
                button_position["viewportWidth"] - 1,
            )
            mouse_y = min(
                max(scroll_target["y"] + scroll_target["height"] / 2, 1),
                button_position["viewportHeight"] - 1,
            )
            self.page.mouse.move(mouse_x, mouse_y)
            self.page.mouse.wheel(0, 450)
            self.page.wait_for_timeout(150)
        else:
            button_position = complete_button.evaluate(
                """element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight
                    };
                }"""
            )

        button_position = complete_button.evaluate(
            """element => {
                const rect = element.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    viewportWidth: window.innerWidth,
                    viewportHeight: window.innerHeight
                };
            }"""
        )
        click_x = button_position["x"] + button_position["width"] / 2
        click_y = button_position["y"] + button_position["height"] / 2
        if click_y > button_position["viewportHeight"]:
            outer_scroll = max(
                75,
                click_y - button_position["viewportHeight"] + 32,
            )
            previous_scroll_y = self.page.evaluate("window.scrollY")
            self.page.evaluate(
                "(scrollDelta) => window.scrollBy(0, scrollDelta)",
                outer_scroll,
            )
            self.page.wait_for_timeout(150)
            button_position = complete_button.evaluate(
                """element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight
                    };
                }"""
            )
            click_x = button_position["x"] + button_position["width"] / 2
            click_y = button_position["y"] + button_position["height"] / 2
            LOGGER.info(
                "Scrolled the outer page after the popup content; window "
                "scrollY %s -> %s, mouse target now (%s, %s)",
                previous_scroll_y,
                self.page.evaluate("window.scrollY"),
                click_x,
                click_y,
            )

        if click_y > button_position["viewportHeight"]:
            required_height = int(click_y + 24)
            height_increase = (
                required_height - button_position["viewportHeight"]
            )
            if height_increase > 250:
                raise AssertionError(
                    "The lower Complete Application button remains outside "
                    "the viewport after scrolling its popup and outer page: "
                    f"button={button_position}"
                )
            self.page.set_viewport_size(
                {
                    "width": button_position["viewportWidth"],
                    "height": required_height,
                }
            )
            complete_button.scroll_into_view_if_needed(timeout=10000)
            button_position = complete_button.evaluate(
                """element => {
                    const rect = element.getBoundingClientRect();
                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        viewportWidth: window.innerWidth,
                        viewportHeight: window.innerHeight
                    };
                }"""
            )
            click_x = button_position["x"] + button_position["width"] / 2
            click_y = button_position["y"] + button_position["height"] / 2
            LOGGER.info(
                "Expanded the headed viewport slightly to expose the fixed "
                "Certificate Preview footer (target: %s, %s; viewport height: %s)",
                click_x,
                click_y,
                button_position["viewportHeight"],
            )

        LOGGER.info(
            "Scrolled the Certificate Preview popup to the lower Complete "
            "Application button; mouse target is (%s, %s) in viewport %s x %s",
            click_x,
            click_y,
            button_position["viewportWidth"],
            button_position["viewportHeight"],
        )
        if not (
            0 <= click_x <= button_position["viewportWidth"]
            and 0 <= click_y <= button_position["viewportHeight"]
        ):
            raise AssertionError(
                "The center of the lower Complete Application button remains "
                "outside the viewport after scrolling its popup: "
                f"button={button_position}"
            )

    def _wait_for_certificate_preview_save(self) -> None:
        saving_indicator = self._certificate_preview_dialog().get_by_text(
            re.compile(r"^Saving(?:\.\.\.|…)$"),
            exact=True,
        )
        if saving_indicator.count():
            expect(saving_indicator).to_be_hidden(timeout=60000)

    def complete_application(
        self,
        download_directory: Path,
        application_id: str,
    ) -> Path:
        """Submit completion and save the generated application PDF."""
        preview = self._certificate_preview_dialog()
        if preview.count() == 0 or not preview.is_visible():
            self.open_certificate_preview(application_id)

        expect(preview).to_be_visible(timeout=30000)
        self._wait_for_certificate_preview_animation()
        completion_action = self._certificate_preview_completion_action()
        expect(completion_action).to_be_visible(timeout=30000)
        completion_action.scroll_into_view_if_needed(timeout=10000)
        self._wait_for_certificate_preview_animation()

        for _ in range(3):
            click_target = completion_action.evaluate(
                """element => {
                    const rect = element.getBoundingClientRect();
                    const x = rect.x + rect.width / 2;
                    const y = rect.y + rect.height / 2;
                    const dialogs = [...document.querySelectorAll(
                        'div[role="dialog"].modal'
                    )].filter(dialog => dialog.getClientRects().length);
                    const owner = element.closest(
                        'div[role="dialog"].modal'
                    );
                    const hit = document.elementFromPoint(x, y)?.closest(
                        'div[role="dialog"].modal'
                    );
                    const hitElement = document.elementFromPoint(x, y);
                    return {
                        ownerIndex: dialogs.indexOf(owner),
                        hitIndex: dialogs.indexOf(hit),
                        sameDialog: owner === hit,
                        ownerClass: owner?.className ?? null,
                        hitClass: hit?.className ?? null,
                        hitElement: hitElement?.outerHTML.slice(0, 500) ?? null,
                        hitElementParent: hitElement?.parentElement?.outerHTML
                            .slice(0, 500) ?? null,
                        x,
                        y
                    };
                }"""
            )
            LOGGER.info(
                "Checking the upper Complete Application mouse target: %s",
                click_target,
            )
            if click_target["sameDialog"]:
                break
            if click_target["hitIndex"] < 0:
                LOGGER.warning(
                    "The upper Complete Application hit test did not map "
                    "to a dialog. Proceeding with Playwright's real click "
                    "and pointer-interception checks: %s",
                    click_target,
                )
                break

            blocking_modal = self.page.locator(
                'div[role="dialog"].modal:visible'
            ).nth(click_target["hitIndex"])
            close_button = blocking_modal.locator("button.btn-delete")
            expect(close_button).to_have_count(1, timeout=5000)
            expect(close_button).to_be_visible(timeout=5000)
            LOGGER.info(
                "Dismissing the actual dialog covering the upper "
                "Complete Application link: %s",
                click_target,
            )
            close_button.click(timeout=15000)
            self._wait_for_modal_animations()
            preview = self._certificate_preview_dialog()
            if preview.count() == 0 or not preview.is_visible():
                self.open_certificate_preview(application_id)
            else:
                self._wait_for_certificate_preview_animation()
            completion_action = self._certificate_preview_completion_action()
            expect(completion_action).to_be_visible(timeout=30000)
        else:
            raise AssertionError(
                "The upper Complete Application link remained covered after "
                "dismissing three intercepting dialogs."
            )

        LOGGER.info("Mouse-clicking upper Complete Application link")
        completion_action.click(timeout=15000)

        closing_email_tab = self._certificate_preview_closing_email_tab()
        closing_email_list_item = closing_email_tab.locator(
            "xpath=ancestor::li[1]"
        )
        try:
            expect(closing_email_list_item).to_have_class(
                re.compile(r"\bactive\b"),
                timeout=5000,
            )
        except AssertionError:
            LOGGER.info(
                "Upper action did not activate Closing Email; "
                "mouse-clicking the Closing Email tab"
            )
            expect(closing_email_tab).to_be_visible(timeout=15000)
            closing_email_tab.click(timeout=15000)
            expect(closing_email_list_item).to_have_class(
                re.compile(r"\bactive\b"),
                timeout=15000,
            )

        self._wait_for_certificate_preview_save()
        self._wait_for_certificate_preview_animation()
        preview = self._certificate_preview_dialog()
        complete_button = self._certificate_preview_complete_button()
        expect(complete_button).to_have_count(1, timeout=30000)
        expect(complete_button).to_be_visible(timeout=30000)
        self._scroll_certificate_completion_into_view(complete_button)
        expect(complete_button).to_be_enabled(timeout=15000)

        download_directory.mkdir(parents=True, exist_ok=True)
        button_position = complete_button.bounding_box()
        if button_position is None:
            raise AssertionError(
                "The lower Complete Application button has no clickable "
                "position after scrolling."
            )
        LOGGER.info(
            "Mouse-clicking lower Complete Application button at %s",
            button_position,
        )
        self.page.mouse.click(
            button_position["x"] + button_position["width"] / 2,
            button_position["y"] + button_position["height"] / 2,
        )
        confirmation = self.page.get_by_role("dialog")
        expect(confirmation).to_be_visible(timeout=15000)
        confirm_button = confirmation.get_by_role(
            "button",
            name="Confirm",
            exact=True,
        )
        expect(confirm_button).to_be_visible(timeout=15000)
        expect(confirm_button).to_be_enabled(timeout=15000)

        with self.page.expect_download(timeout=120000) as download_info:
            confirm_button.click(timeout=15000)
            expect(confirm_button).to_be_hidden(timeout=60000)
            second_yes = self.page.get_by_role(
                "button",
                name="Yes",
                exact=True,
            )
            try:
                expect(second_yes).to_be_visible(timeout=5000)
            except AssertionError:
                LOGGER.info("No additional completion confirmation displayed")
            else:
                expect(second_yes).to_be_enabled(timeout=15000)
                second_yes.click(timeout=15000)

        download = download_info.value
        filename = Path(download.suggested_filename).name
        if Path(filename).suffix.lower() != ".pdf":
            raise AssertionError(
                "Complete Application produced a non-PDF download: "
                f"{download.suggested_filename!r}"
            )

        pdf_path = download_directory / filename
        download.save_as(pdf_path)
        if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            raise AssertionError(
                f"Complete Application PDF was not saved successfully: {pdf_path}"
            )
        with pdf_path.open("rb") as saved_pdf:
            signature = saved_pdf.read(5)
        if signature != b"%PDF-":
            raise AssertionError(
                f"Complete Application download is not a valid PDF: {pdf_path}"
            )

        LOGGER.info("Complete Application PDF saved to %s", pdf_path)
        return pdf_path

    def wait_for_application_completion(self, timeout: int = 120000) -> None:
        """Wait for completion to redirect away from application details."""
        LOGGER.info("Waiting for application completion redirect")
        expect(self.page).not_to_have_url(
            re.compile(r".*/admin/applications#/details/.*"),
            timeout=timeout,
        )
        LOGGER.info("Completion redirect detected: %s", self.page.url)

    def reload_application_details(self) -> None:
        """Reload the application route and wait for the details page."""
        self.page.reload(wait_until="domcontentloaded")
        expect(self.page).to_have_url(
            re.compile(
                rf".*/admin/applications#/details/"
                rf"\d+/(?:details|action-items|products)(?:/.*)?"
            ),
            timeout=30000,
        )
        expect(self.application_status_value()).to_be_visible(timeout=30000)

    @staticmethod
    def _model_list_column_index(model_row: Locator) -> int:
        """Find the List column in tables with semantic or plain-cell headers."""
        table = model_row.locator("xpath=ancestor::table[1]")
        header_row = table.get_by_role("row").first
        headers = header_row.get_by_role("columnheader").all_inner_texts()
        if not headers:
            headers = header_row.get_by_role("cell").all_inner_texts()
        header_texts = [text.strip() for text in headers]

        if header_texts.count("List") != 1:
            raise AssertionError(
                "Expected exactly one List status column in the model table; "
                f"found headers: {header_texts}"
            )

        return header_texts.index("List")

    def validate_model_recommendable(self, model_number: str) -> None:

        """Verify the target model's List radio is selected."""

        model_cell = self.page.get_by_role(

            "cell",

            name=model_number,

            exact=True,

        )

        expect(model_cell).to_have_count(1, timeout=60000)

        model_row = model_cell.locator("xpath=ancestor::tr[1]")



        list_status = (
            model_row.get_by_role("cell")
            .nth(self._model_list_column_index(model_row))
            .get_by_role("radio")
        )

        expect(list_status).to_have_count(1, timeout=15000)

        expect(list_status).to_be_enabled(timeout=15000)

        expect(list_status).to_be_checked(timeout=60000)

        LOGGER.info(

            "Uploaded model is Recommendable: %s",

            model_number,

        )



    def models_are_recommendable(

        self,

        model_numbers: tuple[str, ...],

    ) -> bool:

        """Check whether every expected workbook model is already listed."""

        for model_number in model_numbers:

            model_cell = self.page.get_by_role(

                "cell",

                name=model_number,

                exact=True,

            )

            expect(model_cell).to_have_count(1, timeout=60000)

            model_row = model_cell.locator("xpath=ancestor::tr[1]")

            list_status = (
                model_row.get_by_role("cell")
                .nth(self._model_list_column_index(model_row))
                .get_by_role("radio")
            )

            expect(list_status).to_have_count(1, timeout=15000)

            expect(list_status).to_be_enabled(timeout=15000)

            if not list_status.is_checked():

                return False

        return True



    def set_model_recommendable(self, model_number: str) -> None:

        """Set only the specified model's recommendation status to List."""

        model_cell = self.page.get_by_role(

            "cell",

            name=model_number,

            exact=True,

        )

        expect(model_cell).to_have_count(1, timeout=60000)

        model_row = model_cell.locator("xpath=ancestor::tr[1]")

        list_status = (
            model_row.get_by_role("cell")
            .nth(self._model_list_column_index(model_row))
            .get_by_role("radio")
        )

        expect(list_status).to_have_count(1, timeout=15000)

        expect(list_status).to_be_enabled(timeout=15000)

        list_status.click(timeout=15000)

        expect(list_status).to_be_checked(timeout=60000)

        LOGGER.info(

            "Set only model %s to List",

            model_number,

        )



    def set_application_recommendation_list(self) -> None:

        """Select the application-level Staff Recommendation List option."""

        recommendation_table = self.page.locator(

            "table.table-bordered"

        ).filter(has=self.page.get_by_text("List", exact=True))

        expect(recommendation_table).to_have_count(1, timeout=30000)



        list_option = recommendation_table.get_by_role(

            "cell",

            name="List",

            exact=True,

        ).get_by_role("checkbox")

        expect(list_option).to_have_count(1, timeout=15000)

        expect(list_option).to_be_enabled(timeout=15000)

        if not list_option.is_checked():

            list_option.check(timeout=15000)

        expect(list_option).to_be_checked(timeout=60000)

        LOGGER.info("Application Staff Recommendation List selected")



    def set_application_status_completed(self) -> None:

        """Set Application Status to Completed and save the change."""

        application_status = self.page.get_by_label(

            "Application Status",

            exact=True,

        )

        expect(application_status).to_have_count(1, timeout=30000)

        expect(application_status).to_be_visible(timeout=15000)

        application_status.select_option(label="Completed", timeout=15000)

        completed_value = application_status.input_value()



        save_button = self.page.get_by_role(

            "button",

            name="Save",

            exact=True,

        )

        expect(save_button).to_have_count(1, timeout=15000)

        expect(save_button).to_be_visible(timeout=15000)

        expect(save_button).to_be_enabled(timeout=15000)

        save_button.click(timeout=15000)



        expect(application_status).to_have_value(

            completed_value,

            timeout=60000,

        )

        expect(

            self.page.get_by_text("Completed", exact=True).first

        ).to_be_visible(timeout=60000)

        LOGGER.info("Application status is Completed")



    # ==================================================================

    # Manage Models

    # ==================================================================



    def click_manage_models(self) -> None:



        LOGGER.info(

            "Clicking Manage Models"

        )



        manage_models = self.page.locator(

            self.MANAGE_MODELS

        )



        expect(manage_models).to_have_count(

            1,

            timeout=30000,

        )



        expect(manage_models).to_be_visible(

            timeout=30000,

        )



        expect(manage_models).to_be_enabled(

            timeout=15000,

        )



        manage_models.scroll_into_view_if_needed(

            timeout=10000,

        )



        manage_models.click(

            timeout=15000,

        )



        LOGGER.info(

            "Manage Models menu opened"

        )



    # ==================================================================

    # Upload Model Template

    # ==================================================================



    def upload_model_template(

        self,

        file_path: str,

    ) -> None:



        template_path = Path(

            file_path

        )



        LOGGER.info(

            "Preparing Model Template upload: %s",

            template_path,

        )



        if not template_path.exists():



            raise FileNotFoundError(

                f"Model Template does not exist: "

                f"{template_path}"

            )



        if not template_path.is_file():



            raise FileNotFoundError(

                f"Model Template path is not a file: "

                f"{template_path}"

            )



        LOGGER.info(

            "Model Template exists: %s",

            template_path,

        )



        upload_link = self.page.locator(

            self.UPLOAD_MODEL_TEMPLATE

        )



        expect(upload_link).to_have_count(

            1,

            timeout=30000,

        )



        expect(upload_link).to_be_visible(

            timeout=30000,

        )



        upload_link.scroll_into_view_if_needed(

            timeout=10000,

        )



        LOGGER.info(

            "Clicking Upload Model Template "

            "and waiting for file chooser"

        )



        with self.page.expect_file_chooser(

            timeout=15000

        ) as file_chooser_info:



            upload_link.click(

                timeout=15000

            )



        file_chooser = (

            file_chooser_info.value

        )



        LOGGER.info(

            "Browser file chooser captured"

        )



        file_chooser.set_files(

            str(template_path)

        )



        LOGGER.info(

            "Model Template selected successfully: %s",

            template_path.name,

        )



    # ==================================================================

    # Upload Models Popup

    # ==================================================================



    def validate_upload_models_popup(self) -> None:



        LOGGER.info(

            "Waiting for Upload Models confirmation popup"

        )



        popup = self.page.get_by_role(

            "dialog"

        ).filter(

            has_text=self.UPLOAD_MODELS_TITLE

        )



        expect(popup).to_have_count(

            1,

            timeout=30000,

        )



        expect(popup).to_be_visible(

            timeout=30000

        )



        title = popup.get_by_role(

            "heading",

            name=re.compile(

                rf"^{re.escape(self.UPLOAD_MODELS_TITLE)}(?:\s|$)"

            ),

        )



        expect(title).to_be_visible(

            timeout=15000

        )



        LOGGER.info(

            "Upload Models confirmation popup displayed"

        )



    # ==================================================================

    # Confirm Upload

    # ==================================================================



    def confirm_upload_model_template(self) -> None:



        LOGGER.info(

            "Clicking Yes on Upload Models popup"

        )



        popup = self.page.get_by_role(

            "dialog"

        ).filter(

            has_text=self.UPLOAD_MODELS_TITLE

        )



        expect(popup).to_be_visible(

            timeout=30000,

        )



        yes_button = popup.get_by_role(

            "button",

            name="Yes",

            exact=True,

        )



        expect(yes_button).to_have_count(

            1,

            timeout=30000,

        )



        expect(yes_button).to_be_visible(

            timeout=15000,

        )



        expect(yes_button).to_be_enabled(

            timeout=15000,

        )



        yes_button.click(

            timeout=15000

        )



        LOGGER.info(

            "Upload confirmation accepted"

        )



    # ==================================================================

    # Upload Success

    # ==================================================================



    def validate_upload_success(

        self,

        expected_model_number: str | None = None,

    ) -> None:



        LOGGER.info(

            "Waiting for Upload Models dialog to close"

        )



        popup = self.page.get_by_role(

            "dialog"

        ).filter(

            has_text=self.UPLOAD_MODELS_TITLE

        )



        expect(popup).to_have_count(

            0,

            timeout=60000,

        )



        if expected_model_number is not None:

            model_cell = self.page.get_by_role(

                "cell",

                name=expected_model_number,

                exact=True,

            )



            expect(model_cell).to_be_visible(

                timeout=60000,

            )



            LOGGER.info(

                "Uploaded model is visible: %s",

                expected_model_number,

            )

        else:

            LOGGER.info(

                "Upload dialog closed; no expected model was configured"

            )



    def is_model_uploaded(self, model_number: str) -> bool:

        """Check whether the exact model row is already present."""

        model_cell = self.page.get_by_role(

            "cell",

            name=model_number,

            exact=True,

        )

        count = model_cell.count()

        if count > 1:

            raise AssertionError(

                f"Expected at most one model cell for '{model_number}', "

                f"found {count}."

            )

        return count == 1



    def list_all_unrecommended_models(

        self,

        model_numbers: tuple[str, ...],

    ) -> None:

        """List un-recommended models and validate every workbook model."""

        LOGGER.info(

            "Listing all un-recommended models for this application"

        )



        list_all_button = self.page.locator(

            self.LIST_ALL_MODELS_BUTTON

        )

        expect(list_all_button).to_have_count(1, timeout=30000)

        expect(list_all_button).to_be_visible(timeout=15000)

        expect(list_all_button).to_be_enabled(timeout=15000)

        list_all_button.click(timeout=15000)



        confirmation = self.page.get_by_role("dialog").filter(

            has_text=re.compile(

                r"Are you sure you want to List all the "

                r"un-recommended models on this application\\?"

            )

        )

        expect(confirmation).to_have_count(1, timeout=30000)

        expect(confirmation).to_be_visible(timeout=15000)



        confirm_button = confirmation.get_by_role(

            "button",

            name="Confirm",

            exact=True,

        )

        expect(confirm_button).to_have_count(1, timeout=15000)

        expect(confirm_button).to_be_enabled(timeout=15000)

        confirm_button.click(timeout=15000)



        expect(confirmation).to_have_count(0, timeout=60000)

        for model_number in model_numbers:

            self.validate_model_recommendable(model_number)



        LOGGER.info(

            "All un-recommended models listed; uploaded model is Recommendable: %s",

            model_number,

        )



    # ==================================================================

    # Complete Upload Flow

    # ==================================================================



    def upload_model_template_flow(

        self,

        file_path: str,

        expected_model_number: str | None = None,

    ) -> None:



        LOGGER.info(

            "Starting complete Model Template upload flow"

        )



        self.click_manage_models()



        self.upload_model_template(

            file_path

        )



        self.validate_upload_models_popup()



        self.confirm_upload_model_template()



        self.validate_upload_success(

            expected_model_number

        )



        LOGGER.info(

            "Complete Model Template upload flow finished successfully"

        )
