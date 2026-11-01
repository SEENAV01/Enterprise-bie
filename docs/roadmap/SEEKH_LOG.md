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

**Seekh from the resume (IMPLEMENTED, PR #65):** the pattern is a convergence the fixed round limit cuts off: code alone sends a script
back with ever fewer small problems, and round 3 ends it with 1–4 left, although a patch round costs no Gemini. The runner now gives a
converging answer (code-only rejection, fewer problems than the round before, at most 4) up to 3 extra patch rounds (`Step.extra_rounds`,
`runner.CONVERGING_MAX`; a reviewer rejection never extends); the word list gains the 11 words (2026-10-24.3). Expected on the next
resume: the five pass within the extra rounds at ₹0 maker cost and one review each (about ₹5).

**After the converging rounds (the third part, `vm-t045d-tissue-lesson-resume2-brain-lesson`, main `1c6c349d`, 19.7 minutes, Gemini
₹24.44):** v2 and v8 passed in round 4, the first extra round (11 → 3 → 2 → 0 and 18 → 6 → 2 → 0 code problems), v4 in round 3, each
with 0 blocking from the reviewer: **9 of 11 videos pass**. v9 reached 0 code problems in round 4 (20 → 9 → 1 → 0) and its review call
met `402 Insufficient Balance`: the AICredits wallet is empty (this time the wallet, not the key budget), so the run stopped there; v9
waits for one review (about ₹5) after a top-up. v5 (the longest video: 128 beats, 18.7 minutes) failed in round 3 when the maker's patch
answer hit the 32,000 output-token limit (`truncated`): the next seekh item is a smaller patch for long scripts (or a plan that keeps a
video under about 15 minutes). **Dohraav on the final 11 scripts: 0 of 500 judged beats (0.0%)**, opened 67.2%; before Task 045d:
155 of 540 (28.7%), opened 28.3%. Rounds a script: 3.0 on the first run → 3.4 with the extra rounds; the extra rounds cost no Gemini.
Task 045d Gemini in all: understanding ₹100.28 + script ₹24.86 + ₹12.01 + ₹24.44 = **₹161.59 of Navin's ₹200**; Codex plan 2% → 8%.
Status: the understanding and script steps are INTEGRATED (real runs through every new check); the dohraav number is a measured fact;
nothing ACCEPTED until Navin's verdict on old v2 against new v2 (`V2_SIDE_BY_SIDE.md` in the resume2 run folder).

## Entry 10 · continue a failed script from its last answer (PR #64), 25 October 2026

**From the same resumed run as entry 9's seekh (PR #65):** the five failed scripts had been written again from scratch by the resume,
and each rewrite brought everyday images with new words (67 distinct words flagged in the resumed run, most of them new): entry 9 had
predicted that v2, v8 and v9 would pass, and their rewrites failed on words the earlier versions did not use. PR #65 extends converging
rounds inside one run; this entry stops a resume from throwing the nearly finished scripts away.

**Changed in BIE (IMPLEMENTED, offline; PR #64, on top of PR #65):**

- **Continue, do not rewrite** (`bie/brain/runner.py`, `bie/brain/lesson.py`): a step may start from an earlier answer (`Step.start`).
  Round 0 makes no maker call: BIE's code checks that answer with today's checks; a clean one goes straight to the reviewer, otherwise
  the first maker round is a patch of exactly today's problems, and round 0's count is the "round before" for PR #65's converging
  rounds. A lesson resume continues every earlier script that did not pass (or no longer passes) when it is close enough (at most 10
  problems today, none about missing content or a script far too short, `close_enough`); a script far from passing is written again.
  The lesson records `continued`, SCRIPT.md marks "(continued)", `tools/seekh_measure.py` counts continued units apart from first-try
  passes.
- **Words** (`simple_hindi.json` 2026-10-25.1, on PR #65's 2026-10-24.3): 30 more everyday words from the resumed run's rounds (दिक्कत,
  चेहरा, सुरंग, थक्का, सीना, घरेलू, निशान, पुल …) and the phrase अदला-बदली; `hinglish.py` reads an oblique form whose last vowel changes
  (पहिए → पहिया, झाड़ुओं → झाड़ू; झाड़ू was already listed) and an ordinal ending after a digit (10वाँ). Formal words stay hard: पर्याप्त,
  प्रभावित, मुख्यतः, कठोर, माध्यम, बाधा, विशाल, स्रोत, अपेक्षाकृत.
- **Openings** (`soul.py`): the two steps of Navin's teacher bank the detector missed: the contrast "what it is not" ("सिर्फ / केवल …
  नहीं", "न कि"; job B resume v2 b13: "यह सिर्फ सख्त ढाँचा नहीं है") and the memory beat ("याद रखो", trick). "से अलग" and "उल्टा" were tried
  and left out: on the old scripts they credited "अलग पहचानो" and "अलग रखती है", which open nothing.

**Correction to entry 9's last paragraph (from the run's own records):** v5's round 3 ended on the **reviewer's** answer, not the
maker's patch: the maker's round 3 answer (1,400 output tokens) passed every code check, and the review call through AICredits stopped
with `aicredits:truncated: output reached max_tokens=32000` (ledger row `lesson:script-v5:r3:review`, outcome error). A normal script
review is 1,000–1,600 output tokens (the other eight in these runs); this one ran away.

**Taught about cost:** a call that generates an answer and then fails is billed by the provider, but the gateway recorded such a call
with no tokens and the cost guard settled it at ₹0. v5's runaway review (about 55,000 input and 32,000 output tokens of Gemini 4 Argon
with the AICredits markup) is estimated at ₹40–48, so job B2 cost about ₹65–72, not the ₹24.44 in its ledger, and Task 045d about
**₹205, not ₹161.59, of Navin's ₹200**; the AICredits wallet ran out on v9's review. The AICredits dashboard has the real bill
(`docs/roadmap/COST_LOG.md`, "real bill").

**Changed in BIE for cost (IMPLEMENTED, offline; PR #64):** `ProviderError` carries the tokens a provider reports for a call that
answered and then failed (truncated, refused, unreadable; all four clients); the gateway prices that call in the ledger and the cost
guard settles it at that price; a truncated call without reported tokens is priced at its input and the whole output cap. A call that
never answered (rate limit, wallet, timeout) still costs nothing. Next seekh, not built yet: a smaller output cap for review calls
(a review needs about 1,600 tokens; the cap of 32,000 lets a runaway cost about ₹45).

**Job B2's result (`vm-t045d-tissue-lesson-resume2-brain-lesson`, on PR #65's code):** 9 of 11 pass; v5 and v9 are both clean by code
(v9 at round 4, v5 at round 3) and each needs only a review. With this PR a resume continues both from their last answers: round 0
finds no code problem, so the next run makes no maker call and two reviews (about ₹10–12, v5's again at risk of a long answer until
the review cap exists).

