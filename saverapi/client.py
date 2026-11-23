"""
SaverAPI Python client.

Official SDK for https://saverapi.net — one REST API for social media
downloads and media data: Instagram, TikTok, YouTube, Facebook, Twitter (X),
Snapchat, Pinterest, Likee, SoundCloud, Spotify, Threads, Twitch, Weibo,
Vimeo and more, plus YouTube downloads up to 4K, Telegram-ready YouTube
files, YouTube metadata, Instagram profiles, Shazam music recognition, music
search, Shazam charts and an NSFW scanner.
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional, Tuple, Union

import requests

from .exceptions import NetworkError, SaverAPIError, error_for

DEFAULT_BASE_URL = "https://saverapi.net/api"
ENV_API_KEY = "SAVERAPI_KEY"

#: Statuses worth retrying: rate limiting and temporary server failures.
#: Failed 5xx calls are not charged, so retrying them costs nothing.
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})

#: ``format`` values accepted by :meth:`SaverAPI.youtube` (video height, or ``"mp3"`` for audio).
YOUTUBE_FORMATS: Tuple[str, ...] = ("2160", "1440", "1080", "720", "480", "360", "240", "144", "mp3")

#: ``format`` values accepted by :meth:`SaverAPI.youtube_telegram`.
YOUTUBE_TELEGRAM_FORMATS: Tuple[str, ...] = ("1080", "720", "480", "360", "240", "144", "mp3")

from ._version import __version__ as _version

USER_AGENT = f"saverapi-client/{_version} (+https://saverapi.net)"


def _backoff(attempt: int, base: float) -> float:
    """Exponential backoff with jitter: base, 2·base, 4·base … (+ up to 25%)."""
    delay = base * (2 ** attempt)
    return delay + random.uniform(0, delay * 0.25)


def resolve_api_key(api_key: Optional[str]) -> str:
    key = api_key or os.environ.get(ENV_API_KEY, "")
    if not key:
        raise ValueError(
            f"api_key is required: pass api_key=... or set the {ENV_API_KEY} environment variable. "
            "Get a free key at https://saverapi.net"
        )
    return key


def error_message(data: Any, fallback: str) -> str:
    if isinstance(data, dict):
        for field in ("message", "error", "detail"):
            value = data.get(field)
            if isinstance(value, str) and value:
                return value
    return fallback or "Request failed"


class SaverAPI:
    """Client for the SaverAPI.NET REST API.

    >>> from saverapi import SaverAPI
    >>> api = SaverAPI(api_key="YOUR_API_KEY")          # or set SAVERAPI_KEY
    >>> media = api.download("https://www.instagram.com/reel/xxxx/")
    >>> media["download_url"]

    Every method returns the decoded JSON as a ``dict`` and raises a
    :class:`~saverapi.SaverAPIError` subclass on failure. Rate-limit (429) and
    temporary server errors are retried automatically (``max_retries``).
    """

    BASE_URL = DEFAULT_BASE_URL

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 60,
        base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
        max_retries: int = 2,
        backoff: float = 1.0,
    ) -> None:
        self.api_key = resolve_api_key(api_key)
        self.timeout = timeout
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.max_retries = max(0, int(max_retries))
        self.backoff = backoff
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "x-api-key": self.api_key,
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
        )

    # ------------------------------------------------------------------ #
    # Plumbing
    # ------------------------------------------------------------------ #
    def __enter__(self) -> "SaverAPI":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call any endpoint by path, e.g. ``api.request("/youtube-info", {"url": ...})``.

        Useful for endpoints added to the catalog after this SDK version.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        clean = {k: v for k, v in (params or {}).items() if v is not None}

        attempt = 0
        while True:
            try:
                r = self.session.get(url, params=clean, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(_backoff(attempt, self.backoff))
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
                time.sleep(_retry_after(r.headers.get("Retry-After")) or _backoff(attempt, self.backoff))
                attempt += 1
                continue

            raise error_for(
                r.status_code,
                error_message(data, r.reason),
                data,
                _retry_after(r.headers.get("Retry-After")),
            )

    # Backwards compatibility with 1.0.x.
    _request = request

    # ------------------------------------------------------------------ #
    # Universal social media downloader
    # ------------------------------------------------------------------ #
    def download(self, url: str) -> Dict[str, Any]:
        """All-in-One downloader: one call for a public post link.

        Supports Instagram (posts, Reels), TikTok, Facebook, Twitter (X),
        Snapchat, Pinterest, Likee, SoundCloud, Spotify, Threads, Twitch,
        Weibo, Vimeo and more. The response's ``hosting`` field names the
        platform, ``type`` is ``video`` or ``image`` and ``download_url``
        points at the media file.
        """
        return self.request("/all-in-one-downloader-api", {"url": url})

    # ------------------------------------------------------------------ #
    # YouTube
    # ------------------------------------------------------------------ #
    def youtube(self, url: str, format: Union[str, int] = "720") -> Dict[str, Any]:
        """Download a YouTube video or its audio.

        ``format``: ``"2160"`` (4K), ``"1440"`` (2K), ``"1080"``, ``"720"``,
        ``"480"``, ``"360"``, ``"240"``, ``"144"`` or ``"mp3"`` — see
        :data:`YOUTUBE_FORMATS`. The response's ``url`` points at the file.
        """
        # The service's parameter is spelled "farmat".
        return self.request("/youtube-api", {"url": url, "farmat": str(format)})

    def youtube_telegram(
        self,
        url: str,
        format: Union[str, int] = "720",
        bot_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        """YouTube video or audio as a ready-to-send Telegram file.

        ``format``: ``"1080"``, ``"720"``, ``"480"``, ``"360"``, ``"240"``,
        ``"144"`` or ``"mp3"`` — see :data:`YOUTUBE_TELEGRAM_FORMATS`.

        ``bot_username``: your Telegram bot (``"@MyBot"``). When given, the
        response carries a ``file_id`` valid for that bot: pass it to
        ``sendVideo`` when ``media_type`` is ``"video"`` or ``sendAudio`` when
        it is ``"audio"`` — no re-upload needed, and the id can be stored and
        reused. If ``status`` is ``"processing"``, call again after
        ``retry_after`` seconds.
        """
        return self.request(
            "/youtube-telegram-base",
            {"url": url, "farmat": str(format), "bot_username": bot_username or None},
        )

    def youtube_info(self, url: str) -> Dict[str, Any]:
        """Detailed YouTube metadata: title, author, duration, thumbnails, formats."""
        return self.request("/youtube-info-v2", {"url": url})

    def youtube_info_basic(self, url: str) -> Dict[str, Any]:
        """Lightweight YouTube metadata (title, author, thumbnail) — the cheapest YouTube call."""
        return self.request("/youtube-info", {"url": url})

    # ------------------------------------------------------------------ #
    # Instagram
    # ------------------------------------------------------------------ #
    def instagram_profile(self, username: str) -> Dict[str, Any]:
        """Public Instagram profile: bio, counts, profile picture, stories, highlights, posts."""
        return self.request("/instagram-profile", {"Userinfo": username.lstrip("@")})

    # ------------------------------------------------------------------ #
    # Music: search / recognize / charts
    # ------------------------------------------------------------------ #
    def music_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search music tracks by title or artist."""
        return self.request("/music-search", {"query": query, "limit": str(limit)})

    def shazam_recognize(self, url: str) -> Dict[str, Any]:
        """Identify a song from an audio or video URL using Shazam."""
        return self.request("/shazam-recognize", {"url": url})

    def shazam_top(self, country: str = "us") -> Dict[str, Any]:
        """Shazam Top chart for a country (``"us"``, ``"uz"``, ``"united-kingdom"``…)."""
        return self.request("/shazam-music-top", {"country": country})

    # ------------------------------------------------------------------ #
    # Moderation
    # ------------------------------------------------------------------ #
    def nsfw_scan(self, url: str) -> Dict[str, Any]:
        """Scan an image or video URL for NSFW content."""
        return self.request("/nsfw-scanner-api", {"url": url})

    # ------------------------------------------------------------------ #
    # Account (free calls)
    # ------------------------------------------------------------------ #
    def info_balance(self) -> Dict[str, Any]:
        """Plan, remaining credits, rate limits and subscription dates. Free."""
        return self.request("/infobalans")

    def api_keys_statistics(self) -> Dict[str, Any]:
        """Usage statistics for every API key on the account. Free."""
        return self.request("/api-keys/all-statistics")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def save_file(self, file_url: str, path: str, chunk_size: int = 1 << 15) -> str:
        """Stream a media URL (e.g. ``download_url``) to ``path``; returns the absolute path.

        Media links from social networks expire, so save them right after the call.
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with requests.get(file_url, stream=True, timeout=self.timeout, headers={"User-Agent": USER_AGENT}) as r:
            r.raise_for_status()
            with open(path, "wb") as fh:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        fh.write(chunk)
        return os.path.abspath(path)

    def __repr__(self) -> str:  # pragma: no cover
        masked = (self.api_key[:4] + "…") if self.api_key else "?"
        return f"<SaverAPI key={masked} base_url={self.base_url}>"


def _retry_after(value: Optional[str]) -> Optional[float]:
    try:
        return max(0.0, float(value)) if value else None
    except ValueError:
        return None


__all__ = [
    "SaverAPI",
    "SaverAPIError",
    "DEFAULT_BASE_URL",
    "ENV_API_KEY",
    "YOUTUBE_FORMATS",
    "YOUTUBE_TELEGRAM_FORMATS",
]
