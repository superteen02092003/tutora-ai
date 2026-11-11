"""Gọi model trả JSON, có đo token (telemetry) và thử lại 1 lần khi JSON hỏng.

Model tên `gpt-*` đi OpenAI (Chat Completions), còn lại đi Gemini. Chọn gpt-6-luna
làm mặc định ngày 2026-11-11 sau so sánh 3 lần chạy trên 8 buổi (topi-phone-test/
model-comparison-2026-11-11.md): rẻ hơn ~6 lần, trích dẫn sát transcript hơn, kế
hoạch ổn định hơn Gemini 3.5 Flash-Lite thinking high.
"""
import json
import logging
import re
import time
from types import SimpleNamespace
from typing import Any

import httpx
from google.genai import types

from ...core.config import get_settings
from ..telemetry.usage import track

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_OPENAI_TIMEOUT = httpx.Timeout(600.0, connect=10.0)


def _parse(text: str) -> Any:
    return json.loads(_FENCE.sub("", (text or "").strip()))


def is_openai(model: str) -> bool:
    return model.startswith("gpt-")


async def _openai_call(*, model: str, system: str, prompt: str, max_output_tokens: int) -> tuple[str, Any]:
    """Một lời gọi Chat Completions. Trả (text, response giả dạng Gemini cho telemetry).

    Không gửi temperature: gpt-6-luna chỉ nhận mặc định. Không đặt reasoning_effort:
    mức mặc định (medium) tốt bằng high trong so sánh, rẻ và nhanh hơn ~2 lần.
    """
    key = get_settings().openai_api_key
    if not key:
        raise RuntimeError("OPENAI_API_KEY chưa đặt — Topi cần key khi model là gpt-*")
    body = {
        "model": model,
        # response_format json_object bắt buộc có chữ "JSON" trong messages.
        "messages": [{"role": "system", "content": system + "\nTrả về đúng một JSON object."},
                     {"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "max_completion_tokens": max_output_tokens,
    }
    async with httpx.AsyncClient(timeout=_OPENAI_TIMEOUT) as http:
        r = await http.post(_OPENAI_URL, json=body, headers={"Authorization": f"Bearer {key}"})
    if r.status_code >= 400:
        raise RuntimeError(f"OpenAI HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    usage = data.get("usage") or {}
    reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    meta = SimpleNamespace(
        prompt_token_count=usage.get("prompt_tokens", 0),
        candidates_token_count=(usage.get("completion_tokens", 0) or 0) - reasoning,
        thoughts_token_count=reasoning,
        cached_content_token_count=cached,
        total_token_count=usage.get("total_tokens", 0),
    )
    text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    return text, SimpleNamespace(usage_metadata=meta)


async def generate_json(client, *, model: str, feature: str, system: str, prompt: str,
                        temperature: float = 0.2, max_output_tokens: int = 32768) -> Any:
    last: Exception | None = None
    for attempt in range(2):
        t0 = time.monotonic()
        with track(feature, model) as t:
            if is_openai(model):
                text, resp = await _openai_call(model=model, system=system, prompt=prompt,
                                                max_output_tokens=max_output_tokens)
                t.done(resp)
            else:
                level = get_settings().topi_thinking_level
                cfg = types.GenerateContentConfig(
                    temperature=temperature,
                    system_instruction=system,
                    response_mime_type="application/json",
                    max_output_tokens=max_output_tokens,
                    # 3.5 Flash-Lite mặc định không suy nghĩ và bỏ sót bằng chứng; "high" cần cho Topi.
                    thinking_config=types.ThinkingConfig(thinking_level=level) if level else None,
                )
                text = t.done(await client.aio.models.generate_content(model=model, contents=prompt,
                                                                       config=cfg)).text or ""
        try:
            return _parse(text)
        except json.JSONDecodeError as e:
            last = e
            logger.warning("topi %s: JSON hỏng (lần %d, %.0fs)", feature, attempt + 1, time.monotonic() - t0)
    raise last  # type: ignore[misc]
