# Luna (analysis v2) against Claude Opus — first comparison, 2026-11-17

**Tutor standard: Luna v2 lands in the same band as Opus in 70–72% of behaviour-lessons (production v1: 57–61%; Opus against itself: 96%). Gaps, lessons 3–4: Luna finds 6 of the 7 Opus maths gaps and 4 of the 5 learning-skill gaps, but splits one Opus skill into several narrow ones, so its confidence comes out lower.** Not accuracy: Opus is the benchmark, the human hand check has not been done (golden-set step 5).

## Set-up

- **Lessons:** golden lessons 3–8 (`c1698fb7`, `b8f9fb8c`, `3d497118`, `24aedf8f`, `514fe1df`, `fc8fa23d`). Not 1–2 (blind), not 9–10 (few-shot source).
- **Opus:** lesson-coding v2.1 runs A2 and B2 (2026-11-09); gap tables of process 07 run 2026-11-17 (lessons 3–4 only).
- **Luna:** `gpt-6-luna`, reasoning high, strict JSON schema; 2 independent runs of v2 (r1, r2); 1 run of production v1 (`evidence.extract` + `checker`). Same transcripts, same scoring code (`analysis.tutor_behaviours`, a port of `score_v2.py`). Script: `tools/topi_luna_eval.py`. Data and outputs outside the repo (quotes from minors' lessons).

## Rubric

1. **Band agreement:** for 9 measurable behaviours × 6 lessons = 54 cells, same band (met · near · below) as Opus. Target: ≥ 80%, i.e. near the Opus–Opus 96%.
2. **Gap recall:** an Opus gap counts as found when a Luna gap names the same rule and shares ≥ 1 attempt time (± 30 s). **Precision:** a Luna gap counts as right when it maps to an Opus gap or its attempts. Judged by hand (Claude, this session), each match listed below.
3. **Confidence agreement** on matched gaps.

## 1. Tutor standard (54 cells)

| Pair | Same band | 1 | 2 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Opus A vs Opus B (ceiling) | **52/54 (96%)** | 6/6 | 6/6 | 6/6 | 5/6 | 6/6 | 6/6 | 6/6 | 6/6 | 5/6 |
| Luna v2 r1 vs Opus A | **38/54 (70%)** | 5 | 5 | 4 | 5 | 2 | 3 | 6 | 2 | 6 |
| Luna v2 r2 vs Opus A | 39/54 (72%) | 6 | 6 | 3 | 5 | 2 | 3 | 6 | 3 | 5 |
| Luna v2 r3 vs Opus A (homework + praise fix) | **40/54 (74%)** | 5 | 6 | 5 | 4 | 3 | 4 | 5 | 4 | 4 |
| Luna v2 r4 vs Opus A (same fix) | **43/54 (80%)** | 6 | 6 | 4 | 5 | 2 | 5 | 5 | 5 | 5 |
| Luna v2 r3 vs r4 (stability) | 42/54 (78%) | 5 | 6 | 3 | 5 | 4 | 5 | 6 | 5 | 3 |
| Luna v2 r1 vs r2 (stability) | 42/54 (78%) | 5 | 5 | 2 | 6 | 3 | 6 | 6 | 4 | 5 |
| Luna v1 (production) vs Opus A | **33/54 (61%)** | 5 | 6 | 3 | 6 | 2 | 1 | 3 | 3 | 4 |

**Where Luna v2 still misses** (sorted by cells lost):
- **6 Errors found, not re-solved (2/6):** Luna labels fewer `error_pointed` (1 vs 5 in `24aedf8f`) and more `self_correction`.
- **9 Praise (2–3/6):** Luna labels "Hấp tấp quá" ("too hasty") as `criticism_person`; Opus does not. Fixed in the prompt after this run (a remark on how the pupil worked is about the work); runs r3–r4 test it.
- **7 Homework checked (3/6):** Luna misses the homework check in the first minutes in 3 lessons. Fixed in the prompt (examples of a request to show last lesson's work); r3–r4 test it.
- **4 Asks, not tells (3–4/6):** unstable in Luna itself (r1 vs r2: 2/6) — `gives_answer` and `self_answered` counts swing; also Opus's weakest type (κ 0.17 between Opus runs).

## 2. Gaps, lessons 3–4 (Opus: 7 maths, 5 learning-skill)

| Opus gap | Luna r1 | Luna r2 |
|---|---|---|
| L3 M1 negating inequalities, high | found, split in 3 (medium + 2 slips) | found, high (+1 slip split off) |
| L3 M2 P⇒Q with false P, high | found, medium | found, high |
| L3 M3 converse / equivalence / ∀ by intuition, high | found, split in 3, medium | found, split in 3, medium |
| L3 M4 proposition vs open sentence, medium | found, split in 2, medium | found, split in 2, medium |
| L3 M5 proving ∃ false, low | **missed** | merged into another gap |
| L4 M1 interval brackets, high | found, split in 2, low (slips) | found, medium + slip |
| L4 M2 negating ∀/∃, high | found, low (slip) | found, medium |
| L3 L1 answers before thinking, high | found, medium | found, medium |
| L3 L2 no self-check, medium | found, medium (other evidence) | found, low |
| L3 L3 no written working, low | found, low | found, low |
| L4 L1 does not check, medium | found, high | found, low |
| L4 L2 drops rule under test, low | found, low | found, low |

- **Recall:** maths 6/7 in both runs; learning skills 5/5.
- **Precision:** r1 every Luna gap maps to an Opus gap; r2 has 3 extra gaps: one **high** on graphing an inequality in two variables (Opus lists it as shown correct, first sighting), two low.
- **Confidence agreement:** low. Luna splits one rule into several narrow skills and marks hinted fixes as slips, so a gap Opus calls high is spread over medium and low rows. A naming rule ("name the rule, not the exercise; merge skills that differ only in wording") is in the prompt after this run, **not yet measured**.
- **Code fix found by this run:** grouping gaps by skill-map node merged all five lesson-3 gaps into one node (the grade-10 node covers the whole chapter). Gaps are now grouped by the model's skill words; the node stays an attribute.

## Next

1. r3–r4 (homework and praise fixes): 74% and 80%; behaviour 7 rose to 4–5/6, 9 to 4–5/6; 6 (errors found) still 2–3/6. Next: run r5–r6 with the skill-naming rule; same script, ~$0.02 a lesson.
2. If band agreement reaches ≥ 80% and maths-gap confidence agrees on ≥ 5 of 7, wire v2 into `pipeline.py` behind a setting.
3. All numbers are Luna against Opus; Khanh's hand check (golden-set step 5) is what turns them into accuracy.
