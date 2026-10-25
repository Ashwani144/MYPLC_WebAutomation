from __future__ import annotations

from playwright.sync_api import Page

from mtplc.pages.application_details_page import ApplicationDetailsPage


def test_completion_controls_target_visible_preview_not_covered_side_modal(
    page: Page,
) -> None:
    page.set_content(
        """
        <div class="modal fade in ng-animate ng-enter-active in-add-active"
             role="dialog">
          <h2>Certificate Preview</h2>
          <a class="ml-2 btn btn-primary ng-scope"
             ng-click="comoc.selectTab('closingEmail')">
            Complete Application
          </a>
          <div class="modal fade in right" role="dialog">
            <nav>
              <a ng-click="comoc.selectTab('closingEmail')">Closing Email</a>
            </nav>
            <a class="ml-2 btn btn-primary ng-scope"
               ng-click="comoc.selectTab('closingEmail')">
              Complete Application
            </a>
            <div class="modal-body" style="height: 100px; overflow-y: auto">
              <div style="height: 500px">Application preview</div>
              <button style="display: none"
                      ng-click="cemc.updateWithoutClosingEmail()">
                Complete Application
              </button>
            </div>
            <button style="display: none"
                    ng-click="cemc.updateWithoutClosingEmail()">
              Complete Application
            </button>
          </div>
          <div class="modal-body" style="height: 100px; overflow-y: auto">
            <div style="height: 500px">Application preview</div>
            <button data-testid="bottom-complete"
                    ng-click="cemc.updateWithoutClosingEmail()">
              Complete Application
            </button>
          </div>
          <button style="display: none"
                  ng-click="cemc.updateWithoutClosingEmail()">
            Complete Application
          </button>
        </div>
        """
    )
    details_page = ApplicationDetailsPage(page)

    page.evaluate(
        """() => setTimeout(() => {
            document.querySelector('.modal:not(.right)').classList.remove(
                'ng-animate',
                'ng-enter-active',
                'in-add-active'
            );
        }, 100)"""
    )
    details_page._wait_for_certificate_preview_animation()

    completion_action = details_page._certificate_preview_completion_action()

    assert completion_action.count() == 1
    assert completion_action.inner_text().strip() == "Complete Application"
    assert completion_action.evaluate(
        "(element) => element.closest('.modal').classList.contains('right')"
    ) is False

    closing_email_tab = details_page._certificate_preview_closing_email_tab()
    assert closing_email_tab.count() == 1
    assert closing_email_tab.inner_text().strip() == "Closing Email"

    complete_button = details_page._certificate_preview_complete_button()
    assert complete_button.count() == 1
    assert complete_button.evaluate(
        "(element) => element.closest('.modal').classList.contains('right')"
    ) is False
    details_page._scroll_certificate_completion_into_view(complete_button)
    assert complete_button.is_visible()
    assert complete_button.evaluate(
        "(element) => element.closest('.modal-body').scrollTop > 0"
    )


def test_certificate_preview_waits_for_leaving_duplicate_modal(
    page: Page,
) -> None:
    page.set_content(
        """
        <div class="modal fade in ng-animate ng-leave ng-leave-active"
             role="dialog" style="z-index: 1050">
          <h2>Certificate Preview</h2>
        </div>
        <div class="modal fade in" role="dialog" style="z-index: 1060">
          <h2>Certificate Preview</h2>
        </div>
        <script>
          setTimeout(() => {
            document.querySelector('.ng-leave').remove();
          }, 150);
        </script>
        """
    )
    details_page = ApplicationDetailsPage(page)

    details_page._wait_for_certificate_preview_animation()

    preview = details_page._certificate_preview_dialog()
    assert preview.count() == 1
    assert preview.get_by_role(
        "heading",
        name="Certificate Preview",
        exact=True,
    ).is_visible()

