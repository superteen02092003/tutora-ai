"""Topi v1 — toàn pipeline với Gemini giả (không gọi mạng)."""
import asyncio
import json

from app.models.topi import TopiRunRequest
from app.services.topi import checker, pipeline, plan, report, tips

SEGS = [
    {"start": 0.0, "speaker": "tutor", "text": "Bài 3 nhé: tính 5 − (x − 4)."},
    {"start": 5.0, "speaker": "student", "text": "Dạ, bằng 1 − x ạ."},
    {"start": 9.0, "speaker": "tutor", "text": "Xem lại dấu ở dòng này, dấu trừ trước ngoặc."},
    {"start": 14.0, "speaker": "student", "text": "À, là 9 − x."},
    {"start": 20.0, "speaker": "tutor", "text": "Về nhà làm 5 bài phân tích đa thức trên phiếu nhé."},
    {"start": 25.0, "speaker": "tutor", "text": "Với lại đọc trước bài hằng đẳng thức, nộp trước thứ Sáu nha."},
]

EVIDENCE = {
    "exercises": [{"id": "X1", "start_seg": 0, "end_seg": 3, "quote": "tính 5 − (x − 4)", "kind": "practice",
                   "first_actor": "pupil", "first_help": "hint", "result": "pupil_with_help", "skill_node": "N7.03"}],
    "tutor_events": [{"type": "error_pointed", "seg": 2, "quote": "Xem lại dấu ở dòng này", "exercise_id": "X1"},
                     {"type": "praise_person", "seg": 2, "quote": "em giỏi quá"}],
    "pupil_events": [{"type": "error", "seg": 1, "quote": "bằng 1 − x", "exercise_id": "X1", "error_type": "sign_or_bracket",
                      "skill_node": "N7.03", "earlier_grade": True, "wrong": "-(a - b) = -a - b", "right": "-(a - b) = -a + b"},
                     {"type": "self_correction", "seg": 3, "quote": "là 9 − x", "after": "error_pointed"}],
    "homework_tasks": [
        {"seg": 4, "quote": "Về nhà làm 5 bài phân tích đa thức trên phiếu", "task": "5 bài phân tích đa thức trên phiếu",
         "due": "trước thứ Sáu", "due_seg": 5, "due_quote": "nộp trước thứ Sáu"},
        {"seg": 5, "quote": "đọc trước bài hằng đẳng thức", "task": "đọc trước bài hằng đẳng thức",
         "due": "trước thứ Sáu", "due_seg": 5, "due_quote": "nộp trước thứ Sáu"},
    ],
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
          "homework": {"text": "5 bài phân tích đa thức và đọc trước bài hằng đẳng thức, nộp trước thứ Sáu.",
                       "cites": ["hw1", "hw2"]},
          "tutor_notes": {"text": "Con tự sửa dấu.", "cites": ["P2"]},
          "zalo": {"content": "a", "homework": "Con làm 5 bài phân tích đa thức và đọc trước bài mới, trước thứ Sáu.",
                   "notes": "c"}}


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
    assert out.report["lesson_content"]["cites"] == ["X1"] and out.report["quality_line"] == "86/90 phút"
    # plan: the wrong answer is dropped by SymPy, the gap is the focus with wrong/right kept
    check = out.plan["steps"][0]
    assert check["name"] == "check" and len(check["asks"]) == 2 and all(a["verified"] for a in check["asks"])
    gap = out.plan["gaps"][0]
    assert gap["node"] == "N7.03" and gap["role"] == "focus" and gap["seen_in_lessons"] == 3 and gap["right"]
    assert [s["name"] for s in out.plan["steps"]] == ["check", "homework", "memory", "warmup"]
    # homework: both tasks and the deadline kept, no retry needed
    assert out.report["homework_check"] == "ok" and len(out.evidence["homework_tasks"]) == 2
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


def test_no_homework_heard_is_not_no_homework(monkeypatch):
    """HW-NONE: không nghe thấy bài về nhà thì không khẳng định là không có bài."""
    _fake(monkeypatch)
    ev = dict(EVIDENCE, homework_tasks=[])

    async def fake(client, *, feature, **_):
        return {"topi_evidence": ev, "topi_plan": PLAN, "topi_tips": TIPS, "topi_report": REPORT}[feature]
    for mod in ("evidence", "plan", "tips", "report"):
        monkeypatch.setattr(f"app.services.topi.{mod}.generate_json", fake)
    out = asyncio.run(pipeline.run(None, _req(), evidence_model="m1", write_model="m2"))
    assert out.report["homework"]["text"] == report.NO_HW
    assert out.report["zalo"]["homework"] == report.NO_HW
    assert "Không có bài tập" not in out.report["homework"]["text"]


