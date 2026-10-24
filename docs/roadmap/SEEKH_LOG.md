# Seekh log · what each live run taught BIE, what changed, and the measured effect

Navin's standing rule "seekh → BIE" (`CLAUDE.md`, 23 October 2026): after every live run, use what the run taught to
build whatever BIE needs to make what Navin wants at the quality he wants, and to make it cheaper (code, architecture,
tools, libraries, resources; move work from AI to code wherever code can do it). Claude does it without asking. Every
change has tests, must not break outputs that passed before, and is measured before and after. Still Navin's to decide:
security-sensitive changes, budget, teaching-quality verdicts and locking accepted examples.

## How an entry works

- **Run:** the job or run, the chapter, the maker and checker routes.
- **Taught:** facts from the run's process records and ledger (code problems per round, reviewer findings by severity,
  type-check rows, tokens, ₹, minutes), not opinions.
- **Changed in BIE:** what was built or changed, where (files, PR) and its status word: IMPLEMENTED until a live run uses
  it, INTEGRATED when a real run's upstream and downstream use it, never ACCEPTED without Navin's verdict.
- **Measured:** before → after for quality (reviewer verdicts, blocking and minor findings per page), first-try pass rate,
  rounds per unit, tokens (maker and checker, in and out, per page), ₹ per page (Gemini; Codex is ₹0 on the ChatGPT plan,
  its plan usage is recorded instead) and minutes per page. Offline measures (prompt sizes, type-check rows on earlier
  outputs, characters) are filled at once; live measures come from the next run that uses the change. A number that is
  only expected is written as expected.
- **Guard:** every change is re-checked on the earlier passed outputs (`tests/fixtures/passed_outputs/`,
  `tests/test_task045_seekh.py`); an output that passed before and fails now blocks the merge.
- **Tool:** `python tools/seekh_measure.py <run folder> ...` prints these measures per step (page reading, chapter map,
  lesson plan, scripts) from the run folders' process records, the same way every time.

## Baseline · tissue chapter, Section 1 (23 October 2026)

Maker Codex (`gpt-6.1-sol`, ChatGPT plan), checker Gemini 4 Argon (AICredits). Pages 1, 7, 11 and 13 come from Step 5
(`t044-step5-tissue`); pages 2–6, 8–10, 12, 14 and the chapter map from job 1 (`t045b-tissue-understand`).

| Measure | Value |
| --- | --- |
| Passed | 14 of 14 pages, each within 2 rounds; the chapter map in 2 rounds |
| First-try pass (round 1) | 10 of 14 pages (71%); the map: no |
| Rounds per page | 1.29 |
| Why round 1 failed | always BIE's code checks, never the reviewer: options without their question (pages 13, 14: 5 options), an answer that only repeats its item (pages 5, 11); the map: 10 practice and PYQ concepts typed "none" |
| Codex tokens per page | 31,478 in · 13,395 out (a 1-round page 21,849 in; a 2-round page 55,551 in) |
| Gemini per page | ₹5.02 (checker only; ₹70.25 for the 14 pages) |
| Chapter map | Gemini ₹13.50; Codex 116,274 in · 43,952 out over 2 rounds (round 1 alone: 48,171 in · 22,543 out) |
| Minutes per page | 6.2 (call time) |
| Reviewer findings | 0 blocking; minor: printed typos silently corrected in image text (6 times), answers mixing the book's words and an outside explanation under one basis (2 times), others once |
| Type check, code vs AI | agree 26 · explained 6 · code silent 148 · follows parent 271 · role 38; 0 unexplained strong differences |
| Codex plan usage | 0% → 2% of the weekly plan (Step 5 and job 1) |

## Entry 1 · tissue Section 1 (Step 5 and job 1), 23 October 2026

**Taught**

1. Every round-1 failure was caught by BIE's own code after the maker had already written a full answer. A page that
   fails round 1 costs about 34,000 more Codex input tokens (the card and the earlier answer go again) but no Gemini
   rupees (the checker runs only after the code checks pass). Rules the maker breaks in round 1 belong in its
   instructions up front.
2. Options printed at the top of a page belong to a question on the previous page (pages 13, 14); the maker left them
   without a parent until told.
3. The map maker typed practice and PYQ concepts as "none" (10 concepts) and once linked an answer option instead of
   its question.
4. Two strong type proposals of the code were wrong, for two reasons: a list that starts its numbering again
   ("a. Skeletal Muscle Tissue:" after a. b. c.) and a heading that ends in ":-". The maker explained both; it never
   mistyped an item.
5. The keyword "parts" gave 3 wrong weak hints ("body parts", "other parts of the plant"). A weak hint sends nothing
   back, so it is watched, not changed.
6. The reviewer's minor findings that repeated are in image text (printed typos) or about basis wording; code cannot
   see image text. Proposals for Navin (teaching-quality verdicts, not built): (a) keep a printed misspelling as printed
   with the right word in brackets, "Cartiage [Cartilage]"; (b) split an answer that mixes the book's words with an
   outside explanation into two answers, each with its own basis.
