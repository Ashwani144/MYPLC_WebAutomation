"""
Applications Page Object for MTPLC.

Handles:
    Applications
    -> Incomplete
    -> Application
    -> Models
    -> All Models
    -> Select Model
    -> Add Row
    -> After
    -> Draft Row Data
    -> Save
    -> Confirmation
    -> Success Validation
"""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Page, expect

from mtplc.config.settings import settings
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class ApplicationsPage(BasePage):
    """Page Object for MTPLC Applications / Models functionality."""

    # ============================================================
    # APPLICATION NAVIGATION LOCATORS
    # ============================================================

    APPLICATIONS = (
        "xpath=//a[@href='#/']"
        "//span[@class='nav-label']"
        "[normalize-space()='Applications']"
    )

    INCOMPLETE = (
        "xpath=//a[@href='/Admin/applications/incomplete#/incomplete']"
    )

    ALL_APPLICATIONS = (
        "xpath=//a[@href='/Admin/applications#/all-applications']"
    )

    MODELS = (
        "xpath=//a[@ng-click=\"aadc.selectTab('products')\"]"
    )

    # ============================================================
    # MODELS LOCATORS
    # ============================================================

    ALL_MODELS = (
        "xpath=//button[contains(normalize-space(.), 'All Models')]"
    )

    ACTIVE_ALL_MODELS = (
        "xpath=//button["
        "contains(normalize-space(.), 'All Models') "
        "and contains(@class, 'manage-models-view-active')"
        "]"
    )

    MODEL_NUMBER = "430940"

    MODEL_ROW_TEMPLATE = (
        "xpath=//tr[.//a[normalize-space()='{model_number}']]"
    )

    MODEL_CHECKBOX_TEMPLATE = (
        "xpath=//tr[.//a[normalize-space()='{model_number}']]"
        "//input[@type='checkbox']"
    )

    # ============================================================
    # ADD ROW LOCATORS
    # ============================================================

    # Do NOT use normalize-space()='Add Row'.
    # The button may contain additional whitespace/icon content.
    ADD_ROW = (
        "xpath=//button[contains(normalize-space(.), 'Add Row')]"
    )

    AFTER = (
        "xpath=//a[@ng-click=\""
        "satc.addProductDraftRow("
        "satc.selectedActionBarSection, 'After')"
        "\"]"
    )

    AFTER_BY_NG_CLICK = (
        "xpath=//a[contains(@ng-click, 'addProductDraftRow') "
        "and contains(@ng-click, \"'After'\")]"
    )

    OPEN_DROPDOWN = (
        "css=ul.dropdown-menu:visible"
    )

    # ============================================================
    # DRAFT ROW LOCATORS
    # ============================================================

    DRAFT_MODEL_NUMBER = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]/td[2]/div[1]"
    )

    DRAFT_DESCRIPTION = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]/td[3]/div[1]"
    )

    DRAFT_IAPMO_WESTAND = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]/td[4]/div[1]"
    )

    DRAFT_CAL_GREEN = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]/td[5]/div[1]"
    )

    DRAFT_LEED = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]/td[6]/div[1]"
    )

    # ============================================================
    # DRAFT EDITABLE FIELD LOCATORS
    # ============================================================

    DRAFT_MODEL_NUMBER_INPUT = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        "/td[2]//*["
        "self::input or "
        "self::textarea or "
        "@contenteditable='true' or "
        "@role='combobox'"
        "]"
    )

    DRAFT_DESCRIPTION_INPUT = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        "/td[3]//*["
        "self::input or "
        "self::textarea or "
        "@contenteditable='true' or "
        "@role='combobox'"
        "]"
    )

    DRAFT_IAPMO_WESTAND_INPUT = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        "/td[4]//*["
        "self::input or "
        "self::textarea or "
        "@contenteditable='true' or "
        "@role='combobox'"
        "]"
    )

    DRAFT_CAL_GREEN_INPUT = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        "/td[5]//*["
        "self::input or "
        "self::textarea or "
        "@contenteditable='true' or "
        "@role='combobox'"
        "]"
    )

    DRAFT_LEED_INPUT = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        "/td[6]//*["
        "self::input or "
        "self::textarea or "
        "@contenteditable='true' or "
        "@role='combobox'"
        "]"
    )

    # Exact HTML structure shared by the application for rich fields.
    # Example:
    #
    # <div class="form-control input-sm draft-rich-input ng-binding"
    #      contenteditable="true"
    #      ng-bind-html="..."
    #      ng-blur="satc.setDraftProductEavFromHtml(...)">
    #
    DRAFT_RICH_INPUT = (
        "div.draft-rich-input[contenteditable='true']"
    )

    # ============================================================
    # SAVE / CONFIRMATION / SUCCESS
    # ============================================================

    SAVE = (
        "xpath=//button[@class='btn btn-success btn-sm ng-scope']"
    )

    YES = (
        "xpath=//button[normalize-space()='Yes']"
    )

    SUCCESS_MESSAGE = (
        "xpath=//*[contains("
        "normalize-space(.), "
        "'Models data updated successfully'"
        ")]"
    )

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ============================================================
    # APPLICATIONS
    # ============================================================

    def click_applications(self) -> None:
        """Open Applications module."""

        LOGGER.info("Clicking Applications module")

        applications = self.page.locator(self.APPLICATIONS)

        expect(
            applications
        ).to_have_count(
            1,
            timeout=30000,
        )

        expect(
            applications
        ).to_be_visible(
            timeout=10000,
        )

        applications.scroll_into_view_if_needed(
            timeout=10000
        )

        applications.click()

        LOGGER.info("Applications module clicked")
        expect(
            self.page.locator(self.INCOMPLETE)
        ).to_be_visible(timeout=30000)

    def open_incomplete_applications(self) -> None:
        """Open the Incomplete Applications route without using the sidebar."""
        url = (
            f"{settings.base_url.rstrip('/')}"
            "/Admin/applications/incomplete#/incomplete"
        )
        LOGGER.info("Opening Incomplete Applications directly")
        self.page.goto(url, wait_until="commit")
        expect(self.page).to_have_url(
            re.compile(r".*/Admin/applications/incomplete#/incomplete/?"),
            timeout=30000,
        )
        expect(
            self.page.get_by_role("combobox", name="Show entries")
        ).to_be_visible(timeout=60000)
        LOGGER.info("Incomplete Applications table is ready")

    def open_all_applications(self) -> None:
        """Open the All Applications route without using the sidebar."""
        url = (
            f"{settings.base_url.rstrip('/')}"
            "/Admin/applications#/all-applications"
        )
        LOGGER.info("Opening All Applications directly")
        self.page.goto(url, wait_until="commit")
        expect(self.page).to_have_url(
            re.compile(r".*/Admin/applications#/all-applications/?"),
            timeout=30000,
        )
        expect(
            self.page.get_by_role("combobox", name="Show entries")
        ).to_be_visible(timeout=60000)
        LOGGER.info("All Applications table is ready")

    # ============================================================
    # INCOMPLETE
    # ============================================================

    def click_incomplete(self) -> None:
        """Open Incomplete applications."""

        LOGGER.info("Clicking Incomplete submenu")

        incomplete = self.page.locator(self.INCOMPLETE)

        expect(
            incomplete
        ).to_be_visible(
            timeout=30000
        )

        incomplete.click()

        LOGGER.info("Incomplete submenu clicked")

        expect(
            self.page.get_by_role("combobox", name="Show entries")
        ).to_be_visible(timeout=30000)

        LOGGER.info("Incomplete page opened")

    # ============================================================
    # OPEN APPLICATION
    # ============================================================

    def open_application(
        self,
        application_number: str = "P-252956",
    ) -> None:
        """Search the Incomplete applications table and open the match."""

        LOGGER.info(
            "Opening application %s",
            application_number,
        )

        entries_per_page = self.page.get_by_role(
            "combobox",
            name="Show entries",
        )

        if entries_per_page.count() == 1:
            entries_per_page.select_option(label="All")

        application = self.page.locator(
            "xpath=//a[normalize-space()="
            f"'{application_number}']"
        )

        expect(
            application
        ).to_be_visible(
            timeout=30000,
        )

        application.scroll_into_view_if_needed(
            timeout=10000
        )

        application.click()
        expect(self.page).to_have_url(
            re.compile(r".*#/details/\d+/details(?:/.*)?"),
            timeout=30000,
        )

        LOGGER.info(
            "Application %s opened",
            application_number,
        )

    def open_application_from_all(
        self,
        application_number: str,
    ) -> None:
        """Open an application from the All Applications listing."""
        LOGGER.info(
            "Opening application %s from All Applications",
            application_number,
        )

        self.open_all_applications()

        entries_per_page = self.page.get_by_role(
            "combobox",
            name="Show entries",
        )
        if entries_per_page.count() == 1:
            entries_per_page.select_option(label="All")

        application = self.page.get_by_role(
            "link",
            name=application_number,
            exact=True,
        )
        expect(application).to_be_visible(timeout=60000)
        application.scroll_into_view_if_needed(timeout=15000)
        application.click(timeout=15000)
        expect(self.page).to_have_url(
            re.compile(r".*#/details/\d+/details(?:/.*)?"),
            timeout=30000,
        )

        LOGGER.info(
            "Application %s opened from All Applications",
            application_number,
        )

    # ============================================================
    # MODELS TAB
    # ============================================================

    def click_models(self) -> None:
        """Open Models tab."""

        LOGGER.info("Clicking Models tab")

        models = self.page.locator(self.MODELS)

        expect(
            models
        ).to_be_visible(
            timeout=30000
        )

        models.scroll_into_view_if_needed(
            timeout=10000
        )

        models.click()

        LOGGER.info("Models tab clicked")

        self.page.wait_for_timeout(1500)

        LOGGER.info("Models section loaded")

    # ============================================================
    # ALL MODELS
    # ============================================================

    def click_all_models(self) -> None:
        """Select All Models."""

        LOGGER.info("Clicking All Models")

        last_error = None

        for attempt in range(1, 4):

            try:

                LOGGER.info(
                    "All Models attempt %d/3",
                    attempt,
                )

                all_models = self.page.locator(
                    self.ALL_MODELS
                )

                expect(
                    all_models
                ).to_be_visible(
                    timeout=15000
                )

                all_models.scroll_into_view_if_needed(
                    timeout=10000
                )

                self.page.wait_for_timeout(500)

                # Re-resolve immediately before click.
                all_models = self.page.locator(
                    self.ALL_MODELS
                )

                visible_count = 0
                visible_button = None

                for index in range(all_models.count()):

                    candidate = all_models.nth(index)

                    try:

                        if candidate.is_visible():

                            visible_count += 1
                            visible_button = candidate

                    except Exception:
                        continue

                LOGGER.info(
                    "Visible All Models buttons: %d",
                    visible_count,
                )

                if visible_button is None:
                    raise AssertionError(
                        "No visible All Models button found"
                    )

                visible_button.click(
                    force=True,
                    timeout=15000,
                )

                LOGGER.info(
                    "All Models button clicked"
                )

                self.page.wait_for_timeout(1500)

                active = self.page.locator(
                    self.ACTIVE_ALL_MODELS
                )

                expect(
                    active
                ).to_be_visible(
                    timeout=15000
                )

                LOGGER.info(
                    "All Models is active"
                )

                return

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "All Models attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(1500)

        raise AssertionError(
            "Unable to select All Models after 3 attempts. "
            f"Last error: {last_error}"
        )

    # ============================================================
    # SELECT MODEL
    # ============================================================

    def select_model(
        self,
        model_number: str = MODEL_NUMBER,
    ) -> None:
        """Select model checkbox."""

        LOGGER.info(
            "Selecting model %s",
            model_number,
        )

        model_link = self.page.locator(
            "xpath=//a[normalize-space()="
            f"'{model_number}']"
        )

        expect(
            model_link
        ).to_be_visible(
            timeout=30000
        )

        LOGGER.info(
            "Model %s is visible",
            model_number,
        )

        last_error = None

        for attempt in range(1, 4):

            try:

                LOGGER.info(
                    "Selecting model %s - attempt %d/3",
                    model_number,
                    attempt,
                )

                row = self.page.locator(
                    self.MODEL_ROW_TEMPLATE.format(
                        model_number=model_number
                    )
                )

                expect(
                    row
                ).to_be_visible(
                    timeout=15000
                )

                checkbox = self.page.locator(
                    self.MODEL_CHECKBOX_TEMPLATE.format(
                        model_number=model_number
                    )
                )

                expect(
                    checkbox
                ).to_have_count(
                    1,
                    timeout=15000
                )

                expect(
                    checkbox
                ).to_be_visible(
                    timeout=10000
                )

                checked = checkbox.is_checked()

                LOGGER.info(
                    "Model %s checkbox initial state: %s",
                    model_number,
                    checked,
                )

                if not checked:

                    LOGGER.info(
                        "Clicking checkbox for model %s",
                        model_number,
                    )

                    checkbox.click(
                        force=True,
                        timeout=10000,
                    )

                # Re-resolve after Angular updates the DOM.
                checkbox = self.page.locator(
                    self.MODEL_CHECKBOX_TEMPLATE.format(
                        model_number=model_number
                    )
                )

                expect(
                    checkbox
                ).to_be_checked(
                    timeout=15000
                )

                LOGGER.info(
                    "Model %s selected successfully",
                    model_number,
                )

                return

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "Model selection attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(1500)

        raise AssertionError(
            f"Unable to select model {model_number}. "
            f"Last error: {last_error}"
        )

    # ============================================================
    # FIND VISIBLE ADD ROW BUTTON
    # ============================================================

    def _get_visible_add_row_button(self):
        """
        Return the currently visible Add Row button.

        The application may temporarily contain more than one
        Add Row element while Angular/Bootstrap updates the DOM.
        Therefore we do not require count == 1.
        """

        buttons = self.page.locator(
            self.ADD_ROW
        )

        count = buttons.count()

        LOGGER.info(
            "Add Row matching elements found: %d",
            count,
        )

        for index in range(count):

            try:

                candidate = buttons.nth(index)

                if candidate.is_visible():

                    LOGGER.info(
                        "Visible Add Row button found at index %d",
                        index,
                    )

                    return candidate

            except Exception as exc:

                LOGGER.debug(
                    "Add Row candidate %d unavailable: %s",
                    index,
                    exc,
                )

        return None

    # ============================================================
    # ADD ROW
    # ============================================================

    def click_add_row(self) -> None:
        """Open Add Row dropdown."""

        LOGGER.info("Clicking Add Row")

        last_error = None

        for attempt in range(1, 6):

            try:

                LOGGER.info(
                    "Add Row attempt %d/5",
                    attempt,
                )

                # Wait for the page to settle.
                self.page.wait_for_timeout(500)

                add_row = self._get_visible_add_row_button()

                if add_row is None:

                    raise AssertionError(
                        "No visible Add Row button found"
                    )

                try:

                    add_row.scroll_into_view_if_needed(
                        timeout=5000
                    )

                except Exception:

                    LOGGER.debug(
                        "Add Row scroll skipped"
                    )

                self.page.wait_for_timeout(300)

                # IMPORTANT:
                # Re-resolve again immediately before clicking.
                add_row = self._get_visible_add_row_button()

                if add_row is None:

                    raise AssertionError(
                        "Add Row button disappeared before click"
                    )

                add_row.click(
                    force=True,
                    timeout=10000,
                )

                LOGGER.info(
                    "Add Row clicked"
                )

                # Wait for Bootstrap dropdown.
                dropdown = self.page.locator(
                    self.OPEN_DROPDOWN
                )

                expect(
                    dropdown
                ).to_be_visible(
                    timeout=10000
                )

                LOGGER.info(
                    "Add Row dropdown is open"
                )

                return

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "Add Row attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(1200)

        raise AssertionError(
            "Unable to open Add Row dropdown after 5 attempts. "
            f"Last error: {last_error}"
        )

    # ============================================================
    # AFTER
    # ============================================================

    def click_after(self) -> None:
        """
        Click After from the Add Row dropdown.

        AngularJS/Bootstrap can recreate the dropdown DOM,
        therefore the dropdown and After option are resolved
        again before every click attempt.
        """

        LOGGER.info("Clicking After")

        last_error = None

        for attempt in range(1, 6):

            try:

                LOGGER.info(
                    "After click attempt %d/5",
                    attempt,
                )

                dropdown = self.page.locator(
                    self.OPEN_DROPDOWN
                )

                expect(
                    dropdown
                ).to_be_visible(
                    timeout=10000
                )

                after = dropdown.locator(
                    "a"
                ).filter(
                    has_text=re.compile(
                        r"^\s*After\s*$"
                    )
                )

                if after.count() == 0:

                    after = self.page.locator(
                        self.AFTER_BY_NG_CLICK
                    ).filter(
                        has=self.page.locator(
                            "xpath=ancestor::ul[contains(@class,'dropdown-menu')]"
                        )
                    )

                expect(
                    after
                ).to_have_count(
                    1,
                    timeout=10000
                )

                expect(
                    after
                ).to_be_visible(
                    timeout=10000
                )

                LOGGER.info(
                    "After option is visible"
                )

                # Re-resolve one more time immediately before click.
                dropdown = self.page.locator(
                    self.OPEN_DROPDOWN
                )

                after = dropdown.locator(
                    "a"
                ).filter(
                    has_text=re.compile(
                        r"^\s*After\s*$"
                    )
                )

                expect(
                    after
                ).to_be_visible(
                    timeout=5000
                )

                after.click(
                    force=True,
                    timeout=10000,
                )

                LOGGER.info(
                    "After option clicked successfully"
                )

                break

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "After click attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(1000)

        else:

            raise AssertionError(
                "Unable to click After option after "
                f"5 attempts. Last error: {last_error}"
            )

        # ========================================================
        # WAIT FOR NEW DRAFT ROW
        # ========================================================

        LOGGER.info(
            "Waiting for draft row after clicking After"
        )

        draft_rows = self.page.locator(
            "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
        )

        expect(
            draft_rows.last
        ).to_be_visible(
            timeout=30000
        )

        LOGGER.info(
            "Draft row appeared successfully"
        )

        # Give Angular time to render editable controls.
        self.page.wait_for_timeout(1000)

    # ============================================================
    # DRAFT FIELD HELPER
    # ============================================================

    def _fill_draft_field(
        self,
        locator_xpath: str,
        value: str,
        fallback_xpath: str | None = None,
    ) -> None:
        """
        Fill a draft field reliably.

        Handles:
            input
            textarea
            select
            contenteditable
            Angular combobox

        Important:
        Angular may destroy/recreate the draft row after a field
        is updated. Therefore row, cell and editable control are
        resolved again on every retry.
        """

        LOGGER.info(
            "Filling draft field with value: %s",
            value,
        )

        # ========================================================
        # MAP FIELD TO TABLE COLUMN
        # ========================================================

        column_map = {
            self.DRAFT_MODEL_NUMBER: 2,
            self.DRAFT_DESCRIPTION: 3,
            self.DRAFT_IAPMO_WESTAND: 4,
            self.DRAFT_CAL_GREEN: 5,
            self.DRAFT_LEED: 6,
        }

        column_number = column_map.get(
            locator_xpath
        )

        if column_number is None:

            raise AssertionError(
                "Unknown draft field locator: "
                f"{locator_xpath}"
            )

        LOGGER.info(
            "Draft field mapped to column %s",
            column_number,
        )

        # ========================================================
        # EDITABLE SELECTOR
        # ========================================================

        editable_selector = (
            "input, "
            "textarea, "
            "select, "
            "[contenteditable='true'], "
            "[role='combobox']"
        )

        # ========================================================
        # RETRY ENTIRE LOOKUP + ACTION
        # ========================================================

        last_error = None

        for attempt in range(1, 9):

            try:

                LOGGER.info(
                    "Draft field attempt %d/8 for column %s",
                    attempt,
                    column_number,
                )

                # ------------------------------------------------
                # Fresh draft row lookup
                # ------------------------------------------------

                draft_rows = self.page.locator(
                    "xpath=//tbody/tr[contains("
                    "@class, 'draft-product-row')]"
                )

                row_count = draft_rows.count()

                LOGGER.info(
                    "Draft rows found: %d",
                    row_count,
                )

                if row_count == 0:

                    raise AssertionError(
                        "No draft-product-row found"
                    )

                # Always use latest draft row.
                draft_row = draft_rows.last

                expect(
                    draft_row
                ).to_be_visible(
                    timeout=5000
                )

                # ------------------------------------------------
                # Fresh cell lookup
                # ------------------------------------------------

                cell = draft_row.locator(
                    f"xpath=./td[{column_number}]"
                )

                expect(
                    cell
                ).to_be_attached(
                    timeout=5000
                )

                LOGGER.info(
                    "Draft cell located for column %s",
                    column_number,
                )

                # ------------------------------------------------
                # First look specifically for the application's
                # known rich input.
                # ------------------------------------------------

                rich_input = cell.locator(
                    self.DRAFT_RICH_INPUT
                )

                rich_count = rich_input.count()

                LOGGER.info(
                    "Known draft-rich-input controls: %d",
                    rich_count,
                )

                if rich_count > 0:

                    for index in range(rich_count):

                        try:

                            candidate = rich_input.nth(index)

                            if not candidate.is_visible(
                                timeout=2000
                            ):
                                continue

                            LOGGER.info(
                                "Using draft-rich-input "
                                "candidate %d in column %s",
                                index,
                                column_number,
                            )

                            # ------------------------------------------------
                            # IMPORTANT:
                            # Playwright fill() supports contenteditable.
                            # This is much more stable than:
                            # click -> Ctrl+A -> type
                            # ------------------------------------------------

                            candidate.fill(
                                value,
                                timeout=5000,
                            )

                            # Verify.
                            actual_text = (
                                candidate.inner_text()
                            )

                            if value in actual_text:

                                LOGGER.info(
                                    "Draft rich field filled successfully: %s",
                                    value,
                                )

                                return

                            # Angular may update the DOM immediately.
                            self.page.wait_for_timeout(300)

                            candidate = cell.locator(
                                self.DRAFT_RICH_INPUT
                            ).first

                            actual_text = (
                                candidate.inner_text()
                            )

                            if value in actual_text:

                                LOGGER.info(
                                    "Draft rich field verified after DOM refresh: %s",
                                    value,
                                )

                                return

                        except Exception as exc:

                            last_error = exc

                            LOGGER.debug(
                                "Known rich input candidate %d failed: %s",
                                index,
                                exc,
                            )

                            continue

                # ------------------------------------------------
                # Generic editable controls
                # ------------------------------------------------

                editable_controls = cell.locator(
                    editable_selector
                )

                control_count = editable_controls.count()

                LOGGER.info(
                    "Generic editable controls found: %d",
                    control_count,
                )

                for index in range(control_count):

                    try:

                        # Re-resolve the control from the current
                        # cell before every interaction.
                        candidate = cell.locator(
                            editable_selector
                        ).nth(index)

                        if not candidate.is_visible(
                            timeout=2000
                        ):
                            continue

                        LOGGER.info(
                            "Using editable candidate %d "
                            "in column %s",
                            index,
                            column_number,
                        )

                        tag_name = candidate.evaluate(
                            "(el) => el.tagName.toLowerCase()"
                        )

                        # ------------------------------------------------
                        # INPUT / TEXTAREA
                        # ------------------------------------------------

                        if tag_name in (
                            "input",
                            "textarea",
                        ):

                            candidate.fill(
                                value,
                                timeout=5000,
                            )

                            LOGGER.info(
                                "Draft input/textarea filled: %s",
                                value,
                            )

                            return

                        # ------------------------------------------------
                        # SELECT
                        # ------------------------------------------------

                        if tag_name == "select":

                            try:

                                candidate.select_option(
                                    label=value,
                                    timeout=5000,
                                )

                            except Exception:

                                candidate.select_option(
                                    value=value,
                                    timeout=5000,
                                )

                            LOGGER.info(
                                "Draft select field filled: %s",
                                value,
                            )

                            return

                        # ------------------------------------------------
                        # CONTENTEDITABLE
                        # ------------------------------------------------

                        if (
                            candidate.get_attribute(
                                "contenteditable"
                            )
                            == "true"
                        ):

                            # Use fill() instead of keyboard typing.
                            candidate.fill(
                                value,
                                timeout=5000,
                            )

                            LOGGER.info(
                                "Draft contenteditable field filled: %s",
                                value,
                            )

                            return

                        # ------------------------------------------------
                        # ANGULAR COMBOBOX
                        # ------------------------------------------------

                        if (
                            candidate.get_attribute(
                                "role"
                            )
                            == "combobox"
                        ):

                            candidate.click(
                                force=True,
                                timeout=5000,
                            )

                            candidate.fill(
                                value,
                                timeout=5000,
                            )

                            self.page.wait_for_timeout(
                                500
                            )

                            option = self.page.locator(
                                "xpath=//*["
                                "self::li or "
                                "self::option or "
                                "@role='option'"
                                "]"
                            ).filter(
                                has_text=re.compile(
                                    rf"^\s*{re.escape(value)}\s*$"
                                )
                            )

                            option_count = option.count()

                            for option_index in range(
                                option_count
                            ):

                                try:

                                    option_candidate = (
                                        option.nth(
                                            option_index
                                        )
                                    )

                                    if option_candidate.is_visible():

                                        option_candidate.click(
                                            force=True,
                                            timeout=5000,
                                        )

                                        LOGGER.info(
                                            "Draft Angular combobox "
                                            "filled: %s",
                                            value,
                                        )

                                        return

                                except Exception:

                                    continue

                    except Exception as exc:

                        last_error = exc

                        LOGGER.debug(
                            "Editable candidate %d failed "
                            "for column %s: %s",
                            index,
                            column_number,
                            exc,
                        )

                        continue

                # ------------------------------------------------
                # Fallback locator
                # ------------------------------------------------

                if fallback_xpath:

                    LOGGER.info(
                        "Trying fallback draft field locator"
                    )

                    fallback = self.page.locator(
                        fallback_xpath
                    )

                    fallback_count = fallback.count()

                    LOGGER.info(
                        "Fallback controls found: %d",
                        fallback_count,
                    )

                    for index in range(
                        fallback_count
                    ):

                        try:

                            candidate = fallback.nth(
                                index
                            )

                            if not candidate.is_visible(
                                timeout=2000
                            ):
                                continue

                            tag_name = candidate.evaluate(
                                "(el) => el.tagName.toLowerCase()"
                            )

                            if tag_name in (
                                "input",
                                "textarea",
                            ):

                                candidate.fill(
                                    value,
                                    timeout=5000,
                                )

                            elif tag_name == "select":

                                try:

                                    candidate.select_option(
                                        label=value,
                                        timeout=5000,
                                    )

                                except Exception:

                                    candidate.select_option(
                                        value=value,
                                        timeout=5000,
                                    )

                            elif (
                                candidate.get_attribute(
                                    "contenteditable"
                                )
                                == "true"
                            ):

                                candidate.fill(
                                    value,
                                    timeout=5000,
                                )

                            else:

                                candidate.click(
                                    force=True,
                                    timeout=5000,
                                )

                                candidate.fill(
                                    value,
                                    timeout=5000,
                                )

                            LOGGER.info(
                                "Draft fallback field filled: %s",
                                value,
                            )

                            return

                        except Exception as exc:

                            last_error = exc

                            LOGGER.debug(
                                "Fallback candidate %d failed: %s",
                                index,
                                exc,
                            )

                            continue

                # ------------------------------------------------
                # Wait before complete re-resolution.
                # ------------------------------------------------

                self.page.wait_for_timeout(
                    750
                )

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "Draft field attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(
                    1000
                )

        # ========================================================
        # FINAL FAILURE
        # ========================================================

        raise AssertionError(
            "Unable to locate/fill draft field "
            f"for column {column_number} "
            f"with value '{value}'. "
            f"Last error: {last_error}"
        )

    # ============================================================
    # DRAFT MODEL NUMBER
    # ============================================================

    def enter_draft_model_number(
        self,
        model_number: str,
    ) -> None:
        """Enter draft model number."""

        LOGGER.info(
            "Entering draft model number: %s",
            model_number,
        )

        self._fill_draft_field(
            self.DRAFT_MODEL_NUMBER,
            model_number,
            self.DRAFT_MODEL_NUMBER_INPUT,
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # DRAFT DESCRIPTION
    # ============================================================

    def enter_draft_description(
        self,
        description: str = "By Automation Test",
    ) -> None:
        """Enter draft description."""

        LOGGER.info(
            "Entering draft description: %s",
            description,
        )

        self._fill_draft_field(
            self.DRAFT_DESCRIPTION,
            description,
            self.DRAFT_DESCRIPTION_INPUT,
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # DRAFT IAPMO WESTAND
    # ============================================================

    def enter_draft_iapmo_westand(
        self,
        value: str = "Test",
    ) -> None:
        """Enter IAPMO WEStand value."""

        LOGGER.info(
            "Entering IAPMO WEStand: %s",
            value,
        )

        self._fill_draft_field(
            self.DRAFT_IAPMO_WESTAND,
            value,
            self.DRAFT_IAPMO_WESTAND_INPUT,
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # DRAFT CAL GREEN
    # ============================================================

    def enter_draft_cal_green(
        self,
        value: str = "Test",
    ) -> None:
        """Enter Cal Green value."""

        LOGGER.info(
            "Entering Cal Green: %s",
            value,
        )

        self._fill_draft_field(
            self.DRAFT_CAL_GREEN,
            value,
            self.DRAFT_CAL_GREEN_INPUT,
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # DRAFT LEED
    # ============================================================

    def enter_draft_leed(
        self,
        value: str = "Test",
    ) -> None:
        """Enter Leed value."""

        LOGGER.info(
            "Entering Leed value: %s",
            value,
        )

        self._fill_draft_field(
            self.DRAFT_LEED,
            value,
            self.DRAFT_LEED_INPUT,
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # COMPLETE DRAFT ROW
    # ============================================================

    def enter_draft_row_data(
        self,
        model_number: str = "100101",
        description: str = "By Automation Test",
        iapmo_westand: str = "Test",
        cal_green: str = "Test",
        leed: str = "Test",
    ) -> None:
        """Fill all fields in the newly created draft row."""

        LOGGER.info(
            "Entering complete draft row data"
        )

        self.enter_draft_model_number(
            model_number
        )

        self.enter_draft_description(
            description
        )

        self.enter_draft_iapmo_westand(
            iapmo_westand
        )

        self.enter_draft_cal_green(
            cal_green
        )

        self.enter_draft_leed(
            leed
        )

        LOGGER.info(
            "Draft row data entered successfully"
        )

    # ============================================================
    # SAVE
    # ============================================================

    def click_save(self) -> None:
        """Click Save from the bottom action bar."""

        LOGGER.info("Clicking Save")

        last_error = None

        for attempt in range(1, 4):

            try:

                LOGGER.info(
                    "Save attempt %d/3",
                    attempt,
                )

                save = self.page.locator(
                    self.SAVE
                )

                expect(
                    save.first
                ).to_be_visible(
                    timeout=15000
                )

                expect(
                    save.first
                ).to_be_enabled(
                    timeout=10000
                )

                try:

                    save.first.scroll_into_view_if_needed(
                        timeout=5000
                    )

                except Exception:

                    LOGGER.debug(
                        "Save scroll skipped"
                    )

                self.page.wait_for_timeout(500)

                save = self.page.locator(
                    self.SAVE
                )

                save.first.click(
                    force=True,
                    timeout=10000,
                )

                LOGGER.info(
                    "Save clicked successfully"
                )

                return

            except Exception as exc:

                last_error = exc

                LOGGER.warning(
                    "Save attempt %d failed: %s",
                    attempt,
                    exc,
                )

                self.page.wait_for_timeout(1000)

        raise AssertionError(
            "Unable to click Save after 3 attempts. "
            f"Last error: {last_error}"
        )

    # ============================================================
    # CONFIRM SAVE
    # ============================================================

    def confirm_save(self) -> None:
        """Confirm Save by clicking Yes."""

        LOGGER.info(
            "Waiting for Save confirmation"
        )

        yes = self.page.locator(
            self.YES
        )

        expect(
            yes
        ).to_be_visible(
            timeout=30000
        )

        LOGGER.info(
            "Save confirmation popup displayed"
        )

        yes.click(
            force=True
        )

        LOGGER.info(
            "Save confirmation Yes clicked"
        )

    # ============================================================
    # SUCCESS VALIDATION
    # ============================================================

    def validate_models_update_success(self) -> None:
        """Validate Models data updated successfully message."""

        LOGGER.info(
            "Waiting for Models update success message"
        )

        success = self.page.locator(
            self.SUCCESS_MESSAGE
        )

        expect(
            success.first
        ).to_be_visible(
            timeout=30000
        )

        LOGGER.info(
            "Models data updated successfully message validated"
        )

    # ============================================================
    # COMPLETE ADD MODEL FLOW
    # ============================================================

    def add_model_after(
        self,
        model_number: str = "100101",
        description: str = "By Automation Test",
        iapmo_westand: str = "Test",
        cal_green: str = "Test",
        leed: str = "Test",
    ) -> None:
        """Complete Add Model After flow."""

        self.click_add_row()

        self.click_after()

        self.enter_draft_row_data(
            model_number=model_number,
            description=description,
            iapmo_westand=iapmo_westand,
            cal_green=cal_green,
            leed=leed,
        )

        self.click_save()

        self.confirm_save()

        self.validate_models_update_success()

        LOGGER.info(
            "Add Model After flow completed successfully"
        )
