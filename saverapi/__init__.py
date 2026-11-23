"""
saverapi — official Python SDK for SaverAPI.NET (https://saverapi.net).

Social media downloader and media data API: Instagram, TikTok, YouTube,
Facebook, Twitter (X), Pinterest, Threads, Vimeo and more, plus YouTube up
to 4K, Telegram-ready YouTube files, YouTube metadata, Instagram profiles,
Shazam recognition, music search and an NSFW scanner.

    from saverapi import SaverAPI
    api = SaverAPI(api_key="YOUR_API_KEY")   # or set SAVERAPI_KEY
    api.download("https://www.instagram.com/reel/xxxx/")
"""

from ._version import __version__
from .async_client import AsyncSaverAPI
from .client import YOUTUBE_FORMATS, YOUTUBE_TELEGRAM_FORMATS, SaverAPI
from .exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    SaverAPIError,
    ServerError,
)

__all__ = [
    "SaverAPI",
    "AsyncSaverAPI",
    "SaverAPIError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "NotFoundError",
    "ServerError",
    "NetworkError",
    "YOUTUBE_FORMATS",
    "YOUTUBE_TELEGRAM_FORMATS",
    "__version__",
]
