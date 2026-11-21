"""B6 — kế hoạch 15 phút đầu buổi sau (trang T9 "Before the lesson").

Thứ tự lỗ hổng do CODE xếp (tất định); mô hình chỉ viết câu hỏi và bài; mọi đáp án được
SymPy kiểm, câu nào sai bị bỏ. Bốn bước cố định: Check, Homework, Memory, Warm-up.
"""
import json
from typing import Any, Optional

from . import mathcheck, skill_map
from .checker import homework_tasks_of
from .llm import generate_json

STEP_MINUTES = {"check": 3, "homework": 5, "memory": 3, "warmup": 4}
MAX_TASKS = 40  # chặn prompt quá dài ở buổi rất nhiều bài; trích dẫn bài thường < 60 ký tự

SYSTEM = """Bạn soạn 15 phút đầu buổi học toán cho gia sư. Đầu vào: lỗ hổng trọng tâm (nút kỹ năng, lỗi sai, cách đúng), nội dung buổi vừa học, lớp.

Trả JSON:
{"check": [{"say": "câu gia sư nói, bắt đầu bằng 'Hỏi:'", "problem": "biểu thức SymPy", "answer": "biểu thức SymPy"}],
 "memory": [{"say": "...", "problem": "...", "answer": "..."}],
 "warmup": [{"say": "...", "problem": "...", "answer": "..."}]}

QUY TẮC:
- check: ĐÚNG 2 bài MỚI cho lỗ hổng trọng tâm, khác bài trong buổi vừa rồi, vừa sức lớp đó. Học sinh tự làm, không gợi ý.
- memory: 1–2 câu nhắc lại kiến thức buổi vừa học, gấp vở.
- warmup: ĐÚNG 1 bài ngắn trộn dạng, làm trong 4 phút.
- "say" là tiếng Việt, ngắn, bắt đầu bằng "Hỏi:". Mỗi câu hỏi một bài, không gộp bằng dấu phẩy.
- problem/answer viết bằng cú pháp SymPy: nhân dùng *, luỹ thừa dùng **, biến là chữ thường. Biểu thức thì answer là dạng rút gọn; phương trình "lhs = rhs" thì answer dạng "x = 3".
- Xưng hô: gọi gia sư là "bạn", học sinh là "bé" trong lời dặn gia sư; lời gia sư nói với bé (sau "Hỏi:") xưng "em". Không dùng "thầy", "cô", "con", "học sinh" hay tên riêng.
- Không markdown."""


def rank_gaps(evidence: dict[str, Any], states: list[dict[str, Any]],
              raised: frozenset[str] | set[str] = frozenset()) -> list[dict[str, Any]]:
    """Lỗ hổng = kỹ năng có bằng chứng sai: lỗi trong buổi này, đã sai ở buổi trước,
    hoặc đang ở mức to_do. Kỹ năng "improving" chưa từng sai không phải lỗ hổng: nó
    chỉ chưa đủ buổi để lên standard (luật buổi đầu). `raised`: nút vừa lên standard
    hoặc mastered ở chính buổi này, không đưa vào kế hoạch.

    Buổi 28/10 (học sinh lớp 10): 15 kỹ năng ôn lớp 3–8, 0 lần sai, từng làm danh
    sách "Cần luyện tập" tăng từ 5 lên 22."""
    nodes = skill_map.by_id()
    events = evidence.get("pupil_events") or []
    fixes = [e.get("seg") for e in events
             if e.get("type") == "self_correction" and isinstance(e.get("seg"), int)]
    errors: dict[str, list[dict]] = {}
    for ev in events:
        if ev.get("type") == "error" and ev.get("skill_node") in nodes:
            errors.setdefault(ev["skill_node"], []).append(ev)
    state = {s["node"]: s for s in states}

    def past_wrong(node: str) -> int:
        return len({o.get("lesson_date") for o in (state.get(node, {}).get("observations") or [])
                    if o.get("outcome") == "wrong"})

    def seen(node: str) -> int:
        return past_wrong(node) + (1 if node in errors else 0)

    candidates = set(errors) | {
        n for n, s in state.items() if n in nodes and (
            s.get("level") == "to_do" or (s.get("level") == "improving" and past_wrong(n) > 0))}
    candidates -= set(raised)

    def fixed_alone(ev: dict) -> bool:
        # Bé tự sửa ngay (hoặc sửa được khi gia sư vừa chỉ ra) trong 2 đoạn sau lỗi.
        s = ev.get("seg")
        return isinstance(s, int) and any(s <= f <= s + 2 for f in fixes)

    gap_nodes = {n for n in candidates if state.get(n, {}).get("level", "to_do") in ("to_do", "improving")}
    rows = []
    for n in candidates:
        if n not in gap_nodes and n not in errors:
            continue
        basics_ok = not any(p in gap_nodes for p in nodes[n].get("needs", []))
        now = errors.get(n) or []
        last = (now or [{}])[-1]
        wrong, right = (last.get("wrong") or ""), (last.get("right") or "")
        if mathcheck.identity_holds(right) is not True or mathcheck.identity_holds(wrong) is not False:
            wrong, right = "", ""  # không chứng minh được bằng SymPy -> không hiện
        problems_now = len({e.get("exercise_id") or f"seg{e.get('seg')}" for e in now})
        concept = any(e.get("error_type") in CONCEPT_ERRORS for e in now)
        rows.append({"node": n, "title": nodes[n]["name_vi"], "wrong": wrong, "right": right,
                     "seen_in_lessons": seen(n), "basics_ok": basics_ok,
                     "level": state.get(n, {}).get("level", "to_do"), "quote": last.get("quote", ""), "seg": last.get("seg"),
                     "confidence": _confidence(now, past_wrong(n), fixed_alone),
                     "errors_now": problems_now, "concept": concept})
    rows.sort(key=lambda r: (not r["basics_ok"], -CONFIDENCE_ORDER[r["confidence"]], not r["right"],
                             not r["concept"], -r["errors_now"], -r["seen_in_lessons"], r["node"]))
    focus_taken = False
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        if r["confidence"] == "low":
            r["role"] = "watch"  # lỗi một lần / tự sửa: chỉ theo dõi, không bao giờ thành trọng tâm
        elif not focus_taken and (r["right"] or r["confidence"] == "high"):
            r["role"] = "focus"
            focus_taken = True
        else:
            r["role"] = "next"
    return rows