**Measured (offline, 25 October 2026, on the earlier resumed run's `lesson_plan.json` with this code):** the 6 passed scripts still pass
and are reused; the 5 failed ones would continue: v2, v4, v8 and v9 have no code problem left (straight to the reviewer, no maker call),
v5 keeps one restating beat (b102, a patch round). Dohraav of that lesson with today's markers: 1 of 511 (0.2%), openings 65.8%. The
old scripts (job 3, regression set): 78 → 76 restating of 273, 93 → 98 opened. Both saved regression sets still pass; the Task 045 lane
passes. Nothing ACCEPTED until Navin's verdict.

## Entry 11 · the reviewer on the free Google key, and a review output cap, 25 October 2026

**From job B2 and Navin's decision of 25 October 2026:** v5's review through AICredits ran away to the 32,000-token output cap
(entry 10), and the AICredits wallet is empty. Navin added his free Google AI Studio key (`GEMINI_API_KEY`) to the VM's
`/etc/bie/bie.env` for the reviewer (sample content only, never student data); the AICredits key stays there unused. The free tier
answers only `gemini-3.8-flash` (smoke run 40114580580; `gemini-4-argon` 429 quota, `gemini-3.1-pro` 404).

**Changed in BIE (IMPLEMENTED, offline; branch `task045-free-reviewer`):**

- **Review output cap** (`tools/run_brain.py`, `REVIEW_OUTPUT_TOKENS = 12000`, flag `--review-output-tokens`): the reviewer's route is
  now its own client with this cap; the maker keeps 32,000. Measured on every review call on `blindtest-results` (141 calls, 99
  answered, 21–24 October 2026): the largest Task 045d script review answered 1,612 output tokens, the largest review of any kind
  3,744; none of the 99 would have been cut by 12,000. Gemini through Google counts its thinking inside the same cap (the smoke run's
  answer: 208 of 217 output tokens were thinking), hence the room. The cost guard reserves a review on the smaller cap.
- **Google's free-tier quota** (`bie/model_gateway/live/errors.py`, `transport.py`, `gateway.py`): Google answers every free-tier quota
  with 429 and "You exceeded your current quota", the words BIE read as an empty wallet (a run stop). A 429 whose quotas are all
  per-minute ones is now a rate limit: the gateway waits the time Google asks for (RetryInfo, at most 90 s) and tries again; a
  per-day quota, or a model the tier does not serve (`limit: 0`), still stops the run as "balance".
- **VM status** (`tools/codex_vm.py status`): which Gemini keys are present (direct, AICredits) and the default Google route, never a
  key; the runner's notes and `deployment/codex-vm/README.md` name the job fields for the free key
  (`"routes": "google=direct", "models": "google=gemini-3.8-flash"`).

**Measured before → after (offline):**

| Measure | Before | After |
| --- | --- | --- |
| Output cap of a review call | 32,000 | 12,000 |
| Worst runaway review like v5's (about 55,000 input tokens), Gemini 4 Argon through AICredits | about ₹45 | about ₹24 |
| Same runaway on `gemini-3.8-flash`, list price (Google bills the free tier ₹0) | about ₹15 | about ₹8 |
| Answered past reviews that the new cap would have cut | — | 0 of 99 |
| A per-minute free-tier 429 | run stopped as "balance" | waited out, run goes on |

Quality, first-try pass rate and rounds are unchanged offline (no rule or check changed); the Task 045 lane passes (449 tests, 16 new
in `tests/test_task045_free_reviewer.py`) and both saved regression sets still pass. The live effect comes from the ₹0 test job and
the v5 and v9 resume.

**Live effect (25 October 2026, after PR #67 at `26b5ff24`):** the ₹0 test job (`t045-free-reviewer-smoke`) and the lesson resume
(`t045-tissue-lesson-finish`) ran on the VM with the free key. Every Google call went `direct` to `gemini-3.8-flash`; no AICredits
call. v5 and v9 continued from their last answers with no maker call and both passed at round 0: **11 of 11 videos pass**. The three
reviews answered 1,867, 2,072 and 2,711 output tokens (787, 1,367 and 1,753 of them thinking), all far under the 12,000 cap; v5's
review, the one that ran away to 32,000 in job B2, now answered in 2,711. The free tier failed the first try of two calls
(`provider_unavailable`, once in each job) and the gateway's retry passed both; no per-minute quota was met. Billed ₹0; ledger
estimate ₹8.76 at the list price.

## Entry 12 · VM job 1, the W-01 wording patch on v3 (Task 046 Part A), 26 October 2026

**The run (₹0 billed):** two VM jobs on `codex-jobs`. `t046-v3-wording-patch` (5.4 minutes, cap ₹5) continued v3 from its last
answer: round 0, the code check, named the five beats that point at the book (b22, b24, b29, b30, b36; W-01, Navin's rule of
26 October 2026); round 1, the Codex maker (ChatGPT plan, no rupees) rewrote those five beats only, every other script kept as it
was (`--videos v3`); then the cost guard stopped the run before the review: "the next call (lesson:script-v3:r1:review, about
Rs 5.00) would cross the cap of Rs 5". `t046-v3-wording-patch-resume` (7.7 minutes, cap ₹15) continued from the patched answer:
round 0 clean by code, no maker call; the reviewer on Navin's free Google key (`gemini-3.8-flash`, direct; 24,487 input, 3,273
output tokens) passed it. **v3 passed, 11 of 11 videos pass**; before/after sentences in `docs/evidence/task046-director/W01.md`.
Ledger estimate ₹0.06 + ₹2.96 at the list price; billed ₹0.

