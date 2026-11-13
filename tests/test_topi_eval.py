"""B9 — bộ chấm golden set: chấm từ kết quả đã lưu (không gọi mạng)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("topi_eval", Path(__file__).resolve().parents[1] / "tools" / "topi_eval.py")
topi_eval = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(topi_eval)


def test_score_against_gold():
    topi = {"evidence": {"exercises": [
                {"first_actor": "pupil", "result": "pupil_alone", "skill_node": "N7.03"},
                {"first_actor": "tutor", "result": "tutor_solved", "skill_node": "N8.05"},
                {"first_actor": "pupil", "result": "set_as_homework"}],
             "check": {"kept": 9, "dropped": [{"label": "x", "reason": "bad_seg"}]}},
            "report": {"lesson_content": {"text": "a", "cites": []}, "tutor_notes": {"text": "b", "cites": ["X1"]}},
            "plan": {"steps": [{"asks": [{"problem": "1+1", "verified": True}, {"problem": "x", "verified": False}]}]},
            "errors": {}}
    gold = {"blind": True, "exercises": [{"first_actor": "pupil", "result": "alone", "skill_node": "N7.03"},
                                         {"first_actor": "pupil", "result": "tutor_solved"}]}
    row = topi_eval.score_lesson(topi, gold)
    assert row["exercises_model"] == 2 and row["exercises_gold"] == 2
    assert row["actor_agree"] == "1/2" and row["result_agree"] == "2/2" and row["node_agree"] == "1/1"
    assert row["labels_dropped_pct"] == 10.0 and row["report_uncited"] == 1 and row["plan_verified_pct"] == 50.0


def test_table_has_header():
    assert topi_eval.table([{"lesson": "abc"}]).startswith("| lesson |")
