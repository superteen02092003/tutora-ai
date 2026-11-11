"""Topi generate_json: model gpt-* đi OpenAI, gemini-* đi Gemini; JSON hỏng thử lại 1 lần."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.services.topi import llm


class _FakeResp:
    def __init__(self, status: int, payload: dict):
        self.status_code = status
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def _openai_payload(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 30, "total_tokens": 130,
                      "completion_tokens_details": {"reasoning_tokens": 20}}}


def _patch(monkeypatch, responses: list, sent: list, key: str = "sk-test"):
    monkeypatch.setattr(llm, "get_settings",
                        lambda: SimpleNamespace(openai_api_key=key, topi_thinking_level="high"))

    class _Client:
        def __init__(self, **_):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def post(self, url, json=None, headers=None):
            sent.append({"url": url, "json": json, "headers": headers})
            return responses.pop(0)

    monkeypatch.setattr(llm.httpx, "AsyncClient", _Client)
    recorded = []
    monkeypatch.setattr("app.services.telemetry.usage._Tracker.emit", lambda self: recorded.append(self._record))
    return recorded


def _run(**kw):
    return asyncio.run(llm.generate_json(None, feature="topi_test", system="Hệ thống", prompt="dữ liệu", **kw))


def test_gpt_model_goes_to_openai_without_temperature(monkeypatch):
    sent: list = []
    recorded = _patch(monkeypatch, [_FakeResp(200, _openai_payload('{"ok": 1}'))], sent)
    assert _run(model="gpt-6-luna", temperature=0.4) == {"ok": 1}
    body = sent[0]["json"]
    assert sent[0]["url"].endswith("/v1/chat/completions")
    assert body["model"] == "gpt-6-luna"
    assert "temperature" not in body and "reasoning_effort" not in body
    assert body["response_format"] == {"type": "json_object"}
    assert "JSON" in body["messages"][0]["content"]
    assert sent[0]["headers"]["Authorization"] == "Bearer sk-test"
    # Telemetry tách token suy nghĩ khỏi output.
    rec = recorded[0]
    assert (rec.prompt_tokens, rec.output_tokens, rec.thoughts_tokens) == (100, 10, 20)


def test_bad_json_is_retried_once(monkeypatch):
    sent: list = []
    _patch(monkeypatch, [_FakeResp(200, _openai_payload("không phải json")),
                         _FakeResp(200, _openai_payload('{"ok": 2}'))], sent)
    assert _run(model="gpt-6-luna") == {"ok": 2}
    assert len(sent) == 2


def test_http_error_raises(monkeypatch):
    _patch(monkeypatch, [_FakeResp(429, {"error": {"message": "rate limit"}})], [])
    with pytest.raises(RuntimeError, match="OpenAI HTTP 429"):
        _run(model="gpt-6-luna")


def test_missing_key_raises(monkeypatch):
    _patch(monkeypatch, [], [], key="")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        _run(model="gpt-6-luna")


def test_gemini_model_uses_client_with_thinking_level(monkeypatch):
    monkeypatch.setattr(llm, "get_settings",
                        lambda: SimpleNamespace(openai_api_key="", topi_thinking_level="high"))
    monkeypatch.setattr("app.services.telemetry.usage._Tracker.emit", lambda self: None)
    seen = {}

    async def generate_content(*, model, contents, config):
        seen.update(model=model, config=config)
        return SimpleNamespace(text='{"ok": 3}', usage_metadata=None)

    client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)))
    out = asyncio.run(llm.generate_json(client, model="gemini-3.5-flash-lite", feature="topi_test",
                                        system="s", prompt="p", temperature=0.3))
    assert out == {"ok": 3}
    assert seen["model"] == "gemini-3.5-flash-lite"
    assert seen["config"].temperature == 0.3
    assert seen["config"].thinking_config.thinking_level.value.lower() == "high"
