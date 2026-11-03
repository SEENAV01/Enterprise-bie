# Money v2 demo: how it was made (Claude's demo, not BIE output)

Navin asked (3 Nov 2026) for v2 made by Claude following BIE's workflow start to end, with his interim clone voice, so he
can judge it and, if it passes, the process becomes BIE's. This file records every step and the reasoning, so it can
be turned into BIE's rules, saanche and code.

## 1. Book → what this video must teach

- Source: `chapters/indian-economy-3-money.pdf` pages 2–3 (blindtest-inputs). Items: the 32 chapter-map items BIE's
  own v2 covers (lesson-f), so the comparison with BIE's v2 is fair.
- Teaching order is not the page order: barter → its features → its problems → evolution of money (the page's
  picture) → intrinsic vs extrinsic (the page's table) → commodity money → where it was used (page 3's table) → its
  features and problems → recap. The page puts the comparison table first; a learner needs barter first.

## 2. Narration rules applied (`script.py`, 67 lines, 1,192 words)

1. One idea per sentence; short sentences.
2. Story first, name after: "रामू दो किलो गेहूँ देता है … इसी को barter system कहते हैं".
3. Every English term is opened in plain Hindi the first time (medium of exchange = बीच का ज़रिया, inherent worth =
   अपनी असली क़ीमत, pastoral = जानवर पालकर जीने वाले).
4. Numbers that a learner can follow (10 kg → 8 kg, ₹500 − ₹300 = ₹200).
5. No caution or fact-check lines in the narration (they stay background checks; Navin, 30 Oct).
6. Never "किताब कहती है" (W-01).
7. Same characters through the video (Ramu the farmer, Mohan the cloth seller) so the parts feel like one story.
8. A table row is taught as a spoken comparison with a concrete case, not read out.
9. Avoided images that hurt (no "cutting a cow"; an unsplittable charpai is used for indivisibility).
10. Coverage check by code: every book item of v2 is covered by at least one line (32 of 32).

## 3. Voice

- Navin's interim clone: Chatterbox Multilingual (MIT), his 12 s reference, pitch −2 semitones (his choice, 31 Oct).
- English terms are written in Devanagari for the voice only (subtitles keep them in Latin): "डबल कोइंसिडेंस ऑफ़
  वॉन्ट्स".
- One file per sentence; long tails trimmed; gaps: 0.28 s between sentences, 0.45 s between lines, 0.9 s between
  scenes. Generation is capped by sentence length (the model otherwise keeps generating noise after the sentence).

Run record: 142 sentences generated on a 2-CPU machine without GPU (about 1 minute each, about 2.5 hours in all);
every sentence checked by speech-to-text against its text; 2 regenerated with another seed (one garbled word, one
half-lost sentence); extra noise after sentences cut at the last word. Final narration 10 min 53 s.

## 4. Dikhane ki soch (`builder.py`)

For every line: the THING said is on screen, and the ACTION said happens, on the word it is said (cue words, timed
from the voice). Visual verbs used:

| What the line says | What is shown |
| --- | --- |
| A gives B something | the thing travels from A's hand to B's hand (give/receive poses) |
| refuse / not wanted | head shake + red cross on the thing |
| match / accepted | tick, both smile |
| wants something | thought bubble with that thing |
| quantity changes | the tag on the thing changes (10 kg → 8 kg) |
| sequence / stages | the book's own 6-step strip, camera visits each step |
| comparison | left vs right, one difference at a time, a label each side |
| many-to-many confusion | a web of lines between things with "?" rates |
| cannot be divided | dashed cut line + saw + cross |
| spoils over time | bugs on the sack, 100 kg → 90 kg, calendar |
| payment by phone | QR stand, phone scan screen, "₹300 भेजे", shopkeeper's phone "₹300 मिले", bank → bank arrow |
| place in history | world map (land only, no borders), pin + label + the thing |
| term defined | coloured pill with the term, after the story |

Layout rules followed: people about 40% of frame height; on-screen text at least 40 px at 1080p; a reserved subtitle
strip; a section label top-left; the camera moves in to what is being said and back out; no screen without the thing
being talked about for more than about a second.

## 5. Things needed and where they came from (the needs list)

- Microsoft Fluent Emoji, colour style (MIT; licence file read from the repository): wrench, bicycle, handshake, hut,
  cow, ox, goat, basket, credit card, classical building, balance scale, pot of food, shopping bags, leaf, bucket,
  magnifying glass.
- Drawn as code for this video (would become BIE saanche): sack (wheat/salt, with label), salt packet, wheat, cloth roll
  and stack, coins (gold/silver/copper, no symbols), BIE-style notes (₹ and value, colours unlike RBI's), note bundle,
  gold bar, cheque, QR code and stand, phone with scan / paid / received screens, bank, account card, charpai, matka,
  oil tin, cowries, tea brick, tobacco, calendar, heaps (clean/wet salt, grain), bugs, sweat, marks (cross, tick, ?,
  circle), 10 characters with poses (stand, give, receive, hold, think, point, write, carry, walk, shake, nod) and
  expressions, backgrounds (village, haat, shop with counter, store room, paper, parchment).
- Not used on purpose: Fluent's salt shaker (modern), money bag and bank with "$", real currency designs, real persons.
- Map: Natural Earth land outline via the `world-atlas` package (ISC; data public domain), land only, no country borders.
- Fonts: Baloo 2 and Hind (OFL).

## 6. What BIE does differently today (for the comparison)

- BIE's v2: world kits only shop/bank, goods fixed, actions few; icons chosen by keyword; tables shown for minutes.
- This demo: characters act, things travel, the book's own pictures are drawn, one difference at a time.
- If Navin passes this, the parts to build into BIE: the character kit with poses and hand positions, the action
  templates (give, refuse, bubble, cut, spoil, scan-pay, cheque-transfer), the drawing library above as saanche, the
  cue-word timing from real voice durations, and the layout rules as code checks.
