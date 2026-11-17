"""Sinh app/services/topi/data/skill_map.json từ các file skill map trong toptutor-main.

Mỗi dòng bảng "| Id | Skill (Vietnamese) | Needs | Shows as |" thành một nút:
id, grade, gateway (★), name_vi, needs (chỉ các mã kỹ năng), shows_as.
Nhãn `[check]`, `[ASSUMPTION]`, `[needs …]` bị bỏ khỏi chữ đưa vào prompt.

    python tools/build_topi_skill_map.py <toptutor-main>/10-knowledge
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

FILES = [
    "maths-skill-map-grades-1-5.md",
    "maths-skill-map.md",
    "maths-skill-map-grades-10-12.md",
]
ROW = re.compile(r"^\|\s*([NHT](\d{1,2})\.\d{2})\s*(★)?\s*\|(.*)\|\s*$")
ID = re.compile(r"\b[NHT]\d{1,2}\.\d{2}\b")
TAG = re.compile(r"`?\[(?:check|ASSUMPTION|needs[^\]]*)\]`?", re.IGNORECASE)


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub("", s).replace("\\|", "|")).strip(" ;")


def parse(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", m.group(4))]
        if len(cells) < 3:
            raise ValueError(f"{path.name}: bad row {m.group(1)}")
        name, needs, shows = cells[0], cells[1], "|".join(cells[2:])
        out.append({
            "id": m.group(1),
            "grade": int(m.group(2)),
            "gateway": bool(m.group(3)),
            "name_vi": clean(name),
            "needs": ID.findall(needs),
            "shows_as": clean(shows),
        })
    return out


def main(folder: str) -> None:
    root = Path(folder)
    nodes: list[dict] = []
    for f in FILES:
        nodes += parse(root / f)
    ids = [n["id"] for n in nodes]
    dup = {i for i in ids if ids.count(i) > 1}
    missing = {(n["id"], x) for n in nodes for x in n["needs"] if x not in ids}
    if dup or missing:
        raise SystemExit(f"duplicate ids {sorted(dup)}; unknown needs {sorted(missing)}")
    nodes.sort(key=lambda n: (n["grade"], n["id"][0] != "N", n["id"]))
    out = Path(__file__).resolve().parents[1] / "app/services/topi/data/skill_map.json"
    out.write_text(json.dumps({
        "source": "toptutor-main/10-knowledge/" + " + ".join(FILES),
        "generated": date.today().isoformat(),
        "nodes": nodes,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(nodes)} nodes -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
