"""Centralized configuration loader.

Loads settings from (in order of precedence):
1. Environment variables (highest priority)
2. Environment-specific YAML file (config/environments/<env>.yaml)
3. Base defaults defined here (lowest priority)

Usage:
    from config.settings import settings
    print(settings.base_url)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

# Load .env if present (local development convenience).
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

ENV_DIR = Path(__file__).resolve().parent / "environments"


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    """Immutable-ish runtime settings resolved from env + yaml + defaults."""

    environment: str = "dev"
    base_url: str = "https://qa-myplc.iapmo.org/"
    api_base_url: str = "https://jsonplaceholder.typicode.com"

    # MYPLC (IAPMO) REST API — used by the client-flow API suite.
    myplc_api_base_url: str = "https://qa-myplc.iapmo.org/api"
    myplc_username: str = "vanessa.iraheta"
    myplc_password: str = ""  # supply via MYPLC_PASSWORD env var (never hardcode)
    myplc_user_source: str = "mplc"

    browser: str = "chromium"
    headless: bool = True
    slow_mo: int = 0
    viewport_width: int = 1920
    viewport_height: int = 1080
    default_timeout: int = 30000
    navigation_timeout: int = 30000
    retries: int = 1
    workers: int = 4
    locale: str = "en-US"
    timezone: str = "UTC"
    record_video: bool = False
    record_trace: bool = False
    screenshot_on_failure: bool = True
    image_threshold: int = 1  # minimum images expected on the page

    # Remote / grid / cloud execution
    use_selenium_grid: bool = False
    selenium_grid_url: str = "http://localhost:4444/wd/hub"
    use_browserstack: bool = False
    browserstack_url: str = "wss://cdp.browserstack.com/playwright"
    browserstack_username: str = ""
    browserstack_access_key: str = ""
    use_lambdatest: bool = False
    lambdatest_url: str = "wss://cdp.lambdatest.com/playwright"
    lambdatest_username: str = ""
    lambdatest_access_key: str = ""

    # Notifications
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""

    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Settings":
        env = os.getenv("TEST_ENV", "dev").strip().lower()
        file_cfg = cls._load_yaml(env)

        def pick(key: str, env_key: str, default: Any) -> Any:
            if os.getenv(env_key) is not None:
                return os.getenv(env_key)
            if key in file_cfg:
                return file_cfg[key]
            return default

        return cls(
            environment=env,
            base_url=pick("base_url", "BASE_URL", cls.base_url),
            api_base_url=pick("api_base_url", "API_BASE_URL", cls.api_base_url),
            myplc_api_base_url=pick("myplc_api_base_url", "MYPLC_API_BASE_URL", cls.myplc_api_base_url),
            myplc_username=pick("myplc_username", "MYPLC_USERNAME", cls.myplc_username),
            myplc_password=pick("myplc_password", "MYPLC_PASSWORD", cls.myplc_password),
            myplc_user_source=pick("myplc_user_source", "MYPLC_USER_SOURCE", cls.myplc_user_source),
            browser=pick("browser", "BROWSER", cls.browser),
            headless=_as_bool(pick("headless", "HEADLESS", cls.headless), cls.headless),
            slow_mo=_as_int(pick("slow_mo", "SLOW_MO", cls.slow_mo), cls.slow_mo),
            viewport_width=_as_int(pick("viewport_width", "VIEWPORT_WIDTH", cls.viewport_width), cls.viewport_width),
            viewport_height=_as_int(pick("viewport_height", "VIEWPORT_HEIGHT", cls.viewport_height), cls.viewport_height),
            default_timeout=_as_int(pick("default_timeout", "DEFAULT_TIMEOUT", cls.default_timeout), cls.default_timeout),
            navigation_timeout=_as_int(pick("navigation_timeout", "NAVIGATION_TIMEOUT", cls.navigation_timeout), cls.navigation_timeout),
            retries=_as_int(pick("retries", "RETRIES", cls.retries), cls.retries),
            workers=_as_int(pick("workers", "WORKERS", cls.workers), cls.workers),
            locale=pick("locale", "LOCALE", cls.locale),
            timezone=pick("timezone", "TIMEZONE", cls.timezone),
            record_video=_as_bool(pick("record_video", "RECORD_VIDEO", cls.record_video), cls.record_video),
            record_trace=_as_bool(pick("record_trace", "RECORD_TRACE", cls.record_trace), cls.record_trace),
            screenshot_on_failure=_as_bool(pick("screenshot_on_failure", "SCREENSHOT_ON_FAILURE", cls.screenshot_on_failure), cls.screenshot_on_failure),
            image_threshold=_as_int(pick("image_threshold", "IMAGE_THRESHOLD", cls.image_threshold), cls.image_threshold),
            use_selenium_grid=_as_bool(pick("use_selenium_grid", "USE_SELENIUM_GRID", cls.use_selenium_grid), cls.use_selenium_grid),
            selenium_grid_url=pick("selenium_grid_url", "SELENIUM_GRID_URL", cls.selenium_grid_url),
            use_browserstack=_as_bool(pick("use_browserstack", "USE_BROWSERSTACK", cls.use_browserstack), cls.use_browserstack),
            browserstack_url=pick("browserstack_url", "BROWSERSTACK_URL", cls.browserstack_url),
            browserstack_username=pick("browserstack_username", "BROWSERSTACK_USERNAME", cls.browserstack_username),
            browserstack_access_key=pick("browserstack_access_key", "BROWSERSTACK_ACCESS_KEY", cls.browserstack_access_key),
            use_lambdatest=_as_bool(pick("use_lambdatest", "USE_LAMBDATEST", cls.use_lambdatest), cls.use_lambdatest),
            lambdatest_url=pick("lambdatest_url", "LAMBDATEST_URL", cls.lambdatest_url),
            lambdatest_username=pick("lambdatest_username", "LAMBDATEST_USERNAME", cls.lambdatest_username),
            lambdatest_access_key=pick("lambdatest_access_key", "LAMBDATEST_ACCESS_KEY", cls.lambdatest_access_key),
            slack_webhook_url=pick("slack_webhook_url", "SLACK_WEBHOOK_URL", cls.slack_webhook_url),
            teams_webhook_url=pick("teams_webhook_url", "TEAMS_WEBHOOK_URL", cls.teams_webhook_url),
            extra=file_cfg.get("extra", {}),
        )

    @staticmethod
    def _load_yaml(env: str) -> Dict[str, Any]:
        path = ENV_DIR / f"{env}.yaml"
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def as_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.load()


# Module-level singleton for convenient imports.
settings = get_settings()
