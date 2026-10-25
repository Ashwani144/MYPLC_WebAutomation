# IAPMO Playwright Automation (Unified Master)

This is the master Python automation project. It contains the original IAPMO API/UI suite and the MTPLC application workflows integrated from `MTPLCAutomation`.

## Framework and integration

- Runner: pytest, using the synchronous Python Playwright API.
- The original master fixtures, environment YAML settings, browser/context lifecycle, HTML/Allure/JUnit reporting, screenshots, video, trace, logging, and API helpers remain in place.
- The MTPLC page objects and configuration live in `mtplc/`; tests live in `tests/mtplc/`. That package boundary prevents collisions with the master's `pages/` and `config/` modules.
- The source's maximized-window behavior is applied only to tests under `tests/mtplc/`.
- All 13 MTPLC test modules are included, including locator/config unit coverage, application creation, model workflows, and multi-role application validation.
- MTPLC credentials are read from the root `.env`. No source `.env` values were carried over.

## Setup (Windows PowerShell)

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env
```

Edit `.env` for the target environment and credentials. The master uses `TEST_ENV`, `BASE_URL`, and the browser settings. MTPLC role variables are optional for collection and non-authenticated checks, but must be populated for the corresponding live workflows. Role passwords fall back to `MTPLC_PASSWORD`; the engineer username can fall back to `MTPLC_USERNAME`. Vanessa and administrator usernames need their own values.

Do not commit `.env`, credentials, cookies, or generated reports.

## Running tests

All commands below are from the project root. Pytest defaults in `pytest.ini` create HTML, Allure, JUnit, trace, video, and screenshot artifacts under `reports/`.

```powershell
# Complete regression suite
python -m pytest

# A single test or module
python -m pytest tests/mtplc/test_application_config.py -q
python -m pytest tests/mtplc/test_new_file_application.py -v --headed

# Master UI or API feature groups
python -m pytest tests/ui -m ui
python -m pytest tests/api -m api

# MTPLC scenarios grouped under the source project
python -m pytest tests/mtplc

# Choose a target application for the MTPLC validation workflow
python -m pytest tests/mtplc/test_application_validation.py --application-number P-254481 -v --app-headed

# Specify the populated workbook's application number when it differs from the UI record
python -m pytest tests/mtplc/test_application_validation.py --application-number P-254482 --model-workbook-application-number P-254471 -v --app-headed

# Run or resume the Vanessa Phase 2 workflow
python -m pytest tests/mtplc/test_application_validation.py --phase2-only -v --app-headed
python -m pytest tests/mtplc/test_application_validation.py --phase2-resume-from-list -v --app-headed

# Select a specific test by node ID (module::test function)
python -m pytest tests/mtplc/test_action_item_option_locator.py::test_write_up_option_locator_ignores_hidden_duplicate -q
```

The source project discovers a populated model workbook in the current user's `Downloads` folder by default. Use `--application-number` and/or `--model-workbook-application-number` when needed. Phase 0 creates an application in QA; application validation updates workflow data and may upload models, create action items, change status, or complete an application. Use an appropriate QA record and account.

The master UI tests use the configured base URL and `testdata/login_data.xlsx`; live runs require a reachable test environment and valid credentials. The API suite may call external API endpoints and can create data as part of its lifecycle test.

## Artifacts and reports

- Pytest HTML: `reports/html/report.html`
- JUnit XML: `reports/junit/results.xml`
- Allure results: `reports/allure-results/`
- Playwright artifacts: `reports/test-artifacts/`, `reports/screenshots/`, `reports/videos/`, and `reports/traces/`
- Logs: `reports/logs/`

The MTPLC workflow step/PDF report helper remains in `mtplc/reporting.py`; it keeps its source report behavior isolated from the master's pytest reporter. Existing source screenshots, reports, certificates, `.venv`, `.git`, caches, and live `.env` were excluded as generated or machine/secret-specific data.

## Configuration and dependencies

The master `config/settings.py` and environment YAML files are authoritative for common browser, environment, API, and reporting settings. MTPLC-specific credentials and application number variables are documented in `.env.example`. `requirements.txt` already includes the source project's Playwright, pytest, pytest-playwright, pytest-html, and python-dotenv requirements; there is one consolidated dependency declaration.

See `tests/mtplc/` for the preserved source scenarios and `mtplc/pages/` for their page objects. Original source imports were namespaced to avoid shadowing master modules; scenario logic, selectors, assertions, data, and workflows were retained.