def test_rank_gaps_only_skills_with_evidence_of_a_gap():
    # Buổi 28/10: kỹ năng ôn lớp 3–8 ở mức improving vì luật buổi đầu, chưa sai lần nào.
    states = [
        {"node": "N4.10", "level": "improving", "observations": [{"lesson_date": "2026-10-05", "outcome": "alone"}]},
        {"node": "N6.05", "level": "to_do", "observations": [{"lesson_date": "2026-10-26", "outcome": "wrong"}]},
        {"node": "N9.15", "level": "improving", "observations": [{"lesson_date": "2026-10-21", "outcome": "wrong"}]},
        {"node": "N10.01", "level": "standard", "observations": []},
    ]
    ev = {"pupil_events": [{"type": "error", "skill_node": "H10.01", "quote": "q", "seg": 3}]}
    nodes = {r["node"] for r in plan.rank_gaps(ev, states)}
    assert nodes == {"H10.01", "N6.05", "N9.15"}


def test_rank_gaps_drops_a_skill_raised_this_lesson():
    states = [{"node": "N10.04", "level": "improving",
               "observations": [{"lesson_date": "2026-10-26", "outcome": "wrong"}]}]
    assert [r["node"] for r in plan.rank_gaps({}, states)] == ["N10.04"]
    assert plan.rank_gaps({}, states, {"N10.04"}) == []


def test_rank_gaps_basics_first():
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N7.12", "quote": "q", "seg": 1},   # needs N7.03
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 2}]}
    rows = plan.rank_gaps(ev, [])
    assert rows[0]["node"] == "N7.03"


# ---------- PLAN-FOCUS: trọng tâm phải là lỗ hổng có bằng chứng, không phải lỗi một lần
WR = {"wrong": "-(a - b) = -a - b", "right": "-(a - b) = -a + b"}


def test_single_self_fixed_error_is_watch_never_focus():
    # L9 seg 68: bé lưỡng lự rồi tự sửa ngay — chỉ theo dõi, kể cả khi là dòng duy nhất.
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 68, "exercise_id": "X1", **WR},
        {"type": "self_correction", "seg": 68, "after": "none"}]}
    rows = plan.rank_gaps(ev, [])
    assert [(r["node"], r["role"], r["confidence"]) for r in rows] == [("N7.03", "watch", "low")]


def test_unproven_medium_gap_is_not_focus():
    # L3: một lần sai không tự sửa, nhưng không có cặp sai/đúng kiểm chứng -> không làm trọng tâm.
    ev = {"pupil_events": [{"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 4, "exercise_id": "X1"}]}
    rows = plan.rank_gaps(ev, [])
    assert rows[0]["confidence"] == "medium" and rows[0]["role"] == "next"
    assert not any(r["role"] == "focus" for r in rows)


def test_proven_gap_beats_self_fixed_slip_regardless_of_node_order():
    # Trước đây hoà điểm thì xếp theo mã nút: N6.05 đứng trước N7.03 dù chỉ là lỗi tự sửa.
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N6.05", "quote": "q", "seg": 1, "exercise_id": "X1", "error_type": "slip"},
        {"type": "self_correction", "seg": 2, "after": "error_pointed"},
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 10, "exercise_id": "X2",
         "error_type": "concept", **WR}]}
    rows = {r["node"]: r for r in plan.rank_gaps(ev, [])}
    assert rows["N7.03"]["role"] == "focus" and rows["N6.05"]["role"] == "watch"


def test_errors_on_two_problems_are_high_and_focus_without_proof():
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 1, "exercise_id": "X1"},
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 9, "exercise_id": "X2"}]}
    row = plan.rank_gaps(ev, [])[0]
    assert row["confidence"] == "high" and row["errors_now"] == 2 and row["role"] == "focus"


def test_only_one_focus():
    ev = {"pupil_events": [
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 1, "exercise_id": "X1", **WR},
        {"type": "error", "skill_node": "N6.05", "quote": "q", "seg": 9, "exercise_id": "X2", **WR}]}
    roles = [r["role"] for r in plan.rank_gaps(ev, [])]
    assert roles.count("focus") == 1


