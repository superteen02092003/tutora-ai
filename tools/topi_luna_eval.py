"""Luna (analysis v2) against Claude Opus on the golden set — docs/topi-luna/03-eval-plan.md.

Data folder (kept OUTSIDE the repo: transcripts and labels hold quotes of minors' lessons):
  transcripts/<id>.json   anonymised transcript JSON v2 (segments, grade)
  opusA/<id>.json         Opus lesson-coding v2.1 labels, run A2   (golden, tutor quality)
  opusB/<id>.json         Opus lesson-coding v2.1 labels, run B2   (second Opus run = ceiling)
  luna_v2_r<k>/<id>.json  written by --run: analysis.run() output
  luna_old/<id>.json      written by --run --baseline: production evidence.extract + checker

  python tools/topi_luna_eval.py <folder> --run --runs 2 --baseline <id> <id> ...
  python tools/topi_luna_eval.py <folder>              # score only, from saved files
Needs OPENAI_API_KEY in the environment for --run.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.topi import analysis, checker, evidence  # noqa: E402

BEHAVIOURS = ["1", "2", "4", "5", "6", "7", "8", "9", "10"]  # 3 (wait) not measurable


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


async def run_lesson(folder: Path, lid: str, runs: int, baseline: bool, effort: str, start: int = 1) -> None:
    tr = load(folder / "transcripts" / f"{lid}.json")
    segs, grade = tr["segments"], tr.get("grade")
    jobs = []
    for k in range(start, start + runs):
        out = folder / f"luna_v2_r{k}" / f"{lid}.json"
        if not out.exists():
            jobs.append((out, analysis.run(None, model="gpt-6-luna", segments=segs, grade=grade, reasoning_effort=effort)))
    if baseline and not (folder / "luna_old" / f"{lid}.json").exists():
        async def old():
            raw = await evidence.extract(None, model="gpt-6-luna", segments=segs, grade=grade)
            return checker.check_evidence(raw, segs)
        jobs.append((folder / "luna_old" / f"{lid}.json", old()))
    res = await asyncio.gather(*(j for _, j in jobs), return_exceptions=True)
    for (out, _), r in zip(jobs, res):
        if isinstance(r, Exception):
            print(f"{lid[:8]} {out.parent.name}: FAILED {type(r).__name__}: {str(r)[:200]}")
            continue
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{lid[:8]} {out.parent.name}: ok")


def bands_of(folder: Path, sub: str, lid: str):
    p = folder / sub / f"{lid}.json"
    if not p.exists():
        return None
    data = load(p)
    segs = load(folder / "transcripts" / f"{lid}.json")["segments"]
    ev = data.get("evidence", data)  # v2 output wraps labels in "evidence"
    if "blocks" not in ev and "segments" in ev and isinstance(ev["segments"], list) and ev["segments"] \
            and isinstance(ev["segments"][0], dict) and "type" in ev["segments"][0]:
        ev = dict(ev, blocks=ev["segments"])  # Opus files call the blocks "segments"
    return analysis.tutor_behaviours(ev, segs)["bands"]


def agreement(folder: Path, ids: list[str], a: str, b: str) -> dict:
    per_b = {k: [0, 0] for k in BEHAVIOURS}
    for lid in ids:
        ba, bb = bands_of(folder, a, lid), bands_of(folder, b, lid)
        if not ba or not bb:
            continue
        for k in BEHAVIOURS:
            if ba[k] is None or bb[k] is None:  # no occasion on either side: the cell drops out
                continue
            per_b[k][1] += 1
            per_b[k][0] += ba[k] == bb[k]
    tot = [sum(v[0] for v in per_b.values()), sum(v[1] for v in per_b.values())]
    return {"per_behaviour": {k: f"{v[0]}/{v[1]}" for k, v in per_b.items()}, "total": f"{tot[0]}/{tot[1]}",
            "pct": round(100 * tot[0] / tot[1], 1) if tot[1] else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--effort", default="high")
    ap.add_argument("--start", type=int, default=1)
    args = ap.parse_args()
    folder = Path(args.folder)
    ids = args.ids or sorted(p.stem for p in (folder / "opusA").glob("*.json"))
    if args.run:
        async def all_():
            await asyncio.gather(*(run_lesson(folder, i, args.runs, args.baseline, args.effort, args.start) for i in ids))
        asyncio.run(all_())
    runs = sorted((p.name for p in folder.glob("luna_v2_r*") if p.is_dir()), key=lambda n: int(n.rsplit("r", 1)[1]))
    pairs = [("opusA", "opusB")] + [(r, "opusA") for r in runs] + [(r, "opusB") for r in runs] \
        + [(runs[i], runs[i + 1]) for i in range(0, len(runs) - 1, 2)] + [("luna_old", "opusA"), ("luna_old", "opusB")]
    report = {f"{a} vs {b}": agreement(folder, ids, a, b) for a, b in pairs}
    report["bands"] = {lid[:8]: {s: bands_of(folder, s, lid) for s in ["opusA", "opusB", *runs, "luna_old"]}
                       for lid in ids}
    (folder / "band_agreement.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in report.items():
        if k != "bands":
            print(k, v["total"], v["pct"], v["per_behaviour"])


if __name__ == "__main__":
    main()
