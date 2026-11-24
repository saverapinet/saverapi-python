import asyncio
import json

import httpx
import pytest
import requests

import saverapi
from saverapi import (
    AsyncSaverAPI, AuthenticationError, InsufficientCreditsError, RateLimitError, SaverAPI, SaverAPIError, ServerError,
)
from saverapi.cli import main


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}
        self.reason = "reason"
        self.text = json.dumps(body)

    def json(self):
        return self._body


class FakeSession(requests.Session):
    def __init__(self, responses):
        super().__init__()
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.responses.pop(0)


def client(*responses, **kw):
    session = FakeSession(responses)
    return SaverAPI(api_key="k", session=session, backoff=0, **kw), session


def test_methods_call_the_right_endpoints_and_params():
    api, s = client(*[FakeResponse(200, {"ok": True})] * 15)
    api.download("https://x.com/a/status/1")
    api.youtube("https://youtu.be/a", format="mp3")
    api.youtube_telegram("https://youtu.be/a", 360)
    api.youtube_telegram("https://youtu.be/a", "mp3", bot_username="@MyBot")
    api.youtube("https://youtu.be/a", 2160)
    api.youtube_info("https://youtu.be/a")
    api.youtube_info_basic("https://youtu.be/a")
    api.instagram_profile("@cristiano")
    api.music_search("hello", 5)
    api.shazam_recognize("https://e.com/a.mp3")
    api.shazam_top("uz")
    api.nsfw_scan("https://e.com/v.mp4")
    api.info_balance()
    api.api_keys_statistics()
    api.request("/new-endpoint", {"q": "x", "none": None})
    paths = [c[0].replace("https://saverapi.net/api", "") for c in s.calls]
    assert paths == [
        "/all-in-one-downloader-api", "/youtube-api", "/youtube-telegram-base", "/youtube-telegram-base", "/youtube-api",
        "/youtube-info-v2", "/youtube-info", "/instagram-profile", "/music-search", "/shazam-recognize",
        "/shazam-music-top", "/nsfw-scanner-api", "/infobalans", "/api-keys/all-statistics", "/new-endpoint",
    ]
    assert s.calls[1][1] == {"url": "https://youtu.be/a", "farmat": "mp3"}
    # Without a bot the parameter is not sent at all.
    assert s.calls[2][1] == {"url": "https://youtu.be/a", "farmat": "360"}
    assert s.calls[3][1] == {"url": "https://youtu.be/a", "farmat": "mp3", "bot_username": "@MyBot"}
    assert s.calls[4][1] == {"url": "https://youtu.be/a", "farmat": "2160"}
    assert s.calls[7][1] == {"Userinfo": "cristiano"}
    assert s.calls[14][1] == {"q": "x"}
    assert s.headers["x-api-key"] == "k"


def test_retries_rate_limits_and_server_errors_then_succeeds():
    api, s = client(FakeResponse(429, {"message": "slow"}), FakeResponse(502, {}), FakeResponse(200, {"done": 1}))
    assert api.download("u") == {"done": 1}
    assert len(s.calls) == 3


def test_raises_specific_errors():
    api, _ = client(FakeResponse(401, {"message": "bad key"}))
    with pytest.raises(AuthenticationError) as e:
        api.download("u")
    assert e.value.status_code == 401 and e.value.message == "bad key"

    api, _ = client(FakeResponse(402, {"error": "no credits"}))
    with pytest.raises(InsufficientCreditsError):
        api.download("u")

    api, _ = client(*[FakeResponse(429, {})] * 3)
    with pytest.raises(RateLimitError):
        api.download("u")

    api, _ = client(*[FakeResponse(500, {})] * 3, max_retries=2)
    with pytest.raises(ServerError):
        api.download("u")

    api, _ = client(FakeResponse(400, {"message": "bad url"}))
    with pytest.raises(SaverAPIError) as e:
        api.download("u")
    assert type(e.value) is SaverAPIError


def test_key_from_environment(monkeypatch):
    monkeypatch.setenv("SAVERAPI_KEY", "envkey")
    assert SaverAPI().api_key == "envkey"
    monkeypatch.delenv("SAVERAPI_KEY")
    with pytest.raises(ValueError):
        SaverAPI()


def test_backwards_compatible_request_alias():
    api, s = client(FakeResponse(200, {}))
    api._request("/infobalans")
    assert s.calls[0][0].endswith("/infobalans")


def test_async_client():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"hosting": "tiktok"})

    async def run():
        transport = httpx.MockTransport(handler)
        async with AsyncSaverAPI(api_key="k", backoff=0, client=httpx.AsyncClient(transport=transport)) as api:
            return await api.download("https://www.tiktok.com/@u/video/1")

    assert asyncio.run(run()) == {"hosting": "tiktok"}
    assert calls[-1].headers["x-api-key"] == "k"
    assert calls[-1].url.params["url"] == "https://www.tiktok.com/@u/video/1"


def test_cli_prints_json(monkeypatch, capsys):
    monkeypatch.setenv("SAVERAPI_KEY", "k")
    monkeypatch.setattr(SaverAPI, "info_balance", lambda self: {"plan": "Pro"})
    assert main(["balance"]) == 0
    assert json.loads(capsys.readouterr().out) == {"plan": "Pro"}


def test_retired_endpoints_are_gone_and_formats_exported():
    for cls in (SaverAPI, AsyncSaverAPI):
        assert not hasattr(cls, "youtube_subtitles")
        assert not hasattr(cls, "photolab")
    assert saverapi.YOUTUBE_FORMATS[:2] == ("2160", "1440") and "mp3" in saverapi.YOUTUBE_FORMATS
    assert "2160" not in saverapi.YOUTUBE_TELEGRAM_FORMATS


def test_sync_and_async_expose_the_same_endpoints():
    def public(cls):
        skip = {"close", "aclose", "save_file", "BASE_URL"}
        return {n for n in vars(cls) if not n.startswith("_") and n not in skip}

    assert public(SaverAPI) == public(AsyncSaverAPI)


def test_async_youtube_telegram_sends_bot_username():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"status": "success", "file_id": "BAAC"})

    async def run():
        async with AsyncSaverAPI(api_key="k", client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) as api:
            await api.youtube_telegram("https://youtu.be/a", 720, bot_username="@MyBot")
            return await api.youtube_telegram("https://youtu.be/a")

    assert asyncio.run(run())["file_id"] == "BAAC"
    assert seen[0].url.path.endswith("/youtube-telegram-base")
    assert dict(seen[0].url.params) == {"url": "https://youtu.be/a", "farmat": "720", "bot_username": "@MyBot"}
    assert "bot_username" not in seen[1].url.params


def test_cli_youtube_telegram(monkeypatch, capsys):
    monkeypatch.setenv("SAVERAPI_KEY", "k")
    got = {}
    monkeypatch.setattr(SaverAPI, "youtube_telegram", lambda self, *a: got.setdefault("args", a) and {"file_id": "x"})
    assert main(["youtube-telegram", "https://youtu.be/a", "--format", "mp3", "--bot", "@MyBot"]) == 0
    assert got["args"] == ("https://youtu.be/a", "mp3", "@MyBot")
    with pytest.raises(SystemExit):
        main(["subtitles", "https://youtu.be/a"])


def test_version():
    assert saverapi.__version__ == "2.0.2"
