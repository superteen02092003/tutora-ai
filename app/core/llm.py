"""Gọi model ngôn ngữ (OpenAI, mặc định gpt-6-luna) cho mọi tính năng trừ embedding.

Quyết định 2026-11-11: Gemini chỉ còn dùng cho chép lời (ở backend) và embedding
(gemini-embedding-2, giữ nguyên không gian vector đã lưu); mọi việc sinh chữ trong
tutora-ai đi qua module này.

- complete / acomplete: một lượt, trả text; json=True hoặc schema=... thì trả object đã parse.
- stream_text: sinh từng mảnh text (dùng trong thread worker của luồng giải toán).
- files: [(bytes, mime)] — ảnh (image/*) và PDF (application/pdf) gửi kèm lượt user.
- effort: "none" thay cho thinking_budget=0 của Gemini (trả lời nhanh, không suy luận);
  None = mặc định của model. gpt-6-luna không nhận temperature nên không gửi.
- Token (kể cả token suy luận) ghi vào telemetry như mọi lời gọi khác.
"""
from __future__ import annotations

import base64
import json
import re
from types import SimpleNamespace
from typing import Any, Iterator

import httpx

from .config import get_settings
from ..services.telemetry.usage import track

_URL = "https://api.openai.com/v1/chat/completions"
_TIMEOUT = httpx.Timeout(300.0, connect=10.0)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_WRAP_KEY = "items"  # OpenAI bắt schema gốc là object; gốc mảng được bọc rồi gỡ ra


class LLMError(RuntimeError):
    pass


def model_name() -> str:
    return get_settings().llm_model


# ─────────────────────────── schema ───────────────────────────

