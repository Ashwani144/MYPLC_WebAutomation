"""Slack / Microsoft Teams notification helpers.

These are best-effort: if a webhook URL is not configured the send is a no-op.
Used by the CI pipeline (via a small runner) and can also be called from a
pytest session-finish hook.
"""
from __future__ import annotations

import json
from typing import Optional

import requests

from config.settings import settings
from utils.logger import get_logger

log = get_logger("notifier")


def _post(url: str, payload: dict) -> bool:
    try:
        resp = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as exc:  # best-effort
        log.warning("Notification failed: %s", exc)
        return False


def notify_slack(summary: str, passed: int, failed: int, skipped: int, url: Optional[str] = None) -> bool:
    url = url or settings.slack_webhook_url
    if not url:
        log.debug("Slack webhook not configured; skipping notification")
        return False
    color = "#36a64f" if failed == 0 else "#d00000"
    payload = {
        "attachments": [
            {
                "color": color,
                "title": "Playwright Test Run",
                "text": summary,
                "fields": [
                    {"title": "Passed", "value": str(passed), "short": True},
                    {"title": "Failed", "value": str(failed), "short": True},
                    {"title": "Skipped", "value": str(skipped), "short": True},
                ],
            }
        ]
    }
    return _post(url, payload)


def notify_teams(summary: str, passed: int, failed: int, skipped: int, url: Optional[str] = None) -> bool:
    url = url or settings.teams_webhook_url
    if not url:
        log.debug("Teams webhook not configured; skipping notification")
        return False
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "36a64f" if failed == 0 else "d00000",
        "summary": "Playwright Test Run",
        "sections": [
            {
                "activityTitle": "Playwright Test Run",
                "text": summary,
                "facts": [
                    {"name": "Passed", "value": str(passed)},
                    {"name": "Failed", "value": str(failed)},
                    {"name": "Skipped", "value": str(skipped)},
                ],
            }
        ],
    }
    return _post(url, payload)
