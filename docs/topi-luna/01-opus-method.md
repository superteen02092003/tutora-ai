# How Claude Opus analyses a lesson (the benchmark Luna is tuned against)

**Opus does two separate jobs on one transcript, each in small explicit steps: (1) it labels moments (tutor and pupil events, each with segment, time and verbatim quote) and a script turns the labels into the ten tutor-standard bands; (2) it labels every pupil attempt (alone · after hint · wrong · not finished), groups attempts by skill, and only then decides which are gaps, how confident, slip or misconception.** Written 2026-11-17 for Michael, from toptutor-main at `3c6f740`. Sorted by the order Opus works.

Sources (toptutor-main): `40-processes/07-gap-analyser/PROCESS.md` and `scoring-model.md` (gaps), `runs/2026-11-17_golden-lessons-3-4.md` (Opus gap output), `60-output/01-prompts/lesson-coding-v2.md` (tutor-quality labels), `60-output/02-specs/tutor-standard.md`, `session-quality-score.md` (stability runs), `golden-set-v2.md`, `10-knowledge/topi-ai-evidence.md`. Opus label files of the 10 golden lessons (runs A, B for v2; A2, B2 for v2.1) sit outside the repo, in Khanh's session scratchpad, because they hold transcript quotes.

## 1. Tutor quality (score B) — "lesson coding v2.1"

| Step | What Opus does | Rule that makes it repeatable |
|---|---|---|
| 1 | Reads the whole transcript once | — |
| 2 | Splits it into blocks: `OPEN · HW_CHECK · RECALL · INSTRUCT · DICTATE · GUIDED · INDEPENDENT · FEEDBACK · WRAPUP · MOTIVATE · ORGANISE · OFFTASK` | productive time = HW_CHECK, RECALL, INSTRUCT, GUIDED, INDEPENDENT, FEEDBACK (computed by script) |
| 3 | Lists exercises: kind, first actor, first help, result | **one exercise = one task posed** (read out, dictated, named); lettered parts separate; follow-ups, hints, checks are not new exercises; homework set at the end is not one |
| 4 | Labels tutor events (14 types) | sharp definitions with Vietnamese examples: `question_open` asks for a step, method or reason; `question_check` expects "dạ / rồi" ("yes"); `gives_answer` only while the pupil works, never in a worked example |
| 5 | Labels pupil events: response, spontaneous skill, error (8 types), self-correction | `self_correction.after = error_pointed` when the tutor pointed first |
| 6 | Marks acknowledgement-only pupil turns ("dạ", "vâng" — "yes") | the script leaves them out of talk share |
| 7 | Check pass: re-reads every label against its quote, removes the unsupported | — |
| 8 | **Never scores.** A script (`score_v2.py`) computes the ten behaviours and bands | bands from `tutor-standard.md`, *Reference* table |

**What Opus achieves:** two independent v2.1 runs land in the same band in ≥ 9 of 10 lessons for 8 of 9 measurable behaviours; only learning-skill chances is 7/10 (`session-quality-score.md`, 2026-11-09). Event κ between runs ≥ 0.70 except `gives_answer` 0.17, `question_check` 0.67, `spontaneous_skill` 0.68. This is stability, not accuracy: the hand check has not been done.

**Output shape** (per lesson, JSON): `segments[]`, `exercises[]`, `tutor_events[]`, `pupil_events[]`, `ack_segments[]`, `flags[]`, `homework_set`, `check_pass_removed`. A typical golden lesson: 9–16 blocks, 5–23 exercises, 11–40 tutor events, 6–22 pupil events.

## 2. Pupil gaps — process 07 (gap analyser)

| Step | What Opus does | Rule |
|---|---|---|
| 1 | Splits into blocks; notes grade, topic, length | — |
| 2 | **Labels every pupil attempt**: correct alone · correct after a hint · wrong · not finished | a pointed question ("có dấu bằng không?" — "is there an equals sign?"), a supplied number or "nghĩ lại" ("think again") **is a hint**; an answer to a leading question, or a result only the tutor states, **is no evidence** |
| 3 | Groups attempts by skill, matches a skill-map node | skill outside the map is named in plain words |
| 4 | **A gap needs ≥ 1 wrong attempt or ≥ 1 hint**; the rest is "shown correct" | a hint caps the level at improving; a skill first seen today is never standard |
| 5 | Slip or misconception | fixed alone once pointed at = slip, and the habit behind it is a learning-skill gap; repeated error = maths gap |
| 6 | Learning-skill gaps from a fixed habit list | every one carries a quote; a tutor's report about an earlier lesson alone is low confidence |
| 7 | Confidence by counting independent evidence (`scoring-model.md` §2) | maths high: ≥ 2 wrong/hinted attempts on different problems; medium: 1 wrong not fixed alone, or same error twice on one problem; low: a slip, tutor remark only, or a transcript doubt. Learning skill high: ≥ 3 instances with ≥ 1 of the pupil's own acts |
| 8 | Records doubts: leading questions, duplicated segments, inconsistent numbering, dates | doubts lower confidence one step |

**Output shape** (lesson 3, `c1698fb7`, grade 10, propositions): five maths gaps, e.g. *M1 Negating strict and non-strict inequalities — misses the equals case — attempts 1271 wrong · 1439 wrong, after hint 1494 · 2835 wrong, after hint 2896 · 3385 correct alone — to do — high*; three learning-skill gaps, e.g. *L1 Answers before thinking — tutor: "Hấp tấp quá" ("too hasty", 1514) …— improving — high*; then "shown correct" and "doubts". Lesson 4 (`b8f9fb8c`): two maths gaps, two learning-skill gaps. Total 7 maths and 5 learning-skill gaps; the reviewer has not graded them yet, so H-06 has no number.

## 3. What makes Opus good here — and what Luna must be given instead

| Opus does it unprompted | Luna needs it written down |
|---|---|
| Works in passes: blocks → exercises → attempts → gaps | One call per pass, each with a narrow task and its own schema |
| Quotes first, judges after | Each item has `quote` before `label` in the schema, so the model writes the evidence first |
| Knows a hint when it sees one in Vietnamese | The hint list and 2–3 worked examples (few-shot) taken from Opus output |
| Counts evidence before saying "high" | Code counts; the model never writes a confidence or band |
| Keeps "shown correct" and "doubts" | Explicit fields, so absence of a gap is visible |
| Uses one consistent voice | Fixed terms in the prompt ("bạn" for the tutor, "con" for the pupil) |
