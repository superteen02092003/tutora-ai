"""Gọi Gemini trả JSON, có đo token (telemetry) và thử lại 1 lần khi JSON hỏng."""
import json
import logging
import re
from typing import Any

from google.genai import types

from ..telemetry.usage import track

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _parse(text: str) -> Any:
    return json.loads(_FENCE.sub("", (text or "").strip()))


async def generate_json(client, *, model: str, feature: str, system: str, prompt: str,
                        temperature: float = 0.2, max_output_tokens: int = 32768) -> Any:
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system,
        response_mime_type="application/json",
        max_output_tokens=max_output_tokens,
    )
    last: Exception | None = None
    for attempt in range(2):
        with track(feature, model) as t:
            resp = t.done(await client.aio.models.generate_content(model=model, contents=prompt, config=cfg))
        try:
            return _parse(resp.text or "")
        except json.JSONDecodeError as e:
            last = e
            logger.warning("topi %s: JSON hỏng (lần %d)", feature, attempt + 1)
    raise last  # type: ignore[misc]
