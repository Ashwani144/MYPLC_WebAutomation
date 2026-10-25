"""Custom pytest reporter plugin.

Generates a compact JSON metrics file (``reports/metrics.json``) after every run
containing per-test outcomes, durations and aggregate counts. This feeds test
trend analysis dashboards and can be committed as an artifact in CI.

Enable via ``pytest -p reporters.custom_reporter`` or by listing it in
``pytest.ini`` under ``addopts`` (already configured).
"""
from __future__ import annotations

import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

_OUTPUT = Path("reports") / "metrics.json"


class CustomMetricsReporter:
    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []
        self.start_time: float = 0.0

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self.start_time = time.time()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if report.when != "call":
            return
        self.results.append(
            {
                "test": item.nodeid,
                "outcome": report.outcome,
                "duration_s": round(report.duration, 3),
                "markers": [m.name for m in item.iter_markers()],
            }
        )

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        total_duration = round(time.time() - self.start_time, 3)
        passed = sum(1 for r in self.results if r["outcome"] == "passed")
        failed = sum(1 for r in self.results if r["outcome"] == "failed")
        skipped = sum(1 for r in self.results if r["outcome"] == "skipped")
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "total_duration_s": total_duration,
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": round(passed / len(self.results) * 100, 2) if self.results else 0.0,
            },
            "tests": self.results,
        }
        _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        _OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def pytest_configure(config: pytest.Config) -> None:
    config.pluginmanager.register(CustomMetricsReporter(), "custom-metrics-reporter")
