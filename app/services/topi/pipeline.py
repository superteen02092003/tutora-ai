"""Topi v1 — một lần chạy sau buổi học: bằng chứng -> kiểm -> 4 đầu ra.

Báo cáo, kế hoạch, gợi ý chạy song song sau bước bằng chứng; kỹ năng là code thuần.
Một đầu ra lỗi không làm hỏng các đầu ra khác (ghi vào `errors`).
"""
import asyncio
import logging
from typing import Any

from ...models.topi import TopiRunRequest, TopiRunResponse
from . import checker, evidence as evidence_mod, levels, plan as plan_mod, report as report_mod, tips as tips_mod

logger = logging.getLogger(__name__)

VERSION = "topi-v1.0"


async def run(client, req: TopiRunRequest, *, evidence_model: str, write_model: str) -> TopiRunResponse:
    segments = [s.model_dump() for s in req.transcript.segments]
    resp = TopiRunResponse(lesson_id=req.lesson_id, version=VERSION,
                           models={"evidence": evidence_model, "write": write_model})
    raw = await evidence_mod.extract(client, model=evidence_model, segments=segments, grade=req.grade)
    ev = checker.check_evidence(raw, segments)
    resp.evidence = ev

    states = [s.model_dump() for s in req.skill_states]
    tasks: dict[str, Any] = {}
    if "report" in req.outputs:
        tasks["report"] = report_mod.write(client, model=write_model, evidence=ev,
                                           duration_sec=req.duration_sec, booked_min=req.booked_min)
    if "plan" in req.outputs:
        tasks["plan"] = plan_mod.build(client, model=write_model, evidence=ev, states=states, grade=req.grade,
                                       last_homework=req.last_homework.quote if req.last_homework else None)
    if "tips" in req.outputs:
        tasks["tips"] = tips_mod.write(client, model=write_model, evidence=ev, segments=segments)
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for name, result in zip(tasks, results):
        if isinstance(result, Exception):
            logger.exception("topi %s thất bại (lesson=%s)", name, req.lesson_id, exc_info=result)
            resp.errors[name] = f"{type(result).__name__}: {str(result)[:200]}"
        else:
            setattr(resp, name, result)
    if "skills" in req.outputs:
        try:
            resp.skills = levels.apply(ev, states, req.lesson_date)
        except Exception as e:  # pragma: no cover - code thuần, chỉ phòng hờ
            resp.errors["skills"] = f"{type(e).__name__}: {e}"
    return resp
