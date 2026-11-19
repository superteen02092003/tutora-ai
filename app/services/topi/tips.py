"""B7 — gợi ý cho gia sư (trang T13 "For you").

Mỗi gợi ý trỏ về một khoảnh khắc thật (seg + quote, kiểm bằng code). Tỉ lệ học sinh nói
do code tính; "talk_more" chỉ khi dưới 15%. Kế hoạch thói quen khi có từ 2 lỗi
tính toán/sơ ý (HABIT-MISS, 2026-11-18; careless-calculation-errors.md). Cách gọi học sinh
theo lớp: "bé" đến lớp 5, "em" từ lớp 6 (ADDRESS-BE, 2026-11-18).
"""
import json
from typing import Any, Optional

from .checker import check_labels
from .llm import generate_json
from .report import evidence_items

TALK_SHARE_MIN = 0.15
HABIT_MIN_SLIPS = 2
SLIP_TYPES = {"calculation", "slip", "sign_or_bracket"}

SYSTEM = """Bạn viết gợi ý ngắn cho gia sư sau buổi học toán, từ danh sách bằng chứng đã kiểm. Mỗi gợi ý nêu MỘT cách làm cụ thể và trỏ về một khoảnh khắc thật.

Trả JSON:
{"did_well": {"text": "", "seg": 0, "quote": ""},
 "try_next": {"text": "", "seg": 0, "quote": ""},
 "talk_more": {"text": "", "seg": null, "quote": ""},
 "habit": {"cause": "rushing|overload|anxiety|no_routine", "plan": "", "seg": 0, "quote": ""}}

{ADDRESS}

QUY TẮC:
- quote là nguyên văn lấy từ bằng chứng (trường quote), seg đúng như bằng chứng đó.
- did_well: một việc bạn (gia sư) làm tốt (vd "Bạn chỉ ra dòng sai rồi để {P} tự sửa.").
- try_next: một việc bạn nên thử lần sau, kèm câu nói mẫu (vd "Lần sau, bạn hỏi {P}: \"Em sẽ bắt đầu thế nào?\" thay vì làm mẫu bước đầu.").
- talk_more và habit chỉ viết khi được yêu cầu trong đầu vào; nếu không thì để null.
- habit.plan: 3 lựa chọn ngắn: tìm lỗi trong bài giải sai; đoán - giải - kiểm lại bằng cách thay số; danh sách 2–3 lỗi riêng của {P}. Không viết "cẩn thận".
- Tiếng Việt, mỗi text 1–2 câu. Không markdown."""


def pupil_word(grade: Optional[int]) -> str:
    """Cách gọi học sinh trong text cho gia sư: "bé" đến lớp 5, "em" từ lớp 6 hoặc khi không rõ lớp."""
    return "bé" if isinstance(grade, int) and grade <= 5 else "em"


def address_rule(grade: Optional[int]) -> str:
    p = pupil_word(grade)
    banned = '"thầy", "cô", "anh", "chị", "con", "học sinh"' + (', "em"' if p == "bé" else ', "bé"')
    return (f'XƯNG HÔ: text viết cho gia sư đọc. Gọi gia sư là "bạn", gọi học sinh là "{p}". '
            f'Vd: "Bạn cần chỉ cho {p} dòng sai rồi để {p} tự sửa." Không dùng {banned} hay tên riêng để chỉ gia sư '
            'hoặc học sinh. Riêng câu nói mẫu trong ngoặc kép (lời gia sư nói với học sinh) thì xưng "em" như trong buổi học.')


def system_for(grade: Optional[int]) -> str:
    return SYSTEM.replace("{ADDRESS}", address_rule(grade)).replace("{P}", pupil_word(grade))


def talk_share(segments: list[dict[str, Any]]) -> float:
    words = {"tutor": 0, "student": 0}
    for s in segments:
        if s.get("speaker") in words:
            words[s["speaker"]] += len((s.get("text") or "").split())
    total = words["tutor"] + words["student"]
    return words["student"] / total if total else 0.0


async def write(client, *, model: str, evidence: dict[str, Any], segments: list[dict[str, Any]],
                grade: Optional[int] = None) -> dict[str, Any]:
    share = talk_share(segments)
    slips = [e for e in evidence.get("pupil_events") or [] if e.get("type") == "error" and e.get("error_type") in SLIP_TYPES]
    want = {"talk_more": share < TALK_SHARE_MIN, "habit": len(slips) >= HABIT_MIN_SLIPS}
    raw = await generate_json(client, model=model, feature="topi_tips", system=system_for(grade), temperature=0.3,
                              prompt=json.dumps({"want": want, "pupil_talk_share": round(share, 2),
                                                 "evidence": evidence_items(evidence)}, ensure_ascii=False))
    out: dict[str, Any] = {"pupil_talk_share": round(share, 3)}
    for key in ("did_well", "try_next", "habit"):
        tip = raw.get(key)
        if not isinstance(tip, dict) or (key == "habit" and not want["habit"]):
            out[key] = None
            continue
        kept, _, _ = check_labels([tip], segments, kind=key, expected_speaker=None)
        out[key] = kept[0] if kept else None
    tm = raw.get("talk_more")
    out["talk_more"] = {"text": tm.get("text", ""), "seg": None, "quote": None} if want["talk_more"] and isinstance(tm, dict) else None
    return out
