<div align="center">

# SaverAPI Python SDK

### Social media video downloader API for Python — YouTube (up to 4K), Instagram, TikTok, Facebook, X and more

Official client for **[SaverAPI.NET](https://saverapi.net)**: download videos, Reels and audio, get YouTube in up to 4K or as a ready Telegram `file_id`, read YouTube metadata, look up Instagram profiles, recognise songs with Shazam and scan media for NSFW content — with one API key, from sync code, `asyncio` or the command line.

[![PyPI](https://img.shields.io/pypi/v/saverapi-client.svg?color=6f42c1&label=pypi&logo=pypi&logoColor=white)](https://pypi.org/project/saverapi-client/)
[![Python](https://img.shields.io/pypi/pyversions/saverapi-client.svg?color=3776ab&logo=python&logoColor=white)](https://pypi.org/project/saverapi-client/)
[![License](https://img.shields.io/badge/license-MIT-success.svg)](#license)
[![Downloads](https://img.shields.io/pypi/dm/saverapi-client.svg?color=0ea5e9&label=downloads)](https://pypi.org/project/saverapi-client/)
[![Docs](https://img.shields.io/badge/docs-saverapi.net-4f46e5)](https://saverapi.net/docs)
[![Telegram](https://img.shields.io/badge/telegram-@SaverAPI-26a5e4?logo=telegram&logoColor=white)](https://t.me/SaverAPI)

</div>

```bash
pip install -U saverapi-client            # sync client + CLI
pip install -U "saverapi-client[async]"   # + AsyncSaverAPI (httpx)
```

Get a free API key at **[saverapi.net](https://saverapi.net/auth/register)** — no card needed.

**Why SaverAPI**

- **One API for every major platform** — Instagram Reels and posts, TikTok, YouTube video and MP3, Facebook, X (Twitter), Pinterest, Threads, Snapchat, Vimeo, SoundCloud and more behind a single key.
- **YouTube from 144p to 4K** — `2160`, `1440`, `1080`, `720`… or `mp3` audio, with no yt-dlp, ffmpeg, proxies or cookies to maintain.
- **Built for Telegram bots** — get a ready `file_id` for your own bot and send a YouTube video instantly, without downloading or re-uploading it.
- **Sync, async and CLI** — `SaverAPI` (requests), `AsyncSaverAPI` (httpx, for aiogram / FastAPI) and a `saverapi` terminal command.
- **Documented responses** — a real JSON sample and field table for every method, [right here](#response-reference).
- **Production ready** — automatic retries, typed exceptions, type hints, Python 3.8–3.13.

**Contents:** [Quick start](#quick-start) · [Supported platforms](#supported-platforms) · [Examples](#examples) · [Response reference](#response-reference) · [Async](#async-aiogram-fastapi-asyncio) · [Command line](#command-line) · [Errors and retries](#errors-and-retries) · [FAQ](#faq) · [Changelog](#changelog)

---

## Quick start

```python
from saverapi import SaverAPI

api = SaverAPI(api_key="YOUR_API_KEY")   # or export SAVERAPI_KEY=...

media = api.download("https://www.instagram.com/reel/DPOi9V-CAqH/")
print(media["hosting"], media["type"], media["download_url"])

api.save_file(media["download_url"], "downloads/reel.mp4")
```

One call, one parameter: the **All-in-One downloader** recognises the platform from the link. The response's `hosting` field tells you which network it was, `type` is `video` or `image`, and `download_url` points at the file.

## Supported platforms

| Platform | Method | REST endpoint |
|---|---|---|
| Instagram (posts, Reels) | `api.download(url)` | [`/all-in-one-downloader-api`](https://saverapi.net/instagram-downloader-api) |
| TikTok | `api.download(url)` | [`/all-in-one-downloader-api`](https://saverapi.net/tiktok-downloader-api) |
| Facebook | `api.download(url)` | [`/all-in-one-downloader-api`](https://saverapi.net/facebook-video-api) |
| Twitter / X | `api.download(url)` | [`/all-in-one-downloader-api`](https://saverapi.net/twitter-video-api) |
| Snapchat, Pinterest, Likee, Threads, Twitch, Weibo, Vimeo, SoundCloud, Spotify | `api.download(url)` | [`/all-in-one-downloader-api`](https://saverapi.net/all-in-one-downloader-api) |
| YouTube video (144p–4K) / MP3 | `api.youtube(url, format)` | [`/youtube-api`](https://saverapi.net/youtube-downloader-api) |
| YouTube as a Telegram `file_id` | `api.youtube_telegram(url, format, bot_username)` | `/youtube-telegram-base` |
| YouTube metadata | `api.youtube_info(url)` · `api.youtube_info_basic(url)` | `/youtube-info-v2` · `/youtube-info` |
| Instagram profile | `api.instagram_profile(username)` | `/instagram-profile` |
| Shazam song recognition | `api.shazam_recognize(url)` | [`/shazam-recognize`](https://saverapi.net/shazam-api) |
| Shazam top charts | `api.shazam_top(country)` | `/shazam-music-top` |
| Music search | `api.music_search(query, limit)` | `/music-search` |
| NSFW scanner | `api.nsfw_scan(url)` | `/nsfw-scanner-api` |
| Account balance (free) | `api.info_balance()` | `/infobalans` |
| Key statistics (free) | `api.api_keys_statistics()` | `/api-keys/all-statistics` |

What each method returns: **[Response reference](#response-reference)** below. Live parameter reference: **[saverapi.net/docs](https://saverapi.net/docs)**. Endpoints added to the catalog later can be called with `api.request("/endpoint-path", {"param": "value"})`.

## Examples

### Download a YouTube video (up to 4K) or MP3 in Python

```python
video = api.youtube("https://youtu.be/OORSiK8ScTI", format="720")
api.save_file(video["url"], "video.mp4")

audio = api.youtube("https://youtu.be/OORSiK8ScTI", format="mp3")
uhd = api.youtube("https://youtu.be/OORSiK8ScTI", format="2160")    # 4K, when the video has it

info = api.youtube_info("https://youtu.be/OORSiK8ScTI")
print(info["title"], info["duration"])
```

`format` is one of `2160`, `1440`, `1080`, `720`, `480`, `360`, `240`, `144` or `mp3` (also available as `saverapi.YOUTUBE_FORMATS`).

### YouTube straight into a Telegram bot (`file_id`)

Pass your bot's username and the response carries a `file_id` that is valid for that bot — send it without downloading or re-uploading anything, and store it to reuse later.

```python
import time

res = api.youtube_telegram("https://youtu.be/OORSiK8ScTI", format="720", bot_username="@MyBot")
while res.get("status") == "processing":          # a new video is still being prepared
    time.sleep(res.get("retry_after", 5))
    res = api.youtube_telegram("https://youtu.be/OORSiK8ScTI", format="720", bot_username="@MyBot")

if res["media_type"] == "video":
    bot.send_video(chat_id, res["file_id"])       # your Telegram library's sendVideo
else:
    bot.send_audio(chat_id, res["file_id"])       # format="mp3" → sendAudio
```

Formats here: `1080`, `720`, `480`, `360`, `240`, `144` or `mp3`. The response also has `title`, `author`, `duration`, `size`, `width`, `height` and `thumbnail_url`. Your bot may receive service messages while the file is delivered — do not reply to them.

### Download TikTok, Instagram, Facebook or X videos

```python
for link in [
    "https://www.tiktok.com/@user/video/7300000000000000000",
    "https://www.facebook.com/watch/?v=1234567890",
    "https://x.com/user/status/1234567890",
]:
    media = api.download(link)
    print(media["hosting"], media["download_url"])
```

### Instagram profile data

```python
profile = api.instagram_profile("cristiano")
print(profile["user"]["full_name"], profile["user"]["is_verified"])
```

### Recognise a song, search music, read charts

```python
song = api.shazam_recognize("https://example.com/clip.mp3")
print(song["track"]["title"], "—", song["track"]["subtitle"])

results = api.music_search("Hello Adele", limit=5)
top = api.shazam_top("united-states")
```

### Check your plan and credits (free)

```python
print(api.info_balance())
```

## Response reference

Every method returns the API's JSON decoded into a plain `dict`. The samples below are real responses (long URLs and lists shortened with `…`). Fields can be `null` when the source has no value, so prefer `.get()` for optional ones.

| Method | Key fields in the response |
|---|---|
| [`download()`](#download--all-in-one-downloader) | `hosting`, `type`, `download_url`, `thumb`, `caption` |
| [`youtube()`](#youtube--video-or-mp3) | `url`, `filename`, `title`, `author`, `width`, `height`, `thumbnail` |
| [`youtube_telegram()`](#youtube_telegram--telegram-file_id) | `status`, `file_id`, `media_type`, `title`, `duration`, `size` |
| [`youtube_info()`](#youtube_info--full-metadata) | `title`, `author`, `duration`, `thumbnails`, `formats[]` |
| [`youtube_info_basic()`](#youtube_info_basic--light-metadata) | `title`, `author_name`, `author_url`, `thumbnail_url` |
| [`instagram_profile()`](#instagram_profile) | `user{}`, `counts{}`, `stories[]`, `highlights[]`, `posts[]` |
| [`shazam_recognize()`](#shazam_recognize) | `track.title`, `track.subtitle`, `track.images`, `track.url` |
| [`shazam_top()`](#shazam_top) | `country`, `chart`, `total_songs`, `songs[]` |
| [`music_search()`](#music_search) | `query`, `total_results`, `results[]` |
| [`info_balance()`](#info_balance--free) | `plan`, `credits_remaining`, `limits{}`, `subscription{}` |
| [`api_keys_statistics()`](#api_keys_statistics--free) | `data[].statistics` — per period, per platform |

### `download()` — All-in-One downloader

```python
media = api.download("https://www.instagram.com/reel/DPOi9V-CAqH/")
```

```json
{
  "error": false,
  "hosting": "instagram",
  "shortcode": null,
  "caption": "",
  "type": "video",
  "download_url": "https://scontent-iad3-1.cdninstagram.com/o1/v/t2/f2/m86/AQOua1uN….mp4?…",
  "thumb": "https://scontent-iad6-1.cdninstagram.com/v/t51.82787-15/557983269_….jpg?…"
}
```

| Field | Type | Meaning |
|---|---|---|
| `hosting` | string | Detected platform: `instagram`, `tiktok`, `facebook`, `twitter`… |
| `type` | string | `video` or `image` |
| `download_url` | string | Direct link to the media file (expires — save it right away) |
| `thumb` | string | Preview image |
| `caption` | string | Post text, when the platform provides it |

### `youtube()` — video or MP3

```python
video = api.youtube("https://youtu.be/OORSiK8ScTI", format="720")
```

```json
{
  "status": "tunnel",
  "url": "https://…/tunnel/dd9999da-6d26-46ce-85d1-128f02138f84.mp4",
  "filename": "Музыка для души  Miyagi & Эндшпиль (Hajime Records) - TheNext (720p, h264).mp4",
  "duration": null,
  "width": 1280,
  "height": 720,
  "thumbnail": "https://i.ytimg.com/vi/OORSiK8ScTI/hqdefault.jpg",
  "title": "Музыка для души | Miyagi & Эндшпиль (#music #miyagi) (Hajime Records)",
  "author": "TheNext"
}
```

| Field | Type | Meaning |
|---|---|---|
| `url` | string | Direct link to the video (or audio for `format="mp3"`) — pass it to `api.save_file()` |
| `filename` | string | Suggested file name, with quality and codec |
| `width`, `height` | int | Actual resolution of the returned file |
| `title`, `author`, `thumbnail` | string | Video title, channel name, preview image |

### `youtube_telegram()` — Telegram `file_id`

```python
res = api.youtube_telegram("https://youtu.be/OORSiK8ScTI", format="720", bot_username="@MyBot")
```

```json
{
  "status": "success",
  "youtube_id": "OORSiK8ScTI",
  "youtube_url": "https://youtu.be/OORSiK8ScTI",
  "title": "Музыка для души | Miyagi & Эндшпиль",
  "author": "TheNext",
  "thumbnail_url": "https://i.ytimg.com/vi/OORSiK8ScTI/hqdefault.jpg",
  "format": "720",
  "media_type": "video",
  "size": 25948010,
  "duration": 228,
  "width": 1280,
  "height": 720,
  "bot_username": "@mybot",
  "file_id": "BAACAgIAAxkBAAI…"
}
```

| Field | Type | Meaning |
|---|---|---|
| `status` | string | `success`, or `processing` while a new video is being prepared — then call again after `retry_after` seconds |
| `file_id` | string | Telegram file id valid for `bot_username` — reusable, store it |
| `media_type` | string | `video` → `sendVideo`, `audio` → `sendAudio` |
| `size` | int | File size in bytes |
| `duration` | int | Length in seconds |

### `youtube_info()` — full metadata

```python
info = api.youtube_info("https://youtu.be/bICMVAhktBE")
```

```json
{
  "ok": true,
  "video_id": "bICMVAhktBE",
  "title": "Shohjahon Jo'rayev - Farishtaginam (7-studiya ko'rsatuvida)",
  "author": "JO'RAYEVLAR",
  "author_url": "https://www.youtube.com/channel/UCEmb9urJ-ad8p-mdtYfOJIA",
  "thumbnail": "https://i.ytimg.com/vi/bICMVAhktBE/maxresdefault.jpg",
  "duration": 299,
  "thumbnails": {
    "low": "https://i.ytimg.com/vi/bICMVAhktBE/mqdefault.jpg",
    "max": "https://i.ytimg.com/vi/bICMVAhktBE/maxresdefault.jpg"
  },
  "formats": [
    { "type": "video", "format": "144p", "filesize": 7390784 },
    { "type": "video", "format": "240p", "filesize": 8901511 }
  ]
}
```

`formats` lists every quality the video has, with its size in bytes — check it before asking `youtube()` for `1440` or `2160`.

### `youtube_info_basic()` — light metadata

```python
info = api.youtube_info_basic("https://youtu.be/bICMVAhktBE")
```

```json
{
  "title": "Shohjahon Jo'rayev - Farishtaginam (7-studiya ko'rsatuvida)",
  "author_name": "JO'RAYEVLAR",
  "author_url": "https://www.youtube.com/@jorayevlar2790",
  "type": "video",
  "provider_name": "YouTube",
  "thumbnail_url": "https://i.ytimg.com/vi/bICMVAhktBE/hqdefault.jpg",
  "thumbnail_width": 480,
  "thumbnail_height": 360,
  "html": "<iframe width=\"200\" height=\"113\" src=\"https://www.youtube.com/embed/bICMVAhktBE?feature=oembed\" …></iframe>"
}
```

### `instagram_profile()`

```python
profile = api.instagram_profile("cristiano")
```

```json
{
  "error": false,
  "user": {
    "id": 173560420,
    "username": "cristiano",
    "full_name": "Cristiano Ronaldo",
    "biography": "",
    "external_url": "https://hrbl.me/CR7Pro2col",
    "is_private": false,
    "is_verified": true,
    "profile_pic_url": "https://…/profile.jpg",
    "stats": { "posts": 4121, "followers": 679697682, "following": 634 }
  },
  "counts": { "stories": 0, "highlights": 0, "posts": 12 },
  "stories": [],
  "highlights": [],
  "posts": [
    { "id": "3968787288363683029_173560420", "type": "carousel", "url": "https://…/post.jpg", "taken_at": "2 days" }
  ]
}
```

### `shazam_recognize()`

```python
song = api.shazam_recognize("https://example.com/clip.mp3")
```

```json
{
  "matches": [{ "id": "804915529", "offset": 2.67, "timeskew": 0.0165, "frequencyskew": 0.0028 }],
  "track": {
    "key": "804915529",
    "type": "MUSIC",
    "title": "Nowy dzień",
    "subtitle": "YOTAGAMI",
    "images": {
      "coverart": "https://is1-ssl.mzstatic.com/image/thumb/Music221/…/400x400cc.jpg",
      "coverarthq": "https://is1-ssl.mzstatic.com/image/thumb/Music221/…/400x400cc.jpg"
    },
    "share": { "subject": "Nowy dzień - YOTAGAMI", "href": "https://www.shazam.com/track/804915529/…" },
    "hub": { "type": "APPLEMUSIC", "providers": [{ "type": "SPOTIFY", "caption": "Open in Spotify" }] },
    "genres": { "primary": "Dance" },
    "url": "https://www.shazam.com/track/804915529/…"
  }
}
```

`track.title` is the song and `track.subtitle` the artist. When nothing is recognised, `matches` is empty and there is no `track` — use `song.get("track")`.

### `shazam_top()`

```python
top = api.shazam_top("united-states")
```

```json
{
  "status": "success",
  "country": "United States",
  "country_code": "US",
  "chart": "Top 200 United States",
  "total_songs": 400,
  "songs": [
    { "position": 1, "title": "Loser", "artist": "Tame Impala" }
  ]
}
```

### `music_search()`

```python
found = api.music_search("Hello Adele", limit=5)
```

```json
{
  "query": "Hello Adele",
  "total_results": 5,
  "results": [
    {
      "id": "YQHsXMglC9A",
      "title": "Adele - Hello (Official Music Video)",
      "artist": "Adele",
      "duration": "6:07",
      "thumbnail": "https://i.ytimg.com/vi/YQHsXMglC9A/mqdefault.jpg",
      "year": ""
    }
  ]
}
```

`id` is a YouTube video id — `api.youtube(f"https://youtu.be/{item['id']}", format="mp3")` turns a search hit into an audio file.

### `info_balance()` — free

```python
me = api.info_balance()
```

```json
{
  "success": true,
  "owner": "you@example.com",
  "plan": { "name": "Pro" },
  "credits_total": 100000,
  "credits_remaining": 87350,
  "credits_used": 12650,
  "credits_used_percent": 12.7,
  "limits": { "requests_per_second": 10, "requests_per_hour": 0, "requests_per_day": 0 },
  "subscription": {
    "purchased_at": "2026-11-01T09:00:00.000Z",
    "expires_at": "2026-12-01T09:00:00.000Z",
    "days_remaining": 7
  }
}
```

A limit of `0` means unlimited. The answer is cached for up to 10 minutes.

### `api_keys_statistics()` — free

```python
stats = api.api_keys_statistics()
```

```json
{
  "success": true,
  "data": [
    {
      "apiKeyId": "cm…",
      "apiKeyName": "Production",
      "apiKey": "abcd1234efgh5678ijkl...",
      "createdAt": "2026-09-01T10:00:00.000Z",
      "statistics": {
        "timePeriod": { "hourly": 42, "daily": 910, "weekly": 6120, "monthly": 25400, "total": 181300 },
        "requests": { "success": 178900, "failed": 2400, "successRate": 98.7 },
        "platforms": {
          "YouTube": { "total": 90500, "success": 89600, "failed": 900, "hourly": 20, "daily": 450, "weekly": 3000, "monthly": 12600, "successRate": 99.0 },
          "Instagram": { "total": 60100, "success": 59200, "failed": 900, "hourly": 15, "daily": 300, "weekly": 2100, "monthly": 8400, "successRate": 98.5 }
        }
      }
    }
  ],
  "cached": false,
  "computedAt": "2026-11-24T05:00:00.000Z"
}
```

Statistics are cached for up to an hour. The two account samples above use illustrative numbers.

### `nsfw_scan()`

```python
verdict = api.nsfw_scan("https://example.com/image.jpg")
```

Returns the scanner's verdict for the image or video as JSON; the live sample is in the [API docs](https://saverapi.net/docs).

### Errors

A failed call raises an exception (see [Errors and retries](#errors-and-retries)); the API's JSON body is kept on it:

```python
try:
    api.download("https://www.instagram.com/p/private/")
except SaverAPIError as exc:
    print(exc.status_code)   # e.g. 400
    print(exc.message)       # "…"
    print(exc.payload)       # {"message": "…"}
```

## Async (aiogram, FastAPI, asyncio)

```python
import asyncio
from saverapi import AsyncSaverAPI

async def main():
    async with AsyncSaverAPI() as api:   # reads SAVERAPI_KEY
        results = await asyncio.gather(
            api.download("https://www.instagram.com/reel/DPOi9V-CAqH/"),
            api.youtube_info("https://youtu.be/OORSiK8ScTI"),
        )
        print(results)

asyncio.run(main())
```

### Telegram downloader bot (aiogram 3)

```python
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from saverapi import AsyncSaverAPI, SaverAPIError

bot = Bot("TELEGRAM_BOT_TOKEN")
dp = Dispatcher()
api = AsyncSaverAPI()   # SAVERAPI_KEY from the environment

@dp.message(F.text.startswith("http"))
async def on_link(message: Message):
    try:
        media = await api.download(message.text.strip())
    except SaverAPIError as exc:
        await message.answer(f"Could not download: {exc.message}")
        return
    if media.get("type") == "image":
        await message.answer_photo(media["download_url"])
    else:
        await message.answer_video(media["download_url"])

dp.run_polling(bot)
```

Step-by-step guide: **[Build a Telegram video downloader bot](https://saverapi.net/blog/build-telegram-video-downloader-bot)**.

## Command line

```bash
export SAVERAPI_KEY=your_key
saverapi download https://www.instagram.com/reel/DPOi9V-CAqH/
saverapi youtube https://youtu.be/OORSiK8ScTI --format mp3
saverapi youtube-telegram https://youtu.be/OORSiK8ScTI --bot @MyBot
saverapi youtube-info https://youtu.be/OORSiK8ScTI
saverapi instagram cristiano
saverapi shazam https://example.com/clip.mp3
saverapi balance
```

Prints the JSON response; exits with status 1 on an API error.

## Errors and retries

Rate limits (`429`) and temporary server errors (`5xx`) are retried automatically with exponential backoff (`max_retries=2` by default). Failed 5xx calls are not charged. Everything else raises a specific exception:

```python
from saverapi import (
    SaverAPIError, AuthenticationError, InsufficientCreditsError,
    RateLimitError, NotFoundError, ServerError, NetworkError,
)

try:
    api.download(link)
except AuthenticationError:        # 401/403 — wrong or disabled key
    ...
except InsufficientCreditsError:   # 402 — top up or upgrade at saverapi.net/pricing
    ...
except RateLimitError as exc:      # 429 after retries
    ...
except SaverAPIError as exc:       # anything else; exc.status_code, exc.message, exc.payload
    ...
```

Options: `SaverAPI(api_key=None, timeout=60, base_url=None, session=None, max_retries=2, backoff=1.0)`. Use it as a context manager (`with SaverAPI() as api:`) to close the HTTP session.

## Tips

- Media links (`download_url`) come from the networks' CDNs and **expire** — download them right after the call.
- Only public content can be resolved; private accounts and deleted posts fail.
- Keep the API key on your server; mobile and web apps should call your backend.
- Respect each platform's terms of service and creators' rights.

## FAQ

**How do I download a YouTube video in Python?**
Install `saverapi-client`, then call `api.youtube(url, format="720")` and save `video["url"]` with `api.save_file(...)`. No yt-dlp or ffmpeg is needed — the API does the work. See the [YouTube Downloader API](https://saverapi.net/youtube-downloader-api) page.

**Can I download YouTube in 4K or 1440p?**
Yes: `format="2160"` (4K) and `format="1440"` (2K) are supported alongside 1080, 720, 480, 360, 240 and 144, when the video has that quality.

**How do I convert YouTube to MP3?**
`api.youtube(url, format="mp3")` returns a link to the audio file.

**How do I download Instagram Reels or TikTok videos in Python?**
`api.download(link)` works for Instagram posts and Reels, TikTok, Facebook, X and the other supported networks — the platform is detected from the link. See the [Instagram](https://saverapi.net/instagram-downloader-api) and [TikTok](https://saverapi.net/tiktok-downloader-api) API pages.

**How do I send a YouTube video from a Telegram bot without uploading it?**
Call `api.youtube_telegram(url, format, bot_username="@YourBot")` and pass the returned `file_id` to `sendVideo` / `sendAudio`. Works with aiogram, python-telegram-bot, pyTelegramBotAPI and any other library.

**Is there a free plan?**
Yes — register at [saverapi.net](https://saverapi.net/auth/register) for a free key; paid plans and pay-as-you-go credits are on the [pricing](https://saverapi.net/pricing) page.

**Does it work with asyncio?**
Yes: `pip install "saverapi-client[async]"` and use `AsyncSaverAPI` — same methods, awaited.

## Links

- Website and free API key: https://saverapi.net
- API documentation: https://saverapi.net/docs
- YouTube Downloader API: https://saverapi.net/youtube-downloader-api
- Instagram Downloader API: https://saverapi.net/instagram-downloader-api
- TikTok Downloader API: https://saverapi.net/tiktok-downloader-api
- Facebook Video API: https://saverapi.net/facebook-video-api
- Twitter / X Video API: https://saverapi.net/twitter-video-api
- Shazam Song Recognition API: https://saverapi.net/shazam-api
- Social Media Downloader API: https://saverapi.net/social-media-downloader-api
- All-in-One Downloader API: https://saverapi.net/all-in-one-downloader-api
- Tutorials: https://saverapi.net/blog
  - [YouTube downloader API in Python](https://saverapi.net/blog/youtube-downloader-api-python)
  - [Build a Telegram YouTube downloader bot](https://saverapi.net/blog/build-telegram-youtube-downloader-bot)
  - [Download Instagram Reels with Python](https://saverapi.net/blog/download-instagram-reels-python)
  - [A yt-dlp API alternative](https://saverapi.net/blog/yt-dlp-api-alternative)
- Pricing: https://saverapi.net/pricing
- Telegram: https://t.me/SaverAPI

## Changelog

**2.0.1**
- Documentation: new **Response reference** — a real JSON sample and key-field table for every method. No code changes.

**2.0.0**
- YouTube: `api.youtube()` now documents the new `2160` (4K) and `1440` (2K) formats; the full list is exported as `YOUTUBE_FORMATS`.
- YouTube for Telegram: `api.youtube_telegram(url, format, bot_username="@MyBot")` returns a ready `file_id` for your bot. New CLI command `saverapi youtube-telegram URL --bot @MyBot`.
- **Removed** `youtube_subtitles()` and `photolab()` (and the `saverapi subtitles` command): the `/youtube-subtitles` and `/photolab-api` endpoints were retired from the API and already answered 404. This is the only breaking change — if you do not call these two methods, upgrading from 1.x needs no code changes.
- `format` accepts an `int` as well as a `str` in type hints (`format=720`).

**1.1.0**
- New methods covering the whole catalog: `youtube_telegram`, `youtube_info_basic`, `youtube_subtitles`, `instagram_profile`, `photolab`, and `request()` for any endpoint.
- `AsyncSaverAPI` for asyncio (`pip install "saverapi-client[async]"`).
- `saverapi` command line tool.
- Automatic retries with backoff for 429 and 5xx; specific exception classes.
- API key from the `SAVERAPI_KEY` environment variable; context-manager support; type hints (`py.typed`).
- Fully backwards compatible with 1.0.x.

## License

MIT © SaverAPI.NET
