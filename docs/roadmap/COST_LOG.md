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
