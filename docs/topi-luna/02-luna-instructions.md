# Instructions for gpt-6-luna: Topi analysis v2

**Luna gets four narrow calls instead of one, each with quote-before-label, closed value lists, few-shot lines from Opus output, and a strict JSON schema; code then checks every quote, decides what is a gap, sets confidence, ranks, and scores the tutor standard.** Written 2026-11-17 on branch `feat/topi-luna-opus-parity` (tutora-ai). Not wired into `pipeline.py`: production still runs v1 until the comparison in [03-eval.md](03-eval.md) passes. How Opus works: [01-opus-method.md](01-opus-method.md).

## Where v1 (production) differs from Opus

Sorted by how much each costs quality.

| # | Topi v1 with Luna (`evidence.py`, `plan.py`, `tips.py`) | Opus (process 07, coding v2.1) | Effect seen |
|---|---|---|---|
| 1 | **No attempt labels.** A gap is any `error` event with a skill node (`plan.rank_gaps`) | Every attempt labelled alone · after hint · wrong · not finished; a hinted correct answer counts | Misses gaps where the pupil is right only after a hint; no "shown correct" |
| 2 | **One call does everything** (exercises, 14 tutor types, 4 pupil types, flags) | Separate passes | Long output, types dropped or merged |
| 3 | **Definitions shortened** from coding v2.1 (no examples for `question_open` vs `question_check`, `gives_answer`) | Full definitions with examples | The least stable types are the ones cut |
| 4 | **No blocks, no acknowledgement turns** | Blocks give productive time; "dạ" ("yes") turns left out of talk share | Talk share over the whole lesson |
| 5 | **No confidence, no slip test, no learning-skill gaps** | Counted evidence (scoring-model §2) | Every gap looks equally sure |
| 6 | `wrong`/`right` must be SymPy identities, else blanked | Plain-language "what goes wrong" + quotes | Audit: all 7 gaps without "Sai / Đúng" ("wrong / right") for grade 10 |
| 7 | Ties ranked by node code | — | Audit: focus gap = lowest code |
| 8 | `json_object` mode, reasoning medium | — | Field names drift; fewer hints spotted |

## What v2 does (code: `app/services/topi/analysis.py`, prompts: `analysis_prompts.py`)

| Pass | Model or code | Output |
|---|---|---|
| 1 Structure | Luna | blocks, exercises (one task posed = one exercise), homework sentence, acknowledgement turns |
| 2 Tutor events | Luna, given the exercises | 14 event types with v2.1 definitions and Opus examples; flags |
| 3a Attempts | Luna, given the exercises and skill nodes | every pupil attempt with label, hint quote, "fixed alone after pointing", skill, what went wrong; habit moments (closed list of 5); transcript doubts |
| 3b Pupil events | Luna, given the exercises and the tutor's chances | response, spontaneous skill, error, self-correction |
| Check | code (`checker.check_labels`) | quote verbatim in its segment, right speaker; hint quote must be in a tutor turn |
| Gaps | code | gap = ≥ 1 wrong / hinted / unfinished attempt; confidence by distinct problems; slip → low + `no_self_check` habit; doubt → one step lower; level never "standard" on first sight; rank by confidence, problems, attempts, lower grade |
| Tutor standard | code (port of `score_v2.py`) | the ten behaviours' values and bands |

**Prompt rules applied:** quote first in every schema object; closed enums; Vietnamese examples with English; few-shot only from golden lessons 9–10 (never the lessons scored); strict JSON schema (`llm.generate_json(schema=…)`); `reasoning_effort` high (the 2026-11-11 comparison found high no better than medium for v1; v2's passes are short, so the cost is smaller — check in 03).

## What is not done yet

- **Wiring into `pipeline.py`** and the API response (`topi-api-contract.md` change first).
- **Tips and plan on v2 output:** the plan's "Sai / Đúng" should use the attempt quotes; tips should pick the tutor's lowest band. Voice rules from the audit (S4: "bạn" for the tutor, "con" for the pupil) are not in this branch.
- **Across sessions:** states, stars and medals (scoring-model §3–4) need earlier sessions' gaps.
