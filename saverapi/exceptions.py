"""Exceptions raised by the SaverAPI client."""

from __future__ import annotations

from typing import Any, Optional


class SaverAPIError(Exception):
    """Raised when the SaverAPI service returns a non-success response.

    ``status_code`` is the HTTP status (``0`` for network errors), ``message``
    the server's explanation and ``payload`` the decoded response body.
    """

    def __init__(self, status_code: int, message: str, payload: Any = None):
        self.status_code = status_code
        self.message = message
        self.payload = payload
        super().__init__(f"[{status_code}] {message}")


class AuthenticationError(SaverAPIError):
    """401/403: the API key is missing, wrong or switched off."""


class InsufficientCreditsError(SaverAPIError):
    """402: the plan has no credits left for this request."""


class RateLimitError(SaverAPIError):
    """429: too many requests for the plan's per-second/hour/day limit.

    ``retry_after`` is the server's suggested wait in seconds, when given.
    """

    def __init__(self, status_code: int, message: str, payload: Any = None, retry_after: Optional[float] = None):
        super().__init__(status_code, message, payload)
        self.retry_after = retry_after


class NotFoundError(SaverAPIError):
    """404: the content (or endpoint) could not be found."""


class ServerError(SaverAPIError):
    """5xx: a temporary failure on the service side. Failed 5xx calls are not charged."""


class NetworkError(SaverAPIError):
    """The request never got a response (DNS, connection, timeout)."""


def error_for(status_code: int, message: str, payload: Any = None, retry_after: Optional[float] = None) -> SaverAPIError:
    """The most specific exception for an HTTP status."""
    if status_code in (401, 403):
        return AuthenticationError(status_code, message, payload)
    if status_code == 402:
        return InsufficientCreditsError(status_code, message, payload)
    if status_code == 404:
        return NotFoundError(status_code, message, payload)
    if status_code == 429:
        return RateLimitError(status_code, message, payload, retry_after)
    if status_code >= 500:
        return ServerError(status_code, message, payload)
    return SaverAPIError(status_code, message, payload)
