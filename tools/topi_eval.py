"""B9 — chấm Topi trên golden set (toptutor-main/60-output/specs/golden-set-v2.md).

Thư mục dữ liệu, mỗi buổi 2–3 file cùng tên lesson_id:
  <id>.transcript.json   transcript JSON v2 (có "segments", "grade", "lessonDate", "durationSec")
  <id>.gold.json         Khanh chấm tay: {"exercises": [{"first_actor": "pupil|tutor",
                         "result": "alone|with_help|tutor_solved|not_finished", "skill_node": "N7.03"?}],
                         "blind": true|false}
  <id>.topi.json         (tự sinh) kết quả Topi, để chạy lại không tốn tiền: --offline

Chạy:
  python tools/topi_eval.py <thư mục>            # gọi Gemini thật (cần .env), lưu <id>.topi.json
  python tools/topi_eval.py <thư mục> --offline  # chỉ chấm lại từ <id>.topi.json đã có
In ra bảng Markdown và ghi topi_eval.md vào thư mục đó.

Cổng (topi-build-plan.md): báo cáo 0 câu thiếu căn cứ; kế hoạch 100% đáp án qua SymPy;
kỹ năng khớp chấm tay >= 8/10 buổi.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RESULT_MAP = {"pupil_alone": "alone", "pupil_with_help": "with_help", "tutor_solved": "tutor_solved",
              "not_finished": "not_finished", "set_as_homework": None}


def score_lesson(topi: dict, gold: dict | None) -> dict:
    ev = topi.get("evidence") or {}
    exercises = [e for e in ev.get("exercises") or [] if RESULT_MAP.get(e.get("result")) is not None]
    check = ev.get("check") or {}
    dropped = len(check.get("dropped") or [])
    kept = check.get("kept") or 0
    row = {
        "exercises_model": len(exercises),
        "labels_dropped_pct": round(100 * dropped / (dropped + kept), 1) if dropped + kept else 0.0,
    }
    rep = topi.get("report") or {}
    row["report_uncited"] = sum(1 for k in ("lesson_content", "tutor_notes")
                                if (rep.get(k) or {}).get("text") and not (rep.get(k) or {}).get("cites")
                                and (rep.get(k) or {}).get("text") != "Không có nhận xét thêm.")
    asks = [a for s in (topi.get("plan") or {}).get("steps") or [] for a in s.get("asks") or [] if a.get("problem")]
    row["plan_asks"] = len(asks)
    row["plan_verified_pct"] = round(100 * sum(1 for a in asks if a.get("verified")) / len(asks), 1) if asks else None
    row["errors"] = ",".join(sorted((topi.get("errors") or {}).keys())) or "-"
    if gold:
        g = gold.get("exercises") or []
        row["exercises_gold"] = len(g)
        n = min(len(g), len(exercises))
        row["actor_agree"] = f"{sum(1 for i in range(n) if g[i].get('first_actor') == exercises[i].get('first_actor'))}/{len(g)}"
        row["result_agree"] = f"{sum(1 for i in range(n) if g[i].get('result') == RESULT_MAP.get(exercises[i].get('result')))}/{len(g)}"
        gn = [(i, x.get("skill_node")) for i, x in enumerate(g) if x.get("skill_node")]
        row["node_agree"] = (f"{sum(1 for i, node in gn if i < len(exercises) and exercises[i].get('skill_node') == node)}/{len(gn)}"
                             if gn else "-")
        row["blind"] = "yes" if gold.get("blind") else ""
    return row


async def run_one(client, path: Path, settings) -> dict:
    from app.models.topi import TopiRunRequest
    from app.services.topi import pipeline
    t = json.loads(path.read_text(encoding="utf-8"))
    req = TopiRunRequest(lesson_id=t.get("lessonId") or path.name.split(".")[0], lesson_date=(t.get("lessonDate") or "")[:10] or "2026-01-01",
                         grade=t.get("grade"), duration_sec=t.get("durationSec"), booked_min=t.get("bookedMin"),
                         transcript={"segments": t.get("segments") or []})
    out = await pipeline.run(client, req, evidence_model=settings.topi_evidence_model, write_model=settings.topi_write_model)
    return out.model_dump()


def table(rows: list[dict]) -> str:
    cols = ["lesson", "blind", "exercises_gold", "exercises_model", "actor_agree", "result_agree", "node_agree",
            "labels_dropped_pct", "report_uncited", "plan_asks", "plan_verified_pct", "errors"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    folder = Path(args.folder)
    transcripts = sorted(folder.glob("*.transcript.json"))
    rows = []
    client = settings = None
    if not args.offline:
        from app.core.config import get_settings
        from app.core.dependencies import get_gemini_client
        settings, client = get_settings(), get_gemini_client()
    for tp in transcripts:
        lid = tp.name.split(".")[0]
        cache = folder / f"{lid}.topi.json"
        if args.offline:
            if not cache.exists():
                continue
            topi = json.loads(cache.read_text(encoding="utf-8"))
        else:
            topi = asyncio.run(run_one(client, tp, settings))
            cache.write_text(json.dumps(topi, ensure_ascii=False, indent=1), encoding="utf-8")
        gp = folder / f"{lid}.gold.json"
        gold = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else None
        rows.append({"lesson": lid[:8], **score_lesson(topi, gold)})
    md = table(rows)
    (folder / "topi_eval.md").write_text(md + "\n", encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
