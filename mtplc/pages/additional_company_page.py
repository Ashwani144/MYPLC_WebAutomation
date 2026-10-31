"""Page object for adding an Additional Company and its first model row."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, expect

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class AdditionalCompanyPage(BasePage):
    """Create an Additional Company and save its associated model row."""

    ADDITIONAL_COMPANIES_TAB = (
        "xpath=//a[@ng-click="
        "\"aadc.selectTab('additional-companies')\"]"
    )
    ADD_ADDITIONAL_COMPANY = (
        "xpath=//a[@ng-click='aadc.addNewAddco()']"
    )

    COMPANY_NAME = "input[placeholder='Enter Additional Company Name']"
    BRAND_NAME = "input[placeholder='Enter Brand Name']"

    COMPANY_FORM_SAVE = (
        "xpath=//button[@type='button'][normalize-space()='Save']"
    )

    VISIBLE_EDITOR_IFRAMES = "iframe:visible"

    DRAFT_ROW = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row') "
        "and contains(@class, 'unsaved-new-row')]"
    )
    MAIN_MODEL_NUMBER = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row') "
        "and contains(@class, 'unsaved-new-row')]/td[2]"
        "//input[@placeholder='Reference']"
    )
    ADDITIONAL_COMPANY_MODEL_NUMBER = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row') "
        "and contains(@class, 'unsaved-new-row')]/td[3]/div[1]"
    )
    ADDITIONAL_COMPANY_DESCRIPTION = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row') "
        "and contains(@class, 'unsaved-new-row')]/td[4]/div[1]"
    )

    COMPANY_TABS = 'a[ng-click*="getselectedAddCoTab"]'

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.applications_page = ApplicationsPage(page)

    def open_additional_company_form(self) -> None:
        """Open Additional Companies and click Add Additional Company."""
        tab = self.page.locator(self.ADDITIONAL_COMPANIES_TAB)
        expect(tab).to_be_visible(timeout=30000)
        expect(tab).to_be_enabled(timeout=15000)
        tab.click(timeout=15000)

        add_button = self.page.locator(self.ADD_ADDITIONAL_COMPANY)
        expect(add_button).to_be_visible(timeout=30000)
        expect(add_button).to_be_enabled(timeout=15000)
        add_button.click(timeout=15000)

        expect(
            self.page.locator(self.COMPANY_NAME)
        ).to_be_visible(timeout=30000)

        LOGGER.info("Add Additional Company form opened")

    def _fill_rich_text_editor(
        self,
        editor_index: int,
        value: str,
    ) -> None:
        """Fill the Header or Footer rich-text editor."""
        editors = self.page.locator(self.VISIBLE_EDITOR_IFRAMES)
        expect(editors).to_have_count(2, timeout=15000)

        editor_body = (
            self.page
            .frame_locator(self.VISIBLE_EDITOR_IFRAMES)
            .nth(editor_index)
            .locator("body")
        )
        expect(editor_body).to_be_visible(timeout=15000)
        editor_body.fill(value)

    def save_additional_company_details(
        self,
        company_name: str,
        brand_name: str,
        section_header: str,
        section_footer: str,
    ) -> None:
        """Save company details and wait for its draft model section."""
        company_input = self.page.locator(self.COMPANY_NAME)
        expect(company_input).to_be_visible(timeout=15000)
        company_input.fill(company_name)

        brand_input = self.page.locator(self.BRAND_NAME)
        expect(brand_input).to_be_visible(timeout=15000)
        brand_input.fill(brand_name)

        # The Header editor is first; the Footer editor is second.
        self._fill_rich_text_editor(0, section_header)
        self._fill_rich_text_editor(1, section_footer)

        save_button = self.page.locator(self.COMPANY_FORM_SAVE).last
        expect(save_button).to_be_visible(timeout=15000)
        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)

        # Saving the company form opens a draft model section.
        expect(company_input).to_be_hidden(timeout=30000)
        expect(self.page.locator(self.DRAFT_ROW)).to_be_visible(
            timeout=60000
        )

        LOGGER.info(
            "Additional Company form saved; draft model row is visible"
        )

    def fill_and_save_additional_company_model(
        self,
        main_model_number: str,
        additional_company_model_number: str,
        additional_company_description: str,
    ) -> None:
        """Fill the draft row and confirm its Save Row Changes dialog."""
        draft_row = self.page.locator(self.DRAFT_ROW)
        expect(draft_row).to_be_visible(timeout=30000)

        main_model = self.page.locator(self.MAIN_MODEL_NUMBER)
        expect(main_model).to_be_visible(timeout=15000)
        expect(main_model).to_be_enabled(timeout=15000)
        main_model.fill(main_model_number)

        additional_model = self.page.locator(
            self.ADDITIONAL_COMPANY_MODEL_NUMBER
        )
        expect(additional_model).to_be_visible(timeout=15000)
        expect(additional_model).to_be_editable(timeout=15000)
        additional_model.fill(additional_company_model_number)

        description = self.page.locator(
            self.ADDITIONAL_COMPANY_DESCRIPTION
        )
        expect(description).to_be_visible(timeout=15000)
        expect(description).to_be_editable(timeout=15000)
        description.fill(additional_company_description)

        # Reuse the existing model-row Save and Yes confirmation methods.
        self.applications_page.click_save()
        self.applications_page.confirm_save()
        self.applications_page.validate_models_update_success()

        LOGGER.info(
            "Additional Company model row saved: main=%s, "
            "additional=%s",
            main_model_number,
            additional_company_model_number,
        )

    def validate_company_tab(self, company_name: str) -> None:
        """Verify the saved company appears in Additional Companies."""
        tab = self.page.locator(self.ADDITIONAL_COMPANIES_TAB)
        expect(tab).to_be_visible(timeout=30000)
        tab.click(timeout=15000)

        company_tab = (
            self.page.locator(self.COMPANY_TABS)
            .filter(has_text=company_name)
        )
        expect(company_tab).to_have_count(1, timeout=60000)
        expect(company_tab).to_be_visible(timeout=30000)

        empty_state = self.page.get_by_text(
            "No additional companies for review.",
            exact=True,
        )
        expect(empty_state).to_be_hidden(timeout=30000)

        LOGGER.info(
            "Additional Company tab is visible: %s",
            company_name,
        )

    def add_additional_company_with_model(
        self,
        company_name: str,
        brand_name: str,
        section_header: str,
        section_footer: str,
        main_model_number: str,
        additional_company_model_number: str,
        additional_company_description: str,
    ) -> None:
        """Create the company, save its model row, and verify the company."""
        self.open_additional_company_form()
        self.save_additional_company_details(
            company_name=company_name,
            brand_name=brand_name,
            section_header=section_header,
            section_footer=section_footer,
        )
        self.fill_and_save_additional_company_model(
            main_model_number=main_model_number,
            additional_company_model_number=(
                additional_company_model_number
            ),
            additional_company_description=(
                additional_company_description
            ),
        )
        self.validate_company_tab(company_name)