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
- The checker reads every answer (pages, map, plan, scripts) as compact JSON, without the spaces.
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
