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
| `shop` | `x`, `sign` (the shop's name, in the learner's script), `packets: [{n, cue}]` | the place of a shop story (a kirana shop, a tea stall, a market stall, a bazaar); its stock of goods on the counter (n packets) |
| `price_tag` | `x`, `y`, `string` (hanging length), `steps: [{text, dir, cue}]`, `lift_cue` + `lift_dy` | the price that is struck out and replaced (a price only: '₹65', '₹10,000', at most 9 characters; words go on a board); lift it when demand pulls it up |
| `crowd` | `x0`, `spacing`, `enter_x`, `exit_x`, `face` (-1 looks left), `seed`, `steps: [{n, cue}]`, `carry_cue` + `carry_n` | buyers or bank customers who walk in and out as the number changes; `carry` sends n of them away with goods |
| `bank` | `x`, `sign` (the bank's name, generic, in the learner's script) | the place of a bank story: a stone front with pillars, a teller window and a counter; customers stand before it (`crowd` with `x0` near `x` - 270) |
| `teller` | `x` (the bank's `x`) | the bank's clerk behind the counter (as `shopkeeper` is for the shop) |
| `board` | `x`, `y`, `text` (the title: खाता, EMI, बचत), `fill` (header colour), `steps: [{text, dir, cue}]`, `until_cue` | a standing display whose value changes on its word: a passbook balance ₹0 → ₹500, an EMI due ₹10,000 → ₹0; the old value is struck out, `dir` "up" or "down" adds the arrow. A value is at most 3 lines of 26 characters (your own line breaks are kept, a long line is wrapped at spaces); the teaching stays in the narration, a board shows the number or the few words that change |
| `label` | `x`, `y`, `text`, `fill` (rgba colour), `cue`, `until_cue` | SUPPLY · 3, DEMAND · 12: short labels over the scene |
| `coin_rain` | `x0`, `x1`, `count`, `cue`, `until_cue` | money arriving in people's hands |
| `balance` | `x`, `y`, `tilt`, `cue`, `tilt_cue`, `until_cue` | supply against demand on a balance that tilts on its word |
| `pull_arrow` | `x`, `y0`, `y1`, `text`, `cue` | the force that pulls the price (demand-pull) |
| `title` | `text`, `cue` | the part's name, on its word (at most 30 characters) |
| `lamp`, `foreground` | `x` | street dressing for depth (two or three of each, outside the shop) |

Every element has `cue: [beat_id, word]` with the word exactly as written in that beat (`[beat_id, ""]` for the beat's
start). Something must change at least every 15 s (the code refuses a longer still); aim for a change every 5 s.
Never a real person, logo, emblem or regulator mark: a generic shop sign and generic people only.