def _lower_types(node: Any) -> Any:
    """Schema kiểu Gemini ("OBJECT", "STRING") → JSON Schema ("object", "string")."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if v is None:
                continue
            if k == "type" and isinstance(v, str):
                out[k] = v.lower()
            elif k in ("property_ordering", "propertyOrdering"):
                continue
            else:
                out[k] = _lower_types(v)
        return out
    if isinstance(node, list):
        return [_lower_types(x) for x in node]
    return node


def to_json_schema(schema: Any) -> dict:
    """Nhận dict kiểu Gemini, google.genai types.Schema hoặc class Pydantic → JSON Schema."""
    if isinstance(schema, type) and hasattr(schema, "model_json_schema"):
        return schema.model_json_schema()
    if hasattr(schema, "model_dump"):  # types.Schema
        schema = schema.model_dump(exclude_none=True)
    if not isinstance(schema, dict):
        raise TypeError(f"schema không hỗ trợ: {type(schema).__name__}")
    return _lower_types(schema)


def _response_format(json_mode: bool, schema: Any) -> tuple[dict | None, bool]:
    """Trả (response_format, wrapped)."""
    if schema is not None:
        js = to_json_schema(schema)
        wrapped = js.get("type") != "object"
        if wrapped:
            js = {"type": "object", "properties": {_WRAP_KEY: js}, "required": [_WRAP_KEY]}
        return {"type": "json_schema", "json_schema": {"name": "output", "strict": False, "schema": js}}, wrapped
    if json_mode:
        return {"type": "json_object"}, False
    return None, False


# ─────────────────────────── message ───────────────────────────

def _user_content(prompt: str, files: list[tuple[bytes, str]] | None) -> Any:
    if not files:
        return prompt
    parts: list[dict] = []
    for i, (data, mime) in enumerate(files):
        b64 = base64.b64encode(data).decode()
        if mime == "application/pdf":
            parts.append({"type": "file", "file": {"filename": f"file{i}.pdf",
                                                   "file_data": f"data:application/pdf;base64,{b64}"}})
        else:
            parts.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
    parts.append({"type": "text", "text": prompt})
    return parts


def build_messages(prompt: str | None = None, *, system: str | None = None,
                   history: list[dict] | None = None, files: list[tuple[bytes, str]] | None = None,
                   json_hint: bool = False) -> list[dict]:
    """history: [{"role": "user"|"assistant"|"model", "content": str}] — "model" đổi thành "assistant"."""
    msgs: list[dict] = []
    sys_text = system or ""
    if json_hint:  # response_format json bắt buộc có chữ "JSON" trong messages
        sys_text = (sys_text + "\n" if sys_text else "") + "Trả về đúng một JSON object."
    if sys_text:
        msgs.append({"role": "system", "content": sys_text})
    for m in history or []:
        role = "assistant" if m.get("role") in ("assistant", "model") else "user"
        msgs.append({"role": role, "content": m.get("content", "")})
    if prompt is not None:
        msgs.append({"role": "user", "content": _user_content(prompt, files)})
    return msgs


def _body(messages: list[dict], *, model: str, effort: str | None, max_tokens: int,
          response_format: dict | None, stream: bool = False) -> dict:
    body: dict = {"model": model, "messages": messages, "max_completion_tokens": max_tokens}
    if effort:
        body["reasoning_effort"] = effort
    if response_format:
        body["response_format"] = response_format
    if stream:
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
    return body


def _headers() -> dict:
    key = get_settings().openai_api_key
    if not key:
        raise LLMError("OPENAI_API_KEY chưa đặt")
    return {"Authorization": f"Bearer {key}"}


def usage_response(usage: dict | None) -> SimpleNamespace:
    """Usage của OpenAI → dạng usage_metadata mà telemetry (extract_usage) đọc được."""
    u = usage or {}
    reasoning = (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    return SimpleNamespace(usage_metadata=SimpleNamespace(
        prompt_token_count=u.get("prompt_tokens", 0),
        candidates_token_count=max((u.get("completion_tokens") or 0) - reasoning, 0),
        thoughts_token_count=reasoning,
        cached_content_token_count=(u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0,
        total_token_count=u.get("total_tokens", 0),
    ))


def _finish(data: dict, json_out: bool, wrapped: bool) -> Any:
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    if not json_out:
        return text
    obj = json.loads(_FENCE.sub("", text.strip()))
    return obj.get(_WRAP_KEY) if wrapped and isinstance(obj, dict) else obj


def _check(r: httpx.Response) -> dict:
    if r.status_code >= 400:
        raise LLMError(f"OpenAI HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


# ─────────────────────────── API ───────────────────────────

def _gemini_complete(feature: str, prompt: str, *, system: str | None, json_out: bool,
                     effort: str | None, model: str) -> Any:
    """Nhánh Gemini — chỉ cho trợ lý web (cần nhanh: ~1 s so với ~4 s của gpt-6-luna).
    Gemini 3 không nhận thinking_budget=0: effort "none" → thinking_level "minimal"."""
    from google.genai import types  # import muộn: chỉ nhánh này cần
    from .dependencies import get_gemini_client
    cfg = types.GenerateContentConfig(
        system_instruction=system or None,
        response_mime_type="application/json" if json_out else None,
        thinking_config=types.ThinkingConfig(thinking_level="minimal" if effort == "none" else (effort or "low")),
    )
    with track(feature, model) as t:
        resp = t.done(get_gemini_client().models.generate_content(model=model, contents=prompt, config=cfg))
    text = resp.text or ""
    return json.loads(_FENCE.sub("", text.strip())) if json_out else text


def complete(feature: str, prompt: str | None = None, *, system: str | None = None,
             history: list[dict] | None = None, files: list[tuple[bytes, str]] | None = None,
             json: bool = False, schema: Any = None, effort: str | None = None,
             max_tokens: int = 16000, model: str | None = None) -> Any:
    model = model or model_name()
    if model.startswith("gemini-"):
        if history or files or schema is not None:
            raise LLMError("Nhánh Gemini chỉ hỗ trợ prompt text/JSON đơn giản")
        return _gemini_complete(feature, prompt or "", system=system, json_out=json, effort=effort, model=model)
    fmt, wrapped = _response_format(json, schema)
    msgs = build_messages(prompt, system=system, history=history, files=files, json_hint=fmt is not None)
    body = _body(msgs, model=model, effort=effort, max_tokens=max_tokens, response_format=fmt)
    with track(feature, model) as t:
        with httpx.Client(timeout=_TIMEOUT) as http:
            data = _check(http.post(_URL, json=body, headers=_headers()))
        t.done(usage_response(data.get("usage")))
    return _finish(data, fmt is not None, wrapped)


async def acomplete(feature: str, prompt: str | None = None, *, system: str | None = None,
                    history: list[dict] | None = None, files: list[tuple[bytes, str]] | None = None,
                    json: bool = False, schema: Any = None, effort: str | None = None,
                    max_tokens: int = 16000, model: str | None = None) -> Any:
    model = model or model_name()
    fmt, wrapped = _response_format(json, schema)
    msgs = build_messages(prompt, system=system, history=history, files=files, json_hint=fmt is not None)
    body = _body(msgs, model=model, effort=effort, max_tokens=max_tokens, response_format=fmt)
    with track(feature, model) as t:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as http:
            data = _check(await http.post(_URL, json=body, headers=_headers()))
        t.done(usage_response(data.get("usage")))
    return _finish(data, fmt is not None, wrapped)


def stream_text(messages: list[dict], *, effort: str | None = None, max_tokens: int = 16000,
                model: str | None = None, usage_sink: list | None = None) -> Iterator[str]:
    """Sinh từng mảnh text (đồng bộ — gọi trong thread). Usage cuối stream gắn vào usage_sink."""
    model = model or model_name()
    body = _body(messages, model=model, effort=effort, max_tokens=max_tokens, response_format=None, stream=True)
    with httpx.Client(timeout=_TIMEOUT) as http:
        with http.stream("POST", _URL, json=body, headers=_headers()) as r:
            if r.status_code >= 400:
                r.read()
                raise LLMError(f"OpenAI HTTP {r.status_code}: {r.text[:300]}")
            for line in r.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                if chunk.get("usage") and usage_sink is not None:
                    usage_sink.append(chunk["usage"])
                for choice in chunk.get("choices") or []:
                    piece = (choice.get("delta") or {}).get("content")
                    if piece:
                        yield piece
