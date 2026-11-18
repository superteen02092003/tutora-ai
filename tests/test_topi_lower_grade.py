"""Kỹ năng lớp dưới xa chỉ được ghi khi học sinh làm sai (test điện thoại 2026-11-18)."""
from app.services.topi import levels


def _ev(node, result, error=False):
    ev = {"exercises": [{"id": "X1", "skill_node": node, "result": result, "start_seg": 1, "quote": ""}],
          "pupil_events": []}
    if error:
        ev["pupil_events"].append({"type": "error", "exercise_id": "X1", "skill_node": node})
    return ev


def test_far_lower_grade_with_hint_is_dropped():
    out = levels.apply(_ev("N4.10", "pupil_with_help"), [], "2026-10-28", grade=10)
    assert out["observations"] == [] and out["first_seen"] == []


def test_far_lower_grade_wrong_is_kept():
    out = levels.apply(_ev("N4.10", "tutor_solved"), [], "2026-10-28", grade=10)
    assert [o["outcome"] for o in out["observations"]] == ["wrong"]
    assert out["first_seen"] == [{"node": "N4.10", "level": "to_do"}]


def test_near_grade_with_hint_is_kept():
    out = levels.apply(_ev("N9.15", "pupil_with_help"), [], "2026-10-28", grade=10)
    assert out["first_seen"] == [{"node": "N9.15", "level": "improving"}]


def test_no_grade_keeps_everything():
    out = levels.apply(_ev("N4.10", "pupil_alone"), [], "2026-10-28")
    assert len(out["observations"]) == 1