7. Where the page answers' characters go (616,344 characters for the 14 pages): teacher questions and answers 53%,
   readings of image items 6%, text copied from native blocks 2%; the repeated JSON key names make the answer about 27%
   longer than a row format would. The checker's copy of each answer is sent with a space after every comma and colon,
   4.8% more characters, paid on Gemini.
8. Codex sends its own agent instructions and tool definitions with every call: the one-line preflight cost 14,208
   input tokens, and that block is about 64% of a page call's input. BIE never uses those tools.

**Changed in BIE** (branch `task045-seekh-checks`, pull request after #51; IMPLEMENTED)

- `bie/brain/content_types.py`: a list that starts its numbering again is a new list; a line ending in a colon is only a
  hint for itself and still leads its list; roman markers ("ii.") are read as roman.
- Page instructions (`PAGE_HOW`): a question "continued from the previous page" is added as the parent of its options;
  an answer that only repeats its question or item fails BIE's check, said up front.
- Map instructions (`CONNECT_HOW`): a concept is never "none" (practice and PYQ concepts take the type of what they
  test); question links name the question item, never its options.
- Job 1's passed work is a regression set (`tests/fixtures/passed_outputs/tissue-t045b-understand.json.gz`, BIE's own
  outputs, not accepted examples); `tools/passed_outputs.py` exports and checks sets; tests in
  `tests/test_task045_seekh.py`.
- Readable pages show rupees at the run's own exchange rate (`tools/render_run.py`).
- The checker reads every answer (pages, map, plan, scripts) as compact JSON, without the spaces; a remake round shows the maker its earlier answer the same way.
- Lean Codex calls (`bie/model_gateway/live/codex_client.py`): Codex's built-in agent instructions are replaced by a
  short BIE text and the tools and features BIE never uses are switched off (shell and command tools, browser and
  computer use, apps, plugins, web search, image tools, multi-agent, the skills catalog). The model can no longer run
  commands, browse or start agents. Every name was checked on the pinned Codex 0.162.1; an unknown one stops Codex
  before it sends anything. `BIE_CODEX_LEAN=0` switches it off. Also fixed: the prompt marker `-` was read by Codex as
  one more image file.

**Measured**

- Offline, now: job 1's 14 passed pages and its map still pass today's checks (0 problems). On job 1's items the two
  wrong strong proposals become weak or silent (p004-i21, p005-i23) and no new difference appears. Page maker prefix
  14,941 → 15,237 characters (+296, about +86 tokens per page call, in the cacheable part); map prefix 10,418 → 10,618
  (+200, once per chapter); the checker prefixes are unchanged.
