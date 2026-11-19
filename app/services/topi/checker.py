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


def homework_tasks_of(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Danh sách bài về nhà; nhận cả dạng cũ `homework_set` (một câu) cho kết quả đã lưu."""
    tasks = evidence.get("homework_tasks")
    if isinstance(tasks, list):
        return [t for t in tasks if isinstance(t, dict)]
    hw = evidence.get("homework_set") or {}
    if isinstance(hw, dict) and hw.get("quote"):
        return [{"seg": hw.get("seg"), "quote": hw["quote"], "task": hw["quote"], "due": None}]
    return []


def check_homework(evidence: dict[str, Any], segments: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Mỗi bài phải có câu giao bài nguyên văn của gia sư; hạn nộp phải nghe được ở đoạn đã nêu.

    Hạn không chứng minh được thì bỏ hạn (giữ bài), để báo cáo không bịa hạn.
    """
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, str]] = []
    for i, t in enumerate(homework_tasks_of(evidence)):
        ok, drop, _ = check_labels([t], segments, kind=f"homework_tasks[{i}]", expected_speaker="tutor")
        dropped += drop
        if not ok:
            continue
        task = dict(ok[0])
        task["task"] = (task.get("task") or task["quote"]).strip()
        due, due_quote, due_seg = task.get("due"), task.get("due_quote"), task.get("due_seg")
        if due:
            proof_seg = due_seg if isinstance(due_seg, int) else task["seg"]
            proof = due_quote or due
            if not (0 <= proof_seg < len(segments) and quote_in_segment(proof, segments[proof_seg].get("text", ""))):
                dropped.append({"label": f"homework_tasks[{i}].due", "reason": "quote_not_in_segment"})
                due, due_quote, due_seg = None, None, None
        task["due"], task["due_quote"], task["due_seg"] = due, due_quote, due_seg
        kept.append(task)
    return kept, dropped


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
    tasks, drop = check_homework(evidence, segments)
    out["homework_tasks"] = tasks
    dropped += drop
    # Trường cũ cho backend đang đọc homework_set (một câu): câu của bài đầu tiên.
    out["homework_set"] = ({"seg": tasks[0]["seg"], "quote": tasks[0]["quote"]} if tasks
                           else {"seg": None, "quote": ""})
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
