from __future__ import annotations

import re
from types import SimpleNamespace

from mtplc import reporting as report_config


def test_pdf_includes_each_scenario_and_its_execution_statuses(
    monkeypatch,
    tmp_path,
) -> None:
    scenario_results = [
        {
            "nodeid": "test_add_sections",
            "name": "test_add_sections",
            "status": "PASSED",
            "duration": 12.5,
            "longrepr": "",
            "screenshot": None,
            "url": None,
            "scenario_name": "Add Section Workflow",
            "scenario_steps": ["Create first section", "Create second section"],
            "application_number": "P-12345",
            "model_number_summary": "Model-A, Model-B",
            "completed_steps": [1, 2],
            "started_steps": [1, 2],
        },
        {
            "nodeid": "test_application_status",
            "name": "test_application_status",
            "status": "FAILED",
            "duration": 8.0,
            "longrepr": "Action failed",
            "screenshot": None,
            "url": None,
            "scenario_name": "Application Status Workflow",
            "scenario_steps": ["Open application", "Change status", "Complete"],
            "application_number": "P-67890",
            "model_number_summary": "Workbook model set",
            "completed_steps": [1],
            "started_steps": [1, 2],
        },
    ]
    monkeypatch.setattr(report_config, "TEST_RESULTS", scenario_results)
    monkeypatch.setattr(
        report_config,
        "PDF_SOURCE_HTML",
        tmp_path / "report.html",
    )

    scenarios = report_config._get_report_scenarios()
    assert [scenario["statuses"] for scenario in scenarios] == [
        ["PASSED", "PASSED"],
        ["PASSED", "FAILED", "NOT EXECUTED"],
    ]

    report_config._generate_pdf_source_html()
    report_html = report_config.PDF_SOURCE_HTML.read_text(encoding="utf-8")

    assert "Add Section Workflow" in report_html
    assert "Application Status Workflow" in report_html
    assert "Create first section" in report_html
    assert "Change status" in report_html
    assert "P-12345" in report_html
    assert "P-67890" in report_html
    assert re.search(
        r'class="step-status step-failed">\s*FAILED\s*</td>',
        report_html,
    )
    assert len(
        re.findall(
            r'class="step-status step-passed">\s*PASSED\s*</td>',
            report_html,
        )
    ) == 3
    assert re.search(
        r'class="step-status step-not-executed">\s*NOT EXECUTED\s*</td>',
        report_html,
    )


def test_pdf_marks_active_workflow_step_as_failed(monkeypatch) -> None:
    monkeypatch.setattr(
        report_config,
        "TEST_RESULTS",
        [
            {
                "status": "FAILED",
                "completed_steps": list(range(1, 10)),
                "started_steps": list(range(1, 11)),
            }
        ],
    )

    statuses = report_config._get_scenario_step_statuses()

    assert statuses[:9] == ["PASSED"] * 9
    assert statuses[9] == "FAILED"
    assert statuses[10:] == ["NOT EXECUTED"] * (
        len(report_config.SCENARIO_STEPS) - 10
    )

    scenario_table = report_config._generate_scenario_table()
    assert "R&amp;T Engineer: log in successfully" in scenario_table
    assert "Vanessa: create/verify the Write Up Action Item after reload" in (
        scenario_table
    )
    assert re.search(
        r'class="step-status step-failed">\s*FAILED\s*</td>',
        scenario_table,
    )


def test_report_scenarios_collect_step_screenshots(
    monkeypatch,
    tmp_path,
) -> None:
    screenshot_path = tmp_path / "created-section.png"
    monkeypatch.setattr(
        report_config,
        "TEST_RESULTS",
        [
            {
                "status": "PASSED",
                "scenario_name": "Main Models CRUD",
                "scenario_steps": ["Create section"],
                "completed_steps": [1],
                "started_steps": [1],
                "step_screenshots": [
                    {"step": 1, "path": str(screenshot_path)}
                ],
            }
        ],
    )

    scenarios = report_config._get_report_scenarios()

    assert scenarios[0]["step_screenshots"] == {
        1: str(screenshot_path)
    }


