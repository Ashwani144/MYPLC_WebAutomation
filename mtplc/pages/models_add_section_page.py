"""Page object for adding a model section and its first model."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, expect

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class ModelsAddSectionPage(BasePage):
    """Add a section, then save its first model row."""

    BRAND_NAME = "input[placeholder='Enter Brand Name']"
    ADD_SECTION = "xpath=//button[normalize-space()='Add Section']"

    # Click the Save button containing the supplied save icon.
    SECTION_SAVE_BUTTON = (
        "xpath=//i[@class='fa fa-save']/ancestor::button[1]"
    )

    VISIBLE_EDITOR_IFRAMES = "iframe:visible"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.applications_page = ApplicationsPage(page)

    def open_add_section(self) -> None:
        """Open Models → All Models → Add Section."""
        self.applications_page.click_models()
        self.applications_page.click_all_models()

        add_section = self.page.locator(self.ADD_SECTION)
        expect(add_section).to_be_visible(timeout=30000)
        expect(add_section).to_be_enabled(timeout=15000)
        add_section.click(timeout=15000)

        expect(
            self.page.locator(self.BRAND_NAME)
        ).to_be_visible(timeout=30000)

        LOGGER.info("Add Section form opened")

    def _fill_rich_text_editor(self, editor_index: int, value: str) -> None:
        """Fill one visible rich-text iframe editor."""
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

    def fill_and_save_section(
        self,
        brand_name: str,
        section_header: str,
        section_footer: str,
    ) -> None:
        """Fill Brand Name, Header and Footer, then save the section."""
        brand = self.page.locator(self.BRAND_NAME)
        expect(brand).to_be_visible(timeout=15000)
        expect(brand).to_be_enabled(timeout=15000)
        brand.fill(brand_name)

        # The screenshot shows the Header editor first and Footer second.
        self._fill_rich_text_editor(0, section_header)
        self._fill_rich_text_editor(1, section_footer)

        save_button = self.page.locator(self.SECTION_SAVE_BUTTON)
        expect(save_button).to_be_visible(timeout=15000)
        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)

        # Wait for the Add Section form to close and the draft model row to appear.
        expect(brand).to_be_hidden(timeout=30000)
        expect(
            self.page.locator(
                "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
            )
        ).to_be_visible(timeout=30000)

        LOGGER.info("Section saved; draft model row is visible")

    def fill_and_save_model(
        self,
        model_number: str,
        description: str,
    ) -> None:
        """Fill and save the first model row using existing page methods."""
        self.applications_page.enter_draft_model_number(model_number)
        self.applications_page.enter_draft_description(description)
        self.applications_page.click_save()
        self.applications_page.confirm_save()
        self.applications_page.validate_models_update_success()

        LOGGER.info("Model row saved: %s", model_number)

    def add_section_with_first_model(
        self,
        brand_name: str,
        section_header: str,
        section_footer: str,
        model_number: str,
        description: str,
    ) -> None:
        """Run the complete section and first-model workflow."""
        self.open_add_section()
        self.fill_and_save_section(
            brand_name=brand_name,
            section_header=section_header,
            section_footer=section_footer,
        )
        self.fill_and_save_model(
            model_number=model_number,
            description=description,
        )
    ADD_SECTION_OR_SUFFIX = (
        "xpath=//button[@title='Add Section or Suffix']"
    )
    ADD_SECTION_AFTER = (
        "xpath=//a[normalize-space()='Add Section After']"
    )

    def click_add_section_after(self) -> None:
        """Open the menu and choose Add Section After."""
        add_menu = self.page.locator(self.ADD_SECTION_OR_SUFFIX)
        expect(add_menu).to_be_visible(timeout=15000)
        expect(add_menu).to_be_enabled(timeout=15000)
        add_menu.click(timeout=15000)

        add_after = self.page.locator(self.ADD_SECTION_AFTER)
        expect(add_after).to_be_visible(timeout=15000)
        expect(add_after).to_be_enabled(timeout=15000)
        add_after.click(timeout=15000)

        expect(
            self.page.locator(self.BRAND_NAME)
        ).to_be_visible(timeout=30000)

        LOGGER.info("Add Section After form opened")

    def add_section_after_with_model(
        self,
        brand_name: str,
        section_header: str,
        section_footer: str,
        model_number: str,
        description: str,
    ) -> None:
        """Add a section after the current one and save its first model."""
        self.click_add_section_after()
        self.fill_and_save_section(
            brand_name=brand_name,
            section_header=section_header,
            section_footer=section_footer,
        )
        self.fill_and_save_model(
            model_number=model_number,
            description=description,
        )