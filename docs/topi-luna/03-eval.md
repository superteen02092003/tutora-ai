# Luna (analysis v2) against Claude Opus — comparison, 2026-11-17 (r1–r10)

**Latest (r9–r10, gaps merged by error pattern): band agreement with Opus A 85% and 80% (mean 82%). Maths-gap confidence agrees on 3/7 and 5/7 (was 2/7). r10 meets both wiring thresholds, r9 only the band one; the merge works when Luna writes the same `error_pattern` for a repeated mistake, and it does not always.**

**Latest (r5–r8): band agreement with Opus A 76–82% (mean 78%; r8 against Opus B 85%). Target ≥ 85% not reached. Behaviour 6 diagnosed and fixed in two steps (r5–r6, r7–r8); it is now limited by noise near the band thresholds, not by a labelling bias. Gaps, lessons 3–4: the skill-naming rule lifts maths recall to 7/7 but confidence still agrees on only 2/7 (threshold 5/7).** Details in §1–§2 and Next; the first-comparison text (r1–r4) is kept below it.

**Tutor standard: Luna v2 lands in the same band as Opus in 70–72% of behaviour-lessons (production v1: 57–61%; Opus against itself: 96%). Gaps, lessons 3–4: Luna finds 6 of the 7 Opus maths gaps and 4 of the 5 learning-skill gaps, but splits one Opus skill into several narrow ones, so its confidence comes out lower.** Not accuracy: Opus is the benchmark, the human hand check has not been done (golden-set step 5).

## Set-up