def test_scenario_table_embeds_step_screenshot(
    monkeypatch,
    tmp_path,
) -> None:
    screenshot_path = tmp_path / "created-section.png"
    screenshot_path.write_bytes(b"png")
    monkeypatch.setattr(
        report_config,
        "_image_to_base64",
        lambda _path: "data:image/png;base64,encoded",
    )

    table = report_config._generate_scenario_table(
        ["Create section"],
        ["PASSED"],
        {1: str(screenshot_path)},
    )

    assert "<th class=\"step-evidence-header\">" in table
    assert (
        '<img class="step-evidence-image" '
        'src="data:image/png;base64,encoded"'
    ) in table


def test_pdf_generator_replaces_report_with_fresh_browser_output(
    monkeypatch,
    tmp_path,
) -> None:
    source_html = tmp_path / "source.html"
    source_html.write_text("<html>latest report</html>", encoding="utf-8")
    report_path = tmp_path / "report.pdf"
    report_path.write_bytes(b"old report")

    monkeypatch.setattr(report_config, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(report_config, "PDF_SOURCE_HTML", source_html)
    monkeypatch.setattr(report_config, "PDF_REPORT", report_path)
    monkeypatch.setattr(report_config, "_find_browser", lambda: "edge")

    def create_fresh_pdf(command, **_kwargs):
        assert any(argument.startswith("--user-data-dir=") for argument in command)
        output_argument = next(
            argument
            for argument in command
            if argument.startswith("--print-to-pdf=")
        )
        output_path = output_argument.split("=", maxsplit=1)[1]
        with open(output_path, "wb") as pdf:
            pdf.write(b"%PDF-fresh report")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(
        report_config.subprocess,
        "run",
        create_fresh_pdf,
    )

    report_config._generate_pdf_report()

    assert report_path.read_bytes() == b"%PDF-fresh report"


def test_pdf_generator_does_not_accept_a_stale_report(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    source_html = tmp_path / "source.html"
    source_html.write_text("<html>latest report</html>", encoding="utf-8")
    report_path = tmp_path / "report.pdf"
    report_path.write_bytes(b"old report")

    monkeypatch.setattr(report_config, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(report_config, "PDF_SOURCE_HTML", source_html)
    monkeypatch.setattr(report_config, "PDF_REPORT", report_path)
    monkeypatch.setattr(report_config, "_find_browser", lambda: "edge")
    monkeypatch.setattr(
        report_config.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stderr="",
        ),
    )

    report_config._generate_pdf_report()

    assert report_path.read_bytes() == b"old report"
    assert "fresh PDF output was not created" in caplog.text


def test_pdf_generator_saves_timestamped_report_when_existing_pdf_is_locked(
    monkeypatch,
    tmp_path,
    caplog,
) -> None:
    source_html = tmp_path / "source.html"
    source_html.write_text("<html>latest report</html>", encoding="utf-8")
    report_path = tmp_path / "report.pdf"
    report_path.write_bytes(b"locked old report")

    monkeypatch.setattr(report_config, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(report_config, "PDF_SOURCE_HTML", source_html)
    monkeypatch.setattr(report_config, "PDF_REPORT", report_path)
    monkeypatch.setattr(report_config, "_find_browser", lambda: "edge")

    def create_fresh_pdf(command, **_kwargs):
        output_argument = next(
            argument
            for argument in command
            if argument.startswith("--print-to-pdf=")
        )
        output_path = output_argument.split("=", maxsplit=1)[1]
        with open(output_path, "wb") as pdf:
            pdf.write(b"%PDF-fresh report")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(
        report_config.subprocess,
        "run",
        create_fresh_pdf,
    )
    original_replace = report_config.Path.replace

    def replace_unless_locked(source, target):
        if target == report_path:
            raise PermissionError("report is open")
        return original_replace(source, target)

    monkeypatch.setattr(
        report_config.Path,
        "replace",
        replace_unless_locked,
    )

    report_config._generate_pdf_report()

    timestamped_reports = list(tmp_path.glob("report_*.pdf"))
    assert len(timestamped_reports) == 1
    assert timestamped_reports[0].read_bytes() == b"%PDF-fresh report"
    assert report_path.read_bytes() == b"locked old report"
    assert "existing PDF is locked" in caplog.text