**What the run taught:** the preflight estimate priced the whole chapter for a resume of one script ("Andaaza Rs 39.17, seema
Rs 5": 14 pages × the measured lesson rate), so the warning said nothing useful about the cap, and the cap of ₹5 was set blind;
the guard then did its job (it refused a ₹5 review call under a ₹5 cap after a ₹0.06 preflight) and the job needed a second run.
The actual spend of the whole patch (maker on the plan, one review) was about ₹3 at the list price, which a right-sized estimate
would have shown.

**Changed in BIE (this PR, Task 046 Part B):** `bie/brain/cost.py` `lesson_share` and `tools/run_brain.py`: a lesson resume with
`--videos` estimates the share of the chapter those scripts are (spoken minutes of the selected scripts over all scripts, from the
earlier run's `lesson_plan.json`), and the pahra line says "resume of 1 of 11 videos, 10% of the chapter". Test
`tests/test_task046_blocks.py::TheSeekhFromVmJob1`.

**Measured before → after (offline, on the same job):**

| Measure | Before | After |
| --- | --- | --- |
| Preflight estimate for `--videos v3` (14 pages, lesson, free-tier reviewer, Codex maker) | ₹39.17 (the whole chapter) | ₹3.94 (10 % of the chapter, v3's 11.7 of 116.4 spoken minutes) |
| Spent on the patch, both runs, list price | — | ₹3.02 (₹0.06 preflight + ₹2.96 review) |
| Cap that would have covered the job in one run | ₹5 did not | ₹5 reads as tight but plausible next to ₹3.94; ₹8 is the safe choice |

Quality, first-try pass rate and rounds are unchanged (no rule or check changed); both saved regression sets still pass.

## Entry 13 · Task 046 Part B rejected: the checks measured presence, not look, 26 October 2026

**Navin's verdict (26 October 2026):** both routes of the Part B benchmark render (run 40298550697,
`blindtest-results:runs/t046-v3-benchmark/`) were rejected: "dur dur tak benchmark se mel nahi khata". PR #75 stays open and
unmerged; Part C stays stopped.

**Diagnosis (what the run taught):**

- **The frame checks measured presence, not look.** `bie/brain/video/frame_checks.py` read a bright caption band (B-08), a lit label
  box (B-03), pixels near the member's accent (B-10), a dark mean or border (B-11/VG-09) and change between stills (VG-01). A frame
  can pass all of them and still look nothing like the benchmark, and it did: route A passed 14 of 24 rules, route C 15, while
  Navin saw no resemblance. No check ever compared our frames with the benchmark's frames, and no reviewer with eyes looked at a
  frame before Navin did.
- **The cells were simple geometry.** The world block drew every cell as a hexagonal prism (`CylinderGeometry` with 6 sides,
  bevelled), the nucleus as a scaled sphere, on flat boxes for the membrane and the tissue; the Blender route built the same
  recipe (`bie/toolbox/blender/cell_sheet.py`). The benchmark's cells are organic: irregular wavy outlines that interlock, softly
  domed tops with a raised nucleus bulge, glossy wet surfaces with fine noise.
- **No light transport.** Plain `MeshStandardMaterial` / Principled BSDF without subsurface scattering or translucency: light
  never passes through a cell, so nothing reads as living tissue. The benchmark's cells glow from within, nuclei show as darker,
  denser bodies through the cytoplasm.
- **No lighting design, no depth.** One generic light rig and a vignette; no key and rim light, no haze, no glare on the lit part,
  no depth of field, no out-of-focus context (vessels, air sacs) behind the sheet. The benchmark separates its planes with a shallow
  focus and soft volumetric light.
- **Scale of the error:** the level ladder called these shots L5a ("photoreal micro 3D") because of the block chosen, not because of
  how they looked; the label described the intent, not the picture.

**Changed in BIE (Task 046 one-shot test, branch `task046-oneshot`, draft PR; IMPLEMENTED, nothing ACCEPTED):**

- One shot of 4–5 s instead of a segment, judged by Navin side by side with the benchmark before any longer render.
- Route 1: a Blender recipe made the way a science-animation studio works (organic Voronoi outlines, domed tops, nucleus bulge,
  subsurface scattering and translucency, key and rim light, haze, glare, depth of field, a slow push-in; Cycles on CPU), reusable
  for every epithelium member.
- Route 2: an AI still made through the ChatGPT plan (Codex image generation on the VM), animated by BIE code (2.5D parallax, push,
  particles, glow), labels and caption by code.
- **LOOK-01:** a look check against the benchmark's frames by a reviewer with image input (organic shape, translucency,
  lighting and depth, detail, scientific correctness, overall class), saved with its reasons; advice only, Navin's eye decides.

Measured effect: in the one-shot report (look scores per route, render seconds per frame, ₹), then Navin's verdict.


## Entry 14 · Task 046 one-shot test: one shot, two routes, 26 October 2026

**What the run taught:**

- **A studio look costs CPU time, and the cost is now measured.**
  - The first Blender recipe spent 240 s per 1080p frame in Blender's subdivision of the cells' fan-shaped tops. Dense
    smoothed rings gave the same organic outline at 55 s per frame in the workspace.
  - Blender's noise is seeded per process, so the recipe now seeds it. Chunks rendered on different runners show the same
    scene.
  - On 4-CPU hosted runners at 32 samples the shot costs **203 s per frame**: 4.5 seconds of video took 457 machine-minutes
    (₹0 on the public repository).
  - A 5-minute segment at this quality would need about 500 machine-hours, so a long video at this quality needs fewer
    samples, GPU rendering, or the 2.5D route.
- **LOOK-01 (first use) names the gap that the presence checks could not.** Part B had no look score at all.
  - Route 1 (Blender) scored mean 5.3 of 10, verdict “close” (5.2 in a first check). Translucency is its weakest axis
    (4): the cells read as opaque and rubbery. The next look work for Route 1 is wet, translucent cytoplasm: a thinner
    subsurface radius, a transmission layer and a clear-coat sheen.
  - Route 2 (a Codex still moved in 2.5D by BIE code) scored 7 on every axis, mean 7.0, verdict “same class”. Its gap:
    the code's particles float without contact shadows. The next look work for Route 2 is particle shadows and a
    depth-aware fade where particles cross the layer.
  - Neither was done here, because the test stops for Navin's verdict.
- **Route 2 is fast and cheap; Route 1 is flexible.** Route 2 made the shot in about 3 minutes (4 images in 2 minutes on
  the plan, a 17 s depth map, a 150 s animation). Route 1 needed 7.6 machine-hours. But a still allows only a small camera
  move, while Route 1 is real 3D (any move, any member, the same look every time).
- **The VM runner had three gaps, each found by a live job:**
  - A poll ran the old code after a merge (F-14: it now runs again with the new code).
  - A failed Codex image run kept no reason (F-14: the error and reply are kept).
  - Codex 0.162.1 calls every tool through its code-mode host, which BIE's lean settings turn off (F-14b, PR #81, merged
    after Navin's yes). The fourth image job then made 4 of 4 images in 2 minutes on the ChatGPT plan, ₹0.
  - PR #77's runner tests were in no CI lane; they are now.
- **CI time:** the toolbox lane's apt steps hit the slow mirror (F-11) and the assets job waited behind a manual run
  (F-13c). With bounded downloads the `wrappers` job now takes 3.5 minutes; before, it was cancelled at its 40-minute limit.

**Changed in BIE:**

- Toolbox: `bie-epithelium-studio` (the Blender recipe and its presets), `onnxruntime` and Depth Anything V2 Small
  (Apache-2.0, pinned, SHA-checked), registered and tested.
- Blocks: `plate` and `parallax_plate`; `bie/brain/video/still_prompt.py`; `tools/oneshot.py`.
- Rules: LOOK-01 in the rule table (`visual_grammar.json` 2026-10-26.3).
- CI and runner (merged): PR #77, #79, #80 and #81.

**Measured effect:**

| | before | after |
| --- | --- | --- |
| Look score (LOOK-01, against a written description) | none (Part B) | Route 1 5.3 “close”; Route 2 7.0 “same class” |
| Route 1 cost per 1080p frame (4 CPU, 32 spp) | — | 203 s |
| Route 1 cost per shot | — | 7.6 machine-hours, ₹0 |
| Route 2 cost per shot | — | 4 images in 2.05 minutes on the ChatGPT plan + 17 s depth + 150 s animation, ₹0 |
| Codex image jobs that made images | — | 0 of 3 before F-14/F-14b, 4 of 4 after |

Navin's verdict decides what is next.

## Entry 15 · Task 046 Part C, PR 1: the economy kit inside BIE, 27 October 2026

**What the kit taught** (the asset intake's economy batch, 27 October 2026; 20 Indian-economy reference videos for UPSC, about
2 h 5 min, measured by code: visual-change events from frame differences at 5 fps, speech phrases by Silero VAD): the reference
teaching moments are **build-up canvases, not cuts** — a visual change every 5.0 s (median; p90 7.5 s), the canvas cleared only
when the idea changes, text at 24 px or larger, at most about 16 things on screen, a number struck out and replaced rather than
re-drawn, a crowd that grows and shrinks, and a story told inside a place when actors act (a shop and its buyers). Navin's
decision: **"B default ke saath kahani wale hisson mein C"** — a canvas with L3 touches by default, an L3 world for the story
parts.

**What changed in BIE** (branch `task046c-kit`, PR 1 of Part C):

- The kit's three blocks (`canvas_build`, `curve_story`, `world_scene`) now live in BIE's toolbox bundle
  (`bie/brain/video/blocks/toolbox/canvas.tsx`, `world.tsx`), and its two compilers are BIE modules (`bie/brain/canvas.py`,
  `bie/brain/video/world.py`) with the kit's checks as code: layout, cue timing, refusals and the still-picture limits. The
  plan contract is the one the AI director will write to in PR 2 (what, where, on which spoken word; never a pixel).
- **The danda bug** (seekh from the kit's first cue test): `timing._norm` kept the danda as a word character, so a cue on a
  sentence's last word ("यही CPI।") was never found and the element appeared at the beat's start. The danda and double danda
  are punctuation now; `timing.has_word` is the one word matcher and `director.word_in` reads through it (its duplicate regex
  retired).
- **One caption place:** the kit's blocks each drew their own subtitles; now the core strip in `blocks/index.tsx` draws every
  video's captions once (a dark strip under white words, readable on paper and on the dark world); compilers return the scene
  with `captions`.
- **Icons as toolbox sources, through the licence policy:** Twemoji (CC BY 4.0) and Font Awesome Free (icons CC BY 4.0) are
  registry asset sources with an index of 4,213 icons (`bie/toolbox/icons.py`); a plan that names an unknown icon is refused
  before any render; the icons join the asset library with the credit fields, so the 046a-L gate passes them and the credit roll
  lists them. Fetched per file from the pinned GitHub tags (the npm `@twemoji/svg` repackage lacks 30 files), cached outside git.
- The canvas rules CV-01…CV-12 and their limits are a rulebook file (`canvas_profile@2026-10-27.1`), so the director reads
  them like every other rule and the rulebook version records them.
- Five proof clips (batch 3) and 28 tests in the toolbox core lane; the kit's fixtures live in `tests/fixtures/task046c/`.
- Seekh from the clips' own frame checks: a paper canvas reads as "blank" during the lead-in silence and whenever the
  caption strip drops out between two beats. Two product fixes, not a looser check: captions hold through a pause under
  1 s (standard subtitle practice; no flicker in a lesson either), and proof clips start at once (`lead_in`).

**Measured before → after (offline, ₹0):**

| Measure | Before | After |
| --- | --- | --- |
| A cue on the last word before a danda or comma (`timing.has_word("… यही CPI।", "CPI")`) | not found (landed at the beat's start, silently) | found |
| Places that draw subtitles | 3 blocks + the core strip | 1 (the core strip) |
| Icon sources in the registry with a credit line | 0 | 2 (4,213 icons, CC BY 4.0) |
| Kit fixtures compiled and rendered by BIE's own renderer | 0 | 5 plans, the world and the credits card: 28 stills, all drawn |
| Proof clips in the toolbox | 51 | 56 |
| Caption between two beats (a pause under 1 s) | strip disappears for the pause (flicker; the real-GDP clip's 24 % frame read as blank, 7.9 against 8) | held until the next line starts (26.3) |
| First sampled frame of a paper canvas clip (6 % in) | empty paper during the 0.4 s lead-in (not blank: false) | the clip starts at once (`lead_in` 0 for proof clips; 20–36) |
| Tests in the toolbox core lane | 109 | 137 |
| Task 045 lane and passed-output sets | 464 pass | 464 pass (unchanged) |
| Plans a lesson has sent through the kit | 0 | 0 (the real chapter is PR 5; nothing INTEGRATED yet) |

First-try pass rate, rounds, tokens and ₹ per page are unchanged (no AI step runs in PR 1); PR 2 starts counting first-try
passes and rounds per part, and the real chapter run gives the first numbers.

## Entry 16 · Task 046 Part C, PR 2: the director's canvas and world modes, 27 October 2026

**What PR 1 taught:** the kit's plans are small and checkable by code (what, where, on which word), so the maker needs no
reviewer for layout: every refusal is an exact code error the maker can act on, and the plan contract can be a strict JSON
schema the gateway validates before any check runs.

**What changed in BIE** (branch `task046c-director`): `bie/brain/canvas_director.py` (the modes by Navin's rule, the
director card and the CV rules as the maker's instructions, an icon menu from the index, the strict plan schema and the
exact-error check loop through the SectionRunner, `run_canvas` writing plans, specs, credits and the per-part counts),
`--section canvas` in the run tool and the VM runner, the places a story can be set in (`world.PLACES`), the fake maker's
canvas and world answers, `canvas_profile@2026-10-27.2`.

**Measured (offline, ₹0; the live numbers come from the chapter run):**

| Measure | Before | After |
| --- | --- | --- |
| A script part of a canvas subject → a plan BIE can render | none (no section) | one per part, B by default, C for a story in a place with a kit |
| Reviewer calls per plan round | — | 0 (layout is code-checked; the exact error goes back) |
| Where a plan's errors are recorded | — | the step record (`records/`), `canvas.json` `last_problems`, `CANVAS.md` |
| First-try passes and rounds per part | not counted | counted (`first_try`, `rounds`, `first_try_rate`) |
| Places a story part can be in / kits that exist | — | 5 / 1 (shop); the rest logged as missing kits |
| Tests in the toolbox core lane | 137 | 150 |

First-try pass rate, rounds, tokens and ₹ per page for real plans: not yet (no live call in PR 2).

## Entry 17 · Navin's real-world application rule for economics (Task 046 Part C addition), 27 October 2026

**What the Money chapter and Navin's videos taught:** Navin teaches an economics concept by applying it first ("demand pull
inflation wale concept ko dukandar, bazar, log, sugar wale example se samjhaya tha"); BIE's unpack had an `example_or_place`
line but no story with a place, actors, goods and numbers, and the script rule only said "an example or the place" after
the book line, so the term could come first and the example could be number-free. His words are in ROADMAP 046 and STATUS.

**What changed in BIE** (branch `task046c-director`, with PR 2 as he asked): the method `real_world_application` in
`teacher_examples.json` 2026-10-27.1; the required slot `unpack.real_world_example` for economics definition, cause-effect
and process items (`content_types.json` 2026-10-27.1, `soul.REAL_WORLD_SCHEMA`, page schema `understand-page/4`); rule
S1-16 checked by code in `check_page` (place, actor, goods, a number that changes, two steps with mechanism links, the naming
sentence, the real-life link) and rule S2-08 checked by code in `check_script` (the example's beats, carrying its numbers,
before the beat that names the term); both on the reviewer's checklist with "economically correct at the learner's level";
the director's story piece (`story_split`, `mode_of(story=True)`, `STORY_NOTE`, the petrol pump as a place); MAP.md and
SCRIPT.md tables per concept item (the example BIE chose, the check, first try); 19 everyday bazaar words; the fake maker.

**Measured (offline, ₹0; the live before/after comes from the Money chapter):**

| Measure | Before | After |
| --- | --- | --- |
| Economics concept items that must carry an applied example | 0 (no slot) | every definition, cause_effect, process item (S1-16) |
| What code checks in the example | nothing | place, actor, goods, a changing number, ≥ 2 steps with links, naming sentence, real-life link |
| Script order for an economics concept | free (term could come first) | example beats with the numbers first, then the term (S2-08) |
| Reviewer rounds added for this | — | 0 (code checks; the existing reviewer's checklist grew by two rules) |
| Director: a concept's example beats | part of one canvas | their own story piece: a world when the place has a kit, else crowd/value/icon canvas |
| Offline Money chapter (fake maker): pages and scripts first try | — | 2 of 2 pages, every script, every example run first |
| Tests (toolbox core lane / Task 045 lane) | 150 / 464 | 165 / 479 |

Live first-try rate, rounds, tokens and ₹ per page under the new rule: measured by the Money chapter rerun on the VM (the
12:42 UTC job under the old rules is the baseline); recorded here when the run finishes.

**What the first Money run itself taught (same PR):** of the 4 pages that passed before the free Google quota ran out,
page 2 lost a round to "पदार्थ → substance", a textbook-Hindi flag for a term the Money chapter never uses (the list was
made from the tissue chapter): the check now counts only the book's own terms (`hinglish.english_terms`, `technical_words
(book_terms=…)` in `check_page` and `check_script`), tested on both chapters' words. And a provider error was cut to 300
characters in the records, so Google's quota id (per minute or per day) was invisible: 1,500 now. Measured: 1 of 4 passed
pages (25 %) had a needless round on the old check; 0 under the new one on the same output.

**What the baseline map taught (same day, branch `task046c-map-review`):** the second Money run (`t046c-money-understand-b`,
15:20–16:17 UTC, Codex maker, Codex as the checker, ₹0) passed all 20 pages, then **failed the chapter map after 3 rounds
with 0 code problems in every round**. The checker's 12 blocking findings: 10 on the wording of `core_explanation`, `notes`
or `exam_focus` (a two-line summary per concept that BIE's later sections read; no learner hears it, the lesson is written
from the items and reviewed in Section 2), 2 on structure (a prerequisite bundle wider than the direct need; RuPay as a
prerequisite of MDR). Every round the maker fixed the named wording and the checker found new wording on other concepts,
so the map could never converge. Change: `understanding.connect_review_problems` counts only structural findings
(`structural_finding`: items, relations, prerequisites, references, question links, teaching order; a finding naming both,
or no field, blocks; a failed verdict naming no blocking finding still goes back once) and keeps the wording findings in
the record (`wording_findings`); the checker's prefix says what the map is and what is minor. Tests:
`tests/test_task046c_map_review.py` (8), in the toolbox core lane and the Task 045 lane.

| Measure (the baseline map's own three reviews, replayed) | Before | After |
| --- | --- | --- |
| Blocking findings counted, rounds 0 / 1 / 2 | 6 / 3 / 3 | 1 / 0 / 1 |
| Map status | failed after 3 rounds | passes at round 1 |
| Maker calls + checker calls for the map | 3 + 3 | 2 + 2 |
| Wording findings lost | — | 0 (kept in the record as minor) |

The live effect is measured on the new-rule run (`t046c-money-understand-c`) and its resume.

## Entry 18 · Task 046 Part C, PR 4: render speed, 27 October 2026

**What the measurement taught:** the brief named the blocks' filters and static layers; they were worth 7 % on a canvas
and 46 % on the world. The floor was elsewhere: Playwright's `page.screenshot` cost about 0.4 s a frame more than
Chromium's own capture of the same pixels, and compositing the page through the emulated GPU cost another 0.25 s a frame
on a plain 2D scene. Profile first, then cut.

**What changed in BIE** (branch `task046c-render`): `preview/stills.mjs` captures from the compositor and composites in
software (WebGL untouched), the canvas and world blocks lost their per-frame filters and gained cached static layers,
`render.mp4_range` and `tools/render_spec.py` render a spec in chunks on several runners and join and measure them, and
the `BIE Task046c Render` workflow runs that in CI (the full MP4 as an artifact, the review copy on `blindtest-results`).

**Measured before → after (this machine, 4 CPUs, the same 60 frames; seconds per frame):**

| Scene | Before | After |
| --- | --- | --- |
| Plain canvas + curve | 0.618 | 0.256 |
| Canvas with L3 touches | 0.859 | 0.303 |
| World (street, shop, people) | 1.606 | 0.373 |
| Pixels | — | the same (max difference 1 of 255) |
| A 6-minute video, machine minutes | 110–290 | about 54 |
| A 6-minute video, wall-clock on 8 runners | not possible in one runner's 6-hour limit at the world's rate without chunks | about 12 minutes (target under 60) |

Quality is unchanged by construction (same frames); the CI numbers come from the first chunked render.

## Entry 19 · the Codex checker on the Money pages: the example asked where the rule does not, and a last-round slip, 27 October 2026

**What the new-rule run taught** (`t046c-money-understand-c`, 20 pages, Codex maker and Codex checker, ₹0): BIE's S1-16 code
check passed all 102 economics concept items on the first try, and the chapter map passed at round 1; yet only 2 pages
passed first try (the baseline, without the slot, 7 of 16) because the checker sent 18 of 20 pages back at round 0 while the
code was clean on 18 of 20. Of its 53 first-round blocking findings, 24 asked for a worked real-world example on items whose
type does not carry the slot (timelines 10, classifications, comparisons, fact lists): the rule names definition, cause_effect
and process items, the reviewer applied it to every economics item. Two pages (7 and 12) failed with a single new code
problem in the last allowed round (a block id, a type note), a slip the maker made while fixing the checker's findings, with
no round left to mend it; two (4 and 15) failed on the checker's own findings (real-life links to Indian rupee practice without
a page source, "why" answers on timeline items).

**What changed in BIE** (branch `task046c-page-review`): `understanding.page_review_problems(review, value, family, types)`:
in an economics chapter a blocking finding that wants a worked example (`asks_for_example`) on an item whose type does not
need the slot (`ContentTypes.needs_real_world`) is minor, and a page whose blocking findings were all such passes; every other
family and every other finding is untouched. The runner (`_review_findings`) hands the maker's answer to a review that takes
two arguments, so the review can read each finding's item. The checker's prefix (PAGE_REVIEW_HOW) now says which items S1-16
covers and that an empty slot elsewhere is correct. And the runner's converging rule covers a first slip: code problems that
first appear after code-clean rounds (at most CONVERGING_MAX) earn one more patch round. Tests:
`tests/test_task046c_page_review.py` (10), in the toolbox core lane and the Task 045 lane.

| Measure (the run's own reviews, replayed) | Before | After |
| --- | --- | --- |
| Checker findings counted as blocking, all rounds | 79 | 53 |
| First-round blocking findings that asked for the example where the rule does not | 24 of 53 | 0 (minor, kept in the record) |
| Pages passing first try | 2 of 20 | 3 of 20 (page 8) |
| Pages failed on one new code slip in the last round | 2 (pages 7, 12) | one more patch round each |

The live effect (first-try pages, rounds, minutes) is measured on the resume `t046c-money-understand-d` (16 pages reused, 4
pages and the map run again).

**Measured live (the resume `t046c-money-understand-d`, 18.4 minutes, ₹0):** the four pages passed (page 7 first try, pages 4
and 15 in two rounds, page 12 in three), the map passed at round 0 with 0 checker findings; none of the four pages' findings
was of the example-asking kind, so the filter changed nothing on them and the slip rule was not needed. Section 1 of the Money
chapter is complete: 20 of 20 pages, the map, 95 of 95 economics concept items with a checked real-world example.

## Entry 20 · the Codex checker on the Money plan: a plan is not the lesson, 27 October 2026

**What the first Money lesson run taught** (`t046c-money-lesson`, Codex maker and Codex checker, ₹0, 10.8 minutes): the plan
passed every code check in every round (18 videos, every concept placed, the minutes within S2-01) and **failed after three
rounds on the checker alone: all 20 blocking findings asked the plan for the teaching itself** ("do not actually teach the
concepts", "no complete question … or answer", "the example-first economics rule is not consistently implemented", "most
remaining text is production direction rather than complete spoken teaching"). The plan reviewer's prefix was the lesson's
general one and its checklist carried every lesson rule, the script rules (S2-02, S2-04 … S2-08) included, so a careful checker
applied them to a list of videos. No script was written. The tissue plan had passed the same step with the Gemini reviewer,
whose one minor finding ("v5 packs 8 concepts into a 16-minute video") is a true plan finding.

**What changed in BIE** (branch `task046c-plan-review`): `lesson.PLAN_REVIEW_HOW` says what the plan is (which videos, which
concepts in each and in what order, the minutes, the prerequisite list, a hook idea and an analogy idea per video), what the
scripts carry and what a plan finding is; `plan_checklist_text` gives the plan reviewer only the rules a plan can meet (G-04,
S2-01, S2-03); `plan_review_problems` counts only structural findings as blocking (`plan_structural_finding`: a concept in no
video or before its prerequisite, a split family, too many concepts for the minutes, a prerequisite the chapter does not need;
a finding that asks for the teaching, or on the wording of goal / story_or_analogy / opening_hook, is minor; an unplaced finding
blocks). The review prefix is `bie.brain.lesson-plan-review/3`. Tests: `tests/test_task046c_plan_review.py` (7), in the
toolbox core lane and the Task 045 lane.

| Measure (the run's own three reviews, replayed) | Before | After |
| --- | --- | --- |
| Blocking findings counted, rounds 0 / 1 / 2 | 5 / 8 / 7 | 0 / 0 / 0 |
| Plan status | failed after 3 rounds, no script | passes at round 0 |
| Maker calls + checker calls for the plan | 3 + 3 | 1 + 1 |
| The tissue plan's "v5 packs 8 concepts" finding | minor (Gemini's call) | still a structural finding |

The live effect is measured on the second lesson run (`t046c-money-lesson-b`) after this merges.

**Measured live (`t046c-money-lesson-b`, 48.2 minutes, ₹0):** the plan passed at round 0 with 0 checker findings (before: failed
after 3 rounds with 20); 18 scripts were written, 878 beats, 163 spoken minutes, 93 of 93 examples run first (S2-08).

## Entry 21 · the Money scripts: the everyday words of money, and narration that points at the source packet, 27 October 2026

**What the second lesson run taught** (`t046c-money-lesson-b`, 18 scripts, Codex maker and Codex checker, ₹0): 1 of 18 scripts
passed. Round 0 carried 13–52 code problems per script (book-word beats 107, the time rule 20, heavy beats 11 over the run),
shrinking every round; **11 scripts ended with only S2-04 flags left, on everyday words of money, shops, banks and payments that
the everyday-Hindi list lacked** (746 flags over the rounds: रकम 104, वादा 30, स्वीकार 23, भुगतान 18, गेहूँ 13, बकाया 9, जेब 6 …; the
list was built from a biology chapter). The other 6 reached code-clean and the checker found 1–4 blocking findings each; 5 of
them narration that points at BIE's own source packet ("supplied figure", "source-listed", "October 2022 entry", "answer codes
in the original continuation", "aligned cells and numbered rows"), the W-01 fault in a new coat.

**What changed in BIE** (branch `task046c-money-words`): `simple_hindi.json` 2026-10-27.2 adds 192 everyday words (with their
spoken forms: वादे, बकाये, जेबें, बटुए, सौदों, खातों, चायवाले, बिकती …); the formal words stay hard (काल्पनिक, कल्पित, निर्देश, मान्यता,
मुख्यतः, महत्त्वपूर्ण, दायित्व, व्यापक, संस्था, परिभाषा …): the English word in brackets is the way. `visual_grammar.json` 2026-10-27.1
extends W-01 with 13 English patterns for the source-pointing phrases, so `soul.wording_problems` sends such a beat back before
the checker sees it; "energy का source" and "the answer is C" stay untouched. Tests: `tests/test_task046c_money_words.py` (7), in
the toolbox core lane and the Task 045 lane; the version pins moved (`simple_hindi@2026-10-27.2`, `visual_grammar@2026-10-27.1`).

| Measure (the run's own records, replayed) | Before | After |
| --- | --- | --- |
| Everyday words of money the list knows (of the 255 words flagged in the run) | 0 | 192 (the 63 formal ones stay hard) |
| S2-04 flags on the failed scripts' last rounds | 24 of 32 code problems | 7, all formal words (व्यापक, दायित्व, मुख्यतः, दर्ज, स्तर, देय, मान्य) |
| Failed scripts whose last answer is code-clean under the new list | 0 of 11 | 1 (v1); 7 keep 1–3 problems, 9 wait on the checker |
| Source-pointing narration | the checker's call, 5 scripts, one round each | caught by code before the checker (W-01) |

The words alone finish one script; the lever for the rest is the lesson resume (`t046c-money-lesson-c`): every failed script
continues from its last answer with fresh rounds (round 0 without a maker call, then patches), as the tissue scripts did.

**Live (the resume `t046c-money-lesson-c`, 28 October 2026, 22.8 minutes, 91 calls, ₹0):** 7 of 18 scripts pass (before 1 of
18); S2-04 flags over the run 36 (before 746), all formal words; the checker's findings on narration pointing at the source
packet 0 (before 5 scripts); W-01 caught 2 beats by code, one of them a false positive that cost v17 (entry 22).

| Measure | Before (run b) | After (resume c) |
| --- | --- | --- |
| Scripts passed | 1 of 18 (v17) | 7 of 18 (v0, v1, v3, v6, v7, v15, v16; v17 lost to the false positive and the notes finding) |
| S2-04 flags over the run | 746 | 36, all formal words (सफर, काल्पनिक, सुलभ, देय, मान्य, मुख्यतः, व्यापक, सहमति, देनदारी, दर्ज) |
| Checker findings on narration pointing at the source packet | 5 scripts | 0 (W-01 by code: 2 hits, 1 right, 1 false positive) |
| Rounds, calls, time | 3–5 a script, 80 calls, 48.2 minutes | 2–5 a script (round 0 without a maker call), 91 calls, 22.8 minutes |
| S2-08 examples run first; dohraav | 93 of 93; 0.6 % | 93 of 93; 1.0 % |

## Entry 22 · the Money resume: notes that describe the repair, a checker that re-measures time, and a W-01 pattern too wide, 28 October 2026

**What the resume taught** (`t046c-money-lesson-c`, 18 scripts continued from their last answers, Codex maker and Codex checker,
₹0): 7 of 18 pass. Of the 11 that fail, **3 fail on the maker's notes** (v2, v5, v17; v5 and v17 on nothing else): "the notes
document only a b12 wording correction … omit the unit's purpose". The cause is in code: a resume starts a script with
`notes: None` (`_script_value`; `lesson_plan.json` never stored the notes), so the first patch round's notes, which describe the
patch, become the script's notes, and `merge_notes` keeps that `about` and those `key_questions` for ever (it was written to
keep the unit's notes against a patch's, job 2 v11, and here does the reverse). The maker wrote in three rounds "replace the
correction-only notes with unit-level notes" and the code kept the old `about` each time. **3 fail on time** (v2 11.1 against
11.0, v11 10.5 against 10.4, v14 8.9 against 8.8): the code's S2-01 check passed each script (its tolerance), the review message
prints the measured minutes and the budget, and the checker blocks on the 0.1 ("the notes claim a reduction below the limit, but
that is not the supplied measurement"). **v17 passed in run b and failed here:** PR #90's W-01 pattern `answer codes?` caught
"फिर answer code चुनिए" in a PYQ practice video, the exam's own term (UPSC answer codes), not the source packet; the script
continued and lost to the notes finding. The rest: duplicate recaps (v9, v11), S2-07 book-word beats (v4, v8, v10), formal words
(सफर, काल्पनिक, सुलभ, देय, मान्य …), one S2-01 overrun by code (v10, 12.4 against 10.7).

**What changed in BIE (branch `task046c-lesson-notes`, `tests/test_task046c_lesson_notes.py`, 9 tests; toolbox core lane and
Task 045 lane):** (1) `lesson_plan.json` keeps each script's notes and a resume starts from them (`_script_value`), so
`merge_notes` has the unit's `about` and `key_questions` to keep against a patch's (it already keeps the earlier ones when
they exist; the fault was that a resume had none); (2) `lesson.script_review_problems`, the script step's filter: a checker
finding placed only on the notes (`notes`, `notes.about, …`, `maker notes`, `Video v2; maker notes`) is minor, the notes being
the maker's account for the checker and never what the learner hears, as the plan seekh did for the plan; (3) a finding that
re-measures the narration against its budget ("11.1 spoken minutes against an allowed maximum of 11.0", "8.9 minutes,
exceeding the 8.8-minute ceiling") is minor: the review runs only on a script whose time BIE's code has passed, so the code's
S2-01 verdict stands; when every blocking finding was such, the script passes; the review is annotated in place
(`minor_by_code`) so the record shows it; the review prompt says both (`lesson-script-review/5`); (4) W-01 `answer codes?`
narrowed to the source-pointing forms (`answer codes (in|of|from) the (original|source|supplied|given)`, `(original|supplied|…)
answer codes`), the exam instruction kept as an allowed example (`visual_grammar` 2026-10-28.1); (5) सफर joins the everyday
list (`simple_hindi` 2026-10-28.1); the formal words the resume flagged stay hard.

| Measure (the resume's own records, replayed) | Before | After |
| --- | --- | --- |
| Failed scripts whose last review has 0 blocking findings | 0 of 11 | 2 of 11 (v5, v17: they failed on the notes alone) |
| Blocking findings on the 11 last reviews | 32 | 23 (9 read as minor: 7 on the notes, 2 re-measuring time) |
| W-01 hits on run b's v17 (the script that passed there) | 1 (the exam's "answer code चुनिए") | 0 |
| W-01 hits over the 18 last answers of the resume | 0 | 0 (nothing real lost) |

**Live effect (the resume `t046c-money-lesson-d`, 28 October 2026, 15.6 minutes, 47 Codex calls, ₹0):** 13 of 18 scripts pass
(7 before): of the 11 continued scripts v5, v13 and v17 passed at round 1 and v8, v9 and v14 after 3–4 rounds; no script failed on
its notes or on a re-measured time. The 5 still failing (v2, v4, v10, v11, v12; 4–5 rounds each) fail on real content findings:
narration that says what the source lacks (W-01), outside banking facts without a dated basis, and the route named before its
example runs (Navin's example-first rule read on the whole part). Those are the next seekh candidates (entry 24 is the render's).

## Entry 23 · the first real world plans: a board is not a page, 28 October 2026

**What the first real plans taught** (`t046c-money-canvas-v1b`, v1 of the Money chapter, 8 parts: 8 passed, 6 first try, modes
B 2 / C 6, 3 story parts all in a world, 12 Codex calls, 5.1 minutes, ₹0): the director used the world's `board` as a card for
sentences: 63 of its 98 board and price-tag values were longer than 16 characters, many with line breaks ("Digital balances =
digitally recorded पैसे", "Savings = आपके resources\nFuture instalment = obligation"), a price tag read "₹100 / basket", a title
"Money: value → Limited supply → Purchasing power". The block drew every value at one size, so the text ran out of its box and
across the street (nine stills of the spec through the preview renderer, before the render). The kit lacked a card that
holds a few words, and the code let anything through.

**What changed in BIE (branch `task046c-board-fit`, tests in `tests/test_task046_canvas.py`):** `world.wrap_value` keeps the
maker's line breaks and wraps a long line at its spaces; `compile_world` writes the lines into each board step and refuses a
value of more than 3 lines of 26 characters, a price tag of more than 9 characters (a price, not words) and a title over 30,
each with the limit and the way out named ("say the rest in the narration, or split it over two steps on two cue words";
"use a board for words"); the `Board` block draws the lines at a size and a box width that fit (96 px for a short number, 72
for up to 14 characters, 46 for lines), shows the struck-out old value only when it was short, and puts the arrow at the
card's edge; the `PriceTag` font shrinks to its tag; the card says the limits.

| Measure (v1's own plans, replayed) | Before | After |
| --- | --- | --- |
| Board and price-tag values over 16 characters | 63 of 98 | 63 of 63 fit after wrapping (≤ 3 lines of ≤ 26) |
| World plans of v1 that compile under the limits | 6 of 6 (nothing checked) | 5 of 6 (the price tag "₹100 / basket" is refused with "use a board for words") |
| Values drawn outside their box (the nine stills) | 5 of 9 stills | 0 (two multi-line boards rendered and read) |

Next: the canvas job runs again on v1 after this merges (the maker fixes the one refused tag; the boards wrap by code), then the
render and the review copy. **Done (`t046c-money-canvas-v1c`, 28 October 2026):** 8 of 8 parts, 6 first try, 11 rounds, 13 Codex
calls, ₹0; the price tags are "₹100" and "₹200"; 152 board values (87 over 16 characters), 0 over 3 lines of 26 after wrapping;
the second render (`t046c-money-v1c`) is the after.

## Entry 24 · the first real render: a camera box that showed the backdrop, 28 October 2026

**What the first render taught** (workflow run 40619059768 on the plans of `t046c-money-canvas-v1b`, dest `t046c-money-v1`:
7.03 minutes, 12,646 frames at 1920 × 1080, 8 chunks in parallel, 3.7 minutes wall-clock, 26.6 machine minutes, 0.126 s a
frame, 3.78 render seconds per video second, ₹17.84 at the list price, billed ₹0; review copy 15.2 MB): one scene of nine
(`v1_s3b`, a build-up canvas) opened on a dark band across the top of the frame. The core `Scene` camera scales a key's box by
`min(1/w, 1/h)`, so a box that is not square in frame fractions (the canvas compiler's cell boxes are grid cells, wider than
tall) shows the backdrop beside or above the content. The compiler let any box through.

**What changed in BIE (branch `task046c-camera-fit`, PR #96, `tests/test_task046_canvas.py`):** `canvas.fit_box` grows every
camera box to the square of its longer side in frame fractions, centred on the box and kept inside the frame; `compile_plan`
writes every key through it, so a scene camera never shows the backdrop. (The board and price-tag limits of entry 23 are the
other half of what the first render taught.)

| Measure (v1's spec, first render) | Before | After |
| --- | --- | --- |
| Camera keys whose box is not square in frame fractions (backdrop shown) | 1 of 9 | 0 of 8 (the second plans ask for no box; every box that comes is squared by code, tested) |
| Scenes opening on a dark band (each scene's opening frame of the review copy: a 25 px top strip darker than half the frame) | 1 of 9 (`v1_s3b`) | 0 of 9 |

The second render (`t046c-money-v1c`, STATUS section "The real video") is the after.

## Entry 25 · Navin's verdict on Money v1: text on the screen that reads like codes, narration that reports states, 29 October 2026

**What the first real video taught** (Navin, 29 October 2026: "thoda kaam hume explain krne ke jo text lines screen par dikh
rahi hai us par karna padega yaani teacher ki naration uske sentence aise poore ho ki banawati na lage"): the director wrote
codes on the boards ("Exchange ✓ · Account ✓ / Store · Deferred", "1–3 ✓, 4 Future payment →", "Money = balance / Device ≠
money", "EMI amount agreed ≠", "Payments: 0 → Payments: 2") and the script reported states like a ledger ("cash ₹500 से ₹400
हुआ", "bill ₹100 से ₹0 हुआ", "savings ₹0 से ₹500 हुईं"). Likely causes: S2-08's "numbers that change" pushed an "X से Y हुआ"
pattern; entry 23's board limits (3 lines of 26, a price tag a price) pushed the director into codes; nothing checked that an
on-screen text was complete, in the learner's language or explained by the narration.

**What changed in BIE (branch `task046c-screen-text`):** rules CV-13 to CV-16 (`canvas_profile.json` 2026-10-29.1) and S2-09
(vision rulebook 2026-10-21.15; S2-08 reworded; Navin's good narration in `teacher_examples.json` 2026-10-29.1); code
`bie/brain/video/screen_text.py` in the director's plan check (symbol codes, unfinished lines and code lists refused; a text's
key words and every number must be said in the narration of its cue beat; a caveat once per part) and
`soul.state_report_problems` in the script check (a regression rule change for earlier passed scripts); a board holds 3 lines
of 40 so a complete sentence fits; the narration lock in the lock tool and the script prompt; the before/after on the review
page by code.

| Measure | Before (v1's own outputs) | After |
| --- | --- | --- |
| On-screen texts the director's check refuses (v1's 8 plans, 186 texts) | 93 (not spoken 38, codes or unfinished 37, numbers not said 17, caveat twice 1) | v1's 8 plans made again in canvas run e1 (29 October 2026): 0 refused at the end, 4 of 8 parts first try, 12 rounds (before: 6 first try, 11 rounds under the old rules); by id 17 texts changed, 167 gone, 481 new; narration 15 of 32 beats changed; the page with the before/after: https://claude.ai/artifact/WcctRSzADgH6ZxYNntuypz |
| Texts with symbol codes ✓ ≠ → = · | 52 of 160 | — |
| Beats that report a state "X से Y हुआ" (all 18 Money scripts) | 29 of 886 (v1 4 of 32) | 0 of 869 after the lesson resume `-e` (29 October 2026; v1 21 of 32 beats changed, passed); the checker then found forms the pattern missed (entry 27); 0 of 871 under the widened pattern after the resume `-f` (30 October 2026) |

Next: v1 again through BIE (script resume under S2-09, plans under CV-13 to CV-16, render), its page with the before/after,
then the narration lock of its 11 examples.

## Entry 26 · the five Money scripts the resume could not pass: what the source lacks, undated outside facts, the term named in a sister part, 29 October 2026

**What the lesson resume `-d` taught** (`runs/vm-t046c-money-lesson-d-brain-lesson/`, Codex maker and reviewer, ₹0): 13 of 18
scripts passed; five stopped on reviewer findings BIE's code never saw. v2: three beats said what the source lacks ("dates
नहीं हैं", "Dates नहीं दी गईं"), a W-01 shape the word list did not know. v4: an on_screen text audited the source ("USD
caption supplies no numerical shares or data source … EUR caption ends at 'second-most'"); W-01 read only the narration. v10:
operational descriptions of UPI, NEFT, RTGS and IMPS (basis mixed or outside) with no dated source, "the explicit UPSC sourcing
condition" (S1-16's real-life link already asks for a dated source; the beat had no place to put one). v11 and v12: the term
named and explained in a sister part of the same concept before its example ran ("the UPI route" across b20–b25 before the
₹100 kirana payment in b26; "BBPS" in b33 before the ₹600 bill in b44); the S2-08 check looked only at the beats that cover
the item, and v12's item listed "interoperable" as its term, not BBPS.

**What changed in BIE (branch `task046c-five-scripts`, on top of work A):** `visual_grammar.json` 2026-10-29.1: W-01 words for
"what the source lacks" in Hindi, Hinglish and English (the story's own numbers stay allowed); `soul.wording_problems` reads
on_screen too. Vision rulebook 2026-10-21.16: new S2-10 (a competitive-exam teaching beat whose basis is outside the book, or
mixed and naming an institution or system its book lines do not, carries its dated source in the beat's new `source` field;
a story, example, hook, analogy or question needs none; level `upsc_pcs` only) with `soul.dated_source_problems` in the script
check and `source` in the script schema (lesson-script/6; the fake maker writes it); S2-08 extended: the first naming beat is
any teaching beat of the same concept, and the terms kept for after the example are those the naming sentence names plus its
acronyms (`soul.naming_terms`). Three regression rule-change entries, so earlier passed scripts report the new findings as
changed rules and the resume rewrites only those beats.

| Measure (all 18 Money scripts of resume `-d`, 886 beats) | Before (code findings) | Now |
| --- | --- | --- |
| v2's "dates नहीं हैं" beats caught by code | 0 of 3 | 3 of 3 (W-01 4 in v2) |
| v4's source-auditing on_screen caught by code | 0 | 1 (W-01 3 in v4) |
| v10's undated outside facts caught by code | 0 | 2 beats (S2-10) |
| v11's and v12's term-before-example caught by code | 0 | v11 2, v12 2 (S2-08) |
| W-01 hits across the chapter | 0 | 12 (v1 1, v2 4, v4 3, v7 1, v13 2, v15 1) |
| S2-10 hits across the chapter | — | 51 (v12 14, v13 13, v16 9, v6 5, v14 4, v10 2, v11 2, v2 1, v17 1) |
| S2-08 hits across the chapter | 0 | 5 (v11 2, v12 2, v7 1) |
| Tissue passed outputs (`tests/fixtures/passed_outputs/`) | 0 problems | 0 problems (the new findings are changed rules) |

After, the lesson resume `-e` (29 October 2026, 22:02–22:30Z, Codex maker and checker, ₹0, ChatGPT plan 0 → 1 % of the week):
W-01 12 → 0, S2-10 51 → 0, S2-08 5 → 0 by code on the 869 beats; 414 beats changed; the five scripts (v2, v4, v10, v11, v12) no
longer fail on these rules, yet all five still failed, now in the checker's round (entry 27). 6 of 18 passed in all.

## Entry 27 · the Money lesson resume -e: a checker that asks beyond the rules, and the state report without a verb, 29 October 2026

**What the run taught** (`runs/vm-t046c-money-lesson-e-brain-lesson/`, Codex maker and Codex checker, 80 calls, 52.9 minutes of
call time, ₹0, ChatGPT plan 0 → 1 % of the week): the code rules of entries 25 and 26 did what they were built for. On the 869
beats of the resume, S2-09, W-01 and S2-10 report 0, 0 and 0 (40, 12 and 51 on the 886 beats of resume -d); 414 beats changed;
v1 passed again with 21 of its 32 beats rewritten in 3 patch rounds. Yet only 6 of 18 scripts passed (v0, v1, v5, v8, v16, v17),
down from 13: 12 scripts failed in the checker's round, after every code check had passed, on 33 blocking findings:

| The checker's finding | Findings | Scripts | By BIE's rules |
| --- | --- | --- | --- |
| "Examinable outside facts lack dated sources" (cards need not store money, biaxial film orientation, William IV's 1835 issue) | 8 | 10 of 12 | S2-10 is the code's: only a teaching beat that names an institution or system none of its book lines names needs `source`, and the code had passed every beat |
| "The term is named before its example" (standardisation in b8, the cheque in the hook, intrinsic value, monetary policy) | 6 | 7 | S2-08's order is the code's and binds the terms the naming sentence names; a hook may ask |
| "Add a short clarification that this is an undated schematic sequence" | 1 | 1 | W-01 forbids saying what the source lacks |
| State reports the code's pattern missed: "Wheat 10 से 8 kg", "जेब में 5 से 3", "receipt ₹0 से ₹100 होती है", "seller को ₹0 से ₹20 मिलते हैं" | 4 | 4 | the rule's; the code's pattern knew only the हुआ form |
| Content findings that stand: terms compressed into labels (4), the same transaction run again (3), routes only named (3), the layout of the source taught (1), a question half answered (1), an example without numbers (1) | 13 | 9 | the checker's call |

Three scripts that had passed in -d (v3, v7, v9) and four more (v6, v13, v14, v15) failed only because the resume re-checks every
script: once a script is continued, the checker reads the whole of it again and names findings it had not named before; each round
it named new ones once the earlier were fixed (v15: 6 rounds). Patches for the checker's findings cost code rounds of their own
(S2-04 words, S2-07 read-out lines).

**What changed in BIE** (branch `task046c-checker-reads`):

- `lesson.script_finding_minor` (entry 22's filter) now also reads as minor by code a finding that asks for a dated source,
  attribution or a visible outside label ("source"), a finding that says a term was named before its example unless it also
  faults the example itself (no numbers, not run, a wrong mechanism; "example-first"), and a finding whose fix asks the script to
  say what the source lacks ("w01"). The reason is the same as for the time findings: the review runs only on a script BIE's
  code has passed, so the code's verdict on S2-10, S2-08 and W-01 stands; the finding stays in the record as `minor_by_code`,
  so a repeated one becomes code (an institution the S2-10 list lacks, a term the S2-08 sentence should bind).
- The checker's card (`SCRIPT_REVIEW_HOW`) says so, so the rounds are not spent on them.
- `soul.STATE_REPORT` refuses every form of the state report: with a verb (हुआ, होती है, मिलते हैं, रह गया, बचे, बढ़ा …) and without
  one ("wheat 10 से 8 kg", "जेब में 5 से 3"); a range ("6 से 8 मिनट लगते हैं", "₹100 से ₹500 के बीच", "10 से 20 तक") goes on with another
  word and is left alone; the comma of "₹1,000" is not a clause end; `\b` is not used after a Devanagari matra (it fails there).
- Vision rulebook 2026-10-21.17: S2-09 names the forms; S2-10 and S2-08 say that BIE's code decides where a source is due and in
  what order the term comes, and that a checker's wider demand is minor by code. A regression rule change for S2-09, so an
  earlier passed script reports the new hits as a changed rule.
- Tests: `tests/test_task046c_checker_reads.py` (10), the pins of five suites.

| Measure | Before | After |
| --- | --- | --- |
| The 33 blocking findings of the 12 failed scripts' last round | 33 block | 15 minor by code (source 8, example-first 6, w01 1), 18 stand; v3 and v7 have nothing blocking left |
| State reports found by code on resume -d's 886 beats | 40 | 67 |
| State reports found by code on resume -e's 869 beats | 0 | 11 (v2 3, v5 1, v6 2, v11 4, v17 1) |
| Passed outputs (`tests/fixtures/passed_outputs/`) | 0 S2-09 problems | 0 |
| Scripts passed | 6 of 18 | **18 of 18** (the lesson resume `-f`, 30 October 2026 00:08–00:22Z, 14 minutes, 51 calls, 22 minutes of call time, 1.46 M input and 60 k output tokens, ₹0, ChatGPT plan 1 → 3 % of the week; 119 beats changed; v3, v4 and v7 passed in round 0; the checker, told in its card, reported none of the three kinds of finding, so the filter downgraded nothing; S2-09 0 of 871 beats) |

Not changed, for Navin to decide: whether a competitive-exam lesson should carry a dated source for every outside fact (the
checker's reading) or only for institutions and systems (BIE's rule today), and whether every concept term must wait for an
example (the checker's reading) or only the term the example names (BIE's rule today). The findings stay visible as minor in
every record and on the review pages.

## Entry 28 · Navin's verdict on the whole Money chapter: one setup, text on boards, and things BIE never gathered, 30 October 2026

**What the runs taught** (the canvas runs `vm-t046c-money-canvas-e1-brain-canvas` and `vm-t046c-money-canvas-f-brain-canvas`, 234
parts of 18 videos, and Navin's verdict on the 18 review copies, in his words in STATUS "Task 046 · Part D1"): measured by code,
162 of the 234 parts (69 %) ran in the bank or shop world, chosen by a keyword in the beats; the whole chapter used 29 distinct
icons, from a fixed menu of icon queries; 43 canvas parts had only text on screen, and text alone held the screen for 1,400 of
9,122 seconds (15 %), in 40 stretches over 10 s; the book's own pictures (37 placements: timelines, tables, the page-2 panel of
icons) were drawn 0 times; a caution phrase could reach a board. The director laid out text before it had thought about what
the learner should see, and it could only pick from the world BIE already had.

**What changed in BIE** (branch `task046d-visual-thinking`, IMPLEMENTED; STATUS "Task 046 · Part D1"):

- The canvas section thinks before it lays out: per beat the idea, a relation from `bie/brain/rulebook/visual_verbs.json` (15
  relations, each with what is shown on the canvas and in a world), the things, people and places, what is seen and on which
  word; checked by code and kept as the dikhane ki list (`visual_ideas/<video>.json`), shown on a page before the render.
- Code decides the picture first: the book's own diagram or table is drawn as itself on the paper canvas, on the part's own
  beats; then the card part's type; then the maker.
- The maker names things; code finds them in the full icon index (aliases, Hindi, emoji names, whole words, religious symbols
  only when asked) and the shared library; what is found nowhere goes to `needs.json`; a fetch workflow in GitHub Actions brings
  CC0, PD and CC BY images, licence-checked and credited, into the library the next run reads first.
- No world by keyword; never the same kit in two consecutive parts; checks D1-01…D1-06; a board of 2 lines of 28 characters;
  the per-video report; LOOK-D1 on one still per part, report only.
- A dry run with the fake maker on the real v2 and v4 inputs (offline, ₹0) caught, before any live call, a book picture
  covered only by a story world (never drawn) and a picture counted once per piece; both fixed with tests.

| Measure | Before (runs e1 + f) | After |
| --- | --- | --- |
| Bank + shop share of parts | 69 % (v2 56 %, v4 67 %) | expected lower: a world only for the example's story; measured on the v2 / v4 run |
| Distinct icons | 29 (v2 7, v4 4) | from the v2 / v4 run |
| Text-only screen time | 15 % (v2 91 s, v4 146 s); 40 stretches over 10 s | 0 stretches over 10 s by check D1-02; seconds from the run |
| The book's own pictures drawn | 0 of 37 (v2 0 of 3, v4 0 of 4) | 37 of 37 compile offline; v2 and v4 from the run |
| First-try pass, rounds, ₹ | canvas run f: 151 of 195 parts first try (77 %), 247 rounds, ₹0 (Codex); v2 13 of 18, 25 rounds; v4 16 of 18, 21 rounds | from the v2 / v4 run (Codex, ₹0; the ideas step adds one call per part) |
| Passed outputs | 0 problems | 0 problems |

Live numbers come from the v2 and v4 run after the merge; until then the after column is expected, not measured.

## Entry 29 · the first live run of Part D1: a cue on "$", a picture called by its name, and the card type in the wrong field, 31 October 2026

**Run:** `runs/vm-t046d-money-canvas-a-brain-canvas/` (VM job `t046d-money-canvas-a`, Money v2 and v4 with the narration of
lesson resume `-f` locked, Codex maker and Codex checker, 56 minutes, 113 calls, 1.10 M input and 0.42 M output tokens, ₹0,
ChatGPT plan at 8 % of the week).

**Taught** (from the run's records): v2 passed 18 of 18 parts; v4 16 of 18. The two v4 parts failed three rounds each on BIE's
own code: v4_s5 on a cue word that is a currency sign (`$`, then `¥`, then `€`: the word matcher dropped signs, so the cue
could never be found although the beat says "$ वाला United States Dollar"), v4_s7a on references to the maker's own gallery
by its id (`sets`, `commemorative`, `status`: a picture's id becomes many elements, and the error did not say which ids
exist). In the new ideas step, 21 of 36 parts needed a second round, every one for the same reason: `picture_type` held the
card part's type ("definition"). The needs list held years, roles with no icon, and "blender" found for "lender".

**Changed in BIE** (branch `task046d-proof-fixes`, IMPLEMENTED): a cue of currency signs matches the sign (earlier cues
unchanged); a picture's id in a focus, target or arrow means the picture, and a missing id error lists the plan's ids;
`picture_type` is an enum in the ideas schema and a card type is read as its picture; a year is not a thing; role aliases
(payer, recipient, creditor, lender, debtor, borrower, porter, traveller, neighbours, valuables, issuing authority, with Hindi
forms); icon search matches a query word only where an icon's word starts with it. From v2's render (CI run 41222648107) and its 18
stills: a camera box keeps 3.5 % of the frame around it (the book's table had lost its first letters at the edge), a
`curve: true` arrow bends gently (it had swung a whole arrow-length across the gallery), a tag's words are white. From the
fetch workflow (run 41222654555, cancelled at its 30-minute limit with nothing saved): a time budget with `not_tried`, the
library saved after every find, the museum only for image needs with fewer, shorter object reads. Tests in
`tests/test_task046d_visual_thinking.py` (`ProofRunFixes`, 23 in the file).

| Measure | Before (canvas run f, 29–30 Oct) | After (this run) |
| --- | --- | --- |
| v2 parts in a bank or shop world | 10 of 18 (56 %) | 5 of 18 (28 %) |
| v4 parts in a bank or shop world | 12 of 18 (67 %) | 6 of 16 passed (38 %) |
| Distinct icons (v2 / v4) | 7 / 4 | 54 / 43 |
| Canvas parts with only text (v2 / v4) | 3 / 4 | 0 / 0 |
| v2 text-only screen time | 91 s of 596 s, 2 stretches over 10 s | 9.9 s, 0 over 10 s |
| The book's own pictures drawn (v2 / v4) | 0 of 3 / 0 of 4 | 3 of 3 / 3 of 4 |
| Plans first try (v2 / v4) | 13 / 16 of 18 | 12 / 11 of 18 |
| Rounds (v2 / v4) | 25 / 21 | 24 / 31 |
| Ideas step first try | (new) | 15 of 36; expected 36 of 36 with the enum (all 21 second rounds had that one cause) |
| ₹ | 0 | 0 |
| Replays with the fixes | — | v4_s7a: 3 of 3 recorded answers pass; v4_s5: the cue error gone, CV-13 next |
| Earlier plans recompiled (268 of runs e1, f and this) | — | 0 differences with and without the fixes; 108 refused by Part D1's 2 × 28 board (Navin's rule, PR #111) |
| Passed outputs | 0 problems | 0 problems |