- **Lessons:** golden lessons 3–8 (`c1698fb7`, `b8f9fb8c`, `3d497118`, `24aedf8f`, `514fe1df`, `fc8fa23d`). Not 1–2 (blind), not 9–10 (few-shot source).
- **Opus:** lesson-coding v2.1 runs A2 and B2 (2026-11-09); gap tables of process 07 run 2026-11-17 (lessons 3–4 only).
- **Luna:** `gpt-6-luna`, reasoning high, strict JSON schema; independent runs of v2 (r1–r8; prompt changes between pairs are listed in §1); 1 run of production v1 (`evidence.extract` + `checker`). Same transcripts, same scoring code (`analysis.tutor_behaviours`, a port of `score_v2.py`). Script: `tools/topi_luna_eval.py`. Data and outputs outside the repo (quotes from minors' lessons).

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
| Luna v2 r5 vs Opus A (naming rule + self-correction guard) | 42/54 (78%) | 5 | 6 | 6 | 4 | 3 | 4 | 5 | 4 | 5 |
| Luna v2 r6 vs Opus A (same) | 41/54 (76%) | 6 | 6 | 4 | 4 | 1 | 4 | 5 | 6 | 5 |
| Luna v2 r7 vs Opus A (+ error_pointed prompt) | 42/54 (78%) | 5 | 6 | 3 | 5 | 3 | 5 | 5 | 6 | 4 |
| Luna v2 r8 vs Opus A (same) | **44/54 (82%)** | 5 | 6 | 5 | 4 | 4 | 5 | 5 | 6 | 4 |
| Luna v2 r8 vs Opus B | 46/54 (85%) | 5 | 6 | 5 | 5 | 4 | 5 | 5 | 6 | 5 |
| Luna v2 r9 vs Opus A (+ error_pattern merge) | **46/54 (85%)** | 6 | 6 | 3 | 6 | 4 | 3 | 6 | 6 | 6 |
| Luna v2 r10 vs Opus A (same) | 43/54 (80%) | 6 | 6 | 4 | 5 | 2 | 4 | 6 | 5 | 5 |
| Luna v2 r9 vs Opus B | 44/54 (81%) | 6 | 6 | 3 | 5 | 4 | 3 | 6 | 6 | 5 |
| Luna v2 r10 vs Opus B | 43/54 (80%) | 6 | 6 | 4 | 6 | 2 | 4 | 6 | 5 | 4 |
| Luna v2 r9 vs r10 (stability) | 45/54 (83%) | 6 | 6 | 3 | 5 | 4 | 5 | 6 | 5 | 5 |
| Luna v2 r5 vs r6 (stability) | 45/54 (83%) | 5 | 6 | 4 | 6 | 4 | 4 | 6 | 4 | 6 |
| Luna v2 r7 vs r8 (stability) | 41/54 (76%) | 4 | 6 | 2 | 5 | 2 | 6 | 6 | 6 | 4 |
| Luna v1 (production) vs Opus A | **33/54 (61%)** | 5 | 6 | 3 | 6 | 2 | 1 | 3 | 3 | 4 |

**Where Luna v2 still misses** (sorted by cells lost):
- **6 Errors found, not re-solved (2/6):** Luna labels fewer `error_pointed` (1 vs 5 in `24aedf8f`) and more `self_correction`.
- **9 Praise (2–3/6):** Luna labels "Hấp tấp quá" ("too hasty") as `criticism_person`; Opus does not. Fixed in the prompt after this run (a remark on how the pupil worked is about the work); runs r3–r4 test it.
- **7 Homework checked (3/6):** Luna misses the homework check in the first minutes in 3 lessons. Fixed in the prompt (examples of a request to show last lesson's work); r3–r4 test it.
- **4 Asks, not tells (3–4/6):** unstable in Luna itself (r1 vs r2: 2/6) — `gives_answer` and `self_answered` counts swing; also Opus's weakest type (κ 0.17 between Opus runs).

### Behaviour 6 (errors found, not re-solved), r5–r8

Score = pupil `self_correction` with `after = error_pointed` ÷ pupil `error`; met ≥ 0.6, near ≥ 0.3.

- **Diagnosis (from r3–r4), the opposite of the first note:** Luna did not under-count; it **over-counted** `self_correction`. When the tutor said the fix (`error_resolved_by_tutor`) and the pupil repeated it ("À dạ. Vậy là 7 trên x cộng 3 bình phương" — "Ah yes, so 7 over (x+3) squared"), Luna labelled it a self-correction after pointing. In `24aedf8f` r4: 7 such self-corrections, Opus 1.
- **Fix 1 (r5–r6):** prompt — repeating a correction the tutor already said is not a self-correction; the pupil pass now receives the tutor's error moments (pointed / resolved). Code — `analysis._guard_self_corrections` in `check()`: drop a self-correction whose last tutor error move is `error_resolved_by_tutor`; set `after` from whether an `error_pointed` came first. Result: over-counting gone, but behaviour 6 fell to 1–3/6, because Luna then **under-labelled `error_pointed`**: it tagged pointing questions ("bước một là gì?" — "what is step one?") as `question_open` only, and skipped the pointing when a fix followed.
- **Fix 2 (r7–r8):** prompt — an `error_pointed` may be a question (label both), and when the tutor points and then gives the fix, label both events. `error_pointed` counts now track Opus (`24aedf8f`: 7 vs Opus 5, was 0–1). Behaviour 6: 3/6 and 4/6.
- **What is left:** the remaining misses are lessons whose ratio sits near a threshold (`514fe1df` Opus 0.33, Luna 0.25–0.33; in `fc8fa23d` one extra error turns met into near). More prompt work is unlikely to move this much; a wider band or a count-based rule would, but that also changes the Opus scoring, so it is a rubric decision.

## 2. Gaps, lessons 3–4 (Opus: 7 maths, 5 learning-skill)

| Opus gap | Luna r1 | Luna r2 | Luna r5 (naming rule) | Luna r6 (naming rule) |
|---|---|---|---|---|
| L3 M1 negating inequalities, high | found, split in 3 (medium + 2 slips) | found, high (+1 slip split off) | found, split in 2, **high** + high | found, **high** (+1 slip split off) |
| L3 M2 P⇒Q with false P, high | found, medium | found, high | found, medium | found, medium |
| L3 M3 converse / equivalence / ∀ by intuition, high | found, split in 3, medium | found, split in 3, medium | found, split in 3, medium + 2 slips | found, split in 3, all low (slips) |
| L3 M4 proposition vs open sentence, medium | found, split in 2, medium | found, split in 2, medium | found, split in 2, **medium** | found, split in 3, **medium** |
| L3 M5 proving ∃ false, low | **missed** | merged into another gap | **found**, medium | **found**, medium |
| L4 M1 interval brackets, high | found, split in 2, low (slips) | found, medium + slip | found, split in 2, low (slips) | found, split in 2, low (slips) |
| L4 M2 negating ∀/∃, high | found, low (slip) | found, medium | found, medium | found, medium |
| L3 L1 answers before thinking, high | found, medium | found, medium | found, medium | found, medium |
| L3 L2 no self-check, medium | found, medium (other evidence) | found, low | found, **medium** | found, high |
| L3 L3 no written working, low | found, low | found, low | found, **low** | found, **low** |
| L4 L1 does not check, medium | found, high | found, low | found, **medium** | found, **medium** |
| L4 L2 drops rule under test, low | found, low | found, low | found, medium | found, medium |

**r5–r6 (skill-naming rule):** maths recall **7/7** in both (M5 found for the first time); learning skills 5/5. Precision: r5 has one extra low slip (graphing an inequality in two variables, which Opus lists as shown correct); in r6 every extra row maps to M3/M4 attempts. **Maths confidence agrees on 2/7 in both runs (M1, M4); threshold 5/7 not met.** The naming rule did not stop the splitting: M3 is still three rows (converse, equivalence, universal claim), and L4 M1 is two rows marked slips because each error was fixed after a hint, while Opus calls it high from the tutor's "you are still repeating this error". Learning-skill confidence agrees on 3/5 (r5) and 2/5 (r6). r7–r8 gaps not judged (same naming prompt as r5–r6).

### Gap merge by error pattern (r9–r10)

- **Why code alone could not merge:** in r5–r6 the split rows of one Opus gap share no field — different skill words, exercises, and (for L4 M1) skill-map nodes. What they share is the mistake: "excludes −2 although x ≤ −2" (solving an inequality) and "excludes 4 although it is in both intervals" (intersecting intervals) are both Opus L4 M1.
- **Change:** each wrong / hinted / unfinished attempt now carries `error_pattern`, the mistake in 2–6 English words, independent of topic, repeated word for word when the mistake recurs. Code (`analysis._merge_by_error_pattern`, before confidence is computed) merges skill groups that share a pattern; the merged gap keeps the name of its largest group, and the usual rule applies (≥ 2 problems → high, not a slip).

| Opus gap | Luna r9 | Luna r10 |
|---|---|---|
| L3 M1 negating inequalities, high | **high**, merged (1271–3385) | **high**, merged |
| L3 M2 P⇒Q with false P, high | medium | **high** |
| L3 M3 converse / equivalence / ∀ by intuition, high | split in 3, **high** + 2 medium | **high**, merged into one row (2083, 2272, 3242) |
| L3 M4 proposition vs open sentence, medium | **medium** | split in 3, **medium** |
| L3 M5 proving ∃ false, low | found, medium | found, medium |
| L4 M1 interval brackets, high | merged (834 + 2100), medium (lowered by a transcript doubt at one attempt) | **high**, merged |
| L4 M2 negating ∀/∃, high | low (slip) | low (slip) |
| L3 L1 answers before thinking, high | medium | medium |
| L3 L2 no self-check, medium | **missed** | **medium** |
| L3 L3 no written working, low | **low** | **low** |
| L4 L1 does not check, medium | low | low |
| L4 L2 drops rule under test, low | **low** | medium |

- **Maths:** recall 7/7 in both; confidence agrees on **3/7 (r9)** and **5/7 (r10)**. Learning skills: recall 4/5 and 5/5; confidence 2/5 and 2/5.
- **Precision:** r9 one extra low slip (finding a second witness for an existential claim); r10 one extra **high** (graphing an inequality in two variables, 4296/4348 after hints; Opus lists it as shown correct — the same extra as r2).
- **Limit:** the merge is only as good as the pattern wording. r10 wrote one pattern for the converse, equivalence and universal-claim errors, so M3 merged; r9 wrote "accepts converse without counterexample" and "accepts equivalence without checking both directions", so it did not. L4 M2 stays a slip in both: one wrong item, fixed after pointing, which is what Opus also sees, but Opus rates it high from the tutor's remark that it improved since last lesson — a cross-lesson signal v2 does not have.

Earlier notes, r1–r2:

- **Recall:** maths 6/7 in both runs; learning skills 5/5.
- **Precision:** r1 every Luna gap maps to an Opus gap; r2 has 3 extra gaps: one **high** on graphing an inequality in two variables (Opus lists it as shown correct, first sighting), two low.
- **Confidence agreement:** low. Luna splits one rule into several narrow skills and marks hinted fixes as slips, so a gap Opus calls high is spread over medium and low rows. A naming rule ("name the rule, not the exercise; merge skills that differ only in wording") was added after this run; measured in r5–r6 above: recall up, confidence unchanged.
- **Code fix found by this run:** grouping gaps by skill-map node merged all five lesson-3 gaps into one node (the grade-10 node covers the whole chapter). Gaps are now grouped by the model's skill words; the node stays an attribute.

## Next

0. **r9–r10 (2026-11-17), error-pattern merge:** band 85% / 80%, maths confidence 3/7 / 5/7. One run of two meets both thresholds; not stable enough to wire in yet. Next options: (a) give the attempts pass the error patterns already used in this lesson (a second short call, or patterns listed before attempts), so recurring mistakes reuse the same words; (b) a tutor remark of repetition ("lỗi này con còn lặp lại" — "you are still repeating this error") raises confidence by one step; (c) Khanh's hand check of r10.
0. **r5–r8 (2026-11-17):** 78%, 76%, 78%, 82% against Opus A; behaviour 6 fixed in two steps (above). Wiring threshold (≥ 80% and maths confidence ≥ 5/7) **not met**: band agreement is just under the line on average (78%), confidence is 2/7. Not wired into the pipeline. Options: (a) merge split gaps in code (same exercise block and same kind of error) and let a tutor's "repeated error" remark raise confidence, then re-measure gaps; (b) Khanh's hand check of r8 against Opus, to see whether Luna's narrower gaps are wrong or only finer.
1. r3–r4 (homework and praise fixes): 74% and 80%; behaviour 7 rose to 4–5/6, 9 to 4–5/6; 6 (errors found) still 2–3/6. Next: run r5–r6 with the skill-naming rule; same script, ~$0.02 a lesson.
2. If band agreement reaches ≥ 80% and maths-gap confidence agrees on ≥ 5 of 7, wire v2 into `pipeline.py` behind a setting.
3. All numbers are Luna against Opus; Khanh's hand check (golden-set step 5) is what turns them into accuracy.
