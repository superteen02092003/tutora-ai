"""B3 — báo cáo phụ huynh viết CHỈ từ bằng chứng đã kiểm (session-report v4, lần gọi 2).

Dòng thời lượng do code tính ("86/90 phút"), mô hình không viết. Mỗi câu ghi `cites`
(id bằng chứng); code loại cite không tồn tại.

Bài về nhà (findings HW-ONE, HW-NONE, ZALO-DUE, ZALO-LEN của toptutor-main, 2026-11-18):
mỗi bài là một id hw1, hw2…; code chặn báo cáo bỏ sót bài hoặc hạn nộp (gọi lại một lần,
rồi tự ghép từ danh sách bài); không nghe thấy bài về nhà thì KHÔNG nói "không có bài tập",
mà nói chưa ghi nhận. Mỗi trường Zalo 100–160 ký tự, code không để quá 200.
"""
import json
from typing import Any, Optional

from .checker import homework_tasks_of, normalise
from .llm import generate_json

# Không nghe thấy câu giao bài: không khẳng định là không có bài (HW-NONE).
NO_HW = "Bản ghi chưa ghi nhận bài tập về nhà; phụ huynh hỏi gia sư nếu cần."
ZALO_TARGET, ZALO_MAX = 160, 200

SYSTEM = """Bạn là trợ lý của gia sư TopTutor. Đầu vào là DANH SÁCH BẰNG CHỨNG đã kiểm của một buổi học toán 1 kèm 1 (bài tập, sự kiện của gia sư và học sinh, câu giao bài về nhà). Viết báo cáo CHỈ từ danh sách này. Không thêm điều gì không có trong danh sách.

QUY TẮC:
- Không chép đề bài; viết cụ thể dạng bài đã học. Không nhắc buổi trước. Không khẳng định tiến bộ dài hạn. Không thông tin nhạy cảm. Không viết tắt. Gọi "con" khi viết cho phụ huynh. Không dùng từ chỉ giới tính.
- Mỗi trường có mảng "cites" gồm id bằng chứng làm căn cứ (vd "X1", "P3", "T5", "hw").
- homework: nêu MỌI bài về nhà (mọi id hw1, hw2, …) và hạn nộp của bài nào có hạn (trường "due"), cites gồm MỌI id hw. Nếu danh sách không có id hw nào thì ghi đúng "{NO_HW}"
- tutor_notes là BẢN NHÁP để gia sư sửa: một điều con làm tốt và một điều con cần luyện tiếp, từ bằng chứng. Không có căn cứ thì ghi đúng "Không có nhận xét thêm."
- Không viết dòng thời lượng, không viết chân trang: hệ thống tự thêm.
- zalo: ba trường content, homework, notes; mỗi trường 1–2 câu hoàn chỉnh, 100–160 ký tự, không bao giờ quá 160; văn bản thuần, không markdown, không ký hiệu toán, không emoji, không xuống dòng. zalo.homework giữ MỌI hạn nộp.

Schema: {"lesson_content": {"text": "", "cites": []}, "homework": {"text": "", "cites": []}, "tutor_notes": {"text": "", "cites": []}, "zalo": {"content": "", "homework": "", "notes": ""}}"""


