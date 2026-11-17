"""Topi analysis v2 — code part only (no network): gap rules, confidence, tutor bands, schema strictness."""
from app.services.topi import analysis


def _att(seg, label, ex, skill="phủ định bất đẳng thức", fixed=False):
    return {"seg": seg, "quote": "q", "label": label, "exercise_id": ex, "skill": skill, "skill_node": "",
            "fixed_alone_after_pointing": fixed, "what_went_wrong": "misses =" if label != "alone" else "",
            "hint_seg": None, "hint_verified": False}


def test_two_problems_wrong_is_high_and_alone_only_is_shown_correct():
    ev = {"exercises": [], "attempts": [_att(1, "wrong", "X1"), _att(5, "after_hint", "X2"), _att(9, "alone", "X3"),
                                        _att(12, "alone", "X4", skill="viết mệnh đề đảo")], "habits": [], "doubts": []}
    g = analysis.gaps(ev)
    assert [m["confidence"] for m in g["maths"]] == ["high"]
    assert g["maths"][0]["level"] == "to_do"
    assert [s["skill"] for s in g["shown_correct"]] == ["viết mệnh đề đảo"]


def test_slip_is_low_and_feeds_no_self_check():
    ev = {"exercises": [], "attempts": [_att(1, "wrong", "X1", fixed=True)], "habits": [], "doubts": []}
    g = analysis.gaps(ev)
    assert g["maths"][0]["slip"] and g["maths"][0]["confidence"] == "low"
    assert g["learning_skills"][0]["habit"] == "no_self_check"


def test_doubt_lowers_confidence_and_tutor_only_habit_is_not_high():
    habits = [{"seg": s, "quote": "q", "speaker": "tutor", "habit": "answers_before_thinking", "about_earlier_lesson": False}
              for s in (1, 2, 3)]
    ev = {"exercises": [], "attempts": [_att(1, "wrong", "X1"), _att(5, "wrong", "X2")], "habits": habits,
          "doubts": [{"seg": 5, "note": "unclear"}]}
    g = analysis.gaps(ev)
    assert g["maths"][0]["confidence"] == "medium"
    assert g["learning_skills"][0]["confidence"] == "medium"


def test_tutor_bands_use_blocks_and_ack():
    segs = [{"start": 0, "speaker": "tutor", "text": "chào con"}, {"start": 60, "speaker": "tutor", "text": "một hai ba"},
            {"start": 120, "speaker": "student", "text": "dạ"}, {"start": 180, "speaker": "student", "text": "bốn năm sáu"}]
    ev = {"blocks": [{"type": "GUIDED", "start_seg": 1, "end_seg": 3}], "ack_segments": [2], "exercises": [],
          "tutor_events": [], "pupil_events": []}
    out = analysis.tutor_behaviours(ev, segs)
    assert out["values"]["1_talk_share"] == 0.5 and out["bands"]["1"] == "met"


def test_schemas_are_strict():
    def walk(s):
        if s.get("type") == "object":
            assert s["additionalProperties"] is False and set(s["required"]) == set(s["properties"])
            for v in s["properties"].values():
                walk(v)
        if s.get("type") == "array":
            walk(s["items"])
    for sch in (analysis.STRUCTURE_SCHEMA, analysis.TUTOR_SCHEMA, analysis.ATTEMPTS_SCHEMA, analysis.PUPIL_SCHEMA):
        walk(sch)
