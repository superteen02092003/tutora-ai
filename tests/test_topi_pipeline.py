"""Topi v1 — toàn pipeline với Gemini giả (không gọi mạng)."""
import asyncio

from app.models.topi import TopiRunRequest
from app.services.topi import pipeline, plan

SEGS = [
    {"start": 0.0, "speaker": "tutor", "text": "Bài 3 nhé: tính 5 − (x − 4)."},
    {"start": 5.0, "speaker": "student", "text": "Dạ, bằng 1 − x ạ."},
    {"start": 9.0, "speaker": "tutor", "text": "Xem lại dấu ở dòng này, dấu trừ trước ngoặc."},
    {"start": 14.0, "speaker": "student", "text": "À, là 9 − x."},
    {"start": 20.0, "speaker": "tutor", "text": "Về nhà làm 5 bài phân tích đa thức trên phiếu nhé."},
]

EVIDENCE = {
    "exercises": [{"id": "X1", "start_seg": 0, "end_seg": 3, "quote": "tính 5 − (x − 4)", "kind": "practice",
                   "first_actor": "pupil", "first_help": "hint", "result": "pupil_with_help", "skill_node": "N7.03"}],
    "tutor_events": [{"type": "error_pointed", "seg": 2, "quote": "Xem lại dấu ở dòng này", "exercise_id": "X1"},
                     {"type": "praise_person", "seg": 2, "quote": "em giỏi quá"}],
    "pupil_events": [{"type": "error", "seg": 1, "quote": "bằng 1 − x", "exercise_id": "X1", "error_type": "sign_or_bracket",
                      "skill_node": "N7.03", "earlier_grade": True, "wrong": "-(a - b) = -a - b", "right": "-(a - b) = -a + b"},
                     {"type": "self_correction", "seg": 3, "quote": "là 9 − x", "after": "error_pointed"}],
    "homework_set": {"seg": 4, "quote": "Về nhà làm 5 bài phân tích đa thức trên phiếu"},
    "flags": [],
}

PLAN = {"check": [{"say": "Hỏi: em làm bài này nhé?", "problem": "7 - (2*x - 5)", "answer": "12 - 2*x"},
                  {"say": "Hỏi: còn bài này?", "problem": "10 - (3 - x)", "answer": "7 + x"},
                  {"say": "Hỏi: sai đáp án", "problem": "4 - (2 - 3*x)", "answer": "2 - 3*x"}],
        "memory": [{"say": "Hỏi: viết (a + b)^2", "problem": "(a + b)**2", "answer": "a**2 + 2*a*b + b**2"}],
        "warmup": [{"say": "Hỏi: giải 3x − (x − 6)", "problem": "3*x - (x - 6)", "answer": "2*x + 6"}]}

TIPS = {"did_well": {"text": "Bạn chỉ ra dòng sai rồi để em tự sửa.", "seg": 2, "quote": "Xem lại dấu ở dòng này"},
        "try_next": {"text": "Hỏi trước: em sẽ bắt đầu thế nào?", "seg": 0, "quote": "câu không có thật"},
        "talk_more": None, "habit": None}

REPORT = {"lesson_content": {"text": "Con luyện bỏ ngoặc.", "cites": ["X1", "Z9"]},
          "homework": {"text": "5 bài phân tích đa thức.", "cites": ["hw"]},
          "tutor_notes": {"text": "Con tự sửa dấu.", "cites": ["P2"]},
          "zalo": {"content": "a", "homework": "b", "notes": "c"}}


def _fake(monkeypatch):
    async def fake_generate_json(client, *, feature, **_):
        return {"topi_evidence": EVIDENCE, "topi_plan": PLAN, "topi_tips": TIPS, "topi_report": REPORT}[feature]
    for mod in ("evidence", "plan", "tips", "report"):
        monkeypatch.setattr(f"app.services.topi.{mod}.generate_json", fake_generate_json)


def _req(**kw):
    base = dict(lesson_id="L1", lesson_date="2026-11-09", grade=8, duration_sec=5160, booked_min=90,
                transcript={"segments": SEGS},
                skill_states=[{"node": "N7.03", "level": "to_do", "first_seen": "2026-11-02",
                               "observations": [{"lesson_date": "2026-11-02", "outcome": "wrong"},
                                                {"lesson_date": "2026-11-05", "outcome": "wrong"}]}])
    base.update(kw)
    return TopiRunRequest(**base)


def test_pipeline_end_to_end(monkeypatch):
    _fake(monkeypatch)
    out = asyncio.run(pipeline.run(None, _req(), evidence_model="m1", write_model="m2"))
    assert out.errors == {}
    # praise_person quote is not in seg 2 -> dropped by code
    assert any(d["reason"] == "quote_not_in_segment" for d in out.evidence["check"]["dropped"])
    # report: unknown cite removed, quality line by code
    assert out.report["lesson_content"]["cites"] == ["X1"] and out.report["quality_line"] == "86 of 90 min"
    # plan: the wrong answer is dropped by SymPy, the gap is the focus with wrong/right kept
    check = out.plan["steps"][0]
    assert check["name"] == "check" and len(check["asks"]) == 2 and all(a["verified"] for a in check["asks"])
    gap = out.plan["gaps"][0]
    assert gap["node"] == "N7.03" and gap["role"] == "focus" and gap["seen_in_lessons"] == 3 and gap["right"]
    assert [s["name"] for s in out.plan["steps"]] == ["check", "homework", "memory", "warmup"]
    # tips: an invented quote is dropped
    assert out.tips["did_well"]["seg"] == 2 and out.tips["try_next"] is None
    # skills: to_do -> improving, one star
    assert out.skills["proposed_changes"][0]["to"] == "improving" and out.skills["proposed_changes"][0]["star"]


def test_one_failing_output_does_not_break_others(monkeypatch):
    _fake(monkeypatch)

    async def boom(*a, **k):
        raise RuntimeError("model down")
    monkeypatch.setattr("app.services.topi.tips.generate_json", boom)
    out = asyncio.run(pipeline.run(None, _req(), evidence_model="m1", write_model="m2"))
    assert out.tips is None and "tips" in out.errors and out.report is not None


def test_no_homework_means_fixed_sentence(monkeypatch):
    _fake(monkeypatch)
    ev = dict(EVIDENCE, homework_set={"seg": None, "quote": ""})

    async def fake(client, *, feature, **_):
        return {"topi_evidence": ev, "topi_plan": PLAN, "topi_tips": TIPS, "topi_report": REPORT}[feature]
    for mod in ("evidence", "plan", "tips", "report"):
        monkeypatch.setattr(f"app.services.topi.{mod}.generate_json", fake)
    out = asyncio.run(pipeline.run(None, _req(), evidence_model="m1", write_model="m2"))
    assert out.report["homework"]["text"] == "Không có bài tập về nhà."


def test_rank_gaps_basics_first():
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N7.12", "quote": "q", "seg": 1},   # needs N7.03
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 2}]}
    rows = plan.rank_gaps(ev, [])
    assert rows[0]["node"] == "N7.03"
