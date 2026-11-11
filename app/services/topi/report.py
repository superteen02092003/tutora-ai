"""B3 — báo cáo phụ huynh viết CHỈ từ bằng chứng đã kiểm (session-report v4, lần gọi 2).

Dòng thời lượng do code tính ("86 of 90 min"), mô hình không viết. Mỗi câu ghi `cites`
(id bằng chứng); code loại cite không tồn tại.
"""
import json
from typing import Any, Optional

from .llm import generate_json

SYSTEM = """Bạn là trợ lý của gia sư TopTutor. Đầu vào là DANH SÁCH BẰNG CHỨNG đã kiểm của một buổi học toán 1 kèm 1 (bài tập, sự kiện của gia sư và học sinh, câu giao bài về nhà). Viết báo cáo CHỈ từ danh sách này. Không thêm điều gì không có trong danh sách.

QUY TẮC:
- Không chép đề bài; viết cụ thể dạng bài đã học. Không nhắc buổi trước. Không khẳng định tiến bộ dài hạn. Không thông tin nhạy cảm. Không viết tắt. Gọi "con" khi viết cho phụ huynh. Không dùng từ chỉ giới tính.
- Mỗi trường có mảng "cites" gồm id bằng chứng làm căn cứ (vd "X1", "P3", "T5", "hw").
- homework: nếu có "hw" thì nêu đúng nội dung câu giao bài; nếu không có thì ghi đúng "Không có bài tập về nhà."
- tutor_notes là BẢN NHÁP để gia sư sửa: một điều con làm tốt và một điều con cần luyện tiếp, từ bằng chứng. Không có căn cứ thì ghi đúng "Không có nhận xét thêm."
- Không viết dòng thời lượng, không viết chân trang: hệ thống tự thêm.
- zalo: ba trường content, homework, notes; mỗi trường 1–2 câu hoàn chỉnh, 100–160 ký tự, không quá 180; văn bản thuần, không markdown, không ký hiệu toán, không emoji, không xuống dòng.

Schema: {"lesson_content": {"text": "", "cites": []}, "homework": {"text": "", "cites": []}, "tutor_notes": {"text": "", "cites": []}, "zalo": {"content": "", "homework": "", "notes": ""}}"""


def evidence_items(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Đánh id ổn định: X* bài tập, T* sự kiện gia sư, P* sự kiện học sinh, hw câu giao bài."""
    items = [dict(ex, id=ex.get("id") or f"X{i+1}") for i, ex in enumerate(evidence.get("exercises") or [])]
    items += [dict(ev, id=f"T{i+1}") for i, ev in enumerate(evidence.get("tutor_events") or [])]
    items += [dict(ev, id=f"P{i+1}") for i, ev in enumerate(evidence.get("pupil_events") or [])]
    hw = evidence.get("homework_set") or {}
    if hw.get("quote"):
        items.append({"id": "hw", "type": "homework_given", "seg": hw.get("seg"), "quote": hw["quote"]})
    return items


def quality_line(duration_sec: Optional[int], booked_min: Optional[int]) -> Optional[str]:
    if not duration_sec:
        return None
    mins = round(duration_sec / 60)
    return f"{mins} of {booked_min} min" if booked_min else f"{mins} min"


async def write(client, *, model: str, evidence: dict[str, Any], duration_sec: Optional[int],
                booked_min: Optional[int]) -> dict[str, Any]:
    items = evidence_items(evidence)
    raw = await generate_json(client, model=model, feature="topi_report", system=SYSTEM,
                              prompt="Bằng chứng:\n" + json.dumps(items, ensure_ascii=False), temperature=0.3)
    ids = {it["id"] for it in items}
    for key in ("lesson_content", "homework", "tutor_notes"):
        part = raw.get(key) if isinstance(raw.get(key), dict) else {"text": str(raw.get(key) or ""), "cites": []}
        part["cites"] = [c for c in part.get("cites") or [] if c in ids]
        raw[key] = part
    if not evidence.get("homework_set", {}).get("quote"):
        raw["homework"] = {"text": "Không có bài tập về nhà.", "cites": []}
    raw["quality_line"] = quality_line(duration_sec, booked_min)
    return raw
