# Cost log · ledger estimate against the real bill

Started 22 October 2026 (Task 043). Every live run writes `SUMMARY.json` with a `cost` block: rupees per section
and per page from the ledger, the cap, and `real_bill_inr: null`. The ledger cost is an **estimate**: exact token
counts times the dated price table (`bie/model_gateway/live/pricing.py`), plus the AICredits 10% markup for
AICredits routes, converted at ₹94.59 per dollar (the AICredits rate of 20 October 2026). It is not the bill.

Navin reads the real amount on the provider dashboard (AICredits wallet history; OpenAI billing) and tells
Claude; Claude writes it in the "Dashboard" column. A difference of more than 15% means the price table or the
markup is wrong and is fixed before the next estimate is trusted.

Runs before 22 October were estimated in dollars; their rupee values below use the same ₹94.59 rate.

| Date | Run | What | Routes | Ledger estimate | Dashboard | Difference |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-20 | 39450174687 | smoke, 3 providers | Claude + Gemini via AICredits, GPT direct | ₹0.27 | not recorded | — |
| 2026-10-20 | 39450332562 | blind test, tissue chapter | Claude + Gemini via AICredits, GPT direct | ₹34.09 | not recorded | — |
| 2026-10-21 | 39610917448 | Section 1, pages 3 and 7 | Claude (AICredits) maker, GPT reviewer | ₹339.70 | not recorded | — |
| 2026-10-21 | 39615516524 | Section 1, pages 3 and 7 | Claude (AICredits) maker, GPT reviewer | ₹79.81 | not recorded | — |
| 2026-10-21 | 39617164262 | Section 1, pages 3 and 7 | GPT maker, Gemini (AICredits) reviewer | ₹58.98 | not recorded | — |
| 2026-10-21 | 39620281561 | chain, all 14 pages | GPT maker, Gemini (AICredits) reviewer | ₹242.54 | not recorded | — |
| 2026-10-21 | 39627682253 | chain resume | GPT maker, Gemini (AICredits) reviewer | ₹148.02 | not recorded | — |
| 2026-10-21 | 39634687099 | smoke | Gemini (AICredits); GPT out of credit | ₹0.10 | not recorded | — |
| 2026-10-22 | 39734021966, 39734670129 | probe (model lists) | Gemini (AICredits) | ₹0 | — | — |
| 2026-10-22 | 39734293232 | live smoke, `max_inr` 5: stopped at preflight (checker model not allowed on the key) | Gemini 4 Argon maker, Gemini 3.1 Pro checker | ₹0.08 | not recorded | — |
| 2026-10-22 | 39735198529 | access check of 6 Gemini models (5 refused at no cost) | Gemini (AICredits) | ₹0.08 | not recorded | — |
| 2026-10-23 | VM job t044-step5-tissue | Section 1, tissue pages 1, 7, 11, 13; map stopped by the ₹30 cap | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹23.55 | not recorded | — |
| 2026-10-23 | VM job t045b-tissue-understand (job 1) | Section 1, tissue pages 2–6, 8–10, 12, 14 and the chapter map | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹60.99 | not recorded | — |
| 2026-10-23 | VM job t045b-tissue-lesson (job 2) | Section 2, tissue lesson plan and 17 scripts | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹104.56 | not recorded | — |
| 2026-10-23 | 40007533161 | cache probe: 2 calls with one 5,246-token prefix (no cache hit) | Gemini 4 Argon (AICredits) | ₹2.24 | ₹2.43 (AICredits `usage.cost` in the answers) | the bill is 8.5% above the ledger |
| 2026-10-24 | VM job t045d-tissue-understand (Task 045d job A) | Section 1 under the teaching-soul rules; stopped after page 2 by the AICredits key budget (402 `API Key Budget Exceeded`), not by BIE's cap | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹13.51 | not recorded | — |
| 2026-10-24 | VM job t045d-tissue-understand-resume (probe) | stopped at preflight: the key budget still exceeded | Gemini 4 Argon (AICredits) | ₹0 | — | — |
| 2026-10-24 | VM job t045d-tissue-understand-resume2 (Task 045d job A, part 2) | Section 1 under the teaching-soul rules: 12 of 14 pages passed, stopped by the ₹70 cap before page 14's review | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹65.90 | not recorded | — |
| 2026-10-24 | VM job t045d-tissue-understand-resume3 (Task 045d job A, part 3) | pages 13 and 14 and the chapter map; 14 of 14 pages and the map passed | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹20.87 | not recorded | — |
| 2026-10-23 | VM job t045c-tissue-lesson-v2 (job 3) | prerequisite trim, lesson plan and 11 scripts under the 23 October rules | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹78.17 | not recorded | — |
| 2026-10-23 | VM job t045c-tissue-lesson-v2-resume | the 5 failed tissue scripts again (4 passed) | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹21.39 | not recorded | — |
| 2026-10-23 | VM job t045c-tissue-lesson-v9 | tissue v9 again (passed); the chapter's 11 scripts all pass | Codex maker (ChatGPT plan, ₹0), Gemini 4 Argon (AICredits) checker | ₹6.87 | not recorded | — |
