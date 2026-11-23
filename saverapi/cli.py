"""
Command line for SaverAPI. Prints the JSON response.

    export SAVERAPI_KEY=your_key
    saverapi download https://www.instagram.com/reel/xxxx/
    saverapi youtube https://youtu.be/xxxx --format mp3
    saverapi youtube-telegram https://youtu.be/xxxx --bot @MyBot
    saverapi youtube-info https://youtu.be/xxxx
    saverapi shazam https://example.com/song.mp3
    saverapi balance
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from ._version import __version__
from .client import YOUTUBE_FORMATS, YOUTUBE_TELEGRAM_FORMATS, SaverAPI
from .exceptions import SaverAPIError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="saverapi", description="SaverAPI.NET command line (https://saverapi.net)")
    parser.add_argument("--key", help="API key (default: the SAVERAPI_KEY environment variable)")
    parser.add_argument("--version", action="version", version=f"saverapi-client {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def url_cmd(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("url")
        return p

    url_cmd("download", "All-in-One download: Instagram, TikTok, Facebook, X, Pinterest, Threads, Vimeo…")
    yt = url_cmd("youtube", "Download a YouTube video or audio")
    yt.add_argument("--format", default="720", help="|".join(YOUTUBE_FORMATS) + " (default 720)")
    tg = url_cmd("youtube-telegram", "YouTube as a ready Telegram file (file_id for your bot)")
    tg.add_argument("--format", default="720", help="|".join(YOUTUBE_TELEGRAM_FORMATS) + " (default 720)")
    tg.add_argument("--bot", metavar="@USERNAME", help="your Telegram bot; the response then carries a file_id for it")
    url_cmd("youtube-info", "YouTube metadata")
    url_cmd("shazam", "Recognize a song from an audio/video URL")
    url_cmd("nsfw", "Scan an image/video URL for NSFW content")
    ig = sub.add_parser("instagram", help="Public Instagram profile")
    ig.add_argument("username")
    ms = sub.add_parser("music", help="Search music")
    ms.add_argument("query")
    ms.add_argument("--limit", type=int, default=10)
    top = sub.add_parser("top", help="Shazam top chart for a country")
    top.add_argument("country", nargs="?", default="us")
    sub.add_parser("balance", help="Plan, credits and limits (free)")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        api = SaverAPI(api_key=args.key)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    calls = {
        "download": lambda: api.download(args.url),
        "youtube": lambda: api.youtube(args.url, args.format),
        "youtube-telegram": lambda: api.youtube_telegram(args.url, args.format, args.bot),
        "youtube-info": lambda: api.youtube_info(args.url),
        "shazam": lambda: api.shazam_recognize(args.url),
        "nsfw": lambda: api.nsfw_scan(args.url),
        "instagram": lambda: api.instagram_profile(args.username),
        "music": lambda: api.music_search(args.query, args.limit),
        "top": lambda: api.shazam_top(args.country),
        "balance": api.info_balance,
    }
    try:
        result = calls[args.command]()
    except SaverAPIError as exc:
        print(json.dumps({"error": True, "status": exc.status_code, "message": exc.message}, ensure_ascii=False), file=sys.stderr)
        return 1
    finally:
        api.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
