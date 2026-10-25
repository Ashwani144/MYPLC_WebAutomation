from __future__ import annotations

from playwright.sync_api import Page

from mtplc.pages.application_details_page import ApplicationDetailsPage


def test_model_list_status_supports_plain_cell_headers(page: Page) -> None:
    page.set_content(
        """
        <table>
          <tr>
            <td>Model Number</td>
            <td>Description</td>
            <td>List</td>
            <td>Hold</td>
          </tr>
          <tr>
            <td>HY-1202</td>
            <td>Example model</td>
            <td><input type="radio" name="recommendation"></td>
            <td><input type="radio" name="recommendation"></td>
          </tr>
        </table>
        """
    )
    details_page = ApplicationDetailsPage(page)

    assert not details_page.models_are_recommendable(("HY-1202",))
    details_page.set_model_recommendable("HY-1202")
    details_page.validate_model_recommendable("HY-1202")
    assert details_page.models_are_recommendable(("HY-1202",))