# Lỗi hiểu sai (khái niệm, cách làm) xếp trên lỗi sơ suất khi cùng độ tin cậy.
CONCEPT_ERRORS = frozenset({"concept", "method"})
CONFIDENCE_ORDER = {"high": 2, "medium": 1, "low": 0}


def _confidence(now: list[dict[str, Any]], past_wrong: int, fixed_alone) -> str:
    """Độ tin cậy của một lỗ hổng kỹ năng toán (07 scoring-model, mục 2):
    high   = sai ở ≥ 2 bài khác nhau trong buổi, hoặc sai ở buổi này và một buổi trước;
             hoặc đã sai ở ≥ 2 buổi trước;
    medium = 1 lần sai bé không tự sửa được, cùng lỗi hai lần trong một bài, hoặc sai ở đúng một buổi trước;
    low    = 1 lỗi bé tự sửa (watch), hoặc không có lần sai nào."""
    real = [e for e in now if not fixed_alone(e)]
    problems = {e.get("exercise_id") or f"seg{e.get('seg')}" for e in now}
    if len(problems) >= 2 or (now and past_wrong >= 1) or past_wrong >= 2:
        return "high"
    if real or len(now) >= 2 or past_wrong == 1:
        return "medium"
    return "low"


def _verified(asks: Any) -> list[dict[str, Any]]:
    out = []
    for a in asks if isinstance(asks, list) else []:
        ok = mathcheck.verify(a.get("problem"), a.get("answer"))
        if ok:
            out.append({"say": a.get("say", ""), "problem": a["problem"], "answer": a["answer"], "verified": True})
    return out


async def build(client, *, model: str, evidence: dict[str, Any], states: list[dict[str, Any]],
                grade: Optional[int], last_homework: Optional[str],
                raised: frozenset[str] | set[str] = frozenset()) -> dict[str, Any]:
    gaps = rank_gaps(evidence, states, raised)
    focus = next((g for g in gaps if g["role"] == "focus"), None)
    # Mọi bài trong buổi, không chỉ 8 bài đầu (L3: 21 bài, dạng cuối buổi bị bỏ); bỏ trùng.
    topics = list(dict.fromkeys(q for ex in (evidence.get("exercises") or []) if (q := ex.get("quote"))))[:MAX_TASKS]
    steps: list[dict[str, Any]] = []
    warnings: list[str] = []
    if focus:
        raw = await generate_json(client, model=model, feature="topi_plan", system=SYSTEM, temperature=0.4,
                                  prompt=json.dumps({"grade": grade, "focus": focus, "lesson_tasks": topics}, ensure_ascii=False))
        check, memory, warmup = _verified(raw.get("check")), _verified(raw.get("memory")), _verified(raw.get("warmup"))
        if len(check) < 2:
            warnings.append("check_incomplete")
        steps.append({"name": "check", "minutes": STEP_MINUTES["check"], "asks": check[:2]})
    else:
        memory, warmup = [], []
    tasks = homework_tasks_of(evidence)
    hw = "; ".join(t["quote"] for t in tasks) or last_homework or ""
    pupil = "bé" if isinstance(grade, int) and grade <= 5 else "em"
    steps.append({"name": "homework", "minutes": STEP_MINUTES["homework"],
                  "asks": [{"say": f"Chữa những bài về nhà {pupil} làm sai.", "problem": None, "answer": None,
                            "verified": None, "homework_quote": hw}] if hw else []})
    steps.append({"name": "memory", "minutes": STEP_MINUTES["memory"], "asks": memory[:2]})
    steps.append({"name": "warmup", "minutes": STEP_MINUTES["warmup"], "asks": warmup[:1]})
    return {"gaps": gaps, "steps": steps, "warnings": warnings}
