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
    ev = {"exercises": [], "attempts": [_att(1, "wrong", "X1"), _att(3, "after_hint", "X1")], "habits": [], "doubts": []}
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


def test_repeating_tutor_correction_is_not_self_correction():
    pe = [{"type": "error", "seg": 8}, {"type": "self_correction", "seg": 12, "after": "error_pointed"},
          {"type": "error", "seg": 96}, {"type": "self_correction", "seg": 98, "after": "error_pointed"},
          {"type": "error", "seg": 150}, {"type": "self_correction", "seg": 155, "after": "error_pointed"}]
    te = [{"type": "error_pointed", "seg": 9}, {"type": "error_resolved_by_tutor", "seg": 11},
          {"type": "error_pointed", "seg": 97}]
    out, n = analysis._guard_self_corrections(pe, te)
    sc = [(p["seg"], p["after"]) for p in out if p["type"] == "self_correction"]
    assert sc == [(98, "error_pointed"), (155, "none")] and n == 2


def test_same_error_pattern_in_two_topics_merges_into_one_high_gap():
    a1 = dict(_att(1, "wrong", "X1", skill="giải bất phương trình", fixed=True), error_pattern="Drops the endpoint case")
    a2 = dict(_att(5, "wrong", "X2", skill="giao hai khoảng", fixed=True), error_pattern="drops the endpoint case")
    a3 = _att(6, "alone", "X2", skill="giao hai khoảng")
    a4 = dict(_att(9, "wrong", "X3", skill="mệnh đề đảo"), error_pattern="accepts claim without testing")
    g = analysis.gaps({"exercises": [], "attempts": [a1, a2, a3, a4], "habits": [], "doubts": []})
    rows = [(m["skill"], m["confidence"], m["slip"]) for m in g["maths"]]
    assert rows == [("giao hai khoảng", "high", False), ("mệnh đề đảo", "medium", False)]


def test_homework_with_no_occasion_drops_out_and_not_evidence_attempts_are_left_out():
    segs = [{"start": 0, "speaker": "tutor", "text": "hôm nay buổi đầu"}, {"start": 60, "speaker": "student", "text": "x bằng hai"}]
    ev = {"blocks": [], "ack_segments": [], "exercises": [], "tutor_events": [], "pupil_events": []}
    assert analysis.tutor_behaviours(ev, segs)["bands"]["7"] == "below"
    assert analysis.tutor_behaviours(dict(ev, homework_occasion="no"), segs)["bands"]["7"] is None
    raw = {"attempts": [dict(_att(1, "wrong", "X1"), quote="x bằng hai", not_evidence="reuses_earlier_result")]}
    out = analysis.check(raw, segs)
    assert out["attempts"] == [] and out["check"]["attempts_not_evidence"] == 1


def test_slip_is_decided_in_code_not_by_the_model():
    att = [_att(1, "wrong", "X1", fixed=True), _att(4, "after_hint", "X1")]
    told = [{"type": "error_resolved_by_tutor", "seg": 2}]
    g = analysis.gaps({"exercises": [], "attempts": att, "habits": [], "doubts": [], "tutor_events": told})
    assert not g["maths"][0]["slip"]  # the tutor said the fix: not fixed alone
    g = analysis.gaps({"exercises": [], "attempts": [_att(1, "wrong", "X1")], "habits": [], "doubts": []})
    assert not g["maths"][0]["slip"]  # no next attempt


def _out(bands, maths, habits=()):
    return {"version": "v", "model": "m", "evidence": {}, "tutor_standard": {"values": {}, "bands": bands},
            "gaps": {"maths": maths, "learning_skills": [{"habit": h, "confidence": c, "instances": 1, "evidence": []}
                                                         for h, c in habits], "shown_correct": [], "doubts": []}}


def _gap(skill, conf, segs):
    return {"skill": skill, "confidence": conf, "slip": False, "attempts": [{"seg": s, "label": "wrong"} for s in segs]}


def test_vote_keeps_majority_bands_and_gaps():
    o1 = _out({"6": "near", "7": None}, [_gap("a", "high", [10]), _gap("extra", "high", [99])], [("no_self_check", "high")])
    o2 = _out({"6": "below", "7": None}, [_gap("a2", "medium", [10, 20])], [("no_self_check", "medium")])
    o3 = _out({"6": "near", "7": "met"}, [_gap("a3", "high", [20])], [("no_self_check", "low")])
    v = analysis.vote([o1, o2, o3])
    assert v["tutor_standard"]["bands"] == {"6": "near", "7": None} and v["tutor_standard"]["unsure"] == []
    assert [(g["skill"], g["confidence"], g["votes"]) for g in v["gaps"]["maths"]] == [("a", "high", 3)]
    assert [(h["habit"], h["confidence"]) for h in v["gaps"]["learning_skills"]] == [("no_self_check", "low")]
    v = analysis.vote([o1, o2, _out({"6": "met", "7": None}, [])])
    assert v["tutor_standard"]["bands"]["6"] == "near" and v["tutor_standard"]["unsure"] == ["6"]
