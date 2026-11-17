"""Topi analysis v2 — instructions for gpt-6-luna, one narrow job per call.

Why this file exists: Claude Opus does the gap analysis (toptutor-main process 07) and the
tutor-quality coding (lesson-coding-v2.1) in explicit passes; Luna in one big call misses
hints, merges exercises and writes gaps without evidence (ai-content-audit-2026-11-16).
Each pass here: a narrow task, quote BEFORE label in the schema, a closed list of values,
few-shot lines taken from Opus labels of golden lessons 9–10 (b6322916, 80c2b8ce — never
from the lessons the eval scores), strict JSON schema. The model never scores, counts,
ranks or writes a confidence: analysis.py does that in code.
Description of the Opus method: docs/topi-luna/01-opus-method.md.
"""

COMMON = """You read a transcript of a 1:1 maths lesson in Vietnamese. Input: JSON segments {i, start, speaker, text}; speaker is tutor, student or unknown. The transcript is anonymised.
Hard rules for every item you output:
- "seg" is the index i of ONE segment, and "quote" is copied VERBATIM from that segment's text: the shortest words that prove the item, at most 25 words. Never paraphrase, never join two segments, never fix spelling. No quote, no item.
- Write the quote first, then decide the label from the quote. If the quote does not show the label, drop the item.
- Not audible, not labelled. Nothing about attention, memory, mood, effort or any condition.
- Output exactly the JSON schema given. Use "" or null for an empty field, never invent a value."""

# ---------------------------------------------------------------- pass 1
STRUCTURE = COMMON + """

JOB: the lesson's structure. You do not judge anyone.

1. "blocks": split the whole lesson into consecutive blocks {type, start_seg, end_seg}. Types:
   OPEN (greeting, mic check) · HW_CHECK (last lesson's homework) · RECALL (questions on earlier content) · INSTRUCT (tutor explains or shows a worked example) · DICTATE (tutor reads out a task to copy) · GUIDED (pupil works with the tutor's questions) · INDEPENDENT (pupil works alone, e.g. a quiz) · FEEDBACK (going through finished work) · WRAPUP · MOTIVATE · ORGANISE (scheduling, setting homework) · OFFTASK.
2. "exercises", in order. ONE EXERCISE = ONE TASK POSED: a new exercise starts only when a new task is read out, dictated or named ("bài 3", "câu b", "làm bài này" — "exercise 3", "part b", "do this one"). Each lettered part (a, b, c) is its own exercise. A follow-up question, a hint, a check or a correction on the same task is NOT a new exercise. A worked example the tutor shows during INSTRUCT is NOT an exercise. Homework set at the end is NOT an exercise. An oral question in HW_CHECK or RECALL that asks the pupil for a definition, rule or result IS an exercise (kind review).
   Fields: task_seg and task_quote (the words that pose the task), start_seg, end_seg, kind (new_concept = first use of a rule introduced in THIS lesson; practice; review), skill (the maths skill it practises, 3–8 Vietnamese words, e.g. "phủ định mệnh đề chứa dấu bất đẳng thức"), skill_node (one id from the node list, "" if none fits), first_actor (who works on it first after it is posed: pupil | tutor), first_help (the first help the tutor gives: none | hint | step | answer), result (pupil_alone | pupil_with_help | tutor_solved | not_finished).
3. "homework_set": the tutor's sentence that sets homework {seg, quote}; {"seg": null, "quote": ""} if none.
4. "ack_segments": indexes of student segments that are ONLY acknowledgement ("dạ", "vâng", "ừ", "em hiểu rồi", "con hiểu rồi" — "yes", "OK", "I understand") with nothing else.
"""

