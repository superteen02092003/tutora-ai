"""Topi v1 — schema cho POST /api/v1/topi/run.

Hợp đồng: toptutor-main/60-output/specs/topi-api-contract.md. Đổi tên field thì sửa
hợp đồng trước.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Speaker = Literal["tutor", "student", "unknown"]
Level = Literal["to_do", "improving", "standard", "mastered"]
Outcome = Literal["alone", "hint", "wrong"]


class Segment(BaseModel):
    start: float = 0.0
    speaker: str = "unknown"
    text: str = ""


class Transcript(BaseModel):
    segments: list[Segment] = Field(default_factory=list)


class Observation(BaseModel):
    lesson_date: str
    outcome: Outcome
    exercise_id: Optional[str] = None


class SkillState(BaseModel):
    node: str
    level: Level
    first_seen: Optional[str] = None
    last_change: Optional[str] = None
    standard_since: Optional[str] = None
    observations: list[Observation] = Field(default_factory=list)


class LastHomework(BaseModel):
    quote: str = ""


class TopiRunRequest(BaseModel):
    lesson_id: str
    student_id: Optional[str] = None
    lesson_date: str
    grade: Optional[int] = None
    subject: str = "math"
    duration_sec: Optional[int] = None
    booked_min: Optional[int] = None
    transcript: Transcript
    skill_states: list[SkillState] = Field(default_factory=list)
    last_homework: Optional[LastHomework] = None
    outputs: list[Literal["report", "skills", "plan", "tips"]] = Field(
        default_factory=lambda: ["report", "skills", "plan", "tips"]
    )


class TopiRunResponse(BaseModel):
    lesson_id: str
    version: str
    models: dict[str, str]
    evidence: Optional[dict[str, Any]] = None
    report: Optional[dict[str, Any]] = None
    skills: Optional[dict[str, Any]] = None
    plan: Optional[dict[str, Any]] = None
    tips: Optional[dict[str, Any]] = None
    errors: dict[str, str] = Field(default_factory=dict)
