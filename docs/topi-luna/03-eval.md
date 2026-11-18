# Luna (analysis v2) against Claude Opus — comparison, 2026-11-17 (r1–r10), benchmark updated 2026-11-18

**Update 2026-11-18 — against Michael's full-model run (process 07, lessons 5 and 4, 2026-11-17), which corrects the stage-1 lesson-4 gaps: maths-gap confidence, lessons 3–4, agrees on 4/7 (r9) and 6/7 (r10), not 3/7 and 5/7. Lesson 5, new: recall 6/6, confidence 3/6 and 4/6. Main Luna fault: extra gaps (r10: one high in lesson 4, two medium in lesson 5) on attempts Opus lists as shown correct or as no evidence. The two Opus methods (coding v2.1 + script, and process 07's own tutor table) disagree on 4 of 8 behaviours a lesson, so the band numbers below measure agreement with one method, not truth.** See §0.

**r11–r12 (2026-11-18, behaviour-7 fix + no-evidence attempts left out): band agreement with Opus A 89% and 81% (53 cells; mean 85%). No high or medium extra gap in r11, one medium in r12 (r10: one high, two medium). Maths-gap confidence, lessons 3–5: 8/13 in both (r10: 10/13). Not stable enough to wire in: confidence and the learning-habit rows still swing between runs.** See §0.6.

**Slip in code + vote of 3 runs (2026-11-18): both votes agree with Opus A on 45/53 (85%); the two votes agree with each other on 46/53 (87%), against 79–81% between single runs. No extra gap at medium or high in either vote. Maths-gap confidence, lessons 3–5: 8/13 and 7/13 — the rest is mostly where the lesson-3 stage-1 table departs from Opus's own scoring rules, or where a doubt or a "not finished" label moves one row.** See §0.7.

**Latest (r9–r10, gaps merged by error pattern): band agreement with Opus A 85% and 80% (mean 82%). Maths-gap confidence agrees on 3/7 and 5/7 (was 2/7). r10 meets both wiring thresholds, r9 only the band one; the merge works when Luna writes the same `error_pattern` for a repeated mistake, and it does not always.**

**Latest (r5–r8): band agreement with Opus A 76–82% (mean 78%; r8 against Opus B 85%). Target ≥ 85% not reached. Behaviour 6 diagnosed and fixed in two steps (r5–r6, r7–r8); it is now limited by noise near the band thresholds, not by a labelling bias. Gaps, lessons 3–4: the skill-naming rule lifts maths recall to 7/7 but confidence still agrees on only 2/7 (threshold 5/7).** Details in §1–§2 and Next; the first-comparison text (r1–r4) is kept below it.

**Tutor standard: Luna v2 lands in the same band as Opus in 70–72% of behaviour-lessons (production v1: 57–61%; Opus against itself: 96%). Gaps, lessons 3–4: Luna finds 6 of the 7 Opus maths gaps and 4 of the 5 learning-skill gaps, but splits one Opus skill into several narrow ones, so its confidence comes out lower.** Not accuracy: Opus is the benchmark, the human hand check has not been done (golden-set step 5).

## 0. Against the full-model benchmark (2026-11-18)

Sources (toptutor-main, `origin/main`): `40-processes/07-gap-analyser/runs/2026-11-17_golden-lessons-5-4.md` (full model: confidence, state, award, recommendations, tutor table, one pass) and `scoring-model.md`. Luna runs r9–r10 (gaps merged by error pattern). Judged by hand, same rules as §2.

### 0.1 Lesson 4 (`b8f9fb8c`): the benchmark changed

The full-model run corrects its own stage-1 reading of lesson 4:

