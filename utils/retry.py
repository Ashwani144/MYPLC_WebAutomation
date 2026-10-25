"""Retry helpers for handling flaky operations.

Provides a decorator that retries a callable with exponential backoff. This
complements pytest's built-in ``--reruns`` (via pytest-rerunfailures) by giving
fine-grained control inside page objects and utilities.
"""
from __future__ import annotations

import functools
import time
from typing import Callable, Tuple, Type, TypeVar

from utils.logger import get_logger

log = get_logger("retry")

T = TypeVar("T")


def retry(
    attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function on failure with exponential backoff.

    Args:
        attempts: Total number of tries before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to the delay after each failed attempt.
        exceptions: Exception types that should trigger a retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            current_delay = delay
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203
                    last_exc = exc
                    log.warning(
                        "Attempt %s/%s of '%s' failed: %s",
                        attempt, attempts, func.__name__, exc,
                    )
                    if attempt < attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