# ---------------------------------------------------------------- pass 2
TUTOR_EVENTS = COMMON + """

JOB: label what the TUTOR does. Quotes come from tutor segments only. You get the exercise list; give exercise_id when the event belongs to one, else "".

Types (one event per moment; a segment may carry two events):
- question_open: asks the pupil for a step, method, reason or next move ("Em sẽ bắt đầu thế nào?" — "How will you start?", "Rồi bảng xét dấu?" — "And the sign table?", "Tại sao?" — "Why?"). A question asking only for a number the pupil is computing right now is NOT labelled.
- question_check: yes/no or comprehension check whose expected answer is "dạ / rồi / đúng" ("Hiểu chưa?" — "Got it?", "Đúng không?" — "Right?").
- self_answered: the tutor asks a question and answers it before any pupil segment. Example: "Có cách nhanh hơn không? Ba x bình luôn lớn hơn hoặc bằng không, vậy chỉ cần m lớn hơn hoặc bằng không là đủ." ("Is there a faster way? 3x² is always ≥ 0, so m ≥ 0 is enough.")
- gives_answer: WHILE THE PUPIL IS WORKING on an exercise, the tutor states its result or the step the pupil was meant to find. Example: "Bảng có ba mốc: trừ một, không, một." ("The table has three points: −1, 0, 1."). A worked example during INSTRUCT is NOT gives_answer.
- explain_prompt: asks the pupil to say what they do or why ("Con làm sao?" — "How did you do it?"). EVERY explain_prompt ALSO gets a second event: chance with skill explains, same seg.
- error_pointed: after a pupil error, names or points at the wrong step or the rule it breaks, without saying the corrected step ("Này, con lại viết hợp." — "Look, you wrote 'union' again.", "Dấu ở dòng hai sai rồi." — "The sign on line two is wrong.", "Con xem lại quy tắc nhân hai vế với số âm." — "Check the rule for multiplying both sides by a negative."). It counts even when phrased as a question ("Bước đầu tiên là gì?" — "What is the first step?" right after the pupil skipped it: error_pointed AND question_open, same seg) and even when the tutor ends up giving the fix later: then label BOTH, error_pointed on the pointing seg and error_resolved_by_tutor on the seg where the fix is said. Check every pupil error: when the tutor's next turn reacts to it, it is error_pointed, error_resolved_by_tutor, or both.
- error_resolved_by_tutor: after a pupil error on the same exercise, the tutor says the corrected step or whole solution instead of the pupil.
- homework_checked (how: pupil_fixes | marked_only): checks last lesson's homework or a task set last time ("Ừ, thầy xem rồi. Mình chữa luôn." — "OK, I've looked. Let's correct it now." → pupil_fixes). Look for it in the first minutes: ANY request to show, read out or go through work done since the last lesson counts ("Bài về nhà hôm trước con làm chưa?" — "Did you do last time's homework?", "đưa vở cô xem" — "show me your notebook", "đọc đáp án" — "read your answers"). Label it once, on the tutor's first such request. how = pupil_fixes when the pupil corrects any wrong item, else marked_only.
- wrapup_by_pupil_prompt: asks the pupil to recall what was learned ("Thầy hỏi chốt lại nhé. Điểm cực trị với giá trị cực trị khác nhau chỗ nào?" — "A last question: how do the extremum point and the extremum value differ?").
- wrapup_by_tutor: the tutor summarises ("Thầy tổng kết buổi này." — "Let me sum up this lesson.").
- praise_process: praises a step, method or effort, naming it ("Con để ý đoạn 'ngoài hai nghiệm cùng dấu với a' con áp dụng đúng luôn." — "You noticed 'outside the roots, same sign as a' and applied it right.").
- praise_person: praises the person or ability ("Con nhẩm nhanh phết." — "You calculate fast in your head.").
- criticism_person: criticises who the pupil IS — ability, intelligence, character ("con dốt thế" — "you are so dumb", "con lười lắm" — "you are very lazy"). A remark on HOW the pupil worked just now ("Hấp tấp quá" — "too hasty", "ẩu" — "careless", "sai dấu rồi" — "wrong sign") is about the work: NOT criticism_person (it may be error_pointed).
- chance (skill: reads_task | plans | checks | explains | persists | asks_for_help): creates a moment for a learning skill ("Con đọc thầy nghe đề." — "Read me the task." → reads_task; "Con thấy chỗ nào cần để ý chưa?" — "Do you see anything to watch out for?" → checks).
"how" is "" except for homework_checked; "skill" is "" except for chance.

"flags": tutor_math_error_uncorrected (the tutor states a wrong maths result and it stays) or criticism_person, each {type, seg, quote}.
"""

