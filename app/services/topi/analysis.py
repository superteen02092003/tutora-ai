"""Topi analysis v2 — Luna labels in 4 narrow passes; code checks quotes, finds gaps,
sets confidence and scores the tutor standard.

Flow: structure (pass 1) -> [tutor events, attempts, pupil events] in parallel -> checker
-> gaps() + tutor_behaviours() in code. Rules follow toptutor-main process 07
(PROCESS.md steps 4–8, scoring-model.md §2) and lesson-coding-v2.1 + score_v2.py.
Not wired into pipeline.py yet: it is scored against the Opus golden output first
(docs/topi-luna/03-eval-plan.md).
"""
import asyncio
import json
import re
import statistics as st
from typing import Any, Optional

from . import analysis_prompts as P
from . import skill_map
from .checker import check_labels
from .llm import generate_json

VERSION = "topi-analysis-v2.0"


# ------------------------------------------------------------------ schemas (strict)
def _obj(props: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def _arr(item: dict[str, Any]) -> dict[str, Any]:
    return {"type": "array", "items": item}


def _enum(*v: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(v)}


S, I, NI, B = {"type": "string"}, {"type": "integer"}, {"type": ["integer", "null"]}, {"type": "boolean"}
SKILLS = ("reads_task", "plans", "checks", "explains", "persists", "asks_for_help")

STRUCTURE_SCHEMA = _obj({
    "blocks": _arr(_obj({"type": _enum("OPEN", "HW_CHECK", "RECALL", "INSTRUCT", "DICTATE", "GUIDED", "INDEPENDENT",
                                       "FEEDBACK", "WRAPUP", "MOTIVATE", "ORGANISE", "OFFTASK"),
                         "start_seg": I, "end_seg": I})),
    "exercises": _arr(_obj({"id": S, "task_seg": I, "task_quote": S, "start_seg": I, "end_seg": I,
                            "kind": _enum("new_concept", "practice", "review"), "skill": S, "skill_node": S,
                            "first_actor": _enum("pupil", "tutor"), "first_help": _enum("none", "hint", "step", "answer"),
                            "result": _enum("pupil_alone", "pupil_with_help", "tutor_solved", "not_finished")})),
    "homework_set": _obj({"seg": NI, "quote": S}),
    "ack_segments": _arr(I),
})
TUTOR_SCHEMA = _obj({
    "tutor_events": _arr(_obj({"seg": I, "quote": S, "type": _enum(
        "question_open", "question_check", "self_answered", "gives_answer", "explain_prompt", "error_pointed",
        "error_resolved_by_tutor", "homework_checked", "wrapup_by_pupil_prompt", "wrapup_by_tutor", "praise_process",
        "praise_person", "criticism_person", "chance"), "exercise_id": S, "skill": _enum("", *SKILLS),
        "how": _enum("", "pupil_fixes", "marked_only")})),
    "flags": _arr(_obj({"type": _enum("tutor_math_error_uncorrected", "criticism_person"), "seg": I, "quote": S})),
    "homework_occasion": _enum("yes", "no", "unknown"),
})
ATTEMPTS_SCHEMA = _obj({
    "attempts": _arr(_obj({"exercise_id": S, "seg": I, "quote": S, "hint_seg": NI, "hint_quote": S,
                           "label": _enum("alone", "after_hint", "wrong", "not_finished"),
                           "fixed_alone_after_pointing": B, "skill": S, "skill_node": S, "what_went_wrong": S,
                           "not_evidence": _enum("", "leading_question", "tutor_led", "reuses_earlier_result"),
                           "error_pattern": S})),
    "habits": _arr(_obj({"seg": I, "quote": S, "speaker": _enum("pupil", "tutor"),
                         "habit": _enum("answers_before_thinking", "no_self_check", "no_written_working",
                                        "drops_known_rule_under_test", "gives_up_early"),
                         "about_earlier_lesson": B})),
    "doubts": _arr(_obj({"seg": I, "note": S})),
})
PUPIL_SCHEMA = _obj({
    "pupil_events": _arr(_obj({"seg": I, "quote": S, "type": _enum("response", "spontaneous_skill", "error", "self_correction"),
                               "exercise_id": S, "skill": _enum("", *SKILLS), "chance_seg": NI,
                               "quality": _enum("", "full", "partial", "none"),
                               "error_type": _enum("", "concept", "method", "calculation", "sign_or_bracket", "misread_task",
                                                   "notation", "slip", "did_not_finish"),
                               "after": _enum("", "error_pointed", "none")})),
})


# ------------------------------------------------------------------ passes
def _transcript(segments: list[dict[str, Any]]) -> str:
    return json.dumps([{"i": i, "start": s.get("start", 0), "speaker": s.get("speaker", "unknown"), "text": s.get("text", "")}
                       for i, s in enumerate(segments)], ensure_ascii=False)


async def label(client, *, model: str, segments: list[dict[str, Any]], grade: Optional[int],
                reasoning_effort: Optional[str] = "high") -> dict[str, Any]:
    """Four Luna calls; returns the raw labels (not yet checked)."""
    nodes = skill_map.prompt_list(grade)
    tr = _transcript(segments)
    head = f"Lớp (grade): {grade or 'unknown'}\n\n"
    kw = dict(model=model, reasoning_effort=reasoning_effort)
    structure = await generate_json(client, feature="topi_a_structure", system=P.STRUCTURE, schema=STRUCTURE_SCHEMA,
                                    prompt=head + f"Skill nodes (id — name — sign):\n{nodes}\n\nTranscript:\n{tr}", **kw)
    ex_list = json.dumps([{k: e[k] for k in ("id", "start_seg", "end_seg", "task_quote", "skill")}
                          for e in structure.get("exercises") or []], ensure_ascii=False)
    tutor_t = generate_json(client, feature="topi_a_tutor", system=P.TUTOR_EVENTS, schema=TUTOR_SCHEMA,
                            prompt=head + f"Exercises:\n{ex_list}\n\nTranscript:\n{tr}", **kw)
    att_t = generate_json(client, feature="topi_a_attempts", system=P.ATTEMPTS, schema=ATTEMPTS_SCHEMA,
                          prompt=head + f"Skill nodes (id — name — sign):\n{nodes}\n\nExercises:\n{ex_list}\n\nTranscript:\n{tr}", **kw)
    tutor, attempts = await asyncio.gather(tutor_t, att_t)
    chances = json.dumps([{"seg": e["seg"], "skill": e["skill"]} for e in tutor.get("tutor_events") or []
                          if e.get("type") == "chance"], ensure_ascii=False)
    err_moments = json.dumps([{"seg": e["seg"], "tutor": "pointed" if e["type"] == "error_pointed" else "resolved_by_tutor"}
                              for e in tutor.get("tutor_events") or []
                              if e.get("type") in ("error_pointed", "error_resolved_by_tutor")], ensure_ascii=False)
    pupil = await generate_json(client, feature="topi_a_pupil", system=P.PUPIL_EVENTS, schema=PUPIL_SCHEMA,
                                prompt=head + f"Exercises:\n{ex_list}\n\nTutor chances:\n{chances}\n\n"
                                f"Tutor error moments:\n{err_moments}\n\nTranscript:\n{tr}", **kw)
    return {**structure, **tutor, **attempts, **pupil}


# ------------------------------------------------------------------ code checks
def check(raw: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Every quote verbatim in its segment, right speaker; hints checked against tutor turns."""
    out, dropped = dict(raw), []
    for key, spk in (("tutor_events", "tutor"), ("pupil_events", "student"), ("flags", None), ("habits", None)):
        kept, drop, _ = check_labels(raw.get(key) or [], segments, kind=key, expected_speaker=spk)
        out[key], dropped = kept, dropped + drop
    kept, drop, _ = check_labels(raw.get("attempts") or [], segments, kind="attempts", expected_speaker="student")
    dropped += drop
    no_ev = [a for a in kept if a.get("not_evidence")]  # process 07 step 4: no evidence, not counted
    kept = [a for a in kept if not a.get("not_evidence")]
    for a in kept:
        if a.get("hint_quote"):
            h, _, _ = check_labels([{"seg": a.get("hint_seg"), "quote": a["hint_quote"]}], segments,
                                   kind="hint", expected_speaker="tutor")
            a["hint_verified"] = bool(h)
            if h:
                a["hint_seg"] = h[0]["seg"]
    out["attempts"] = kept
    n = len(segments)
    out["exercises"] = [e for e in raw.get("exercises") or [] if 0 <= e.get("start_seg", -1) <= e.get("end_seg", -1) < n]
    out["ack_segments"] = [i for i in raw.get("ack_segments") or []
                           if isinstance(i, int) and 0 <= i < n and segments[i].get("speaker") == "student"]
    out["pupil_events"], relabelled = _guard_self_corrections(out["pupil_events"], out["tutor_events"])
    out["check"] = {"dropped": dropped, "dropped_n": len(dropped), "self_correction_relabelled": relabelled,
                    "attempts_not_evidence": len(no_ev)}
    return out


def _guard_self_corrections(pe: list[dict[str, Any]], te: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """A pupil repeating a correction the tutor already said is not a self-correction (behaviour 6).

    Look at the tutor's last error move before the self_correction (after the pupil's last error, if any):
    error_resolved_by_tutor -> drop it; error_pointed -> after="error_pointed"; none -> after="none".
    """
    errs = [p["seg"] for p in pe if p.get("type") == "error"]
    moves = sorted((t["seg"], t["type"]) for t in te if t.get("type") in ("error_pointed", "error_resolved_by_tutor"))
    out, n = [], 0
    for p in pe:
        if p.get("type") == "self_correction":
            s = p["seg"]
            # the move on the same seg as the pupil's error can belong to it; moves on the pupil's own seg cannot
            last_err = max((e for e in errs if e < s), default=-1)
            last = next((m for m in reversed(moves) if last_err <= m[0] < s), None)
            if last and last[1] == "error_resolved_by_tutor":
                n += 1
                continue
            after = "error_pointed" if last else "none"
            if p.get("after") != after:
                p, n = dict(p, after=after), n + 1
        out.append(p)
    return out, n


# ------------------------------------------------------------------ gaps (process 07 steps 5–7, scoring-model §2)
CONF = ["low", "medium", "high"]
_WS = re.compile(r"\s+")


def _skill_key(a: dict[str, Any], ex_skill: dict[str, str]) -> str:
    """Group by the model's fine-grained skill words, NOT by node: a grade-10 node covers a
    whole chapter (eval 2026-11-17: lesson c1698fb7's five Opus gaps fell into one node)."""
    name = a.get("skill") or ex_skill.get(a.get("exercise_id", ""), "") or a.get("skill_node", "")
    return "txt:" + _WS.sub(" ", name.strip().lower())


def _down(c: str) -> str:
    return CONF[max(0, CONF.index(c) - 1)]


def _merge_by_error_pattern(groups: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Merge skill groups whose wrong/hinted attempts share an error_pattern (eval 2026-11-17, r5–r6).

    Luna names the topic of each exercise, so one mistake made in three topics became three narrow,
    low-confidence gaps where Opus has one high gap. The model tags the mistake; code decides the merge.
    The merged gap keeps the name of its largest group.
    """
    keys = list(groups)
    parent = {k: k for k in keys}

    def find(k: str) -> str:
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    owner: dict[str, str] = {}
    for k in keys:
        for a in groups[k]:
            pat = _WS.sub(" ", (a.get("error_pattern") or "").strip().lower())
            if not pat or a.get("label") not in ("wrong", "after_hint", "not_finished"):
                continue
            if pat in owner:
                parent[find(k)] = find(owner[pat])
            else:
                owner[pat] = k
    merged: dict[str, list[str]] = {}
    for k in keys:
        merged.setdefault(find(k), []).append(k)
    out: dict[str, list[dict]] = {}
    for members in merged.values():
        name = max(members, key=lambda m: (len(groups[m]), -keys.index(m)))
        out[name] = [a for m in members for a in groups[m]]
    return out


def gaps(ev: dict[str, Any]) -> dict[str, Any]:
    nodes = skill_map.by_id()
    ex_skill = {e["id"]: e.get("skill", "") for e in ev.get("exercises") or []}
    doubt_segs = {d.get("seg") for d in ev.get("doubts") or []}
    groups: dict[str, list[dict]] = {}
    for a in ev.get("attempts") or []:
        groups.setdefault(_skill_key(a, ex_skill), []).append(a)
    groups = _merge_by_error_pattern(groups)

    maths, shown_correct, slips = [], [], []
    for key, atts in groups.items():
        bad = [a for a in atts if a["label"] in ("wrong", "after_hint", "not_finished")]
        name = key[4:]
        node_ids = [a["skill_node"] for a in atts if a.get("skill_node") in nodes]
        node = max(set(node_ids), key=node_ids.count) if node_ids else ""
        if not bad:
            shown_correct.append({"skill": name, "node": node, "segs": [a["seg"] for a in atts]})
            continue
        wrong_or_hint = [a for a in bad if a["label"] in ("wrong", "after_hint")]
        problems = {a.get("exercise_id") or f"seg{a['seg']}" for a in wrong_or_hint}
        not_fixed = [a for a in bad if a["label"] == "wrong" and not a.get("fixed_alone_after_pointing")]
        is_slip = bool(wrong_or_hint) and all(a.get("fixed_alone_after_pointing") for a in wrong_or_hint if a["label"] == "wrong") \
            and len(problems) == 1
        if len(problems) >= 2:
            conf = "high"
        elif not_fixed or len(wrong_or_hint) >= 2:
            conf = "medium"
        else:
            conf = "low"  # a slip, a hint once, or not finished only
        if is_slip:
            conf = "low"
            slips += [a for a in wrong_or_hint if a["label"] == "wrong"]
        if any(a["seg"] in doubt_segs for a in bad):
            conf = _down(conf)
        alone = sum(1 for a in atts if a["label"] == "alone")
        level = "improving" if alone > len(bad) else "to_do"  # first seen today: never standard
        maths.append({
            "skill": name, "node": node, "type": "maths", "confidence": conf,
            "slip": is_slip, "level": level,
            "what_goes_wrong": next((a["what_went_wrong"] for a in bad if a.get("what_went_wrong")), ""),
            "attempts": [{"seg": a["seg"], "label": a["label"], "hint_seg": a.get("hint_seg") if a.get("hint_verified") else None,
                          "quote": a["quote"]} for a in sorted(atts, key=lambda a: a["seg"])],
            "_problems": len(problems), "_bad": len(bad),
            "_grade": nodes[node]["grade"] if node else 99,
        })
    # Rank: confidence, then distinct problems, then bad attempts, then lower grade first (audit 2026-11-16: no code-order ties).
    maths.sort(key=lambda g: (-CONF.index(g["confidence"]), -g["_problems"], -g["_bad"], g["_grade"], g["skill"]))

    habits: dict[str, list[dict]] = {}
    for h in ev.get("habits") or []:
        habits.setdefault(h["habit"], []).append(h)
    for a in slips:  # a slip is the pupil's own act showing no self-check (process 07 step 7)
        habits.setdefault("no_self_check", []).append({"seg": a["seg"], "quote": a["quote"], "speaker": "pupil",
                                                       "habit": "no_self_check", "about_earlier_lesson": False})
    learning = []
    for habit, items in habits.items():
        now = [h for h in items if not h.get("about_earlier_lesson")]
        n_inst = len({h["seg"] for h in now})
        own = any(h["speaker"] == "pupil" for h in now)
        if n_inst >= 3 and own:
            conf = "high"
        elif n_inst >= 2:
            conf = "medium"
        else:
            conf = "low"
        learning.append({"habit": habit, "type": "learning_skill", "confidence": conf, "instances": n_inst,
                         "evidence": [{"seg": h["seg"], "speaker": h["speaker"], "quote": h["quote"]} for h in items]})
    learning.sort(key=lambda g: (-CONF.index(g["confidence"]), -g["instances"], g["habit"]))
    for g in maths:
        for k in ("_problems", "_bad", "_grade"):
            g.pop(k)
    return {"maths": maths, "learning_skills": learning, "shown_correct": shown_correct,
            "doubts": ev.get("doubts") or []}


# ------------------------------------------------------------------ tutor standard (port of score_v2.py)
_WORD = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)
_TAG = re.compile(r"\[[^\]]{0,20}\]")
PRODUCTIVE = {"HW_CHECK", "RECALL", "INSTRUCT", "GUIDED", "INDEPENDENT", "FEEDBACK"}


def _band(v, met, near):
    return None if v is None else ("met" if v >= met else ("near" if v >= near else "below"))


def tutor_behaviours(ev: dict[str, Any], segments: list[dict[str, Any]]) -> dict[str, Any]:
    """Same formulas and bands as toptutor-main score_v2.py (tutor-standard.md, reference bands)."""
    n = len(segments)
    prod = set()
    for b in ev.get("blocks") or []:
        if b.get("type") in PRODUCTIVE:
            prod.update(range(max(0, b["start_seg"]), min(n - 1, b["end_seg"]) + 1))
    prod = prod or set(range(n))
    ack = set(ev.get("ack_segments") or [])
    tw = sw = 0
    for i in prod:
        w = len(_WORD.findall(_TAG.sub(" ", segments[i].get("text") or "")))
        if segments[i].get("speaker") == "tutor":
            tw += w
        elif segments[i].get("speaker") == "student" and i not in ack:
            sw += w
    talk = sw / (tw + sw) if tw + sw else None
    te, pe = ev.get("tutor_events") or [], ev.get("pupil_events") or []
    ex = ev.get("exercises") or []
    ex_ids = {x["id"] for x in ex}
    hours = max((segments[-1]["start"] - segments[0]["start"]) / 3600, 0.25) if n > 1 else 1
    cnt = lambda t: sum(1 for e in te if e.get("type") == t)  # noqa: E731
    newc = [x for x in ex if x.get("kind") == "new_concept"] or ex
    tries = sum(1 for x in newc if x.get("first_actor") == "pupil") / len(newc) if newc else None
    tells, opens = (cnt("self_answered") + cnt("gives_answer")) / hours, cnt("question_open") / hours
    expl = {p.get("exercise_id") for p in pe if p.get("type") == "response" and p.get("skill") == "explains"
            and p.get("quality") in ("full", "partial") and p.get("exercise_id") in ex_ids}
    errs = [p for p in pe if p.get("type") == "error"]
    fixed = [p for p in pe if p.get("type") == "self_correction" and p.get("after") == "error_pointed"]
    hw = [e for e in te if e.get("type") == "homework_checked"]
    ch = {e.get("exercise_id") for e in te if e.get("type") == "chance" and e.get("exercise_id") in ex_ids}
    values = {"1_talk_share": talk, "2_tries_first": tries, "4_tells_per_h": tells, "4_open_per_h": opens,
              "5_explains": len(expl) / len(ex) if ex else None,
              "6_errors_found": min(1.0, len(fixed) / len(errs)) if errs else None,
              "10_chances": len(ch) / len(ex) if ex else None, "n_exercises": len(ex), "n_errors": len(errs)}
    bands = {
        "1": _band(talk, 0.40, 0.25), "2": _band(tries, 0.70, 0.35), "3": None,
        "4": "met" if tells <= 5 and opens >= 10 else ("near" if tells <= 5 or opens >= 10 else "below"),
        "5": _band(values["5_explains"], 0.5, 0.25), "6": _band(values["6_errors_found"], 0.6, 0.3),
        # no occasion (first lesson with the pupil, or nothing set last time) drops out (tutor-standard.md)
        "7": ("met" if any(e.get("how") == "pupil_fixes" for e in hw) else "near") if hw
        else (None if ev.get("homework_occasion") == "no" else "below"),
        "8": "met" if cnt("wrapup_by_pupil_prompt") else ("near" if cnt("wrapup_by_tutor") else "below"),
        "9": "below" if cnt("criticism_person") else ("met" if cnt("praise_process") else "near"),
        "10": _band(values["10_chances"], 0.5, 0.25),
    }
    return {"values": values, "bands": bands}


async def run(client, *, model: str, segments: list[dict[str, Any]], grade: Optional[int],
              reasoning_effort: Optional[str] = "high") -> dict[str, Any]:
    raw = await label(client, model=model, segments=segments, grade=grade, reasoning_effort=reasoning_effort)
    ev = check(raw, segments)
    return {"version": VERSION, "model": model, "evidence": ev, "gaps": gaps(ev),
            "tutor_standard": tutor_behaviours(ev, segments)}
