"""Client page object for the IAPMO MyPLC Admin portal.

Encapsulates the Clients list and the "Create New Client" dialog. Generated from
a recorded Playwright MCP session; selectors favour accessible roles/placeholders
captured from the live QA portal.
"""
from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.logger import get_logger

log = get_logger("client_page")


class ClientPage(BasePage):
    """Clients list + Create New Client workflow."""

    CLIENTS_URL = "https://qa-myplc.iapmo.org/Admin/clients#/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---- navigation --------------------------------------------------------
    def open_clients_list(self) -> "ClientPage":
        """Click the "Clients" item in the left navigation."""
        log.info("Opening Clients list from the left navigation")
        # The nav link's accessible name has a leading icon space; substring
        # matching (default) resolves it.
        self.page.get_by_role("link", name="Clients").click()
        self.page.wait_for_url("**/Admin/clients#/")
        return self

    def open_create_form(self) -> "ClientPage":
        """Open the "Create New Client" dialog from the Clients list."""
        log.info("Opening the Create New Client dialog")
        self.page.get_by_text("Create New Client").first.click()
        expect(
            self.page.get_by_role("heading", name="Create New Client")
        ).to_be_visible()
        return self

    # ---- form fill ---------------------------------------------------------
    def _select_dropdown(self, current_label: str, option_text: str) -> None:
        """Open a custom button-dropdown and pick an option by visible text."""
        self.page.get_by_role("button", name=current_label).click()
        self.page.get_by_text(option_text, exact=True).click()

    def create_client(
        self,
        *,
        name: str,
        address: str,
        phone: str,
        website: str,
        tax_type: str = "VAT",
        tax_id: str = "121212",
        note: str = "Created by automation",
        address_format: str = "GOOGLE_LOCATIONS",
    ) -> None:
        """Fill the Create New Client form and submit it."""
        log.info("Creating client %r", name)

        self.page.get_by_placeholder("Please enter Client Name").fill(name)

        # Primary Address: choose a Format, then use the revealed autocomplete.
        self._select_dropdown("Please select a Format", address_format)
        self._fill_google_location(address)

        self.page.get_by_placeholder("Please enter Phone Number").fill(phone)
        self.page.get_by_placeholder("Please enter Website").fill(website)

        # Tax Type dropdown reveals the Tax Id field once a type is selected.
        self._select_dropdown("Please Select Tax Type", tax_type)
        self.page.get_by_placeholder("Please enter Tax Id").fill(tax_id)

        self.page.get_by_placeholder("Please enter a Note").fill(note)

        self.page.get_by_role("button", name="Create Client").click()
        # Dialog closes and the app returns to the Clients list.
        self.page.wait_for_url("**/Admin/clients#/")

    def _fill_google_location(self, address: str) -> None:
        """Type into the Google Places autocomplete and select the first match."""
        field = self.page.get_by_role("textbox", name="GOOGLE_LOCATIONS")
        field.click()
        field.type(address, delay=50)
        # Google Places renders suggestions in ``.pac-item`` elements.
        suggestion = self.page.locator(".pac-item").first
        try:
            suggestion.wait_for(state="visible", timeout=5000)
            suggestion.click()
        except Exception:  # pragma: no cover - fallback if no dropdown appears
            log.warning("No autocomplete suggestion appeared; keeping typed value")
            field.press("Enter")

    # ---- assertions --------------------------------------------------------
    def search_client(self, name: str) -> "ClientPage":
        """Type a name into the grid search box and run the search."""
        log.info("Searching Clients grid for %r", name)
        self.page.get_by_role("searchbox", name="Search:").fill(name)
        self.page.get_by_role("button", name="Search").click()
        # Let the grid re-query and re-render before asserting.
        self.page.wait_for_load_state("networkidle")
        return self

    def client_cell(self, name: str):
        """Return the grid cell locator for a client name (for expect assertions)."""
        return self.page.get_by_role("gridcell", name=name).first

    def is_client_listed(self, name: str) -> bool:
        """Return True if a row/cell containing ``name`` is visible in the grid."""
        return self.client_cell(name).is_visible()

