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
    errors: dict[str, list[dict]] = {}
    for ev in evidence.get("pupil_events") or []:
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

    gap_nodes = {n for n in candidates if state.get(n, {}).get("level", "to_do") in ("to_do", "improving")}
    rows = []
    for n in candidates:
        if n not in gap_nodes and n not in errors:
            continue
        basics_ok = not any(p in gap_nodes for p in nodes[n].get("needs", []))
        last = (errors.get(n) or [{}])[-1]
        wrong, right = (last.get("wrong") or ""), (last.get("right") or "")
        if mathcheck.identity_holds(right) is not True or mathcheck.identity_holds(wrong) is not False:
            wrong, right = "", ""  # không chứng minh được bằng SymPy -> không hiện
        rows.append({"node": n, "title": nodes[n]["name_vi"], "wrong": wrong, "right": right,
                     "seen_in_lessons": seen(n), "basics_ok": basics_ok,
                     "level": state.get(n, {}).get("level", "to_do"), "quote": last.get("quote", ""), "seg": last.get("seg")})
    rows.sort(key=lambda r: (not r["basics_ok"], -r["seen_in_lessons"], r["node"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["role"] = "watch" if r["seen_in_lessons"] <= 1 else ("focus" if i == 0 else "next")
    if rows and rows[0]["role"] == "watch":
        rows[0]["role"] = "focus"
    return rows


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
    topics = [ex.get("quote", "") for ex in (evidence.get("exercises") or [])][:8]
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
