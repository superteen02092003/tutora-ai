"""B4 — luật mức kỹ năng, tất định (toptutor-main/60-output/specs/skills-detector.md).

Quyết định 2026-11-11: một sao cho MỖI lần lên một mức (to_do -> improving -> standard
-> mastered, tối đa 3); mức lúc thấy lần đầu không có sao.
"""
from datetime import date
from typing import Any, Optional

ORDER = ["to_do", "improving", "standard", "mastered"]
MASTERED_AFTER_DAYS = 21  # "ít nhất 3 tuần"; bằng chứng nghiêng về ~4 tuần
STANDARD_ALONE = 2        # 2 bài mới tự làm đúng, không gợi ý


def _d(s: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(s[:10]) if s else None
    except ValueError:
        return None


def first_level(obs: list[str]) -> str:
    """Mức lúc mới thấy kỹ năng (không sao). Thận trọng: chưa bao giờ lên standard ngay
    buổi đầu, vì standard cần buổi SAU."""
    if not obs:
        return "to_do"
    wrong = obs.count("wrong")
    good = obs.count("alone") + obs.count("hint")
    if wrong >= good:
        return "to_do"
    return "improving"


def next_level(
    current: str,
    lesson_obs: list[str],
    *,
    lesson_date: str,
    first_seen: Optional[str],
    standard_since: Optional[str],
) -> tuple[str, str]:
    """Trả (mức mới, mã luật). Mỗi buổi lên tối đa 1 mức; xuống tối đa 1 mức."""
    today = _d(lesson_date)
    alone = lesson_obs.count("alone")
    hint = lesson_obs.count("hint")
    wrong = lesson_obs.count("wrong")
    later_lesson = first_seen is None or (_d(first_seen) is not None and today is not None and today > _d(first_seen))

    if current in ("standard", "mastered") and wrong > 0 and alone == 0:
        return ORDER[ORDER.index(current) - 1], "R-down"
    if current == "to_do" and (alone > 0 or hint > 0) and alone + hint > wrong:
        return "improving", "R-improving"
    if current == "improving" and alone >= STANDARD_ALONE and wrong == 0 and later_lesson:
        return "standard", "R-standard"
    if current == "standard" and alone >= 1 and wrong == 0:
        since = _d(standard_since)
        if since and today and (today - since).days >= MASTERED_AFTER_DAYS:
            return "mastered", "R-mastered"
    return current, ""


def outcome_of(exercise_result: str, had_error: bool) -> str:
    """alone chỉ khi tự làm đúng và không vấp lỗi nào ở nút này; có gợi ý hoặc tự sửa
    sau khi sai -> hint; gia sư giải hoặc chưa xong -> wrong."""
    if exercise_result == "pupil_alone":
        return "hint" if had_error else "alone"
    if exercise_result == "pupil_with_help":
        return "hint"
    return "wrong"


def apply(evidence: dict[str, Any], states: list[dict[str, Any]], lesson_date: str) -> dict[str, Any]:
    """Từ evidence đã kiểm + trạng thái cũ -> observations, proposed_changes, first_seen."""
    by_ex_errors: dict[str, set[str]] = {}
    for ev in evidence.get("pupil_events") or []:
        if ev.get("type") == "error" and ev.get("exercise_id"):
            by_ex_errors.setdefault(ev["exercise_id"], set()).add(ev.get("skill_node") or "")

    observations: list[dict[str, Any]] = []
    for ex in evidence.get("exercises") or []:
        node = ex.get("skill_node") or ""
        if not node or ex.get("result") == "set_as_homework":
            continue
        had_error = node in by_ex_errors.get(ex.get("id", ""), set())
        observations.append({
            "node": node, "exercise_id": ex.get("id"),
            "outcome": outcome_of(ex.get("result", ""), had_error),
            "seg": ex.get("start_seg"), "quote": ex.get("quote", ""),
        })
    # lỗi gắn nút khác nút của bài -> thêm quan sát "wrong" cho nút đó
    for ex_id, nodes in by_ex_errors.items():
        for node in nodes:
            if node and not any(o["node"] == node and o["exercise_id"] == ex_id for o in observations):
                observations.append({"node": node, "exercise_id": ex_id, "outcome": "wrong", "seg": None, "quote": ""})

    known = {s["node"]: s for s in states}
    per_node: dict[str, list[str]] = {}
    for o in observations:
        per_node.setdefault(o["node"], []).append(o["outcome"])

    proposed, first_seen = [], []
    for node, obs in per_node.items():
        st = known.get(node)
        if st is None:
            first_seen.append({"node": node, "level": first_level(obs)})
            continue
        new, rule = next_level(st["level"], obs, lesson_date=lesson_date,
                               first_seen=st.get("first_seen"), standard_since=st.get("standard_since"))
        if new != st["level"]:
            up = ORDER.index(new) > ORDER.index(st["level"])
            proposed.append({"node": node, "from": st["level"], "to": new, "star": up, "rule": rule,
                             "evidence_segs": [o["seg"] for o in observations if o["node"] == node and o["seg"] is not None]})
    return {"observations": observations, "proposed_changes": proposed, "first_seen": first_seen}
