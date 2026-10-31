"""Page object for moving, adding, editing, and deleting model sections."""

from __future__ import annotations

import logging

from playwright.sync_api import Page, expect

from mtplc.pages.applications_page import ApplicationsPage
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class ModelsSectionCrudPage(BasePage):
    """Manage model sections and their first model rows."""

    SECTION_CARDS = "div[id^='model-section-section-']"

    BRAND_NAME = "input[placeholder='Enter Brand Name']"
    ADD_SECTION_OR_SUFFIX = "button[title='Add Section or Suffix']"

    SECTION_SAVE_BUTTON = (
        "xpath=//i[@class='fa fa-save']/ancestor::button[1]"
    )
    VISIBLE_EDITOR_IFRAMES = "iframe:visible"

    DRAFT_MODEL_ROW = (
        "xpath=//tbody/tr[contains(@class, 'draft-product-row')]"
    )

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.applications_page = ApplicationsPage(page)

    def section_order(self) -> list[str]:
        """Return the section IDs in their displayed order."""
        cards = self.page.locator(self.SECTION_CARDS)
        count = cards.count()

        if count == 0:
            raise AssertionError("No model section cards are visible.")

        section_ids: list[str] = []
        for index in range(count):
            section_id = cards.nth(index).get_attribute("id")
            if not section_id:
                raise AssertionError(
                    f"Section card {index} has no id attribute."
                )
            section_ids.append(section_id)

        return section_ids

    def _section_by_brand(self, brand_name: str):
        """Find a section card by its displayed Brand Name."""
        section = (
            self.page.locator(self.SECTION_CARDS)
            .filter(has_text=brand_name)
        )
        expect(section).to_have_count(1, timeout=30000)
        expect(section).to_be_visible(timeout=15000)
        return section

    def _reload_models_view(self) -> None:
        """Reload the application and reopen its Models tab."""
        self.page.reload(wait_until="domcontentloaded")
        self.applications_page.click_models()

        cards = self.page.locator(self.SECTION_CARDS)
        expect(cards.first).to_be_visible(timeout=30000)

    def _wait_for_section_order(
        self,
        expected_ids: list[str],
    ) -> None:
        """Verify the refreshed section order."""
        cards = self.page.locator(self.SECTION_CARDS)
        expect(cards).to_have_count(len(expected_ids), timeout=30000)

        for index, expected_id in enumerate(expected_ids):
            expect(cards.nth(index)).to_have_attribute(
                "id",
                expected_id,
                timeout=30000,
            )

    def _select_move_target(self, target_section_id: str) -> None:
        """Select a section from the open move menu."""
        menu = self.page.locator("ul.dropdown-menu:visible").last
        expect(menu).to_be_visible(timeout=15000)

        target = menu.get_by_role(
            "link",
            name=f"Section {target_section_id.removeprefix('model-section-section-')}",
            exact=True,
        )
        expect(target).to_be_visible(timeout=15000)
        target.click(timeout=15000)

    def move_section_after(self, brand_name: str) -> None:
        """Move a section down one position."""
        before = self.section_order()
        section = self._section_by_brand(brand_name)
        section_id = section.get_attribute("id")

        if section_id not in before:
            raise AssertionError(
                f"Section for brand {brand_name!r} was not in the section list."
            )

        index = before.index(section_id)
        if index >= len(before) - 1:
            raise AssertionError(
                f"Section {brand_name!r} is already the last section."
            )

        target_section_id = before[index + 1]
        expected = before.copy()
        expected[index], expected[index + 1] = (
            expected[index + 1],
            expected[index],
        )

        move_button = section.locator("button[title='Move After']")
        expect(move_button).to_be_visible(timeout=15000)
        expect(move_button).to_be_enabled(timeout=15000)
        move_button.click(timeout=15000)
        self._select_move_target(target_section_id)

        self._reload_models_view()
        self._wait_for_section_order(expected)
        LOGGER.info(
            "Moved section %s down and verified after reload",
            brand_name,
        )

    def move_section_before(self, brand_name: str) -> None:
        """Move the identified section up by one position."""
        before = self.section_order()
        section = self._section_by_brand(brand_name)
        section_id = section.get_attribute("id")

        if section_id not in before:
            raise AssertionError(
                f"Section for brand {brand_name!r} was not in the section list."
            )

        index = before.index(section_id)
        if index == 0:
            raise AssertionError(
                f"Section {brand_name!r} is already the first section."
            )

        target_section_id = before[index - 1]
        move_button = section.locator("button[title='Move Before']")
        expect(move_button).to_be_visible(timeout=15000)
        expect(move_button).to_be_enabled(timeout=15000)
        move_button.click(timeout=15000)
        self._select_move_target(target_section_id)

        expected = before.copy()
        expected[index - 1], expected[index] = (
            expected[index],
            expected[index - 1],
        )

        self._reload_models_view()
        self._wait_for_section_order(expected)
        LOGGER.info("Moved section %s up", brand_name)

    def _fill_rich_text_editor(
        self,
        editor_index: int,
        value: str,
    ) -> None:
        """Fill one visible rich-text editor iframe."""
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

    def _save_section_form(
        self,
        brand_name: str,
        section_header: str,
        section_footer: str,
    ) -> None:
        """Fill and save a section form."""
        brand = self.page.locator(self.BRAND_NAME).last
        expect(brand).to_be_visible(timeout=15000)
        brand.fill(brand_name)

        # The Header editor is first; the Footer editor is second.
        self._fill_rich_text_editor(0, section_header)
        self._fill_rich_text_editor(1, section_footer)

        save_button = self.page.locator(self.SECTION_SAVE_BUTTON).last
        expect(save_button).to_be_visible(timeout=15000)
        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)

        expect(brand).to_be_hidden(timeout=30000)
        expect(
            self.page.locator(self.DRAFT_MODEL_ROW)
        ).to_be_visible(timeout=30000)

    def add_section_before(
        self,
        anchor_brand_name: str,
        new_brand_name: str,
        section_header: str,
        section_footer: str,
        model_number: str,
        description: str,
    ) -> None:
        """Add and populate a section before the identified section."""
        anchor = self._section_by_brand(anchor_brand_name)

        action_button = anchor.locator(self.ADD_SECTION_OR_SUFFIX)
        expect(action_button).to_be_visible(timeout=15000)
        expect(action_button).to_be_enabled(timeout=15000)
        action_button.click(timeout=15000)

        menu = self.page.locator(
            "div.btn-group.section-suffix-action-menu.open"
        )
        expect(menu).to_have_count(1, timeout=15000)
        expect(menu).to_be_visible(timeout=15000)
        add_before = menu.locator("li").first.locator("a")
        expect(add_before).to_be_visible(timeout=15000)
        add_before.click(timeout=15000)

        expect(
            self.page.locator(self.BRAND_NAME).last
        ).to_be_visible(timeout=30000)

        self._save_section_form(
            brand_name=new_brand_name,
            section_header=section_header,
            section_footer=section_footer,
        )

        self.applications_page.enter_draft_model_number(model_number)
        self.applications_page.enter_draft_description(description)
        self.applications_page.click_save()
        self.applications_page.confirm_save()
        self.applications_page.validate_models_update_success()

        self._reload_models_view()
        expect(
            self._section_by_brand(new_brand_name)
        ).to_be_visible(timeout=30000)

        LOGGER.info(
            "Added section %s before %s with model %s",
            new_brand_name,
            anchor_brand_name,
            model_number,
        )

    def edit_section_brand(
        self,
        old_brand_name: str,
        edited_brand_name: str,
    ) -> None:
        """Edit a section's Brand Name and save the section."""
        section = self._section_by_brand(old_brand_name)
        edit_button = section.locator(
            "xpath=.//i[@class='fa fa-pencil']/ancestor::button[1]"
        )
        expect(edit_button).to_be_visible(timeout=15000)
        expect(edit_button).to_be_enabled(timeout=15000)
        edit_button.click(timeout=15000)

        brand = self.page.locator(self.BRAND_NAME).last
        expect(brand).to_be_visible(timeout=30000)
        brand.fill(edited_brand_name)

        save_button = self.page.locator(self.SECTION_SAVE_BUTTON).last
        expect(save_button).to_be_visible(timeout=15000)
        expect(save_button).to_be_enabled(timeout=15000)
        save_button.click(timeout=15000)

        expect(brand).to_be_hidden(timeout=30000)
        expect(
            self._section_by_brand(edited_brand_name)
        ).to_be_visible(timeout=30000)

        LOGGER.info(
            "Edited section brand from %s to %s",
            old_brand_name,
            edited_brand_name,
        )

    def delete_section(self, brand_name: str) -> None:
        """Delete the identified section and confirm the prompt."""
        section = self._section_by_brand(brand_name)
        delete_button = section.locator(
            "xpath=.//i[@class='fa fa-trash']/ancestor::button[1]"
        )
        expect(delete_button).to_be_visible(timeout=15000)
        expect(delete_button).to_be_enabled(timeout=15000)
        delete_button.click(timeout=15000)

        yes_button = self.page.get_by_role(
            "button",
            name="Yes",
            exact=True,
        ).last
        expect(yes_button).to_be_visible(timeout=15000)
        expect(yes_button).to_be_enabled(timeout=15000)
        yes_button.click(timeout=15000)

        expect(section).to_have_count(0, timeout=60000)
        LOGGER.info("Deleted section %s", brand_name)