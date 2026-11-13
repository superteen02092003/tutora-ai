"""Bản đồ kỹ năng toán lớp 6–9 (sinh từ toptutor-main/01-background/maths-skill-map.md)."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

_PATH = Path(__file__).parent / "data" / "skill_map.json"


@lru_cache()
def nodes() -> list[dict]:
    return json.loads(_PATH.read_text(encoding="utf-8"))["nodes"]


@lru_cache()
def by_id() -> dict[str, dict]:
    return {n["id"]: n for n in nodes()}


def for_grade(grade: Optional[int]) -> list[dict]:
    """Nút của lớp đó và các lớp dưới (lỗ hổng lớp dưới vẫn phải gắn được)."""
    if not grade:
        return nodes()
    return [n for n in nodes() if n["grade"] <= grade]


def prompt_list(grade: Optional[int]) -> str:
    return "\n".join(f'{n["id"]} — {n["name_vi"]} (dấu hiệu: {n["shows_as"]})' for n in for_grade(grade))
