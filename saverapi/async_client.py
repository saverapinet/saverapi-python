"""
Async SaverAPI client for asyncio apps: aiogram / python-telegram-bot bots,
FastAPI backends and crawlers that make many calls at once.

Requires the ``async`` extra::

    pip install "saverapi-client[async]"

>>> import asyncio
>>> from saverapi import AsyncSaverAPI
>>> async def main():
...     async with AsyncSaverAPI() as api:          # reads SAVERAPI_KEY
...         media = await api.download("https://www.tiktok.com/@user/video/123")
...         print(media["download_url"])
>>> asyncio.run(main())
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Union

from .client import DEFAULT_BASE_URL, RETRY_STATUSES, USER_AGENT, _backoff, _retry_after, error_message, resolve_api_key
from .exceptions import NetworkError, error_for

try:  # pragma: no cover - import guard
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]


class AsyncSaverAPI:
    """Asynchronous twin of :class:`saverapi.SaverAPI` — same methods, awaited."""

    BASE_URL = DEFAULT_BASE_URL

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60,
        base_url: Optional[str] = None,
        max_retries: int = 2,
        backoff: float = 1.0,
        client: Optional["httpx.AsyncClient"] = None,
    ) -> None:
        if httpx is None:
            raise ImportError('AsyncSaverAPI needs httpx: pip install "saverapi-client[async]"')
        self.api_key = resolve_api_key(api_key)
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.max_retries = max(0, int(max_retries))
        self.backoff = backoff
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._headers = {"x-api-key": self.api_key, "Accept": "application/json", "User-Agent": USER_AGENT}

    async def __aenter__(self) -> "AsyncSaverAPI":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call any endpoint by path; see :meth:`saverapi.SaverAPI.request`."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        attempt = 0
        while True:
            try:
                r = await self._client.get(url, params=clean, headers=self._headers)
            except httpx.HTTPError as exc:
                if attempt < self.max_retries:
                    await asyncio.sleep(_backoff(attempt, self.backoff))
                    attempt += 1
                    continue
                raise NetworkError(0, f"Network error: {exc}") from exc

            try:
                data = r.json()
            except ValueError:
                data = {"raw": r.text}

            if r.status_code == 200:
                return data
            if r.status_code in RETRY_STATUSES and attempt < self.max_retries:
                await asyncio.sleep(_retry_after(r.headers.get("Retry-After")) or _backoff(attempt, self.backoff))
                attempt += 1
                continue
            raise error_for(
                r.status_code,
                error_message(data, r.reason_phrase),
                data,
                _retry_after(r.headers.get("Retry-After")),
            )

    async def download(self, url: str) -> Dict[str, Any]:
        """All-in-One downloader (Instagram, TikTok, Facebook, X, Pinterest, Threads, Vimeo…)."""
        return await self.request("/all-in-one-downloader-api", {"url": url})

    async def youtube(self, url: str, format: Union[str, int] = "720") -> Dict[str, Any]:
        """YouTube video or audio; ``format`` 2160/1440/1080/720/480/360/240/144/mp3."""
        return await self.request("/youtube-api", {"url": url, "farmat": str(format)})

    async def youtube_telegram(
        self,
        url: str,
        format: Union[str, int] = "720",
        bot_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Telegram-ready YouTube file; with ``bot_username`` the response has a ``file_id``
        for that bot. See :meth:`saverapi.SaverAPI.youtube_telegram`."""
        return await self.request(
            "/youtube-telegram-base",
            {"url": url, "farmat": str(format), "bot_username": bot_username or None},
        )

    async def youtube_info(self, url: str) -> Dict[str, Any]:
        return await self.request("/youtube-info-v2", {"url": url})

    async def youtube_info_basic(self, url: str) -> Dict[str, Any]:
        return await self.request("/youtube-info", {"url": url})

    async def instagram_profile(self, username: str) -> Dict[str, Any]:
        return await self.request("/instagram-profile", {"Userinfo": username.lstrip("@")})

    async def music_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        return await self.request("/music-search", {"query": query, "limit": str(limit)})

    async def shazam_recognize(self, url: str) -> Dict[str, Any]:
        return await self.request("/shazam-recognize", {"url": url})

    async def shazam_top(self, country: str = "us") -> Dict[str, Any]:
        return await self.request("/shazam-music-top", {"country": country})

    async def nsfw_scan(self, url: str) -> Dict[str, Any]:
        return await self.request("/nsfw-scanner-api", {"url": url})

    async def info_balance(self) -> Dict[str, Any]:
        return await self.request("/infobalans")

    async def api_keys_statistics(self) -> Dict[str, Any]:
        return await self.request("/api-keys/all-statistics")
