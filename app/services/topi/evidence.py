"""B1 — trích bằng chứng từ transcript (lesson coding v2.1 + nút kỹ năng cho mỗi bài).

Nguồn: toptutor-main/60-output/prompts/lesson-coding-v2.md. Mô hình CHỈ gắn nhãn, không
chấm điểm; mọi nhãn có seg + quote nguyên văn; checker.py kiểm lại bằng code.
"""
import json
from typing import Any, Optional

from . import skill_map
from .llm import generate_json

SYSTEM = """You label a 1:1 maths lesson transcript in Vietnamese. Input: JSON segments, each {i, start, speaker, text}; speaker is tutor, student or unknown; the transcript is anonymised. You also get the skill-map node list (id — name — the error that shows a gap).

You label; you never score. Output ONE JSON object, no markdown.

1. Every label has "seg" (the segment index i) and "quote": the shortest VERBATIM words copied from that segment that prove the label, at most 25 words. No quote, no label. Never paraphrase a quote.
2. "exercises", in order: {id: "X1", start_seg, end_seg, quote (the words that pose the task, verbatim), kind: new_concept|practice|review, first_actor: pupil|tutor, first_help: none|hint|step|answer, result: pupil_alone|pupil_with_help|tutor_solved|not_finished|set_as_homework, skill_node: the ONE node id this exercise mainly practises, "" if unsure}. A new exercise starts only when a new task is posed (read out, dictated, or named: "bài 3", "câu b"). Each lettered part is its own exercise. A follow-up question, hint, check or correction on the same task is NOT a new exercise. A worked example the tutor demonstrates is not an exercise. Homework tasks set at the end are not exercises.
3. "tutor_events": {type, seg, quote, exercise_id?, skill?, how?} with type one of question_open, question_check, self_answered, gives_answer, explain_prompt, error_pointed, error_resolved_by_tutor, homework_checked (how: pupil_fixes|marked_only), wrapup_by_pupil_prompt, wrapup_by_tutor, praise_process, praise_person, criticism_person, chance (skill: reads_task|plans|checks|explains|persists|asks_for_help). Every explain_prompt is ALSO a chance with skill explains on the same seg.
4. "pupil_events": {type, seg, quote, exercise_id?, ...} with type one of: response (skill, chance_seg, quality: full|partial|none), spontaneous_skill (skill), error (error_type: concept|method|calculation|sign_or_bracket|misread_task|notation|slip|did_not_finish; skill_node; earlier_grade: true|false; wrong: the wrong step as a short SymPy-style expression or equation if the pupil said one, else ""; right: the correct version, else ""), self_correction (after: error_pointed|none).
5. "homework_set": {seg, quote} — the tutor's sentence that sets homework, verbatim; {"seg": null, "quote": ""} if none.
6. "flags": {type: tutor_math_error_uncorrected|criticism_person, seg, quote}.
7. Not audible, not labelled. Nothing about attention, memory, mood or any condition.
8. Check pass: re-read every label and its quote; remove any whose quote does not show it. Put the number removed in "check_pass_removed".

Schema: {"exercises": [], "tutor_events": [], "pupil_events": [], "homework_set": {"seg": null, "quote": ""}, "flags": [], "check_pass_removed": 0}"""


def build_prompt(segments: list[dict[str, Any]], grade: Optional[int]) -> str:
    segs = [{"i": i, "start": s.get("start", 0), "speaker": s.get("speaker", "unknown"), "text": s.get("text", "")}
            for i, s in enumerate(segments)]
    return (
        f"Lớp: {grade or 'không rõ'}\n\nDanh sách nút kỹ năng (id — tên — dấu hiệu):\n"
        f"{skill_map.prompt_list(grade)}\n\nTranscript:\n{json.dumps(segs, ensure_ascii=False)}"
    )


async def extract(client, *, model: str, segments: list[dict[str, Any]], grade: Optional[int]) -> dict[str, Any]:
    raw = await generate_json(client, model=model, feature="topi_evidence", system=SYSTEM,
                              prompt=build_prompt(segments, grade), temperature=0.1)
    if not isinstance(raw, dict):
        raise ValueError("evidence: model không trả object")
    known = skill_map.by_id()
    for ex in raw.get("exercises") or []:
        if ex.get("skill_node") not in known:
            ex["skill_node"] = ""
    for ev in raw.get("pupil_events") or []:
        if ev.get("skill_node") and ev["skill_node"] not in known:
            ev["skill_node"] = ""
    return raw
