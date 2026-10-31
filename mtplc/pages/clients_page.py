"""
Clients Page Object for MTPLC.

Handles:

    Clients
        -> Open Client
        -> Validate Client Details
        -> Applications Tab
        -> New File Application
        -> Select cUPC
        -> Select Include Canadian
        -> Start Application

Additional application steps can be added later.
"""

from __future__ import annotations

import logging
import re

from playwright.sync_api import Page, expect

from mtplc.config.settings import settings
from mtplc.pages.base_page import BasePage


LOGGER = logging.getLogger(__name__)


class ClientsPage(BasePage):
    """Page Object for MTPLC Clients functionality."""

    # ============================================================
    # CLIENTS MODULE
    # ============================================================

    CLIENTS = (
        "xpath=//span[@data-i18n='nav.clients']"
    )

    # ============================================================
    # CLIENT
    # ============================================================

    CLIENT_LINK_TEMPLATE = (
        "xpath=//a[normalize-space()="
        "'{client_name}']"
    )

    CLIENT_NAME = (
        "1948610 ONTARIO LTD. VOGT INDUSTRIES"
    )

    CLIENT_ID = "6824"

    # ============================================================
    # CLIENT DETAILS
    # ============================================================

    CLIENT_DETAILS_URL_TEMPLATE = (
        r".*/admin/clients#/details/{client_id}/details/.*"
    )

    # ============================================================
    # CLIENT APPLICATIONS TAB
    # ============================================================

    APPLICATIONS_TAB = (
        "xpath=//a[@ng-click=\"dc.selectTab('applications')\"]"
    )

    # ============================================================
    # NEW FILE APPLICATION
    # ============================================================

    NEW_FILE_APPLICATION = (
        "xpath=//a[@class='btn btn-edit btn-primary']"
    )

    # ============================================================
    # NEW FILE APPLICATION OPTIONS
    # ============================================================

    # Actual HTML:
    #
    # <label class="col-md-12 ng-binding">
    #     <input type="checkbox" ...>
    #     cUPC
    # </label>
    #
    # We target the actual checkbox inside the cUPC label.
    CUPC = (
        "xpath=//label[normalize-space()='cUPC']"
        "//input[@type='checkbox']"
    )
    UPC_ALIAS = (
        "xpath=//label[normalize-space()='UPC']"
        "//input[@type='checkbox']"
    )

    # Include Canadian
    INCLUDE_CANADIAN = (
        "xpath=//label[@class='col-md-offset-1']"
        "//span[contains(text(),'Include Canadian?')]"
    )

    # ============================================================
    # START APPLICATION
    # ============================================================

    START_APPLICATION = (
        "xpath=//button[@class='btn btn-primary btn-block']"
    )

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ============================================================
    # CLIENTS MODULE
    # ============================================================

    def click_clients(self) -> None:
        """
        Click Clients from the left navigation menu.
        """

        LOGGER.info("Clicking Clients module")

        clients = self.page.locator(
            self.CLIENTS
        )

        expect(clients).to_have_count(
            1,
            timeout=30000,
        )

        expect(clients).to_be_visible(
            timeout=30000,
        )

        clients.scroll_into_view_if_needed(
            timeout=10000,
        )

        clients.click(
            timeout=15000,
        )

        LOGGER.info("Clients module clicked")

        self.page.wait_for_timeout(1000)

        LOGGER.info("Clients page opened")

    # ============================================================
    # OPEN CLIENT
    # ============================================================

    def open_client(
        self,
        client_name: str = CLIENT_NAME,
    ) -> None:
        """
        Open a client from the Clients list.
        """

        LOGGER.info(
            "Opening client: %s",
            client_name,
        )

        client = self.page.locator(
            self.CLIENT_LINK_TEMPLATE.format(
                client_name=client_name,
            )
        )

        expect(client).to_have_count(
            1,
            timeout=30000,
        )

        expect(client).to_be_visible(
            timeout=30000,
        )

        LOGGER.info(
            "Client link is visible: %s",
            client_name,
        )

        client.scroll_into_view_if_needed(
            timeout=10000,
        )

        client.click(
            timeout=15000,
        )

        self.page.wait_for_timeout(1500)

        LOGGER.info(
            "Client opened: %s",
            client_name,
        )

    # ============================================================
    # VALIDATE CLIENT DETAILS
    # ============================================================

    def validate_client_details(
        self,
        client_name: str = CLIENT_NAME,
        client_id: str = CLIENT_ID,
    ) -> None:
        """
        Validate that the Client Details page is opened.

        URL validation is used because the application has
        already confirmed the client-specific Client Details route.
        """

        LOGGER.info(
            "Validating Client Details page"
        )

        expect(self.page).to_have_url(
            re.compile(
                self.CLIENT_DETAILS_URL_TEMPLATE.format(
                    client_id=re.escape(client_id),
                )
            ),
            timeout=30000,
        )

        LOGGER.info(
            "Client Details URL validated: %s",
            self.page.url,
        )

        LOGGER.info(
            "Client Details page validated for client: %s",
            client_name,
        )

    # ============================================================
    # APPLICATIONS TAB
    # ============================================================

    def open_client_applications(self, client_id: str) -> None:
        """Open a client's Applications route directly."""
        if not client_id.isdigit():
            raise ValueError(
                f"Client ID must contain only digits, not {client_id!r}."
            )

        applications_url = (
            f"{settings.base_url.rstrip('/')}/admin/clients"
            f"#/details/{client_id}/applications/"
        )
        LOGGER.info(
            "Opening Applications for client ID %s",
            client_id,
        )
        self.page.goto(
            applications_url,
            wait_until="commit",
        )
        expect(self.page).to_have_url(
            re.compile(
                rf".*/admin/clients#/details/{re.escape(client_id)}"
                r"/applications/?"
            ),
            timeout=30000,
        )
        expect(
            self.page.locator(self.NEW_FILE_APPLICATION)
        ).to_be_visible(timeout=60000)
        LOGGER.info(
            "Client Applications page opened for client ID %s",
            client_id,
        )

    def click_applications_tab(self) -> None:
        """
        Click Applications tab from Client Details.
        """

        LOGGER.info(
            "Clicking Applications tab"
        )

        applications_tab = self.page.locator(
            self.APPLICATIONS_TAB
        )

        expect(applications_tab).to_have_count(
            1,
            timeout=30000,
        )

        expect(applications_tab).to_be_visible(
            timeout=30000,
        )

        applications_tab.scroll_into_view_if_needed(
            timeout=10000,
        )

        applications_tab.click(
            timeout=15000,
        )

        LOGGER.info(
            "Applications tab clicked"
        )

        self.page.wait_for_timeout(1000)

    # ============================================================
    # NEW FILE APPLICATION
    # ============================================================

    def click_new_file_application(self) -> None:
        """
        Click New File Application button.
        """

        LOGGER.info(
            "Clicking New File Application"
        )

        new_file_application = self.page.locator(
            self.NEW_FILE_APPLICATION
        )

        expect(new_file_application).to_have_count(
            1,
            timeout=30000,
        )

        expect(new_file_application).to_be_visible(
            timeout=30000,
        )

        expect(new_file_application).to_be_enabled(
            timeout=15000,
        )

        new_file_application.scroll_into_view_if_needed(
            timeout=10000,
        )

        new_file_application.click(
            timeout=15000,
        )

        LOGGER.info(
            "New File Application clicked"
        )

        self.page.wait_for_timeout(1000)

    # ============================================================
    # cUPC
    # ============================================================

    def select_cupc(self) -> None:
        """
        Select cUPC checkbox in New File Application.
        """

        LOGGER.info(
            "Selecting cUPC"
        )

        cupc = self.page.locator(self.CUPC)
        if cupc.count() == 0:
            cupc = self.page.locator(self.UPC_ALIAS)
            LOGGER.info(
                "The form labels cUPC as UPC; selecting the UPC checkbox"
            )

        # Validate that exactly one checkbox matches the requested option.
        expect(cupc).to_have_count(
            1,
            timeout=30000,
        )

        # Validate visibility.
        expect(cupc).to_be_visible(
            timeout=30000,
        )

        checkbox_label = cupc.locator("xpath=ancestor::label[1]")
        expect(checkbox_label).to_have_count(
            1,
            timeout=10000,
        )
        expect(checkbox_label).to_be_visible(
            timeout=30000,
        )

        # The checkbox input can be outside the viewport inside the overlay;
        # clicking its visible label reliably toggles the associated control.
        checkbox_label.scroll_into_view_if_needed(
            timeout=10000,
        )

        # Select only when it is not already selected.
        if not cupc.is_checked():
            checkbox_label.click(
                timeout=15000,
            )

        # Confirm selection.
        expect(cupc).to_be_checked(
            timeout=15000,
        )

        LOGGER.info(
            "cUPC selected successfully"
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # INCLUDE CANADIAN
    # ============================================================

    def select_include_canadian(self) -> None:
        """
        Select Include Canadian option.
        """

        LOGGER.info(
            "Selecting Include Canadian"
        )

        include_canadian = self.page.locator(
            self.INCLUDE_CANADIAN
        )

        expect(include_canadian).to_have_count(
            1,
            timeout=30000,
        )

        expect(include_canadian).to_be_visible(
            timeout=30000,
        )

        include_canadian.scroll_into_view_if_needed(
            timeout=10000,
        )

        include_canadian.click(
            timeout=15000,
        )

        LOGGER.info(
            "Include Canadian selected"
        )

        self.page.wait_for_timeout(500)

    # ============================================================
    # START APPLICATION
    # ============================================================

    def click_start_application(self) -> None:
        """
        Click Start Application.
        """

        LOGGER.info(
            "Clicking Start Application"
        )

        start_application = self.page.locator(
            self.START_APPLICATION
        )

        expect(start_application).to_have_count(
            1,
            timeout=30000,
        )

        expect(start_application).to_be_visible(
            timeout=30000,
        )

        expect(start_application).to_be_enabled(
            timeout=15000,
        )

        start_application.scroll_into_view_if_needed(
            timeout=10000,
        )

        start_application.click(
            timeout=15000,
        )

        LOGGER.info(
            "Start Application clicked"
        )

        self.page.wait_for_timeout(1500)

    # ============================================================
    # COMPLETE CURRENT FLOW
    # ============================================================

    def start_new_file_application(
        self,
    ) -> str:
        """
        Start a cUPC application from the client's Applications page.
        """
        self.click_new_file_application()
        self.select_cupc()
        self.click_start_application()
        expect(self.page).to_have_url(
            re.compile(r".*/admin/applications#/details/(\d+)/details/?"),
            timeout=60000,
        )
        application_id_match = re.search(
            r"#/details/(\d+)/details/?",
            self.page.url,
        )
        if application_id_match is None:
            raise AssertionError(
                "Starting the new application did not open its Details page. "
                f"Current URL: {self.page.url}"
            )

        LOGGER.info(
            "New cUPC File Application %s started successfully",
            application_id_match.group(1),
        )
        return application_id_match.group(1)
