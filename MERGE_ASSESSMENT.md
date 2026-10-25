# Merge assessment and validation record

## Project inventory

| Area | IAPMOPlayWrightAutomation master | MTPLCAutomation source |
|---|---|---|
| Runner/API | pytest; synchronous Playwright UI and requests-based API tests | pytest; synchronous Playwright UI tests |
| Test modules | `tests/api/test_api.py`, `tests/api/test_client_flow.py`, `tests/ui/test_create_client.py`, `tests/ui/test_launch.py` | 13 `test_*.py` modules listed below |
| Browser setup | Root `conftest.py`, `fixtures/browser_fixtures.py`, `fixtures/page_fixtures.py`; session browser, function context/page, local or remote configuration | pytest-playwright `page` fixture; maximized Chromium and `no_viewport` fixtures in source conftest |
| Page objects | `pages/base_page.py`, `client_page.py`, `login_page.py` | `base_page.py`, `application_details_page.py`, `applications_page.py`, `clients_page.py`, `launch_page.py`, `login_page.py`, `logout_page.py` |
| Other fixtures/hooks | API, browser, data, page, utility fixtures; custom reporter, failure screenshot, environment metadata, optional Slack/Teams summary | Browser args/context overrides, CLI options, test-step collection, failure screenshots, HTML/PDF report helpers |
| Configuration/data | `config/settings.py`; `config/environments/{dev,staging,prod}.yaml`; JSON, YAML, XLSX, Postman data and schemas under `testdata/` | `config/settings.py`, `config/application_config.py`, `config/test_data/applications.json`; role credentials and application selection from `.env`/Downloads |
| Dependencies | Pinned Playwright/pytest stack, PyYAML, dotenv, jsonschema, openpyxl, requests, reporting and visual snapshot packages | Playwright, pytest, pytest-playwright, pytest-html, dotenv; all are covered by master requirements |
| Artifacts/docs | Master HTML/Allure/JUnit, screenshots/videos/traces/logs, README, Docker and GitHub Actions | HTML plus workflow PDF report generation, screenshots, PDFs/certificates and a README |

MTPLC test modules retained:

- `test_action_item_option_locator.py`
- `test_add_model.py`
- `test_application_completion_locator.py`
- `test_application_config.py`
- `test_application_routes.py`
- `test_application_validation.py`
- `test_applications.py`
- `test_launch_login_logout.py`
- `test_model_recommendation_locators.py`
- `test_new_file_application.py`
- `test_pdf_workflow_steps.py`
- `test_phase_zero_client_application.py`
- `test_upload_model_template.py`

## Conflicts and integration choices

1. **Top-level module names:** both projects define `pages` and `config`; merging files at the root would shadow master imports. Source implementation is namespaced under `mtplc/`, and source imports point there. The master modules remain unchanged.
2. **Runner and Playwright API:** both use pytest and synchronous Playwright, so no runner migration or async bridge was needed. Source tests continue to use pytest-playwright's `page` fixture; master tests keep their `app_page` fixture.
3. **Browser defaults:** the source maximized window/no fixed viewport behavior is kept in `tests/mtplc/conftest.py`, scoped to that suite. The master browser and context lifecycle remains authoritative elsewhere.
4. **Settings and credentials:** the master environment settings provide the base URL/browser. MTPLC role-specific environment variable names and password fallback behavior are retained, while missing credentials now raise only when a role login is requested so pytest collection and non-live tests work without secrets. The source `.env` was excluded; only variable names are in `.env.example`.
5. **CLI options:** MTPLC application-selection and Phase 2 flags were added to the existing root option registration. The `--headed` option remains from pytest-playwright; master framework fixtures also expose `--app-headed`.
6. **Dependency versions:** master pins Playwright 1.49.1 and pytest 8.3.4. Source accepts Playwright >=1.45,<2 and pytest >=8,<9; the pinned master versions satisfy those ranges. All source requirements were already declared by the master, so `requirements.txt` remains one authoritative file.
7. **Test/report overlaps:** source login/application workflows overlap at a high level with master UI flows, but their selectors, roles, and business operations differ. No scenario was dropped or combined. Source workflow PDF and failure-report hooks remain under the MTPLC suite; master HTML/Allure/JUnit reporting remains enabled.
8. **Generated and machine-specific files:** `.venv`, `.git`, caches, Playwright inspection dumps, old logs, reports, screenshots, and downloaded certificate PDFs were excluded from the delivered codebase. These do not form reusable test logic or clean test data. The source JSON application dataset and master snapshots/test data were retained.

## Validation performed (2026-10-24)

- **Passed:** `python -m compileall -q outputs\IAPMOPlayWrightAutomation` (all merged Python files compiled).
- **Passed:** pytest collection for `tests/mtplc` and `tests/ui`: 27 collected, zero collection errors. This used selected pure-Python packages from the archive's bundled environment because the host Python does not have all declared dependencies installed.
- **Passed:** parsed project JSON, the three environment YAML files, and the login workbook successfully. Source page-object and scenario imports also resolved during collection.
- **Passed:** `tests/mtplc/test_application_config.py` and `tests/mtplc/test_pdf_workflow_steps.py`: 8 passed.
- **Blocked:** full test collection on the host Python. The environment lacks the pinned master dependencies; the archive virtual environment targets a Python 3.13 installation absent from this computer. After adding pure-Python dependencies for validation, the two master API modules still could not collect because `rpds` needs a compiled extension matching the current Python version. No project dependency pins were altered to mask this.
- **Not run:** live browser scenarios from either project. They need configured QA credentials and reachable external services. MTPLC model upload/validation also needs the matching populated application workbooks in the user's Downloads folder. Those workflows mutate QA application data.
- **Blocked:** a mocked Playwright browser test was started but did not return within 60 seconds and was interrupted; no browser scenario is counted as passed. The local Python 3.12 Playwright install does not have a confirmed compatible browser runtime.
- **PDF:** the MTPLC workflow HTML source was generated; Microsoft Edge exited nonzero without diagnostic output and did not produce the PDF. The helper logs the failed conversion. The master HTML report is generated during pytest runs.
- No end-to-end test is reported as passed. The source ZIP and master source behavior were left untouched; work was made only in the delivered master folder.

## Follow-up setup

Create a fresh virtual environment on the target computer and install the unified `requirements.txt`, then install Chromium with `python -m playwright install chromium`. Populate `.env` with the appropriate environment and role credentials. Run the exact commands in the root README. Before executing workflows that create or update applications, confirm the QA record and matching workbook.