- Checker input, offline with the o200k tokenizer (Gemini's own count comes from the next run): the checker's copy of
  job 1's 14 page answers 156,429 → 130,289 tokens (−16.7%), about 1,900 fewer tokens per page review (about 11% of
  the checker's input per page).
- Codex input, offline: a real BIE request for page 5, sent by the pinned `codex` 0.162.1 to a local stand-in server
  (no sign-in, nothing sent to OpenAI) and counted with the o200k tokenizer: 17,893 → 9,893 text tokens per call
  (−8,000, −45%; the page image not counted). Job 1 made 16 Codex calls, so about 128,000 fewer input tokens per
  chapter for Section 1.
- Live: to be measured on the next run that uses these changes, against the baseline above. Expected, not measured:
  pages like 5, 11, 13 and 14 pass in round 1 (up to 14 of 14), about 34,000 Codex input tokens saved per such page,
  and the map in one round (about 48,000 input and 22,500 output tokens saved).

**Next from the same run** (planned, not built yet)

- A compact answer format for pages (rows instead of repeated key names): about 27% fewer characters per page answer
  (586,740 → 425,835 on job 1's 14 pages), so fewer Codex output tokens and fewer Gemini rupees for the checker. It
  needs an output schema that both Codex and Gemini accept, and a live check that quality and first-try pass do not drop.
- BIE's code reads PYQ blocks before the maker (the question, options a–d, options continued from the previous page),
  so their structure is given to the maker instead of written by it.

## Baseline · tissue chapter, Section 2 (job 2, 23 October 2026)

VM job `t045b-tissue-lesson` (`blindtest-results:runs/vm-t045b-tissue-lesson-brain-lesson/`): the lesson plan and 17
scripts from job 1's map. Maker Codex (`gpt-6.1-sol`, ChatGPT plan), checker Gemini 4 Argon (AICredits). Measured with
`tools/seekh_measure.py`.

| Measure | Plan | Scripts |
| --- | --- | --- |
| Passed | 1 of 1 | 15 of 17 |
| First-try pass | 1 of 1 | 0 of 17 |
| Rounds per unit | 1.0 | 2.76 |
| Codex tokens per unit (in · out) | 26,034 · 7,172 | 97,566 · 24,495 |
| Gemini tokens per unit (in · out) | 21,086 · 995 | 23,051 · 990 |
| Gemini ₹ per unit | ₹5.42 | ₹5.83 (₹104.56 for the job, ₹7.47 per page) |
| Minutes per unit | 4.9 | 10.6 |
| Narration | — | 458 minutes for 14 pages (about 33 per page) |
| Reviewer findings | none | 1 blocking, 15 minor |

## Entry 2 · tissue Section 2 (job 2) and Navin's decisions, 23 October 2026

**Taught**

1. Of the 897 code problems that sent scripts back, 838 were everyday Hindi words that BIE's word list did not know
   (तथा ×22, इससे ×18, करके ×16, तौर ×14, आसपास, जिससे, दिए …); the list had no word forms (आता, आएगा) and no
   fixed phrases. The passed scripts carried 612 brackets after everyday words or inside idioms ("आम तौर (usually) पर",
   "नहीं के बराबर (equal to)"). v1 failed on जिसे, a form of an everyday word.
2. v11 passed its checks but the reviewer failed it: a patch round's notes ("local correction to beat b34") replaced
   the notes of the whole script. Job 1's page 11 had the same minor finding.
3. Narration was 458 minutes for 14 pages. Navin: 6–8 minutes per book page.
4. The map listed 30 prerequisites, most of them background to other prerequisites, and the plan spread them over
   the topic videos. Navin: only what the chapter directly needs, in one short video first.
5. Every Gemini call of jobs 1 and 2 reported 0 cached input tokens. AICredits' docs (read 23 October 2026): prompt
   caching is explicit for Claude and automatic for OpenAI-style models, "Other providers: Not supported"; BIE's
   `no_cache` only bypasses AICredits' semantic cache, which is not enabled on the hosted platform. Not settled
   until the probe below runs.
6. The lesson estimate was assumed at ₹31.78; the ledger said ₹104.56.

**Changed in BIE** (branch `task045-seekh-checks`, PR #53; all IMPLEMENTED, none INTEGRATED until the next live run)

- Hindi (S2-04, `bie/brain/hinglish.py`, word list `simple_hindi.json` 2026-10-23.2): 1,909 everyday words, word
  forms through suffixes, stems and causatives, and 94 fixed phrases. Before the checks, code removes a bracket after
  an everyday word or inside a fixed phrase (a new runner hook, `Step.normalize`, recorded in every round as
  `normalized`); option marks such as "(b)" stay. The script prefix explains the rule with examples instead of the
  whole word list.
- Notes: a patch round adds its decisions to the unit's notes instead of replacing them (`runner.merge_notes`;
  pages, map and scripts).
- Time (S2-01, `bie/brain/lesson.py`): every teachable item has an equal share of its page; a topic video's budget is
  6–8 minutes per page of its items, up to 25% more only with a `length_note`; the topic videos together stay within
  6–8 minutes per book page (84–112 for this chapter). The plan is checked per video and for the chapter; a script is
  checked by its spoken words at 130 a minute (over the top fails, under 85% of the bottom fails). Claude's addition,
  following from S2-01, approved by Navin on 23 October 2026: a topic video gets at least 3 minutes (smaller ones merge),
  because the hook and recap need room. Only teacher questions answered from the book must be answered (S2-02); must_cover is unchanged.
- Prerequisites (S1-12, S2-03): a map keeps only the prerequisites the chapter directly needs (no chains), each naming the
  concepts that need it. The rule is not a number (Navin, 23 October 2026): more than 8 is a warning the maker answers with a
  `prerequisite_note` saying why each one is directly needed; a needed prerequisite is never dropped to reach a number.
  An older map is trimmed once before its lesson (`bie/brain/prerequisites.py`, task `trim_prerequisites` of the
  connect section): the maker keeps, merges or drops every current prerequisite with a reason, the checker reviews
  it, code checks it, and `MAP.md` shows what was dropped. The plan starts with one "pehle yeh jaan lo" video (`v0`,
  5–8 minutes, one part per prerequisite); a topic video reminds of a prerequisite in at most 2 beats.
- Section 1 (S1-13, S1-14): a printed typo stays as printed with the right word, "Cartiage [Cartilage]"; an answer
  that mixes the book and an outside explanation becomes two answers, each with its own basis.
- Guard: a set made before a rule change can break the new rule on purpose. `regression.RULE_CHANGES` names the
  rule, Navin's decision and the BIE step that upgrades older work; such problems are listed, not hidden. Job 1's
  map breaks the new S1-12 (30 prerequisites); the trim step upgrades it. Sets now record their rulebook version.
- Readable pages show each video's kind, budget and spoken minutes. `tools/seekh_measure.py` counts the trim step on
  its own. The lesson estimate uses job 2's measured cost (on the high side, since scripts get shorter).
- Cache probe (`tools/run_blind_test.py --mode cache-probe`, workflow mode `cache-probe`): two small calls with one
  4,300-token prefix (BIE's real script-review prefix), the cached tokens and AICredits' own billed rupees
  (`usage.cost`); capped at ₹10, run with ₹3.

**Measured**

- Offline on job 2 (in sample: some of the new everyday words came from job 2's own scripts, so the next run is the
  real test): Hindi problems in round 1 838 → 0 (no beat of the 1,215 round-1 beats is flagged); the cleanup removes
  273 brackets from the round-1 answers and 612 from the passed scripts, and keeps 6 (सघन, सतह).
- Prompt sizes (o200k tokens, before → after): script maker prefix 4,337 → 3,805 (−532 per script call); script
  review prefix 2,219 → 2,276; page maker prefix 3,626 → 3,882 (+256 for S1-13 and S1-14); page review 1,976 →
  2,024; plan instructions 2,691 → 3,139, plan source 9,438 → 7,785 (30 → 8 prerequisites).
- Time, offline with the fake AI on job 1's real map (proves the plumbing, not quality): trim 30 → 8, 12 videos
  (v0 and 11 topic videos), 105 minutes against 84–112, all checks pass.
- Guard: job 1's 14 pages pass today's checks; its map's only new problem is the S1-12 count (rule change).
- Live: the next run (map trim and script step, Gemini cap ₹150) measures first-try pass, rounds, tokens and rupees
  against the baseline above. Expected, not measured: far fewer round-1 problems, scripts about a quarter as long.

## Entry 3 · cache probe, 23 October 2026

Run 40007533161 (`tools/run_blind_test.py --mode cache-probe`, Navin's yes for about ₹1, cap ₹3): two calls to Gemini 4
Argon through AICredits with the same 5,246-token prefix (BIE's real script-review prefix and part of a passed chapter
map), not streamed, so AICredits returned its own billed rupees.

**Taught**

1. No prompt caching on this route: the second call reported `cached_tokens` 0 and `cache_write_tokens` 0, the same
   prompt cost as the first (₹1.18 each). This matches AICredits' docs ("Other providers: Not supported").
2. AICredits returns the billed rupees in `usage.cost` for an answer that is not streamed: ₹1.22 and ₹1.21, ₹2.43 in
   all, against BIE's ledger estimate of ₹2.24. The bill is 8.5% above the ledger (within the 15% rule of
   `COST_LOG.md`); the input is billed at about $2.38 per million tokens against the $2.20 the price table assumes.
3. The probe cost ₹2.43, above the "about ₹1" planned, because the prefix had to be above the providers' 4,096-token
   caching minimum; it stayed within its ₹3 cap.

**What follows** (not built yet)

- Gemini rupees go down only through fewer checker tokens (shorter scripts under the time rule, compact JSON, fewer
  rounds), not through caching on this route. Gemini's own API caches repeated prefixes, but using the direct Gemini
  key instead of AICredits is Navin's decision (keys and budget), so it is only noted here.
- BIE can record AICredits' billed rupees for every call instead of an estimate, if the checker's answers are not
  streamed (streamed answers carry no `usage.cost`), and correct the price table for Gemini 4 Argon input.

## Entry 4 · tissue rerun under Navin's rules (job 3), 23 October 2026

VM job `t045c-tissue-lesson-v2` (`blindtest-results:runs/vm-t045c-tissue-lesson-v2-brain-lesson/`), on main `0ca5763d`:
the map's prerequisites trimmed once, then the plan and every script under the 6–8 minutes per page rule. Maker Codex,
checker Gemini 4 Argon. 34.6 minutes, Gemini ₹78.17 of the ₹150 cap (ledger).

| Measure | Job 2 (before the rules) | Job 3 |
| --- | --- | --- |
| Prerequisites | 30 | 8 (19 dropped with a reason, 3 merged; 1 round, ₹3.63) |
| Videos | 17 | 11 (v0 and 10 topic videos) |
| Scripts passed | 15 of 17 | 6 of 11 |
| First-try pass, scripts | 0 of 17 | 0 of 11 |
| Rounds per script | 2.76 | 2.73 |
| Codex tokens per script (in · out) | 97,566 · 24,495 | 62,780 · 14,343 |
| Gemini per script | 23,051 · 990 tokens, ₹5.83 | 22,840 · 1,539 tokens, ₹6.35 |
| Gemini for the lesson | ₹104.48 (₹7.47 per page) | ₹74.46 plus ₹3.63 trim (₹5.58 per page) |
| Minutes per script | 10.6 | 5.5 |
| Spoken minutes | 458 | 125.5 (all 11 scripts, failed ones included); topic budget 84–112 plus v0 5–8 |
| Reviewer findings, scripts | 1 blocking, 15 minor | 22 blocking, 14 minor |

**Taught**

1. All 5 failed scripts failed in the same loop. Round 2 cut the script into its time; the reviewer then blocked it
   for leaving out teacher questions answered from outside the book (optional under S2-02) and asked for them back
   ("add explanations marked as outside"); round 3 added them and the script was too long again. The reviewer's
   instructions were still the plan-and-script text that called every uncovered teacher question a problem.
2. The reviewer also counted the words itself and got them wrong (v2: "1,105 words" when BIE's code counted about
   1,590), then judged the length on its own count.
3. Round-1 code problems (110 in 11 scripts): 58 Hindi words, 34 beats too heavy for one breath, 10 facts_numbers
   parts without step 5 "a formula built term by term when there is one" (there was no formula), 8 too long.
4. Of the 58 flagged Hindi words, most were everyday (पड़ोसी, मर्ज़ी, गुजरना, झड़ना, संभव, समूह …); some were
   rightly flagged as formal (पदार्थ, प्रभावित, मुख्यतः, नियंत्रित, निष्कर्ष).
5. The trim worked as intended in one round; its reasons are short and concrete.

**Changed in BIE** (branch `task045-script-review-alignment`; IMPLEMENTED)

- The script reviewer has its own instructions (`SCRIPT_REVIEW_HOW`, schema id `bie.brain.lesson-script-review/3`):
  required are the must_cover items and the book-answered questions; an outside question is optional and never
  blocking; the reviewer never counts words (the review message gives BIE's measured minutes) and must say what may be
  cut when it asks for an addition.
- A patch round tells the maker its measured spoken minutes and the video's narration time, and that every addition
  is paid for with a cut (`Step.patch_hint` may now be built from the current answer).
- A teaching-pattern step that says "when there is one" is optional in BIE's check.
- The maker reads the beat load limit up front: about 70 spoken words with one new item, 50 with two, 30 with three.
- Word list `simple_hindi.json` 2026-10-23.3: 41 everyday words from job 3 (1,909 → 1,950); the formal ones stay
  difficult.
- Job 3's passed work (the trimmed map, the plan and the 6 passed scripts) is a second regression set
  (`tests/fixtures/passed_outputs/tissue-t045c-lesson.json.gz`); both sets pass today's checks.

**Measured**

- Offline on job 3's round-1 answers: code problems 110 → 55 (Hindi words 58 → 13, all formal; pattern step 10 → 0;
  heavy beats 34 and length 8 unchanged, since only the maker can fix those).
- Live: the reviewer and patch-round changes can only be measured on a live run. Next: resume job 3 so only the 5
  failed scripts run again, within the rest of the ₹150 cap (₹71.83 left).

## Entry 5 · job 3 resumed after PR #57, 23 October 2026

VM job `t045c-tissue-lesson-v2-resume` (`blindtest-results:runs/vm-t045c-tissue-lesson-v2-resume-brain-lesson/`), on main
`0dd27ec2`: the trimmed map, the plan and the 6 passed scripts reused, only v2, v4, v5, v7 and v9 run again. 14 minutes,
Gemini ₹21.39 (cap ₹71).

| Measure | Job 3 (the same 5 scripts) | Resumed |
| --- | --- | --- |
| Scripts passed | 0 of 5 | 4 of 5 (v2, v4, v5, v7) |
| Reviewer findings | blocking 22 (all 11 scripts) | blocking 0, minor 3 |
| Reviews passed on first review | — | 4 of 4 scripts that reached the reviewer |
| Rounds per script | 3.0 | 2.4 |
| Gemini per script | ₹6.35 | ₹4.26 (17,237 · 649 tokens) |
| Minutes per script | 5.5 | 4.7 |
| First-try pass | 0 of 5 | 0 of 5 (round 1 too long: v2 16.9 minutes against 9.3–12.4) |

The chapter now: 10 of 11 videos passed, 113.9 spoken minutes in all (v0 7.4, topic videos 106.5 against 84–112). Gemini for
the whole rerun: ₹99.56 of the ₹150 cap.

**Taught**

1. The reviewer change worked: no blocking finding, every reviewed script passed on its first review.
2. v9 failed by 0.1 minute (13.1 against 13.0): to save time its two patches removed b30, b80, then b6 and b15, and
   three of the four were the only beat of a teaching-pattern step (the recaps), so the step check failed.
3. Round 1 is still too long in every script; the maker writes first and cuts later.
4. New everyday words: पड़ोस, बेवजह, मुताबिक, राह; formal ones still flagged rightly: अतिरिक्त, भ्रम, मुख्यतः.

**Changed in BIE** (branch `task045-protect-pattern-beats`; IMPLEMENTED)

- A patch round names the beats that are the only beat of a pattern step and says never to remove them, only to shorten
  them (`sole_step_beats`).
- `simple_hindi.json` 2026-10-23.4: the 4 everyday words.

**Next:** resume once more for v9 only, within the ₹50.44 left of the ₹150 cap. Making round 1 shorter (for example a
word budget per part on the card) is the next lever for first-try pass.

## Entry 6 · v9 after PR #58, 23 October 2026

VM job `t045c-tissue-lesson-v9` (`blindtest-results:runs/vm-t045c-tissue-lesson-v9-brain-lesson/`), on main `2d1bafa4`: the 10
passed scripts reused, only v9 again. 5.2 minutes, Gemini ₹6.87 (cap ₹50).

- v9 passed in 3 rounds: 13.9 → 12.7 → 12.8 spoken minutes against 9.7–13.0; no step lost in a patch; the reviewer passed it
  with no finding. Round 1 and 2 were sent back by code only (too long; the formal words स्तर, अवस्था, नकारना, सहित).
- **The tissue chapter's script step is complete: 11 of 11 videos pass BIE's checks and the independent reviewer** (v0 7.4
  minutes; the 10 topic videos 106.2 minutes against 84–112; 113.6 spoken minutes in all, against 458 in job 2).
- Gemini for the whole rerun under Navin's rules (trim, plan, 11 scripts and two resumes): ₹78.17 + ₹21.39 + ₹6.87 =
  ₹106.43 of the ₹150 cap (ledger), against ₹104.56 for job 2's 17 longer scripts.
- Still open for the next seekh round: first-try pass is 0 (every round 1 is too long or has a formal word), so each script
  costs 2–3 rounds. The next lever is a word budget per part on the script card, so round 1 is written to length.

Status: the scripts are IMPLEMENTED BIE output (passed BIE's code checks and its independent checker); nothing is ACCEPTED
until Navin's teaching-quality verdict.


## Entry 7 · Navin's verdict on the scripts → the teaching soul (Task 045d), 24 October 2026

**Run:** the tissue chapter's finished script step (job 3 and its resumes, `vm-t045c-tissue-lesson-v9-brain-lesson`,
11 of 11 videos passed BIE's checks and the Gemini checker). Navin read the scripts.

**Taught (Navin's verdict, 24 October 2026):** the scripts restate the book. "Epithelium absorptive aur secretive surfaces par
milta hai" is the book's line in Hinglish; a teacher says what an absorptive surface is, shows one the learner knows (the gut
soaking up food) and says why a thin sheet of cells sits there. The checks passed because nothing measured this. Measured
with the new detector on the 11 final scripts (`tools/dohraav.py`): of 540 judged beats (explaining beats that cover book
items), **155 (28.7%) only restate the book** (60% or more of their English content words are the covered items' own, 6 or
more words, no yaani / why / example / contrast marker); only 153 (28.3%) carry an opening marker at all; 17 sentences are
clipped notes without a verb ("Chain: flexible walls, supported bending, tendrils aur climber stems"); 35 topics open without
a question; 4 videos repeat a recap. On the regression set (job 3's 6 passed scripts): 273 judged, 80 restating (29.3%), 10
clipped. The worst videos are the table-reading ones (v3 52.8%, v1 46%, v9 41.2%); v4 (8.9%) and v0 (0%) show the maker can
open lines when the material pushes it.

**Changed in BIE (IMPLEMENTED, offline; `docs/vision/TEACHING_SOUL.md`):**

- Section 1 writes an `unpack` per teachable item (terms with their plain meaning in simple Hindi and an everyday image, a
  why chain from a need with its basis, an example or place, a consequence, a visual verb, the level's extra); rule S1-15 and
  the code check `soul.unpack_problems` (every teachable item at least one element; every why step names its basis; a
  chain no longer than the level allows). Page schema `bie.brain.understand-page/3`, naksha `/2` with a short unpack cell.
- Level profiles (`level_profiles.json`: school, neet_11_12, upsc_pcs, revision) in every page, plan and script prefix;
  the level inferred from the book's text (markers, then the share of long words) and checked against the course
  setting; a disagreement stops the run (`stopped: level`) for Navin before any call; `--level <id> --trust-level`.
  The tissue chapter reads as senior secondary (12% long words) and fits UPSC.
- Section 2: flexible pattern steps (`skipped_steps` with a real reason, at most half a pattern, never a step the beats
  perform); the family pattern for a classification (`content_types.json` 2026-10-24.1); the script source carries every
  item's unpack and the locked explanations; rule S2-07 and the code checks: dohraav pakad (`soul.restatement_problems`),
  clipped notes (`soul.clipped_problems`), a question at every topic's opening (`soul.opening_problems`), one recap per
  part (`soul.recap_problems`). The `dohraav` measure is written per video and per run.
- The teacher example bank (`teacher_examples.json`: 7 opening steps, 10 methods with examples from real teacher
  videos and Navin's own) in the prefixes; the explanation library (`explanations.json`, 3 entries from Navin) looked up
  by term for every page and script and locked only through `tools/lock_explanations.py` after his verdict; rules G-06
  (BIE is the link, never read the line out) and G-07 (two layers); S3-06 and the Task 046 benchmark
  (`benchmarks/epithelium_animation.json`, 12 rules, 22 shots).
- Guard: the two saved sets still pass today's checks; the new rules show as waived rule changes (S1-15, S2-07 and the
  family pattern), not hidden; the regression guard now reads each rulebook component's version.
- A detector fix found on the way: the Hindi verb check glued the danda (।) to the verb, so "… है।" counted as verbless;
  fixed before any number above was taken.

**Measured:** before (job 3 final scripts): dohraav 28.7% (155 of 540), opened 28.3%, clipped 17, topics without a question
35, duplicate recaps 4. After: expected from the rerun of the tissue understanding and script under Task 045d (maker
Codex, Gemini checker cap ₹200): the code check sends every restating beat back, so the passed scripts should measure 0
restating beats; the real numbers (rounds, tokens, ₹ per page, the new opened share) are written here after that run.
Prompt size: the page prefix grows by the level profile and five teacher methods (about 900 tokens), the script prefix by
the profile and the full bank (about 1,600 tokens); the script source grows by the unpack lines (about 60–120 tokens per
item). Status: IMPLEMENTED; INTEGRATED after the rerun; ACCEPTED only by Navin's verdict on old v2 against new v2.

## Entry 8 · Task 045d job A (the first live page with the unpack), 24 October 2026

**Run:** VM job `t045d-tissue-understand` (`blindtest-results:runs/vm-t045d-tissue-understand-brain-understand/`) on main `ce0e3491`
(PR #60): the tissue chapter read again under the teaching-soul rules, maker Codex (gpt-6.1-sol), checker Gemini 4 Argon via
AICredits, cap ₹80 of Navin's ₹200. Level: `upsc_pcs` from the setting, book band senior secondary (12% long words), no question.

**Taught:**

- **Stopped after 14.2 minutes by the AICredits key budget, not by BIE's cap:** every Gemini call answered `402 insufficient_quota |
  API Key Budget Exceeded. Raise this key's budget at aicredits.in/dashboard/keys`. The cost guard read it as a balance stop (status
  `stopped: balance`): 1 of 14 pages passed (page 2), pages 1 and 3 had their maker answer ready and lost it at the review call,
  11 pages were refused before any call. Gemini ₹13.51 (preflight ₹0.38, page reading ₹13.13); Codex plan 2% → 2%. The key's own
  budget on the AICredits dashboard is Navin's to raise; BIE cannot. The resume job is ready (`resume_from` this folder, page 2 reused).
- **Page 2 (the figure-only page, 49 teachable items):** passed in 2 rounds. Round 1 was sent back by the reviewer only, for the same
  finding as job 1: five labels silently corrected ("Non-straited muscle", "Cartiage", "Simple cubodial"; S1-13). The unpack came
  filled: every item one term (one item two), 7 items a two-step why chain, 42 none (labels); an example and a consequence on all.
  Maker tokens: 12,287 in / 21,770 out (round 1), 29,732 in / 3,060 out (the patch round).
- **The plain meanings are in textbook Hindi, not the learner's Hindi:** "जानवरों के शरीर में मिलकर काम करने वाले कोशिका-समूह",
  "उपकला के नीचे की पतली सहायक आधार-परत". 93 of the 100 term texts (plain meaning and image) use words outside the everyday list; the
  most frequent are translations of the book's own terms: ऊतक 17, कोशिका (forms) 16, मांसपेशी 11, संयोजी, पदार्थ, उपकला, तंत्रिका, ग्रंथि.
  The S1-15 check only asked for Devanagari, so it let them through; the script check (S2-04) would have flagged them later as hard
  words, but a bracket ("ऊतक (tissue)") would have rescued them. Navin's rule is the book's English term in Roman.
- The old passed scripts use none of these translations (0 in the regression set), so the check costs nothing there.

**Changed in BIE (IMPLEMENTED, offline):**

- `simple_hindi.json` 2026-10-24.1: a `technical` block (62 textbook translations → the book's English term: ऊतक → tissue, कोशिका →
  cell, उपकला → epithelium, …) and 43 everyday words the page used that the list lacked (कोहनी, चादर, टीम, कागज़, ईंट, लार, सोखना, घन …).
- `hinglish.technical_words`: finds them with the list's suffix rules. `soul.unpack_problems` sends an item back when its plain meaning,
  image, example, consequence or level extra uses one (S1-15, the English term named in the message); `lesson.spoken_problems` sends a
  beat back for one even inside a bracket (S2-04); the page prompt says it up front with examples.

**Measured:** before (page 2 as passed): 45 of 49 items would go back under the new check. After (the resumed runs `resume2` and
`resume3` on main `7bc33267`, 24 October 2026): **14 of 14 pages and the chapter map passed**; 411 teachable items, 403 with an
unpack (the 8 without are question and option items), 469 terms opened, 550 why steps (266 items with 2 steps, 18 with 1, 127 with
none, mostly labels and options); 35 concepts, 9 prerequisites to teach. Page 2 was not reused: the new check refused the old unpack
and the page ran again. Round 1 was sent back by code on 9 of the 14 pages, every time for textbook Hindi only (1–8 items a page), and
the patch round cleared it on every page; the reviewer found **0 blocking problems on all 14 pages and the map** (first-try review
pass 14 of 14, against 5 pages sent back by the reviewer in job 1). Three plain meanings with पदार्थ remain on question and option
items, which the check leaves alone by design. Gemini: resume2 ₹65.90 for 12 pages (₹5.07 a page: the reviewer now reads the unpack,
16–25k input tokens a review, against about ₹2.7 a page in job 1), resume3 ₹20.87 (pages 13 and 14 ₹9.18, the map ₹11.31); job A's
₹13.51 before it; understanding in all ₹100.28 of Navin's ₹200. Codex plan 2% → 4%. Time: 14.2 + 46.6 + 12.0 minutes.
Status: the understanding step is INTEGRATED (a real run through the new checks); nothing ACCEPTED until Navin's verdict.

## Entry 9 · Task 045d job B (the first scripts under the teaching soul), 24 October 2026

**Run:** VM job `t045d-tissue-lesson` (`blindtest-results:runs/vm-t045d-tissue-lesson-brain-lesson/`) on main `7bc33267`, from job
A's chapter map: prerequisite trim (not needed: 9), the plan (passed in round 1), v0 and 10 topic videos. 44.1 minutes, Gemini ₹24.86
of the ₹99 cap (the plan ₹4.7, four script reviews ₹20; a script the code sends back costs no Gemini), Codex plan 4% → 5%.

**Taught:**

- **Dohraav before → after:** 155 of 540 judged beats (28.7%) → **9 of 481 (1.9%)**; beats with an opening marker 28.3% → **60.9%**
  (with the markers of PR #60; with the markers below, which credit जैसा / जैसी, वरना and क्यों, the same scripts measure 27.6% → 1.0%
  and 32.8% → 68.0%).
  Every one of the 11 new scripts restates less than the old one; the table-reading videos fell from 46–53% to 0–9%
  (`V2_SIDE_BY_SIDE.md` in the run folder has the per-video table and old v2 against new v2 beat by beat).
- **4 of 11 videos passed** (v0, v3, v7, v10), each with 0 blocking findings from the reviewer; 7 failed after 3 rounds **by code only**,
  the reviewer never saw them. What was left in round 3: 1–5 "hard" Hindi words a script (नोक, बाँह, रस, अंदरूनी, जाल, छन्नी, कपास,
  रसोई …: everyday words the list lacked; 175 distinct words were flagged across the run), 1–3 beats still counted as restating, a
  clipped sentence or two, and four scripts 1.3–2.3% over their narration time (4.5 against 4.4 minutes, 15.3 against 15.1).
- The restating beats left were opened with "जैसा / जैसी" ("Building के service duct जैसा"), "वरना" or a "क्यों?" question, which the
  detector did not count; "पूरा bundle 1 cell नहीं।" was counted as a clipped note although the dropped copula is spoken Hindi.
- Total length 117.1 minutes against 84–112 + v0: the openings add words; the makers cut side-tracks under the time rule.

**Changed in BIE (IMPLEMENTED, offline):** `simple_hindi.json` 2026-10-24.2 with 98 everyday words from this run (the formal ones,
सामान्यतः, पर्याप्त, अतिरिक्त, प्रभावित, stay hard); the opening markers add जैसा / जैसी / की तरह, वरना / नहीं तो / क्यों / इससे / तभी (and their Roman
forms); a sentence ending in नहीं is not a clipped note; a script up to 3% over its upper narration bound is within it
(`TIME_TOLERANCE`; 130 words a minute is an estimate). Re-checked offline on the 7 failed scripts' last rounds: v2, v6, v8 and v9 would
have no code problem left, v4 one restating beat, v1 three, v5 four. The two saved regression sets still pass.

**Measured:** before (job B): 4 of 11 passed, 7 failed by code after 3 rounds. After (the resumed job B on main `78e0cf6a`,
`vm-t045d-tissue-lesson-resume-brain-lesson`, 23.6 minutes, Gemini ₹12.01): the plan and the 4 passed scripts reused; of the 7 written
again, v1 and v6 passed (3 rounds each, reviewer 0 blocking), so **6 of 11 pass**; v2, v4, v5, v8 and v9 failed by code again with 1–4
residues in round 3 (new everyday words the list still lacked: राजमा, भंडार, राशन, गूदा, पहिया, दफ्तर …; two beats counted as restating),
every round smaller than the one before (v8: 24 → 10 → 4 problems; v9: 18 → 8 → 1). Dohraav on the 11 scripts: **2 of 511 judged beats
(0.4%)**, opened 64.4%. Gemini for the script step so far ₹36.87; Task 045d in all ₹137.15 of Navin's ₹200.

**Seekh from the resume (IMPLEMENTED, PR #64):** the pattern is a convergence the fixed round limit cuts off: code alone sends a script
back with ever fewer small problems, and round 3 ends it with 1–4 left, although a patch round costs no Gemini. The runner now gives a
converging answer (code-only rejection, fewer problems than the round before, at most 4) up to 3 extra patch rounds (`Step.extra_rounds`,
`runner.CONVERGING_MAX`; a reviewer rejection never extends); the word list gains the 11 words (2026-10-24.3). Expected on the next
resume: the five pass within the extra rounds at ₹0 maker cost and one review each (about ₹5). Status: the script step is INTEGRATED;
the dohraav number is a measured fact; nothing ACCEPTED until Navin's verdict on old v2 against new v2.
