"""B2 — kiểm bằng chứng bằng CODE, không bằng LLM.

Mỗi nhãn phải có `seg` hợp lệ, `quote` nằm nguyên văn trong đoạn đó (sau khi chuẩn hoá),
và người nói khớp (sự kiện học sinh -> đoạn của student, sự kiện gia sư -> tutor).
Nhãn không qua bị loại và ghi vào `check.dropped` để còn đo.
"""
import re
import unicodedata
from typing import Any, Optional

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Chữ thường, NFC, bỏ dấu câu, gộp khoảng trắng. Giữ dấu tiếng Việt."""
    t = unicodedata.normalize("NFC", text or "").lower()
    t = _PUNCT.sub(" ", t)
    return _SPACES.sub(" ", t).strip()


def quote_in_segment(quote: str, segment_text: str) -> bool:
    q = normalise(quote)
    return bool(q) and q in normalise(segment_text)


def _speaker_ok(expected: Optional[str], actual: str) -> tuple[bool, bool]:
    """(qua, là_unknown). `unknown` cho qua nhưng được đánh dấu."""
    if expected is None:
        return True, False
    if actual == "unknown":
        return True, True
    return actual == expected, False


def check_labels(
    labels: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    *,
    kind: str,
    expected_speaker: Optional[str],
    window: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], int]:
    """Trả (nhãn giữ lại, nhãn bị loại, số nhãn qua nhờ speaker=unknown).

    `window`: cho phép quote nằm ở đoạn liền kề (máy tách câu không đều), nhưng `seg`
    được sửa về đúng đoạn chứa quote.
    """
    kept, dropped, unknown = [], [], 0
    n = len(segments)
    for i, lab in enumerate(labels):
        name = f"{kind}[{i}]"
        seg = lab.get("seg")
        quote = lab.get("quote") or ""
        if not isinstance(seg, int) or not (0 <= seg < n):
            dropped.append({"label": name, "reason": "bad_seg"})
            continue
        found = None
        for s in [seg] + [seg + d for d in range(-window, window + 1) if d]:
            if 0 <= s < n and quote_in_segment(quote, segments[s].get("text", "")):
                found = s
                break
        if found is None:
            dropped.append({"label": name, "reason": "quote_not_in_segment"})
            continue
        ok, was_unknown = _speaker_ok(expected_speaker, segments[found].get("speaker", "unknown"))
        if not ok:
            dropped.append({"label": name, "reason": "wrong_speaker"})
            continue
        unknown += was_unknown
        fixed = dict(lab)
        fixed["seg"] = found
        fixed["ts"] = segments[found].get("start", lab.get("ts"))
        kept.append(fixed)
    return kept, dropped, unknown


def check_evidence(evidence: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Áp kiểm tra lên toàn bộ evidence; trả evidence đã lọc kèm khối `check`."""
    out = dict(evidence)
    dropped: list[dict[str, str]] = []
    kept_total, unknown_total = 0, 0
    for key, speaker in (("tutor_events", "tutor"), ("pupil_events", "student"), ("flags", None)):
        kept, drop, unk = check_labels(evidence.get(key) or [], segments, kind=key, expected_speaker=speaker)
        out[key] = kept
        dropped += drop
        kept_total += len(kept)
        unknown_total += unk
    hw = evidence.get("homework_set") or {}
    if hw.get("quote"):
        kept, drop, _ = check_labels([hw], segments, kind="homework_set", expected_speaker="tutor")
        out["homework_set"] = kept[0] if kept else {"seg": None, "quote": ""}
        dropped += drop
    # Bài tập: chỉ cần khoảng đoạn hợp lệ.
    exercises = []
    for i, ex in enumerate(evidence.get("exercises") or []):
        a, b = ex.get("start_seg"), ex.get("end_seg")
        if isinstance(a, int) and isinstance(b, int) and 0 <= a <= b < len(segments):
            ex = dict(ex)
            q = ex.get("quote") or ""
            if q and not any(quote_in_segment(q, segments[s].get("text", "")) for s in range(a, b + 1)):
                # Không chứng minh được đề bài -> không tin nút kỹ năng gắn với bài này.
                dropped.append({"label": f"exercises[{i}].skill_node", "reason": "quote_not_in_segment"})
                ex["quote"], ex["skill_node"] = "", ""
            exercises.append(ex)
        else:
            dropped.append({"label": f"exercises[{i}]", "reason": "bad_seg"})
    out["exercises"] = exercises
    out["check"] = {"kept": kept_total, "dropped": dropped, "speaker_unknown": unknown_total}
    return out