def test_no_focus_means_no_check_step(monkeypatch):
    async def fake(client, *, feature, **_):
        raise AssertionError("không có trọng tâm thì không gọi model soạn câu hỏi")
    monkeypatch.setattr("app.services.topi.plan.generate_json", fake)
    ev = {"pupil_events": [{"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 1},
                           {"type": "self_correction", "seg": 1, "after": "none"}]}
    out = asyncio.run(plan.build(None, model="m", evidence=ev, states=[], grade=8, last_homework=None))
    assert "check" not in [s["name"] for s in out["steps"]]


def test_plan_sees_every_exercise_not_only_first_eight(monkeypatch):
    seen = {}

    async def fake(client, *, feature, prompt, **_):
        seen.update(json.loads(prompt))
        return {"check": [], "memory": [], "warmup": []}
    monkeypatch.setattr("app.services.topi.plan.generate_json", fake)
    ex = [{"quote": f"bài {i}"} for i in range(21)] + [{"quote": "bài 0"}]
    ev = {"exercises": ex, "pupil_events": [
        {"type": "error", "skill_node": "N7.03", "quote": "q", "seg": 1, "exercise_id": "X1", **WR}]}
    asyncio.run(plan.build(None, model="m", evidence=ev, states=[], grade=8, last_homework=None))
    assert len(seen["lesson_tasks"]) == 21 and seen["lesson_tasks"][-1] == "bài 20"


# ---------- HW-ONE: mọi bài về nhà và hạn nộp đều đến phụ huynh
def _report_fake(monkeypatch, *answers):
    calls = []

    async def fake(client, *, feature, prompt, **_):
        calls.append(prompt)
        return answers[min(len(calls), len(answers)) - 1]
    monkeypatch.setattr("app.services.topi.report.generate_json", fake)
    return calls


def _checked():
    return checker.check_evidence(EVIDENCE, SEGS)


def test_report_dropping_a_task_is_retried(monkeypatch):
    dropped = dict(REPORT, homework={"text": "5 bài phân tích đa thức, trước thứ Sáu.", "cites": ["hw1"]})
    calls = _report_fake(monkeypatch, dropped, REPORT)
    out = asyncio.run(report.write(None, model="m", evidence=_checked(), duration_sec=600, booked_min=None))
    assert len(calls) == 2 and "hw2" in calls[1] and out["homework_check"] == "retried"
    assert out["homework"]["cites"] == ["hw1", "hw2"]


def test_report_twice_without_deadline_is_composed_by_code(monkeypatch):
    no_due = dict(REPORT, homework={"text": "Hai bài về nhà.", "cites": ["hw1", "hw2"]},
                  zalo={"content": "a", "homework": "Hai bài về nhà.", "notes": "c"})
    _report_fake(monkeypatch, no_due, no_due)
    out = asyncio.run(report.write(None, model="m", evidence=_checked(), duration_sec=600, booked_min=None))
    assert out["homework_check"] == "composed"
    text = out["homework"]["text"]
    assert "5 bài phân tích đa thức trên phiếu" in text and "đọc trước bài hằng đẳng thức" in text
    assert text.count("trước thứ Sáu") == 2 and "trước thứ Sáu" in out["zalo"]["homework"]


def test_unproven_deadline_is_dropped_not_invented():
    ev = dict(EVIDENCE, homework_tasks=[{"seg": 4, "quote": "Về nhà làm 5 bài phân tích đa thức trên phiếu",
                                         "task": "5 bài", "due": "thứ Hai", "due_seg": 4, "due_quote": "thứ Hai"}])
    out = checker.check_evidence(ev, SEGS)
    assert out["homework_tasks"][0]["due"] is None
    assert any(d["label"] == "homework_tasks[0].due" for d in out["check"]["dropped"])


def test_old_homework_set_still_read():
    ev = {k: v for k, v in EVIDENCE.items() if k != "homework_tasks"}
    ev["homework_set"] = {"seg": 4, "quote": "Về nhà làm 5 bài phân tích đa thức trên phiếu"}
    out = checker.check_evidence(ev, SEGS)
    assert len(out["homework_tasks"]) == 1 and out["homework_set"]["seg"] == 4


# ---------- ZALO-LEN, QLINE-EN
def test_zalo_rows_never_over_200(monkeypatch):
    long = "Con luyện bỏ ngoặc sau dấu trừ và tự sửa được dấu ở bài ba. " * 6
    too_long = dict(REPORT, zalo={"content": long, "homework": REPORT["zalo"]["homework"], "notes": "c"})
    _report_fake(monkeypatch, too_long, too_long)
    out = asyncio.run(report.write(None, model="m", evidence=_checked(), duration_sec=600, booked_min=None))
    assert len(out["zalo"]["content"]) <= report.ZALO_MAX and out["zalo"]["content"].endswith(".")


def test_quality_line_is_vietnamese():
    assert report.quality_line(5160, 90) == "86/90 phút" and report.quality_line(600, None) == "10 phút"


# ---------- ADDRESS-BE, HABIT-MISS
def test_pupil_is_em_from_grade_6():
    assert tips.pupil_word(5) == "bé" and tips.pupil_word(10) == "em" and tips.pupil_word(None) == "em"
    assert '"bé"' not in tips.system_for(10).split("Không dùng")[0] and "gọi học sinh là \"em\"" in tips.system_for(10)


def test_habit_tip_from_two_slips(monkeypatch):
    seen = {}

    async def fake(client, *, prompt, **_):
        seen["want"] = __import__("json").loads(prompt)["want"]
        return {"did_well": None, "try_next": None, "talk_more": None, "habit": None}
    monkeypatch.setattr("app.services.topi.tips.generate_json", fake)
    ev = {"pupil_events": [{"type": "error", "error_type": "sign_or_bracket", "seg": 1, "quote": "bằng 1 − x"},
                           {"type": "error", "error_type": "calculation", "seg": 3, "quote": "là 9 − x"}]}
    asyncio.run(tips.write(None, model="m", evidence=ev, segments=SEGS, grade=8))
    assert seen["want"]["habit"] is True
