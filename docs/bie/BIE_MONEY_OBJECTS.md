# BIE's money pictures: the rules and how BIE keeps them

Task 046 Part D2 item F, 1 November 2026. Navin's brief: "BIE's own SVG components for money things: Indian coins (₹1, ₹2,
₹5, ₹10, ₹20, 50 paise, 25 paise) and notes drawn in BIE's own style with their denomination, clearly not replicas of real
RBI designs (check RBI's reproduction rules and record them); cheque, passbook, QR stand, POS machine, phone payment screen,
salt sack, cowrie shells, cattle, grain sack, cloth roll." and "add Microsoft Fluent Emoji (MIT; licence-check, pin, record
the licence, credit line) as an icon source with its 3D style, preferred for objects".

**Retired on 2 November 2026** (Navin's addendum to Part D2: "maine salt aur kapde ka example diya ... aise to kal kisi aur
cheej ka jikar aayega to salt aur kapda hi dikhaoge, jabki mera kehna hai jis cheej ka jikar hai wohi cheej dikhe; yeh udaharan
maine is rup mein diye the"). The 26 drawings, `tools/bie_objects.py`, their icon index rows and the aliases that named them are
removed; the files stay in git history (commit `ef77d816` and earlier). Nothing is hand-made for one chapter any more: a thing
a beat names goes the general path (the shared library, the icon index, the fetch step, then BIE's coder, `bie/brain/coder.py`,
CONTRACTS §8c). The money rules below stay in force for anything BIE draws: the coder's card (`bie/brain/rulebook/coder_card.md`)
forbids a copy of a real banknote, coin, stamp or payment document, an emblem, a portrait or any words on the picture.

Status before the retirement: IMPLEMENTED (the drawings, the index rows, the search words, the licence gate, tests); never
INTEGRATED or ACCEPTED.

## What BIE now has

| Set | Ids | Files | Licence | Credit |
| --- | --- | --- | --- | --- |
| BIE's own drawings | `bie:coin-1`, `bie:coin-2`, `bie:coin-5`, `bie:coin-10`, `bie:coin-20`, `bie:coin-50p`, `bie:coin-25p`, `bie:note-10`, `bie:note-20`, `bie:note-50`, `bie:note-100`, `bie:note-200`, `bie:note-500`, `bie:note-2000`, `bie:cheque`, `bie:passbook`, `bie:qr-stand`, `bie:pos-machine`, `bie:phone`, `bie:salt-sack`, `bie:cowrie-shells`, `bie:cattle`, `bie:grain-sack`, `bie:cloth-roll`, `bie:gold-bar`, `bie:ledger` (26) | `bie/toolbox/icons/bie/*.svg`, drawn by `tools/bie_objects.py`, read from the repository (no network) | CC0 1.0 (BIE's own work; policy `own_work`: `bie-objects`) | none needed ("BIE's own drawings (Book Intelligence Engine)" is recorded on the asset) |
| Microsoft Fluent Emoji, 3D style | `fl:<name>` (1,595: every emoji, skin-tone variants left out, the default kept) | 256 × 256 PNG, fetched once per file from `raw.githubusercontent.com/microsoft/fluentui-emoji/1ffb34c752ecf5d402f04cfb4b392c77f57c54bc/` into the asset cache, never into git | MIT, for this source only | "Fluent Emoji by Microsoft, MIT" with the licence URL at the pinned commit and the repository |

The phone has a plain light screen so the video can write on it ("₹300 paid"); the QR stand carries a decorative pattern.
`python -m bie.toolbox.icons search "50 paise"` finds `bie:coin-50p`, "25 paise" finds `bie:coin-25p`, "cheque" finds
`bie:cheque`, "salt" (commodity money) finds the salt sack, "₹500 का नोट" the ₹500 note. A bare "coin", "coins" or
"सिक्का" still finds the plain Twemoji coin: a lesson about old gold coins must not show a modern ₹1.

## The rules (what Indian law and RBI say)

Checked on 1 November 2026. Quotes are short; the statute text was read on secondary bare-act copies because India Code
(`indiacode.nic.in`) answered 504 to the cloud workspace that day. Nothing here is legal advice; where a rule is unclear it
says so.

### 1. Bharatiya Nyaya Sanhita, 2023 (Act 45 of 2023, in force from 1 July 2024; it replaced IPC 489A to 489E)

- **s. 2(4), "counterfeit"**: "A person is said to "counterfeit" who causes one thing to resemble another thing, intending by
  means of that resemblance to practise deception". Explanation 1: "It is not essential to counterfeiting that the imitation
  should be exact." Explanation 2: when the resemblance is such that a person might be deceived, intent is presumed "until
  the contrary is proved". ([devgan.in, BNS s. 2](https://devgan.in/bns/section/2/))
- **s. 178, counterfeiting coin, Government stamps, currency-notes or bank-notes** (was IPC 489A for notes): imprisonment for
  life or up to ten years and fine. Its Explanation defines a bank-note as "a promissory note or engagement for the payment
  of money to bearer on demand" issued by a banker or a state "intended to be used as equivalent to, or as a substitute for
  money". ([devgan.in, BNS s. 178](https://devgan.in/bns/section/178/))
- **ss. 179 to 181**: using forged notes or coins as genuine, possessing them, and making or possessing the instruments or
  materials for counterfeiting (were IPC 489B, 489C, 489D). ([devgan.in, BNS s. 181](https://devgan.in/bns/section/181/))
- **s. 182, making or using documents resembling currency-notes or bank-notes** (was IPC 489E): whoever makes, uses or
  delivers "any document purporting to be, or in any way resembling, or so nearly resembling as to be calculated to deceive,
  any currency-note or bank-note" is "punished with fine which may extend to three hundred rupees"; (2) a person whose name
  is on such a document and who will not tell the police who printed it: fine up to ₹600; (3) the person named on it is
  presumed to have caused it to be made.
  ([AdvocateKhoj, BNS s. 182](https://www.advocatekhoj.com/library/bareacts/bharatiyanyayasanhita/182.php),
  [devgan.in, BNS s. 182](https://devgan.in/bns/section/182/))

**Unclear:** s. 182 says "in any way resembling", with no intent to deceive needed and no exception for teaching. It speaks
of a *document* that is made, used or delivered; a picture inside a video is not obviously a document, and no Indian case
about lesson videos was found. BIE therefore keeps as far from resemblance as a picture that still says "₹500" can be.

### 2. RBI's caution (press release 2000-2001/497, 29 September 2000)

"It has come to the notice of the Reserve Bank of India that toys with the reproduction of bank notes of Rs.1, 2, 5 and 50
are being sold in the market. The Reserve Bank has cautioned the members of public that reproduction of bank notes and
selling/possessing the toys/items looking like bank notes is an offence under the law."
([RBI press release](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=3803))

Police still book "Children Bank of India" play notes under the counterfeiting sections when they are passed as money
([Free Press Journal, Navi Mumbai](https://www.freepressjournal.in/amp/mumbai/navi-mumbai-2-held-for-possessing-fake-currency-notes-with-children-bank-of-india-printed-on-them-in-nerul)).

**Unclear:** RBI publishes no rule or permission process for pictures of notes in films, advertisements, websites or
lessons (unlike the European Central Bank, Decision ECB/2013/10, which asks for "SPECIMEN" across a digital image and at most
72 dpi at full size ([ECB FAQ](https://www.ecb.europa.eu/euro/banknotes/images/html/ecb.faq_reproduction_rules_euro_banknotes.en.html)),
or the Bank of England, which asks for its written permission for film or TV advertisements:
[Bank of England](https://www.bankofengland.co.uk/banknotes/using-images-of-banknotes)). In an RTI reply reported in October 2017, RBI withheld "The
information on form, material, design and security features of banknotes" beyond what is public, under s. 8(1)(a) of the
RTI Act ([Scroll, 15 October 2017](https://scroll.in/latest/854195/scroll_in)). BIE does not rely on any permission: it does
not reproduce notes at all.

### 3. What a real note carries (RBI's own list, so BIE can leave every item out)

RBI's press releases for the Mahatma Gandhi (New) Series list the salient features. For the ₹50 note (2017-2018/481): "See
through register", "Portrait of Mahatma Gandhi at the centre", "Micro letters 'RBI', 'भारत', 'INDIA'", "Windowed
demetalised security thread", "Guarantee Clause, Governor's signature with Promise Clause and RBI emblem", "Ashoka Pillar
emblem", "Mahatma Gandhi portrait and electrotype (50) watermarks", "Number panel", "Year of printing", "Swachh Bharat logo
with slogan", "Language panel", the motif (Hampi with Chariot), base colour "Fluorescent Blue", size "66 mm x 135 mm".
The ₹10 note (2017-2018/1848) has the same list with the Sun Temple, Konark motif, base colour "Chocolate Brown" and size
"63 mm x 123 mm". ([₹50](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=41412),
[₹10](https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=42782))

### 4. The State Emblem (State Emblem of India (Prohibition of Improper Use) Act, 2005)

s. 3: "no person shall use the emblem or any colourable imitation thereof in any manner which tends to create an impression
that it relates to the Government or that it is an offical document of the Central Government". s. 4: "No person shall use
the emblem for the purpose of any trade, business, calling or profession". Notes and coins carry the Lion Capital emblem;
a paid course is a business. ([Act text, PRS India](https://prsindia.org/files/bills_acts/acts_parliament/2005/the-state-emblem-of-india-(prohibition-of-improper-use)-act-2005.pdf))

### 5. Coins (Coinage Act, 2011, ss. 12 to 14) and bearer notes (RBI Act, 1934, s. 31)

The Coinage Act forbids using "any metal piece as coin whether stamped or unstamped, intended to be used as money" without
the Government's authority, and making, issuing or holding such pieces to circulate them
([Coinage Act ss. 12 to 28](https://tilakmarg.com/acts/coinage-act-2011-sections-12-to-28/)). It is about metal pieces, not
pictures; BIE makes no tokens. s. 31 of the RBI Act reserves to the Reserve Bank (and the Central Government) the issue of a
promissory note or engagement "payable to bearer on demand" (paraphrase; the exact wording was not re-read:
[AdvocateKhoj, RBI Act s. 31](https://www.advocatekhoj.com/library/bareacts/reservebankofindia/31.php)). BIE's notes carry no
promise clause.

## How BIE's drawings keep these rules

| Rule | What BIE's coins and notes do |
| --- | --- |
| No portrait | No Mahatma Gandhi and no person on any note or coin; the round panel holds the word "BIE". |
| No emblem or seal | No Ashoka Lion Capital, no "सत्यमेव जयते", no RBI seal or logo, no Swachh Bharat logo. |
| No issuer or promise | No "Reserve Bank of India", "भारतीय रिज़र्व बैंक", "Government of India", "भारत सरकार", no guarantee clause, no "I promise to pay the bearer", no governor's name or signature. A test refuses these words in every drawing. |
| No security features | No serial or number panel, no thread, no watermark, no micro-lettering, no see-through register, no latent image, no identification marks, no year of printing, no language panel, no motif, no Devanagari numeral panel. |
| Not the shape or size | BIE's notes are 1.6 : 1 with round corners, one side only, a thick cartoon outline (RBI's ₹10 is 63 × 123 mm, 1.95 : 1; ₹50 is 66 × 135 mm, 2.05 : 1; square corners). In a video they are icons at screen size; BIE never prints them. |
| Not the colours | BIE's own palette: ₹10 teal, ₹20 coral, ₹50 green, ₹100 orange, ₹200 rose, ₹500 violet, ₹2000 navy (RBI's ₹10 is chocolate brown, ₹50 fluorescent blue). |
| A clear non-currency mark | Every note: the "BIE" panel and "नमूना · not money" on a white band. Every coin: a small "BIE". |
| Coins are BIE's own | Each coin has its own size, colour and edge (₹2 scalloped, ₹5 and 50 paise milled, ₹10 and ₹20 two-metal, ₹20 eight-sided, 25 paise dotted ring) and only its denomination ("₹10", "50 पैसे"); no emblem, motif, year or mint mark. |
| QR, cheque, card machine | The QR pattern is pseudo-random on a 19 × 19 grid (no QR version has 19 modules, so nothing can be decoded) with "SCAN · PAY", no UPI or NPCI mark. The cheque and passbook name no bank and carry no IFSC, MICR band or account number; the card machine shows no card network logo. |

The drawings are made by code (`tools/bie_objects.py`), so a check is exact: `python tools/bie_objects.py --check` and
`tests/test_task046d2_pictures.py` fail if a committed file differs from what the script draws, if a forbidden word appears,
if a note's shape comes near a real note's, or if a drawing loads anything from outside.

## Licences recorded

- **BIE's drawings:** BIE's own work, published as CC0 1.0 (`licence_policy.json` `own_work`: `bie-objects`, added
  1 November 2026; CC0 was already allowed). Registry: `bie-objects`, status wrapped.
- **Fluent Emoji:** `LICENSE` at commit `1ffb34c752ecf5d402f04cfb4b392c77f57c54bc` (read 1 November 2026): "MIT License,
  Copyright (c) Microsoft Corporation", permission to "use, copy, modify, merge, publish, distribute, sublicense, and/or
  sell" provided "The above copyright notice and this permission notice shall be included in all copies or substantial
  portions of the Software". The policy's licence classes are unchanged: MIT is still "own terms, needs Navin" in general,
  and only the source `fluentui-emoji` is approved by name (`sources.approved_by_navin`, 2026-11-01, Navin's words above),
  with the condition: the credit "Fluent Emoji by Microsoft, MIT", the licence URL at the pinned commit and the repository;
  a game or notes package that ships the PNG files ships the MIT licence text with them. Registry: `fluentui-emoji`,
  licence flag `custom`, status wrapped. Fluent Emoji has no logos; no flag of an organisation or brand is in it.

## Open points for Navin

1. **Colours.** BIE's notes use their own colours, so a learner who knows that the real ₹10 is brown will see a teal BIE ₹10.
   The denomination is written large; this was chosen for "clearly not replicas". Changing it is a teaching-quality call.
2. **The legal reading.** RBI gives no written rule for pictures of notes in lessons; BIE follows the strictest reading
   (nothing that resembles a note). A lawyer's or RBI's written answer would settle it.
3. **Fluent PNG size.** The 3D PNGs are 256 × 256; drawn larger than about 256 px on a 1080p frame they soften.

## Rebuilding

    python tools/bie_objects.py                                   # draws the SVGs and icons/bie/objects.json
    python -m bie.toolbox.icons add-sets [--fluent <clone>]       # re-makes the fl and bie rows; tw and fa rows stay as they are

The Fluent clone needs only metadata: `GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none --sparse
https://github.com/microsoft/fluentui-emoji` at the pinned commit, then `git sparse-checkout set --no-cone
'/assets/*/metadata.json'`; the PNG paths come from `git ls-tree`. The index is written with a fixed gzip time, so the same
inputs give the same bytes.
