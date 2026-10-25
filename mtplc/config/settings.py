"""MTPLC configuration backed by the master project's environment settings."""
from __future__ import annotations

import os
from dataclasses import dataclass

from config.settings import settings as master_settings


class ConfigurationError(RuntimeError):
    """Raised when a required MTPLC setting or role credential is missing."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    username: str
    password: str
    engineer_username: str
    engineer_password: str
    vanessa_username: str
    vanessa_password: str
    admin_username: str
    admin_password: str
    browser: str
    headless: bool
    timeout_ms: int

    def credentials_for(self, role: str) -> tuple[str, str]:
        credentials = {
            "engineer": (self.engineer_username, self.engineer_password),
            "vanessa": (self.vanessa_username, self.vanessa_password),
            "admin": (self.admin_username, self.admin_password),
        }
        try:
            username, password = credentials[role]
        except KeyError as exc:
            raise ValueError(f"Unknown application role '{role}'.") from exc
        if not username or not password:
            raise ConfigurationError(
                f"Credentials for the {role} role are not configured. "
                "Set the corresponding MTPLC variables in .env."
            )
        return username, password


def _env(name: str, fallback: str = "") -> str:
    return os.getenv(name, fallback).strip()


def _role_password(name: str) -> str:
    return _env(name) or _env("MTPLC_PASSWORD")


settings = Settings(
    base_url=master_settings.base_url.rstrip("/"),
    username=_env("MTPLC_USERNAME"),
    password=_env("MTPLC_PASSWORD"),
    engineer_username=_env("R_AND_T_ENGINEER_USERNAME") or _env("MTPLC_USERNAME"),
    engineer_password=_role_password("R_AND_T_ENGINEER_PASSWORD"),
    vanessa_username=_env("VANESSA_USERNAME"),
    vanessa_password=_role_password("VANESSA_PASSWORD"),
    admin_username=_env("R_AND_T_ADMIN_USERNAME"),
    admin_password=_role_password("R_AND_T_ADMIN_PASSWORD"),
    browser=master_settings.browser,
    headless=master_settings.headless,
    timeout_ms=int(_env("PLAYWRIGHT_TIMEOUT_MS", "15000")),
)
