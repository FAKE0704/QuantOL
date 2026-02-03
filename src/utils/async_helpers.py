"""Async utilities for database operations and retry logic.

This module provides reusable async helpers including:
- Generic retry decorator with exponential backoff
- Database lock retry logic
"""

import asyncio
from functools import wraps
from typing import Callable, TypeVar, Coroutine, Any

T = TypeVar('T')


async def retry_on_locked(
    coro: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
    delay: float = 0.1
) -> T:
    """Retry a coroutine on database lock error with exponential backoff.

    This function is useful for SQLite database operations that may fail
    due to "database is locked" errors under concurrent access.

    Args:
        coro: Callable that returns a coroutine to execute
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (will be exponentially increased)

    Returns:
        The result of the coroutine

    Raises:
        The original exception if all retries fail
    """
    for attempt in range(max_retries):
        try:
            return await coro()
        except Exception as e:
            error_str = str(e).lower()
            is_lock_error = 'locked' in error_str or 'database is locked' in error_str

            if is_lock_error and attempt < max_retries - 1:
                # Exponential backoff: delay * 2^attempt
                await asyncio.sleep(delay * (2 ** attempt))
                continue
            raise
    return None  # Should never reach here


def async_retry(
    max_retries: int = 3,
    delay: float = 0.1,
    exceptions: tuple = (Exception,)
):
    """Decorator for async functions with retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries
        exceptions: Tuple of exception types to catch

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2 ** attempt))
                        continue
                    raise
            return None
        return wrapper
    return decorator
