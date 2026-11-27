# Yaadein: what the script writer has learned

Newest at the bottom. Add a few lines after each heading you finish and after each verdict Navin gives: the date, the
book and heading, what you learned, his words verbatim when he gave any. Keep entries short; this file is read every
session. When it grows past about 300 lines, fold old entries into the skill or `navin-ki-baatein.md` in a reviewed PR.

## 2026-11-26 · Chapter 11 (Photosynthesis), headings 11.6.2 and 11.6.3

- The gold standard (11.6.3 c2–c3) was written by a Claude after Navin returned its first cut ("truncate kiya hai");
  the full rewrite passed. A good script comes from the way and from his review together.
- A fresh Claude given only BIE's messages wrote 11.6.3 much closer to the gold standard than Codex (BIE's problems
  17 → 2 → 0), but less tight: a few bookish "fact" lines, no wrong idea, a weaker slope picture, and 235 → 344
  sentences from fix rounds. So the writer matters most, and patching hurts.
- Claude's own 11.6.2 (relay daud misaal; ATP as a charged battery; gulel for bond energy; Figure 11.6 walked label by
  label; the 680 nm wrong idea) and Claude's 11.6.3 c4–c12 (carriers that take only an electron against those that take
  H⁺ too; PQ moving inside the membrane; Fd and FNR; lumen pH about 5 against stroma about 8, so about a thousand times
  the H⁺; the energy from light to electron to H⁺ to ATP; "biosynthetic" opened) are Claude's demos: Navin's verdict
  is pending, so they are not gold.
- Every plain-text call BIE sent Codex ended "Reply with one JSON object" (fixed in PR #224); if a BIE message seems to
  ask for two forms, follow the task's own form.

## 2026-11-27 · Chapter 11, heading 11.7.2 (Calvin cycle) · job c3, the taught chat's copy on the VM

- First heading written on the VM by the copy of the chat Navin taught (PR #227), a heading it had never written.
  181 sentences, 15.8 words each, 25 % spoken to the learner, 57 facts (9 teacher's extras); BIE's checks 0 problems
  after one rewording round that added nothing. Codex s6 on the same heading: 85 sentences, 18.4 words, 31 problems,
  English-heavy ("carbon ledger", "acceptor pool").
- Puzzle: every CO₂ uses up one RuBP, so why does the leaf never run out? The deeper turn held for regeneration with
  "ruko, pehle khud socho: RuBP ke paanch carbon kahan se aayenge?". Running picture: dukaan ki poonji (RuBP = poonji,
  CO₂ = naya rupaya, ATP + NADPH = bijli-mazdoori, sugar = kamaai), which carries the count exactly (₹15 + ₹3, ₹15
  back, ₹3 kamaai), why regeneration matters ("jo dukaandar poonji kha jaaye, uski dukaan agle din nahi khulti") and
  why RuBP is not in the In/Out table.
- Cost (Navin's Usage screen): one heading ≈ 14 % of a 5-hour session and ≈ 1 % of the week; 83 turns, each re-reading
  the whole memory.

## 2026-11-27 · heading 11.7.2 again · job c5, the same copy with a packet from BIE (kept out)

- 209 sentences, all 11 items, 0 problems; 63 turns, ≈ 12 % of a session. A new picture (dahi aur jaman) and finer exam
  points, but less of c3's why and no "ruko" at the real turn. The same copy writes differently each time: the way is
  what holds, not the lines.

## 2026-11-27 · Navin's verdict on c3 and c5

- "Bilkul c3 hi meri choice thi … uske teacher ka bolne ka tarika". "C3 is our golden benchmark after rectifying recap
  ke sath yaad rakhein ant mein shuru ka sawal aur khula chhodo." Keep c3's way; within it add the exam's fine points
  and B3's two ends (`navin-ki-baatein.md`, B3 and "Exam ki baareek baatein"). The packet is taken out again ("packet
  needs wala option bhi hata do").
- What c3 missed: "yaad rakhein" in the opening recap, and its closing question was half answered ("…apna khaas
  tareeka rakhte hain"); c5 asked the opening question again at the end and left the next one open.

## 2026-11-27 · heading 11.7.2 · job c6, Navin's verdict applied to c3, locked as the golden benchmark

- The same copy applied his verdict to its own c3 in 22 turns: the recap's third line opens "Yaad rakhein:" and a new
  line "Aage hum dekhenge ki yahi ek baat ek badi paheli khadi kar deti hai" leads into the question; at the end the
  opening question comes back and is answered (with the dukaan), and the C₄ question stays open: "C₄ paudhe alag kis
  baat mein hain, yeh aage hum dekhenge." 11 of 13 points word for word, 0 problems, 181 → 185 sentences.
- Learned: a closing question carries no part of its answer; "yaad rakhein" sits best on the recap line that already
  holds the one thing to keep, so the recap does not grow.
- Navin: "Haan, pakka karo". The heading is `references/benchmark-11.7.2.json` (learn the way, never copy; withheld
  while 11.7.2 of this book is written). The `bridge` field still names how C₄ plants differ; it is not spoken.

## 2026-11-27 · heading 11.6.2 · job c7, Navin's verdict on Claude's 11.6.2, locked as a golden namuna

- "Script yeh bhi bahut badhiya bani thi yeh bhi ek golden namune layak hai of course with the changes described in c3".
  The same copy added, in 26 turns: the recap's "Yaad rakhein: is safar mein electron ek hi disha mein chalta hai …" and
  "Aage hum dekhenge …"; one exam point (PS I is numbered for the order of discovery, not of work); at the end the
  opening question again with its answer, and "ATP bana kaise, yeh aage hum dekhenge." 4 of 7 points word for word.
- Navin: "Haan, pakka karo". The heading is `references/benchmark-11.6.2.json`. Its film (26 Nov) had a shot with no
  picture (the gulel, lines 18–19: black screen, labels only) and arrow colours that differ from the script: film work.
