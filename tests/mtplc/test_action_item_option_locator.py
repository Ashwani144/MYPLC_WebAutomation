from __future__ import annotations

from datetime import date

from playwright.sync_api import Page

from mtplc.pages.application_details_page import ApplicationDetailsPage


def test_write_up_option_locator_ignores_hidden_duplicate(page: Page) -> None:
    page.set_content(
        """
        <div role="listbox">
          <div role="option" style="display: none">Write Up</div>
          <div role="option">Write Up</div>
        </div>
        """
    )
    details_page = ApplicationDetailsPage(page)
    write_up_option = details_page._write_up_option()

    assert write_up_option.count() == 1
    assert write_up_option.is_visible()


def test_write_up_action_item_defaults_priority_and_dates_to_today(
    page: Page,
) -> None:
    page.set_content(
        """
        <div role="dialog">
          <button id="priority">Select Priority</button>
          <div id="priority-menu" hidden>
            <a id="high" href="#">High</a>
          </div>
          <input type="date" aria-label="Reminder Date">
          <input type="date" aria-label="Due Date">
        </div>
        <script>
          const button = document.querySelector("#priority");
          const menu = document.querySelector("#priority-menu");
          const high = document.querySelector("#high");
          button.addEventListener("click", () => { menu.hidden = false; });
          high.addEventListener("click", (event) => {
            event.preventDefault();
            button.textContent = "High";
            menu.hidden = true;
          });
        </script>
        """
    )
    details_page = ApplicationDetailsPage(page)
    dialog = page.get_by_role("dialog")

    details_page._configure_write_up_action_item(dialog)

    assert dialog.locator("#priority").inner_text() == "High"
    expected_date = date.today().isoformat()
    assert dialog.get_by_label("Reminder Date").input_value() == expected_date
    assert dialog.get_by_label("Due Date").input_value() == expected_date