def evidence_items(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Đánh id ổn định: X* bài tập, T* sự kiện gia sư, P* sự kiện học sinh, hw câu giao bài."""
    items = [dict(ex, id=ex.get("id") or f"X{i+1}") for i, ex in enumerate(evidence.get("exercises") or [])]
    items += [dict(ev, id=f"T{i+1}") for i, ev in enumerate(evidence.get("tutor_events") or [])]
    items += [dict(ev, id=f"P{i+1}") for i, ev in enumerate(evidence.get("pupil_events") or [])]
    for i, t in enumerate(homework_tasks_of(evidence)):
        items.append({"id": f"hw{i+1}", "type": "homework_given", "seg": t.get("seg"), "quote": t.get("quote"),
                      "task": t.get("task"), "due": t.get("due")})
    return items


def quality_line(duration_sec: Optional[int], booked_min: Optional[int]) -> Optional[str]:
    if not duration_sec:
        return None
    mins = round(duration_sec / 60)
    return f"{mins}/{booked_min} phút" if booked_min else f"{mins} phút"


def _clean(raw: dict[str, Any], ids: set[str]) -> dict[str, Any]:
    raw = dict(raw)  # never change the model's answer in place
    for key in ("lesson_content", "homework", "tutor_notes"):
        part = dict(raw[key]) if isinstance(raw.get(key), dict) else {"text": str(raw.get(key) or ""), "cites": []}
        part["cites"] = [c for c in part.get("cites") or [] if c in ids]
        raw[key] = part
    zalo = raw.get("zalo") if isinstance(raw.get("zalo"), dict) else {}
    raw["zalo"] = {k: " ".join(str(zalo.get(k) or "").split()) for k in ("content", "homework", "notes")}
    return raw


def problems(raw: dict[str, Any], tasks: list[dict[str, Any]]) -> list[str]:
    """Những lỗi code bắt được trong một bản báo cáo; rỗng = qua."""
    out: list[str] = []
    hw_ids = [f"hw{i+1}" for i in range(len(tasks))]
    cited = set(raw["homework"].get("cites") or [])
    missing = [h for h in hw_ids if h not in cited]
    if missing:
        out.append("homework thiếu bài " + ", ".join(missing))
    for i, t in enumerate(tasks):
        due = t.get("due")
        if not due:
            continue
        if normalise(due) not in normalise(raw["homework"].get("text", "")):
            out.append(f"homework thiếu hạn nộp của hw{i+1} ({due})")
        if normalise(due) not in normalise(raw["zalo"].get("homework", "")):
            out.append(f"zalo.homework thiếu hạn nộp của hw{i+1} ({due})")
    for k, v in raw["zalo"].items():
        if len(v) > ZALO_TARGET:
            out.append(f"zalo.{k} dài {len(v)} ký tự, tối đa {ZALO_TARGET}")
    return out


def homework_from_tasks(tasks: list[dict[str, Any]]) -> str:
    """Câu bài về nhà ghép bằng code khi mô hình hai lần bỏ sót bài hoặc hạn."""
    parts = [t["task"] + (f" (hạn {t['due']})" if t.get("due") else "") for t in tasks]
    return "Bài về nhà: " + "; ".join(parts) + "."


def shorten(text: str, limit: int = ZALO_MAX) -> str:
    """Cắt ở cuối câu gần nhất trong giới hạn; không có thì ở khoảng trắng, thêm "…"."""
    if len(text) <= limit:
        return text
    head = text[:limit]
    end = max(head.rfind(". "), head.rfind("! "), head.rfind("? "))
    if end >= limit // 2:
        return head[: end + 1]
    return head[: head.rfind(" ", 0, limit - 1)].rstrip(" ,;") + "…"


async def write(client, *, model: str, evidence: dict[str, Any], duration_sec: Optional[int],
                booked_min: Optional[int]) -> dict[str, Any]:
    items = evidence_items(evidence)
    tasks = homework_tasks_of(evidence)
    ids = {it["id"] for it in items}
    system = SYSTEM.replace("{NO_HW}", NO_HW)
    prompt = "Bằng chứng:\n" + json.dumps(items, ensure_ascii=False)
    raw = _clean(await generate_json(client, model=model, feature="topi_report", system=system,
                                     prompt=prompt, temperature=0.3), ids)
    found = problems(raw, tasks)
    check = "ok"
    if found:
        # Gọi lại một lần, nêu đúng lỗi.
        retry = prompt + "\n\nBản trước bị chặn vì: " + "; ".join(found) + ". Viết lại, sửa đúng các lỗi này."
        raw = _clean(await generate_json(client, model=model, feature="topi_report", system=system,
                                         prompt=retry, temperature=0.2), ids)
        found = problems(raw, tasks)
        check = "retried"
    if tasks and any("homework" in f for f in found):
        # Lần hai vẫn sót: ghép từ danh sách bài đã kiểm, không để phụ huynh thiếu bài.
        text = homework_from_tasks(tasks)
        raw["homework"] = {"text": text, "cites": [f"hw{i+1}" for i in range(len(tasks))]}
        raw["zalo"]["homework"] = shorten(text)
        check = "composed"
    if not tasks:
        raw["homework"] = {"text": NO_HW, "cites": []}
        raw["zalo"]["homework"] = NO_HW
    raw["zalo"] = {k: shorten(v) for k, v in raw["zalo"].items()}
    raw["homework_check"] = check
    raw["quality_line"] = quality_line(duration_sec, booked_min)
    return raw
