"""Topi v1 — POST /api/v1/topi/run (backend gọi sau khi lưu transcript).

Server-to-server qua X-API-Key (middleware chung). Hợp đồng:
toptutor-main/60-output/specs/topi-api-contract.md
"""
import logging

from fastapi import APIRouter, Depends, HTTPException

from ..core.config import get_settings
from ..core.dependencies import get_gemini_client
from ..models.topi import TopiRunRequest, TopiRunResponse
from ..services.topi import pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/topi")


@router.post("/run", response_model=TopiRunResponse)
async def run(body: TopiRunRequest, gemini=Depends(get_gemini_client)) -> TopiRunResponse:
    if not body.transcript.segments:
        raise HTTPException(status_code=400, detail="Transcript không có đoạn nào")
    s = get_settings()
    try:
        return await pipeline.run(gemini, body, evidence_model=s.topi_evidence_model, write_model=s.topi_write_model)
    except Exception as e:
        logger.exception("topi/run thất bại (lesson=%s)", body.lesson_id)
        raise HTTPException(status_code=502, detail=f"Topi thất bại ở bước bằng chứng: {e}")
