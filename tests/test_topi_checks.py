"""Topi v1 — kiểm tra bằng code (không gọi mạng): trích dẫn, người nói, SymPy, luật mức."""
from app.services.topi import checker, levels, mathcheck

SEGS = [
    {"start": 0.0, "speaker": "tutor", "text": "Bài 3 nhé: tính 5 − (x − 4)."},
    {"start": 5.0, "speaker": "student", "text": "Dạ, bằng 1 − x ạ."},
    {"start": 9.0, "speaker": "tutor", "text": "Xem lại dấu ở dòng này, dấu trừ trước ngoặc."},
    {"start": 14.0, "speaker": "student", "text": "À, là 9 − x."},
]


# ---------- checker
def test_normalise_keeps_vietnamese_marks():
    assert checker.normalise("  Dạ, BẰNG 1 − x ạ. ") == "dạ bằng 1 x ạ"


def test_quote_must_be_in_its_segment():
    kept, dropped, _ = checker.check_labels(
        [{"seg": 1, "quote": "bằng 1 − x"}, {"seg": 1, "quote": "bằng 2 − x"}], SEGS,
        kind="pupil_events", expected_speaker="student")
    assert len(kept) == 1 and dropped[0]["reason"] == "quote_not_in_segment"


def test_quote_in_neighbour_segment_is_moved_to_it():
    kept, _, _ = checker.check_labels([{"seg": 2, "quote": "là 9 − x"}], SEGS,
                                      kind="pupil_events", expected_speaker="student")
    assert kept[0]["seg"] == 3 and kept[0]["ts"] == 14.0


def test_wrong_speaker_is_dropped():
    _, dropped, _ = checker.check_labels([{"seg": 2, "quote": "xem lại dấu"}], SEGS,
                                         kind="pupil_events", expected_speaker="student")
    assert dropped[0]["reason"] == "wrong_speaker"


def test_bad_seg_is_dropped():
    _, dropped, _ = checker.check_labels([{"seg": 99, "quote": "x"}], SEGS, kind="flags", expected_speaker=None)
    assert dropped[0]["reason"] == "bad_seg"


def test_check_evidence_blanks_node_of_unproven_exercise():
    ev = {"exercises": [{"id": "X1", "start_seg": 0, "end_seg": 3, "quote": "bài 7", "skill_node": "N7.03"}],
          "tutor_events": [{"type": "error_pointed", "seg": 2, "quote": "xem lại dấu ở dòng này"}],
          "pupil_events": [], "flags": [], "homework_set": {"seg": None, "quote": ""}}
    out = checker.check_evidence(ev, SEGS)
    assert out["exercises"][0]["skill_node"] == "" and out["check"]["kept"] == 1


# ---------- mathcheck
def test_expression_answer_checked():
    assert mathcheck.verify("7 - (2*x - 5)", "12 - 2*x") is True
    assert mathcheck.verify("7 - (2*x - 5)", "2 - 2*x") is False


def test_unicode_minus_and_powers():
    assert mathcheck.verify("(x + 3)(x − 1) − (x − 2)(x + 2)", "2x + 1") is True
    assert mathcheck.verify("x² − 25", "(x - 5)*(x + 5)") is True


def test_equation_answer_checked():
    assert mathcheck.verify("3*x - (x - 6) = 10", "x = 2") is True
    assert mathcheck.verify("3*x - (x - 6) = 10", "x = 3") is False


def test_unsafe_input_rejected():
    assert mathcheck.verify("__import__('os').system('x')", "0") is False
    assert mathcheck.verify("", "1") is None


def test_identity():
    assert mathcheck.identity_holds("-(a - b) = -a + b") is True
    assert mathcheck.identity_holds("-(a - b) = -a - b") is False
    assert mathcheck.identity_holds("no equals here") is None


# ---------- levels (decision of 2026-11-11: a star per level moved up)
def test_first_seen_earns_no_star():
    ev = {"exercises": [{"id": "X1", "result": "pupil_alone", "skill_node": "N8.01", "start_seg": 0}], "pupil_events": []}
    out = levels.apply(ev, [], "2026-11-09")
    assert out["first_seen"] == [{"node": "N8.01", "level": "improving"}] and out["proposed_changes"] == []


def test_to_do_to_improving_gives_one_star():
    ev = {"exercises": [{"id": "X1", "result": "pupil_with_help", "skill_node": "N7.03", "start_seg": 0}], "pupil_events": []}
    st = [{"node": "N7.03", "level": "to_do", "first_seen": "2026-11-02"}]
    ch = levels.apply(ev, st, "2026-11-09")["proposed_changes"]
    assert ch == [{"node": "N7.03", "from": "to_do", "to": "improving", "star": True, "rule": "R-improving", "evidence_segs": [0]}]


def test_standard_needs_two_alone_in_a_later_lesson():
    two = {"exercises": [{"id": "X1", "result": "pupil_alone", "skill_node": "N7.03", "start_seg": 0},
                         {"id": "X2", "result": "pupil_alone", "skill_node": "N7.03", "start_seg": 1}], "pupil_events": []}
    one = {"exercises": two["exercises"][:1], "pupil_events": []}
    st = [{"node": "N7.03", "level": "improving", "first_seen": "2026-11-02"}]
    assert levels.apply(two, st, "2026-11-12")["proposed_changes"][0]["to"] == "standard"
    assert levels.apply(one, st, "2026-11-12")["proposed_changes"] == []
    same_day = [{"node": "N7.03", "level": "improving", "first_seen": "2026-11-12"}]
    assert levels.apply(two, same_day, "2026-11-12")["proposed_changes"] == []


def test_mastered_after_three_weeks_only():
    ev = {"exercises": [{"id": "X1", "result": "pupil_alone", "skill_node": "N8.05", "start_seg": 0}], "pupil_events": []}
    early = [{"node": "N8.05", "level": "standard", "first_seen": "2026-10-12", "standard_since": "2026-11-01"}]
    late = [{"node": "N8.05", "level": "standard", "first_seen": "2026-10-12", "standard_since": "2026-10-19"}]
    assert levels.apply(ev, early, "2026-11-09")["proposed_changes"] == []
    assert levels.apply(ev, late, "2026-11-09")["proposed_changes"][0]["to"] == "mastered"


def test_error_after_standard_moves_down_without_star():
    ev = {"exercises": [{"id": "X1", "result": "tutor_solved", "skill_node": "N8.05", "start_seg": 0}], "pupil_events": []}
    st = [{"node": "N8.05", "level": "standard", "first_seen": "2026-10-12", "standard_since": "2026-10-19"}]
    ch = levels.apply(ev, st, "2026-11-09")["proposed_changes"][0]
    assert ch["to"] == "improving" and ch["star"] is False


def test_self_corrected_error_is_not_alone():
    ev = {"exercises": [{"id": "X1", "result": "pupil_alone", "skill_node": "N7.03", "start_seg": 0}],
          "pupil_events": [{"type": "error", "exercise_id": "X1", "skill_node": "N7.03"}]}
    obs = levels.apply(ev, [], "2026-11-09")["observations"]
    assert obs[0]["outcome"] == "hint"
