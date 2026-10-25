from __future__ import annotations

import re

from mtplc import reporting as report_config


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