# ---------------------------------------------------------------- pass 3a
ATTEMPTS = COMMON + """

JOB: the pupil's attempts, for finding gaps. You label; code decides what is a gap.

1. "attempts": EVERY time the pupil gives an answer, a step or a judgement on a maths task, one item. Fields, in this order:
   - exercise_id (from the list; "" if none fits), seg, quote: the PUPIL's own words (a student segment).
   - hint_seg, hint_quote: the tutor's help between the task and this answer, if any; else null and "".
   - label:
     * alone: correct, with no help since the task was posed.
     * after_hint: correct, but only after help. HELP COUNTS AS A HINT: a pointed question ("có dấu bằng không?" — "is there an equals sign?", "Chắc chưa?" — "Sure?"), a supplied number or case ("thử x bằng 0 xem" — "try x = 0"), "nghĩ lại" / "xem lại" ("think again" / "look again"), a named wrong step.
     * wrong: incorrect (also: "không biết" — "don't know").
     * not_finished: started, did not reach an answer.
   - NOT AN ATTEMPT (leave out): an answer to a leading question whose answer is in the question ("…đúng không con?" — "…right?" answered "dạ đúng" — "yes, right"); a result only the tutor states; "dạ" alone.
   - fixed_alone_after_pointing: true when this attempt is wrong and the pupil's NEXT attempt on the same exercise is correct after the tutor only pointed at the error (no step given).
   - skill: the maths RULE this attempt tests, 3–8 Vietnamese words. Name the rule, not the exercise, and use the SAME words for every attempt that tests that rule, across all exercises and blocks (homework, quiz, new topic). Example: solving 2x − 4 = 0 in homework, 3x + 1 = 7 in a quiz and moving terms in x² − 5x = −6 all test "chuyển vế đổi dấu" ("moving a term across the equals sign changes its sign"); finding y' of x³, of 1/x and of √x all test "đạo hàm hàm cơ bản" ("derivatives of basic functions"). Before you output, merge skills that differ only in wording.
   - skill_node: one id from the node list, "" if none fits.
   - what_went_wrong: for wrong / after_hint / not_finished, one short English line saying the error ("misses the equals case when negating >"); "" for alone.
   - error_pattern: for wrong / after_hint / not_finished, the underlying MISTAKE in 2–6 English words, independent of the topic, e.g. "forgets the domain condition", "adds numerators and denominators". When the same mistake shows up again — even in another topic, exercise or block — write EXACTLY the same words. Different mistakes get different words. "" for alone.
2. "habits": moments that show a learning habit. habit is one of: answers_before_thinking · no_self_check · no_written_working · drops_known_rule_under_test · gives_up_early. Each {seg, quote, speaker: pupil | tutor, habit, about_earlier_lesson}. A tutor remark counts ("Đọc kỹ đề rồi hãy trả lời" — "read the task carefully before answering" → answers_before_thinking; "Làm xong phải thay lại kiểm tra chứ" — "when done you must substitute back to check" → no_self_check); about_earlier_lesson = true when the remark is about a past lesson. A GOOD habit shown unprompted is not listed here.
3. "doubts": moments where the transcript itself is unreliable: an unclear word, a duplicated segment, inconsistent task numbering, a date that does not fit. {seg, note}.
"""

# ---------------------------------------------------------------- pass 3b
PUPIL_EVENTS = COMMON + """

JOB: label what the PUPIL does, for the tutor-quality score. Quotes from student segments only. You get the exercise list and the tutor's chances (seg, skill).

Types:
- response: answers a tutor chance; chance_seg = that chance's seg; skill = the chance's skill; quality full | partial | none (none = no answer or only "dạ", "vâng"). Example: "y phẩy bằng trừ ba x bình cộng sáu x. Cho bằng không thì x bằng không hoặc x bằng hai." ("y' = −3x² + 6x; set to 0, x = 0 or x = 2") → response, explains, full.
- spontaneous_skill: uses a skill with no chance just before (skill reads_task | plans | checks | explains | persists | asks_for_help). Example: "lúc đầu con định ghi ngoặc vuông ở số 3, nhưng nghĩ lại A có 3 đâu ạ." ("at first I was going to write a square bracket at 3, but then A doesn't contain 3") → checks.
- error: a wrong step; error_type concept | method | calculation | sign_or_bracket | misread_task | notation | slip | did_not_finish. Example: "đồng biến trên trừ căn hai đến không hợp căn hai đến cộng vô cùng." ("increasing on (−√2, 0) ∪ (√2, +∞)") → notation.
- self_correction: the pupil fixes their own error, producing the corrected step THEMSELF; after error_pointed (the tutor only pointed at the error first) or none. Example: "A, dạ. 'Và'. Con quên" ("Ah, yes. 'And'. I forgot") → after error_pointed. NOT a self_correction: the pupil repeats or accepts a correction the tutor already said (tutor: "Chia cho v bình phương con ơi." — "Divide by v squared."; pupil: "À dạ. Vậy là 7 trên x cộng 3 bình phương." — "Ah yes, so 7 over (x+3) squared.") — leave it out. Use the tutor's error moments below: after a seg marked resolved_by_tutor, the pupil's next right answer is not a self_correction.
Fields not used by a type are "" (or null for chance_seg).
"""
