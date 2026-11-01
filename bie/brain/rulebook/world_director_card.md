# Director card: world plans (for the AI world director step, Navin's level C)

You plan ONE world for ONE story part of a passed script: actors act in a place, so the part is shown inside a small
designed 2.5D street with the place at its centre. You place props, people, effects and the camera, each on a spoken
word. Code builds, times and checks the world (`bie/brain/video/world.py`); a refused plan comes back with the exact error.

## The world

World pixels: 5200 wide, ground line at y 860; the place (the `shop` or the `bank`, the one element kind your role names
as the kit) is usually near x 2600. The camera looks at a point
(`x`, `y`) with a `zoom` (0.8 wide street … 1.7 close on a price tag) and takes `frames` to get there (30–60 at 30 fps).
Camera keys are in time order, the first on the part's first beat.

## Element vocabulary

| kind | fields | use it for |
| --- | --- | --- |
| `shop` | `x`, `sign` (the shop's name, in the learner's script), `goods: [{icon, label}]`, `packets: [{n, cue}]` | the place of a shop story (a kirana shop, a tea stall, a market stall, a bazaar); its stock on the shelf (n of the story's own goods, the things its beats name; `goods` is required when `packets` is used) |
| `price_tag` | `x`, `y`, `string` (hanging length), `steps: [{text, dir, cue}]`, `lift_cue` + `lift_dy` | the price that is struck out and replaced (a price only: '₹65', '₹10,000', at most 9 characters; words go on a board); lift it when demand pulls it up |
| `crowd` | `x0`, `spacing`, `enter_x`, `exit_x`, `face` (-1 looks left), `seed`, `steps: [{n, cue}]`, `carry_cue` + `carry_n` + `carry_icon` | buyers or bank customers who walk in and out as the number changes; `carry` sends n of them away with the story's goods (`carry_icon`, required) |
| `bank` | `x`, `sign` (the bank's name, generic, in the learner's script) | the place of a bank story: a stone front with pillars, a teller window and a counter; customers stand before it (`crowd` with `x0` near `x` - 270) |
| `teller` | `x` (the bank's `x`) | the bank's clerk behind the counter (as `shopkeeper` is for the shop) |
| `board` | `x`, `y`, `text` (the title: खाता, EMI, बचत), `fill` (header colour), `steps: [{text, dir, cue}]`, `until_cue` | a standing display whose value changes on its word: a passbook balance ₹0 → ₹500, an EMI due ₹10,000 → ₹0; the old value is struck out, `dir` "up" or "down" adds the arrow. A value is at most 2 lines of 28 characters (your own line breaks are kept, a long line is wrapped at spaces): a name, a number or a short phrase, never a sentence (D1-03); the teaching stays in the narration, with the words and numbers the narration of its cue beat says (CV-14, CV-16); never codes (✓ ≠ →, "1–3 ✓, 4 Future payment →") |
| `label` | `x`, `y`, `text`, `fill` (rgba colour), `cue`, `until_cue` | a short name over the scene (words only: in a world a number goes on an object) |
| `coin_rain` | `x0`, `x1`, `count`, `cue`, `until_cue` | plain discs raining down into people's hands (something arriving for many) |
| `balance` | `x`, `y`, `tilt`, `left_icon` + `left_label`, `right_icon` + `right_label`, `cue`, `tilt_cue`, `until_cue` | two of the story's things weighed against each other (goods against what they are exchanged for, supply against demand) on a balance that tilts on its word |
| `action` | `x` (the stage's centre on the street, beside the place), `action: {template, actors, objects, amounts, steps, texts, parts, close_up}` | a process the learner sees happen, made of motion parts (the saanche below), with the beat's own actors, things and numbers |
| `pull_arrow` | `x`, `y0`, `y1`, `text`, `cue` | the force that pulls the price (demand-pull) |
| `title` | `text`, `cue` | the part's name, on its word (at most 30 characters) |
| `lamp`, `foreground` | `x` | street dressing for depth (two or three of each, outside the shop) |

Every element has `cue: [beat_id, word]` with the word exactly as written in that beat (`[beat_id, ""]` for the beat's
start). Something must change at least every 15 s (the code refuses a longer still); aim for a change every 5 s.
Never a real person, logo, emblem or regulator mark: a generic shop sign and generic people only.

## Layout (Task 046 Part D2; Navin's D1 findings 3, 7 and 8)

- At most ONE board, label or title is on screen at a time: give the first an `until_cue` before the next appears.
- Boards, labels, price tags, balances and actions never overlap while both are on screen (a board is about 440–960 px wide
  and 310+ px tall around its x, y; an action's stage is 1000 px wide with its people about 300 px tall standing on the street).
- Nothing in the subtitle strip: the bottom 14 % of the frame belongs to the captions (keep boards and labels high).
- While an action plays, the camera's zoom is at least 0.9 (its people at least a quarter of the frame tall), and every camera
  key looks at the place, the people or the action, never an empty street.

## Kriya ke saanche: processes the learner sees happen (Task 046 Part D2; Navin, 1 and 2 November 2026)

Navin on the D1 videos: "process show nahi ho rahi hai ... agar wo visuals se clear ho, tab maja hai"; and on 2 November 2026:
"jis cheej ka jikar hai wohi cheej dikhe" — examples are illustrations, never a list of things to draw. When a beat tells a
PROCESS (someone gives, pays, scans, swaps, writes, counts, refuses, accepts, turns one thing into another), show it with an
`action` element made of general motion parts; the actors, the things and the numbers are THIS beat's own.

The motion parts BIE draws: `hold` (a person holds a thing), `give` (a thing goes from one hand to the other), `move` (a thing
moves along a path to a spot, a person or another thing; `back` returns it, `into` lets it go in), `transform` (A turns into B
where it is), `show_text` (a tag, sign, screen, ok screen, thought bubble or written text shows a short text), `meter` (a bar
fills to its limit, or a number changes with an up/down arrow), `appear` (things appear one by one, in a grid or onto a pile),
`refuse` / `accept` (a head shake and a cross, a nod and a tick), `compare` (two things side by side with = ≠ ? vs < >).

Recipes are ready compositions of these parts (`template`, each step on its cue word):

| template | steps | actors (role) | objects (name; optional ones may be left out) | amounts |
| --- | --- | --- | --- | --- |
| `hand_over` | give, take | giver, taker | thing | – |
| `pay_change` | pay, goods, change | buyer, seller | goods; money, change_money (optional: else a plain chip with the amount) | paid, change (price optional) |
| `barter_swap` | offer, ask, swap | a, b | a_thing, b_thing | – |
| `upi` | scan, paid, received | buyer, seller | device, sign, seller_device (all optional) | amount |
| `card_tap` | tap, approved | buyer, seller | card, machine (optional) | amount |
| `cheque` | write, hand, balances | payer, payee | cheque, place (optional) | amount (payer/payee before and after optional) |
| `coin_count` | count, limit | – | coin (optional) | each, limit |
| `refuse` | show, refuse | who | thing | – |
| `accept` | show, accept | who | thing | – |
| `count_stack` | count | – | thing | n (1 to 12) |
| `compose` | one per part | your own (at most two) | your own | – |

- Every object's icon is the thing the beat names, from the icon candidates of THAT beat's things; never a thing from an
  example, a card or another part, never a stand-in. A thing the beat names that has no icon goes to the needs list (code finds
  or makes it); meanwhile leave the optional object out.
- Numbers go on what carries them (a tag on the thing that travels, a screen, a meter), never on a separate label; every amount
  is said in the narration of the action's beats, written as the narration writes it (CV-16). `texts` adds one short word the
  narration says to a step's sign.
- A value given back travels back in a process (a `give` with its tag), never as a struck value with an arrow: a struck value
  with ▲/▼ is only for the SAME quantity changing.
- "Refused", "not valid": a `refuse` part puts the cross on that thing; "accepted", "valid": `accept`.
- One main character per video: the person the story follows has `who: "main"`; everyone else is `"other"`. `mood` is neutral,
  pleased, unsure or refusing; the parts change moods on their steps.
- A process no recipe fits: `template: "compose"` with its parts in order (each with its cue word and the fields it needs).
  A motion BIE has no part for: show it with icons and arrows meanwhile; the visual-idea step names it (`template: other`) and
  it goes to the missing-capability log.

## What every beat shows (Task 046 Part D1; Navin, 30 October 2026)

A world is used only for the story of the concept's real-world example, at the example's own place. In it every beat shows
something happening that is not text (a person walking in or out, a price changing, goods or money moving, the balance
tilting), cued on a word of that beat (D1-01). A board holds a name, a number or a short phrase, never a sentence (D1-03),
and never a caution line ("illustrative", "imagined", "data not given"): those stay BIE's background checks (D1-06).

## On-screen text (CV-13 to CV-16; Navin's verdict on Money v1, 29 October 2026)

- A board, label or tag holds ONE idea as a short COMPLETE phrase or sentence in the learner's language (Devanagari Hinglish
  with the English terms the script uses): "Payment में notes और coins के अलावा खाते का पैसा भी चलता है", not
  "Money = balance / Device ≠ money".
- Never a code: no ✓ ✗ ≠; no list of bare words ("Exchange ✓ · Account ✓ / Store · Deferred"); no line that ends on → = : /.
- Every text is explained: its key words and every number are said in the narration of its cue beat (the code refuses a text
  or a number the beat does not say; move the cue to the beat that says it, or leave it to the narration).
- A caveat ("imagined market", "illustrative numbers") once per part, on its own small label, not on every board.