| Lesson-4 gap | Stage 1 (used in §2) | Full model | Luna r9 | Luna r10 |
|---|---|---|---|---|
| Interval brackets (N10.02) | high | high | medium (lowered by a doubt) ✗ | **high** ✓ |
| Negating ∀/∃ (N10.01) | high | **low (watch)**: one slip; the other evidence is the tutor's remark about an earlier lesson | low ✓ | low ✓ |
| No self-check before handing in | medium | **high**: three slips on different problems | low ✗ | low ✗ |
| Drops a known rule under test | low | **medium** | low ✗ | **medium** ✓ |
| Inequality in two variables (N10.03) | not a gap | **shown correct** (the tutor computed the line's points) | not a gap ✓ | **extra high gap** ✗ |

With the corrected lesson 4, maths-gap confidence for lessons 3–4 agrees on **4/7 (r9) and 6/7 (r10)**. The wiring threshold (≥ 5/7) holds for r10, but r10 also has the extra high gap, which would reach a parent.

### 0.2 Lesson 5 (`3d497118`), first gap comparison

| Opus gap (full model) | Luna r9 | Luna r10 |
|---|---|---|
| L1 no self-check (signs), high | medium ✗ | **high** ✓ |
| M1 N10.01 proposition or open sentence, medium | **medium** ✓ | **medium** ✓ |
| M2 N8.05 (a + b)², medium (the tutor applied the identity) | low, slip ✗ | low, slip ✗ |
| M3 N7.03 bracket after a minus, low (slip) | medium ✗ (named "moving terms") | medium ✗ |
| M4 N9.15 reversing the inequality, low | **low** ✓ | **low** ✓ |
| M5 N8.07 factorising, low | medium ✗ | **low** ✓ |
| M6 N10.01 judging a "for all" claim, low (lowered by a doubt) | **low** ✓ | **low** ✓ |

- **Recall:** maths 6/6 in both runs. **Confidence:** 3/6 (r9), 4/6 (r10).
- **Extra gaps:** r9 two low rows on attempts Opus excludes as no evidence (1745 reuses the corrected factors; 2970 a substitution the tutor set up). r10 **two medium rows** on proposition items (3057, 3232) that Opus lists as shown correct. Plus one extra habit each (answers before thinking, drops a rule).
- **Cause:** the attempts prompt already says that an answer to a leading question, or a result the tutor states, is no evidence, but Luna still counts reused and tutor-led answers.

### 0.3 Tutor table: two Opus methods

Process 07 writes its own tutor table (holistic, with evidence) in the same pass. Against coding v2.1 + script (Opus A, used in §1):

| | Lesson 5 | Lesson 4 |
|---|---|---|
| Opus 07 vs Opus A differ on | 1, 2, 7, 10 | 2, 5, 6, 10 |
| Luna r9 / r10 = Opus A | 9/9 · 7/9 | 8/9 · 8/9 |
| Luna r9 / r10 = Opus 07 | 5/8 · 3/8 (7: no occasion) | 5/9 · 5/9 |

- **Behaviour 7, scoring bug:** lesson 5 is the tutor's first lesson with this pupil. `tutor-standard.md` drops a behaviour with no occasion from the score; `analysis.tutor_behaviours` (and so Opus A and Luna) score it "below".
- **Behaviour 6, lesson 4:** Opus 07 finds 3 of 3 errors fixed by the pupil once pointed at (met); Luna r9–r10 say met; Opus A says near.
- **Behaviours 5 and 10:** Opus 07 counts unprompted explaining and check prompts after an error; coding v2.1 counts only an `explain_prompt` / `chance`.
- **Bands:** the code mixes the two tables of `tutor-standard.md`: behaviours 1 and 2 use the reference (evidence) bands, 5, 6 and 10 the draft bands; `golden-set-v2.md` says the reference bands.
- So Opus A against Opus B (96%) is the stability of one method, not accuracy. Which Opus method is the yardstick is a decision for Michael and Khanh.

### 0.4 What Luna v2 does not output yet

The full model (one pass, decision of 2026-11-17) also gives, per gap row, the **state** across sessions, the **award**, a **recommendation** to the tutor (and to the parent on high rows); per lesson, **one thing done well and one to try** (with Vietnamese), and the facts process 08 needs (**homework set, quiz result, what the lesson covered**). Luna v2 gives gaps, confidence and tutor bands only. These are needed before Luna can replace Opus in the 07 → 08 chain.

### 0.5 Next, from this comparison

1. ~~Fix behaviour 7~~ done in r11–r12 (§0.6). Still open: pick one band table.
2. ~~Stop extra gaps in code~~ done in r11–r12 (`not_evidence`, §0.6). Next: stabilise the slip decision (`fixed_alone_after_pointing`), e.g. derive it in code from the next attempt and the hint type instead of asking the model.
3. Decide the yardstick (coding v2.1 + script, or process 07), then re-score r1–r10 against it.
4. Add the missing outputs (§0.4) to the v2 schema.

### 0.6 r11–r12: the two fixes (2026-11-18)

**Changes.**
- **Behaviour 7:** the tutor pass outputs `homework_occasion` (yes · no · unknown). "No" (first lesson with the pupil, nothing set last time) makes the band `None`, and the eval drops a cell when either side is `None` (54 → 53 cells: lesson 5). Opus A still scores lesson 5 "below" under the old rule; that cell is the one dropped.
- **Extra gaps:** each attempt carries `not_evidence` (leading_question · tutor_led · reuses_earlier_result); `check()` leaves those attempts out (process 07 step 4). The attempts prompt also says that a hint on another step (the tutor computes the line's points) does not make the pupil's own step (choosing the side) "after hint".

**Behaviour 7:** both runs set `homework_occasion = no` for lesson 5 (the tutor's first lesson with the pupil) and `yes` for the other five. Behaviour 7 now agrees 4/5 and 5/5.

**Tutor standard, against Opus A (53 cells):**

| Run | Same band | 1 | 2 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Luna v2 r11 | **47/53 (89%)** | 5 | 6 | 6 | 6 | 4 | 4/5 | 5 | 6 | 5 |
| Luna v2 r12 | 43/53 (81%) | 5 | 6 | 4 | 6 | 2 | 5/5 | 5 | 5 | 5 |
| r11 vs r12 (stability) | 43/53 (81%) | 6 | 6 | 4 | 6 | 2 | 4/5 | 6 | 5 | 4 |

Against Opus B: 45/53 (85%) and 41/53 (77%). Behaviours 4 and 6 still carry most of the run-to-run swing.

**Gaps, against the full-model benchmark (lesson 3: stage 1; lessons 4–5: full model):**

| | r9 | r10 | r11 | r12 |
|---|---|---|---|---|
| Maths confidence, lessons 3–4 (of 7) | 4 | 6 | 5 | 4 |
| Maths confidence, lesson 5 (of 6) | 3 | 4 | 3 | 4 |
| Maths recall, lessons 3–5 (of 13) | 13 | 13 | 13 | 13 |
| Extra gaps at medium or high | 0 | 3 (1 high) | **0** | 1 |
| Lesson-4 "no self-check" (Opus high) | low | low | low | low |
| Lesson-5 "no self-check" (Opus high) | medium | high | **missed** | high |

- **Fixed:** the lesson-4 extra high gap (inequality in two variables) is gone in both runs; lesson 5's (a + b)² is now medium, as in Opus (the tutor-led re-expansion at 1382 is left out). Luna marked 1–8 attempts per lesson as no evidence.
- **Still wrong:** lesson 3's M3 merges in r11 (high) but splits in r12 (three medium rows); M2 and M5 come out medium (Opus high and low). Lesson 5's slips (bracket after a minus, reversing the sign, factorising) come out medium in r11, which also loses the slip-fed "no self-check" habit. Lesson 4's "no self-check" stays low in every run: Luna marks only one slip there (1643), while Opus reads the two bracket errors as slips too.
- **Extra gaps left:** r12 one medium row on lesson 5 (3057, which Opus lists as shown correct); low "watch" rows on 3232 in lesson 5 in both runs.

**Reading:** the two fixes did what they were meant to (behaviour 7 right in every run; extra gaps at medium or high down to 0–1). Maths-gap confidence did not improve (8/13 in both, against 7/13 and 10/13 for r9–r10): it depends on the slip decision (`fixed_alone_after_pointing`), which swings between runs and feeds both the maths rows and the "no self-check" habit. That flag is the next target.

### 0.7 Slip decided in code, and a vote of 3 runs (2026-11-18)

**Changes.**
- **Slip in code** (`analysis._derive_fixed_alone`, used by `gaps()`): a wrong attempt is "fixed alone once pointed at" when the pupil's next attempt on the same exercise (same skill words when there is no exercise id) is correct, alone or after a hint, and the tutor did not say the fix or the answer in between (`error_resolved_by_tutor`, `gives_answer`). The model's `fixed_alone_after_pointing` is ignored.
- **Every such error feeds "no self-check",** also when the errors repeat and form a maths gap (the full-model run reads lesson 4's two bracket errors both ways).
- **Vote** (`analysis.vote`, `analysis.run_voted`): 3 independent runs. A band stands when 2 of 3 agree; with no majority, "near", and the behaviour is listed as unsure. Gaps of different runs are one gap when they share a wrong or hinted attempt; a gap is kept when 2 of 3 runs have it; its confidence is the majority, else the lowest. Habits by name, same rule. The eval script builds votes from saved runs (`--vote A=11,12,13`), recomputing gaps and bands with today's code.
- Runs r13–r16 (same prompt as r11–r12). Vote A = r11, r12, r13; vote B = r14, r15, r16.

**Tutor standard, against Opus A (53 cells):**

| Run | Same band | 1 | 2 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| r13 | 41/53 (77%) | 5 | 6 | 4 | 5 | 3 | 4/5 | 5 | 5 | 4 |
| r14 | 41/53 (77%) | 6 | 6 | 3 | 5 | 3 | 4/5 | 5 | 5 | 4 |
| r15 | 45/53 (85%) | 5 | 6 | 4 | 5 | 5 | 4/5 | 6 | 6 | 4 |
| r16 | 44/53 (83%) | 5 | 6 | 3 | 5 | 5 | 4/5 | 5 | 5 | 6 |
| **Vote A (r11–r13)** | **45/53 (85%)** | 5 | 6 | 5 | 6 | 3 | 5/5 | 5 | 6 | 4 |
| **Vote B (r14–r16)** | **45/53 (85%)** | 5 | 6 | 4 | 5 | 5 | 4/5 | 5 | 6 | 5 |
| Vote A vs vote B (stability) | **46/53 (87%)** | 6 | 6 | 4 | 5 | 4 | 4/5 | 6 | 6 | 5 |
| Single runs vs each other (r11/12, r13/14, r15/16) | 79–81% | | | | | | | | | |

Against Opus B: 43/53 (81%) for both votes. Single runs r11–r16 against Opus A span 77–89% (mean 82%); both votes land at 85%, so the vote mainly removes the spread. Behaviour 4 (`gives_answer`, κ 0.17 even between Opus runs) and 6 still differ most.

**Gaps, lessons 3–5 (lesson 3: stage-1 table; 4–5: full model):**

| | r10 (best single) | r11 / r12 recomputed | Vote A | Vote B |
|---|---|---|---|---|
| Maths confidence, lesson 3 (of 5) | 4 | 3 / 2 | 3 | 3 |
| Maths confidence, lesson 4 (of 2) | 2 | 2 / 2 | 2 | 0 |
| Maths confidence, lesson 5 (of 6) | 4 | 4 / 4 | 3 | 4 |
| **Total (of 13)** | **10** | 9 / 8 | **8** | **7** |
| Maths recall (of 13) | 13 | 13 / 13 | 12 (lesson 5 M6) | 12 (lesson 3 M5) |
| Extra gaps at medium or high | 3 | 0 / 1 | **0** | **0** |
| "No self-check": lesson 3 / 4 / 5 (Opus medium / high / high) | — | high / medium / high | high / medium / **high** | high / low / **high** |

**Where the votes still differ from Opus, and why:**
- **Lesson 3 M2 (P⇒Q with a false P), Opus high, votes medium.** One wrong attempt on one problem; Opus's own scoring model (§2: high needs 2 problems) gives medium. The lesson-3 table is stage 1, written before the scoring model.
- **Lesson 3 M5 (proving ∃ false), Opus low "not finished", votes medium or missed:** Luna labels 2945 "wrong", Opus "not finished".
- **Lesson 3 "no self-check", Opus medium, votes high:** the slip rule now feeds every pointed-at fix into the habit; Opus counts three tutor-proposed tests there.
- **Lesson 4, vote B:** brackets medium (a transcript doubt at 2063 lowers it one step; Opus has the same doubt but kept high) and ∀/∃ medium (Luna labels the fix at 2337 "not finished", so it is no slip).
- **Lesson 5 (a + b)², Opus medium, votes low (slip):** the pupil recalls the identity after a hint (1299); Opus counts it unfixed because the tutor then applied it (1321). The slip rule only looks for the tutor saying the fix before the next attempt.

**Reading:** the vote does what it is for — the band result no longer depends on the run (85% twice, 87% between votes) and extra gaps at medium or high are gone. Maths-gap confidence stays at 7–8 of 13 against this benchmark; about half of the remaining misses are rows where the stage-1 lesson-3 table does not follow the scoring model Luna's code implements. A full-model run of lesson 3 (and 6–10) by process 07 would give a consistent benchmark.

### 0.8 One benchmark for lessons 3–8: process 07 full model (2026-11-18)

Process 07 (full model, steps 3–9 of PROCESS.md with scoring-model.md) was run by Claude Opus subagents on lessons 3, 6, 7 and 8 — one fresh subagent per lesson, reading only the anonymised transcript and the process files (no Luna output). Records: `<data>/opus07/<id>.md` (outside the repo; quotes of minors' lessons). Lessons 4–5: Michael's full-model run of 2026-11-17. The new lesson-3 record follows the scoring model (P⇒Q with one wrong attempt is medium, not high; no ∃ gap).

**Maths gaps, votes against this benchmark (28 Opus gaps in 6 lessons):**

| Lesson | Opus gaps | Vote A: recall · confidence | Vote B: recall · confidence |
|---|---|---|---|
| 3 `c1698fb7` | 5 | 5 · **5** | 5 · **5** |
| 4 `b8f9fb8c` | 2 | 2 · 2 | 2 · 0 |
| 5 `3d497118` | 6 | 5 · 3 | 6 · 4 |
| 6 `24aedf8f` | 6 | 4 · 4 | 3 · 2 |
| 7 `514fe1df` | 5 | 3 · 2 | 4 · 3 |
| 8 `fc8fa23d` | 4 | 4 · 2 | 3 · 1 |
| **Total** | **28** | **23 (82%) · 18 (64%)** | **23 (82%) · 15 (54%)** |

- **Extra gaps at medium or high:** vote A 1 (lesson 3, an ∃ item), vote B 1 (lesson 6, a factorising row, high).
- **Learning habits are the weak part:** Opus's high habits (answers before thinking in lessons 3 and 8; no self-check in lessons 4, 5, 7) come out high only in lesson 5; elsewhere medium or low.
- **What is missed:** single-attempt gaps where Luna has no wrong attempt (lesson 6 Δ′ ≤ 0, lesson 7 domain in the sign table), and rows Luna merges with a neighbour (lesson 7 open interval into "values at points").
- **Tutor tables** of process 07 agree with coding v2.1 + script only partly (§0.3); the band numbers in §1 stay against Opus A.

**Reading:** against one consistent benchmark, the vote finds 82% of Opus's maths gaps and agrees on the confidence of 54–64%; it is strongest where the evidence is several wrong attempts (lesson 3: 5/5), weakest on one-attempt gaps and on habits. This is still Opus against Luna, not accuracy; Khanh's hand check (golden-set step 5) is the test.

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
