# Phase 1 · Part F ka faisla-report: BIE ka Money v4 बनाम Claude ka v2 demo

4 November 2026 · Claude ki report Navin ke liye · har number asli run se, kuch bhi haath se nahi.

## Dekhne ke liye

- **Faisla-page (frames + numbers ek saath):** https://claude.ai/artifact/WFQoPjcxZURK6QmYg5pfsr
  (repo copy: `runs/p1f-decision/index.html`, branch `blindtest-results`)
- **BIE ka v4 video:** `runs/p1f-money-v4/videos/v4.mp4` (14.7 min, captions-only — awaaz aapke yes ka intezaar)
- **v4 ka poora review page (notes + game samet):** `runs/p1f-money-v4/REVIEW.html`
- **Claude ka v2 demo, usi road se render:** `runs/p1f-money-v2demo/review-720p.mp4` — label: **Claude's demo, not BIE output**

## Ek line mein

BIE ne pehli baar poora kaam khud kiya — kitab ke lesson se scene plan, notes aur game **BIE ke AI ne likhe**,
compiler ne jaancha, one button ne render karke ek page par rakha. Quality aapke verdict ki baat hai; road ab
poori tarah judi hui hai aur ₹0 AI kharch par chalti hai.

## Numbers (ek hi engine, ek hi render road, ek hi naap)

| | BIE ka v4 | Claude ka v2 demo |
| --- | --- | --- |
| Kisne likha | **BIE ke director ne** (Codex, VM pe) | Claude ne haath se (gold example) |
| Scenes / cheezein | 12 scenes · 274 cheezein | 20 scenes |
| Lambai | 14.67 min (26,398 frames) | 10.87 min (19,564 frames) |
| Rounds | 2 (compiler ne 3 overlap pakde, director ne patch kiya) | — |
| AI kharcha | ₹0 (ChatGPT plan) | ₹0 |
| Render | 5.5 min wall · ₹24.43 list · ₹0 billed | 4.1 min wall · ₹18.68 list · ₹0 billed |
| Frame-audit: texts dikhe | 338 | 320 |
| 36 px se chhote (≥1 s) | **65** | 32 |
| Ek-doosre par (≥1 s) | **28** | 10 |

Notes: **9 panne, pehli hi koshish mein pass** (0 picture-panne — sab flow/compare/table). Game: **11 levels,
4 mechanics** (run_process, place_right, build_timeline, find_partner), 2 rounds.

## Aankh se jaanch (imaandaari se)

- **Achha:** 0:45 gold-backed bank ki kahani (cards, log, bank — sab padhne layak); 3:00 Sweden 1661 ka card;
  10:20 legal tender ka ₹1 hisaab; 13:40 deposit-transfer ke teen log. Look v2 demo jaisi hi hai.
- **Kamzor:** 6:40 ke aas-paas narration Euro par hai aur screen par khaali thela — dikhaya-bola mel nahi.
  Chhote text dono video mein hain, jad ek hi hai: **saanche ke andar ke labels** (card headers 16–21 px,
  "24K", "चावल") jo plan-compiler nahi dekhta. v4 zyada labeled saanche istemal karta hai, isliye uske
  number zyada. Yeh agla code-fix hai (saanche ke label-size floor + build-time check).
- v4 ke plan mein **map saancha kahin nahi** — India-outline wala niyam (4 Nov) is video ko chhoota hi nahi.

## Road ne kya sikhaya (paanch seekh-PR, sab merged, SEEKH 42–46)

| Run ne kya sikhaya | BIE mein kya badla |
| --- | --- |
| Codex free-form schema par request hi thukra deta tha | strict-ready guard — band schema provider ko, khula prompt se (PR #135) |
| Maker ko jawab ka envelope dikhta hi nahi tha | schema ab prompt ke andar jaata hai (PR #136) |
| Galat shape par BIE ka apna check crash ho kar job maar deta tha | crash ab naam-wala round-problem hai, job kabhi nahi marta (PR #140) |
| Notes ke zaroori fields prompt mein the hi nahin (5 fail rounds) | page ka poora shape asli constants se prompt mein — pehli-baar pass (PR #143) |
| Render ki frames-ginti sirf purana spec-shape jaanti thi | `render.total_frames` dono kinds; one button bana-banaya render skip karta hai (PR #144) |

One button ko do baar dabana pada (pehla press render ke us bug par ruka); ab wahi bug test se bandha hai.
Ek aur sudhaar: pehle maine VM ko "atka hua" samjha tha — galat; gamelevels job 150 minute soch raha tha.

## Status words

Parts A–E **INTEGRATED** (asli chapter par, asli upstream/downstream ke saath). Kuch bhi **ACCEPTED nahi** —
woh aapka verdict hai. Awaaz abhi captions-only (aapke yes ka intezaar).

## Aapke liye sawaal

1. **Verdict:** BIE ka v4 kaisa laga — aage is road par aur chapters, ya pehle kuch sudhaar?
2. Chhote saancha-label fix (floor + build-time check) agla kaam ho?
3. Dikhaya-bola mel (6:40 jaisa) ke liye director par ek aur check lagayein?
