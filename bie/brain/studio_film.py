"""The film-first course studio, stage 2: one film per approved student question (Navin, 18 November 2026).

The maker writes the film as shots. Each shot has one visual (an AI photo made by Codex image_gen, or a diagram the maker
draws as SVG) and its sentences; every sentence carries what appears on screen while it is spoken: pins (label + point),
arrows, effects (rise, rain, glow), the SVG parts it lights up and where the camera moves. That is Navin's rule from the
Monsoon reviews: the picture speaks with the narration ("dikhaya = bola"), the scenes play by themselves, caution lines and
source names never reach the screen. Code checks all of it and sends the exact problems back.

Motion (Navin, 19 November 2026, to reach the Campbell 17 film): what travels is shown travelling. A sentence can send
things along a path over the picture (``moves``: pollen grains, cells, molecules, drops, light, sparks), grow a living line
(``grows``: a pollen tube, a root, a signal), show a fusion (``fuses``: two parts merge into one with its label), and move
the camera (``zoom`` up to 2.2x: from the whole flower into the anther). A shot can be a ``cutaway`` (an AI picture drawn
as a transparent scientific cutaway, like the inside of the ovule) and can ``dive`` into a point of the previous picture.
The phone's browser plays all of it; nothing is rendered on a GPU.

Living films (Navin, 20 November 2026, on the first three Photosynthesis films: "slides jaisa lag raha hai", the stroma was a
box with "CO2 fixation" written in it, and no voice reached him). A film is now one world the camera travels into: every shot
after the first dives into a point of the picture before it (at most one cut), the pictures share one look (``look``), and
processes happen on AI pictures, not on flat diagrams (at most one diagram, for a comparison or a graph). Molecules are
actors from BIE's kit (``molecule_kit.json``: ATP, NADPH, CO2, RuBP, 3-PGA, G3P, ...); ``reacts`` brings inputs in to one
point and sends the products out, ``cycles`` turns a wheel of stations (the Calvin cycle takes CO2, ATP and NADPH and gives
ADP, NADP+ and sugar as it turns), the ``spin`` effect turns a rotor. Every shot moves, at least half the sentences of a long
film move, and the film opens on a question. The player's voice goes through Web Audio (``studio_voice_player.js``).

Every book line taught (Navin, 20 November 2026, on the first living film, Q14: "video ki script jo teacher samjha raha hai
usse har baat cover honi chahiye", "tum mujhe batao is video se NCERT ka konsa text clear hota hai", the end "ek khichdi ban
gaya", and the shot numbers under the film read as slides). The maker gets the question's book lines numbered (whole
sentences with their printed page, ``studio.book_lines``) and every narration sentence names the lines it teaches
(``teaches``), anything it says beyond the book (``beyond``, for the review page only) and its ``part`` of the whole
picture. Navin's answers the same day: going beyond the book is welcome wherever it makes the concept clearer (a
prerequisite told first, an example, a story, where it is used in the real world, NEET depth: "warna bachcha kitab ki
lines hi na padh leta"), and when a film touches a process another film teaches in detail, its context and basics must
still be clear; every film carries the prerequisite, the concept and where it is used or what it causes. And words are
free ("agar mai strict boundation lga dunga ki book ki lines se bahar ek bhi word use nahi karna to humara padhana kaise
hai wala section kamjor ho jaaega"): no word, name or analogy is refused for not being in the book; words the chapter
never uses are only listed on the review page. Code checks that every line is taught by a sentence that speaks its
words, that a wheel with n stations is explained station by station, that at most MAX_KINDS different molecules are on
screen at once, and that the film has a prerequisite and a use sentence. ``coverage_page`` writes the NCERT-to-film page
Navin reads beside the book.
"""
from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from . import studio as studio_terms
from .studio import SOURCE_WORDS, parse
from .studio_voice import unsaid

N = {"type": "number"}
S = {"type": "string"}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
SHOTS = {"long": (5, 12), "short": (2, 5)}
EFFECTS = ("rise", "rain", "glow", "spin")
SPRITES = ("pollen", "cell", "dot", "drop", "molecule", "light", "spark")
KIT_FILE = Path(__file__).with_name("molecule_kit.json")
KIT = json.loads(KIT_FILE.read_text(encoding="utf-8"))
MOLECULES = tuple(KIT["molecules"])
ACTORS = SPRITES + MOLECULES                 # what can travel, react or ride a cycle
COLOURS = ("gold", "green", "blue", "red", "white", "purple")
VISUALS = ("photo", "cutaway", "diagram")
# what a sentence does to a part cut out of its AI picture (Navin, 23 November 2026, routeS: "pressure moving rotating khulna
# band hona jaise nigalna pakdna kisi jagah par chipkana"); bie/brain/picture_parts.py cuts the parts, the player moves them
# Navin, 24 November 2026, on the r2 remake of 11.6.3b: "hilte huye lage jaise compress hone suction effect koi chij suck
# krne ka pakde ka chipakne ka effect": squeeze (pressed, it gives), suck (its opening pulls a molecule in), grab (it closes
# on a molecule and holds it); Navin, 24 November 2026, on r3: "proton pump jeeta jaagta ... aisa lage jaise proton ko
# pakadke lumen mein chhod rha ho": carry (it grips a molecule on its near side and lets it go on the far side, at toward)
DOES = ("turn", "spin", "stop", "open", "loose", "tight", "squeeze", "suck", "grab", "carry", "stick", "leave", "arrive",
        "glow")
TOWARD = ("open", "tight", "suck", "grab", "carry", "stick", "leave", "arrive")   # acts that need a point: where it closes,
#                                                                                   pulls, lets go or goes
RIDES = ("spin", "suck", "grab", "carry")   # acts that take a molecule: riding on a spinning part, pulled in, held, carried
UNCOVERS = ("turn", "open", "tight", "grab", "stick", "leave", "arrive")   # acts that uncover what lay under the part (a plate)
MAX_PARTS = 6                 # parts cut from one picture
MAX_ACTS = 3                  # acts in one sentence: one thing at a time
PICTURE_PINS = 8              # different pins on one picture (6 until Navin, 24 November 2026: "labelling bahut kam")
ZOOM_MAX = 2.2
I = {"type": "integer"}
B = {"type": "boolean"}
SVG_BANNED = re.compile(r"(?i)<\s*(script|foreignObject|iframe|image|use|style)\b|\son[a-z]+\s*=|javascript:|href\s*=")
MAX_SVG = 60000
WORD = re.compile(r"[A-Za-zऀ-ॿ]{3,}")
MAX_KINDS = 5                 # different molecules on screen at once (the Q14 ending showed 8 and read as khichdi)
MAX_SHOT_CHARS = 560          # roman per shot, about 40 seconds of voice (the Q14 review: two shots of 54 s on one picture)
PIN_GAP = 8                   # percent between two pins of one sentence (the Q14 review: thylakoid and lumen stacked)
TEACHER_MATCH = 0.7           # share of a teacher's line's words the film's sentence keeps (spelling slips fixed)
ADDED_WORDS = 2               # words a script film's sentence may not add to its script line (one is a spelling slip
                              # fixed; Navin, 26 November 2026, B8: "koi chhut nahi", the film says the lines as written)
# the teacher study (four Chapter 11 teachers, 22 November 2026; Navin's yes to F1, F2 and F3, judged on a BIE video):
PROCESS_FROM = 3              # a question with this many process points tells the process step by step on one picture (F1)
STEPS_FROM = 3                # numbered steps that make a shot a process built on one picture
STEP_SHOT_SENTENCES = 10      # a stepped shot may hold more sentences, because every step changes the picture
STEP_SHOT_CHARS = 2 * MAX_SHOT_CHARS
BEADS_MAX = 12                # beads in one group of a count (F3: "5 + 1 = 6 → 3 + 3", carbon counted as beads)
NUMBER = (r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|ek|do|teen|chaar|char|paanch|panch|chhah|chhe|"
          r"saat|aath|nau|das|baarah)")
COUNT_SAID = re.compile(rf"\b{NUMBER}\s*(?:\+|plus)\s*{NUMBER}\s*(?:=|equals|barabar|ke barabar)", re.I)
MAPPING = re.compile(r"\S\s*=\s*\S")
OPENERS_FROM = 4              # answers (a sentence said right after a question) before their first words are counted
OPENER_SHARE = 0.5            # one opener on more than this share of them is a habit, not a teacher (final script round,
                              # 22 November 2026: "Dekho," opened most of 244 answers; Navin, 23 November: "Tum wali
                              # chalegi", the voice stays and only the openers vary)
SENTENCE_END = re.compile(r"(?<=[.?!])(?<!\b[A-Z]\.)\s+")   # never after an initial ("J.A. Bassham", "T.W. Engelmann")
TEACHER_OPENERS = ('"Dekho, …", "Iska seedha sa jawab hai …", "Aisa isliye hai kyunki …", "Hota yeh hai ki …", '
                   '"Wajah yeh hai ki …"')
PARTS = ("hook", "prerequisite", "concept", "use", "recap")   # the film's whole picture (Navin, 20 November 2026)
PART_NAMES = {"hook": "sawaal", "prerequisite": "pehle ki baat", "concept": "concept", "use": "kahan kaam aata hai / asar",
              "recap": "yaad rakhiye"}
STOP = set("""this that with from which there their these those have been will would into also only more most such than
then them they when where what while very each other some through because about after before being both does done made
make many much must over same shall should since upon used uses using well were your here just like even known called
take takes taken part parts form forms place given gives give provide provides show shows hence thus therefore
happen happens happened definitely right""".split())      # the last line: the book talking to the reader ("You are
# definitely right.", "Let us see how this happens.", Photosynthesis q06 and q08, 21 November 2026), never a key word


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


WHAT = {"type": "string", "enum": list(ACTORS)}
BEADS = _arr(_obj({"n": I, "label": S, "colour": {"type": "string", "enum": list(COLOURS)}}))
SENTENCE = _obj({
    "roman": S, "voice": S,
    "pins": _arr(_obj({"label": S, "x": N, "y": N})),
    "arrows": _arr(_obj({"points": _arr(_arr(N)), "label": S})),
    "effects": _arr(_obj({"type": {"type": "string", "enum": list(EFFECTS)}, "x0": N, "x1": N, "y0": N, "y1": N})),
    "focus": _arr(S),
    "zoom": _obj({"x": N, "y": N, "scale": N}),
    "moves": _arr(_obj({"what": {"type": "string", "enum": list(ACTORS)},
                        "colour": {"type": "string", "enum": list(COLOURS)}, "label": S,
                        "points": _arr(_arr(N)), "count": I, "ms": N, "loop": B})),
    "grows": _arr(_obj({"points": _arr(_arr(N)), "label": S, "ms": N})),
    "fuses": _arr(_obj({"x": N, "y": N, "label": S})),
    "reacts": _arr(_obj({"inputs": _arr(_obj({"what": WHAT, "from": _arr(N)})), "at": _arr(N),
                         "outputs": _arr(_obj({"what": WHAT, "to": _arr(N)})), "label": S, "ms": N, "loop": B})),
    "cycles": _arr(_obj({"x": N, "y": N, "rx": N, "ry": N, "label": S, "carriers": I, "ms": N,
                         "stations": _arr(_obj({"at": N, "label": S, "becomes": WHAT, "takes": _arr(WHAT),
                                                "gives": _arr(WHAT)}))})),
    "acts": _arr(_obj({"part": S, "do": {"type": "string", "enum": list(DOES)}, "toward": _arr(N), "turns": N,
                       "rider": {"type": "string", "enum": [""] + list(ACTORS)}})),
    "step": I,
    "count": _obj({"x": N, "y": N, "groups": BEADS, "then": BEADS}),
    "teaches": _arr(I), "beyond": S, "part": {"type": "string", "enum": list(PARTS)},
})
SCHEMA = _obj({
    "title": S, "look": S,
    "shots": _arr(_obj({
        "id": S, "title": S, "key": S, "covers": _arr({"type": "integer"}),
        "visual": _obj({"type": {"type": "string", "enum": list(VISUALS)}, "image_prompt": S, "svg": S, "library": S,
                        "parts": _arr(_obj({"id": S, "name": S, "looks": S}))}),
        "dive": _obj({"x": N, "y": N}),
        "place": S,
        "aside": B,
        "sentences": _arr(SENTENCE),
    })),
})

INSTRUCTIONS = """You are BIE's film director and teacher. Write ONE film that teaches ONE student question of a {course}
chapter. Learner-facing language: {language} (Navin's natural spoken Hinglish in Roman script for "roman"; the same
sentence in Devanagari for "voice", which the narrator speaks).

How a BIE film works (approved benchmark: Monsoon and Pollen-to-seed films; Navin rejected films that felt like slides,
with a process written inside a box instead of happening on screen):
- ONE WORLD, NOT SLIDES. The film is one journey the camera makes into the real thing (leaf, then the cell, then the
  chloroplast, then the membrane and the stroma). Every shot after the first is a closer look INSIDE a point of the picture
  before it, and sets dive to that point; at most one shot may cut instead (dive -1, -1). "look" is one line of art
  direction every picture shares (palette, light, material, camera), so the pictures read as one place; it also names
  the colour of every structure that is seen in more than one picture (for example "ATP synthase: violet head, amber
  channel"), and each image_prompt draws that structure in those colours (a part that changed colour between shots
  read as a different thing). BIE adds a structure's colours only to the pictures whose image_prompt names it, so a
  structure appears only on the pictures at its own scale. {look_rule}
- REAL PLACES, LIVING PROCESSES. Places and processes are shown on AI pictures (photo or cutaway) that look like the real
  structure as electron micrographs and structural models show it (for a chloroplast: stacked thylakoid discs, the fluid
  stroma between them, membranes with depth; a protein in its known shape, such as ATP synthase: a ring in the membrane, a
  central stalk and a round head of six lobes facing the stroma), never invented blobs, ribbons or fantasy forms; a close-up
  keeps enough of the surroundings (the membrane, the stroma) that the learner knows where they are. SCALE GROWS STEP BY
  STEP: the opening picture is the biggest scale the question needs (for a process inside a cell: the leaf, then the
  cell, then the organelle, then the membrane), and a protein or molecule appears only in a picture whose scale lets it
  be seen (never a protein sitting on a whole chloroplast). A compartment whose contents matter is drawn closed (a
  thylakoid as a closed flattened sac with its lumen inside), so the learner sees what is trapped. What a sentence says
  happens is drawn so it can be seen (a leak is a clear gap that the moving H+ pass through). The process HAPPENS on
  that picture: molecules arrive, join, split, are spent and are made while the narration says so. Leave
  open space in the picture where the action will happen and say so in image_prompt. A diagram is only for a comparison or
  a graph, at most one per film; never draw a process as boxes with its name written inside.
- The film opens on the question's curiosity (its first sentence is a question) and ends on a one-line recap.
- EVERY BOOK LINE IS TAUGHT. The question's book lines are numbered (B1, B2, ...). Each sentence lists in "teaches" the
  numbers of the book lines it teaches ([] for the opening question, a bridge or the recap); together the sentences teach
  every book line, in the teacher's own words but with every fact of the line kept (names, numbers, "several molecules"),
  and a sentence that teaches a line speaks that line's own key words. Words are free: use whatever words, names,
  analogies and everyday Hinglish make the idea clear, including words the book never uses; where the book has its own
  name for something you call differently, say the book's name too, because the exam asks in the book's words.
- GO BEYOND THE BOOK WHEREVER IT MAKES THE CONCEPT CLEARER. The learner should think a step beyond the book's lines, not
  just hear them: tell the prerequisite they need first, give an example or a short story, show where and how it works in
  the real world, and go to NEET depth where it helps. "beyond" is "" when the sentence says only what the book says;
  otherwise a short note for BIE's review page (never shown) naming what it adds beyond the book, written in
  {language} in Roman script, because Navin reads that page beside the book.
- THE WHOLE PICTURE. Every sentence has its part: "hook" (the opening question), "prerequisite" (what the learner must
  already know to follow this; recall it briefly, even when another film teaches it), "concept" (the question's own
  ideas), "use" (where this concept is used next, in the plant or in life, and the effect of what happened; shown
  happening, moving, in its basic form, not as still parts) or "recap".
  The film has at least one prerequisite sentence and at least one use sentence.
- CONTEXT AND BASICS. Other films of this course teach the chapter's other questions (listed with the question). When
  this film touches a process another film teaches in detail (for example the Calvin cycle in a film about making ATP),
  its context and basics are still clear here: what goes in, what comes out, why it matters for this question, shown
  slowly; its step-by-step details stay in its own film. A process that comes back to where it began (the Calvin cycle
  making RuBP again) is shown as a wheel (cycles), so the learner sees it return.
- THE WHOLE MECHANISM. A machine that turns is shown turning, in the sentence that says so (ATP synthase: H+ flowing
  through CF0 turns the central stalk, and the turning stalk changes the shape of CF1's catalytic parts): on a photo or
  cutaway the turning part itself turns (acts, below); a spin effect only on a diagram. A sentence that says something
  is made again (RuBP dobara banta hai) has a wheel in its shot.
- MACHINE PARTS THAT MOVE (Navin, 23 November 2026, after the ATP synthase demos: "pressure, moving, rotating, khulna band
  hona jaise nigalna pakdna, kisi jagah par chipkana"). On a photo or cutaway where a machine works (a rotor turning, a
  catalytic site opening and closing, a channel opening, an enzyme gripping and joining molecules), BIE cuts the parts
  that move out of the AI picture and moves them while the narration says so. visual.parts lists them ([] when nothing
  in the picture moves): id (short, a-z and _), name (what the narration calls the part, spoken in every sentence that
  acts on it), looks (how it looks in this picture, so it can be found: colour, shape, place). The image_prompt draws
  every listed part in its own colour, opaque and fully in view, not hidden behind another part, with the opening drawn
  where something opens and room around a part that moves, and as real and detailed as the rest of the picture (its true
  structure and surface, never a simplified or toy shape: Navin on the first parts film, 23 November 2026, "ekdum
  nakli"); a molecule that will be moved is
  drawn as one compact ball-and-stick group. Each sentence's acts show what its words say happens to a part, while it is
  said: turn (the part turns about its centre by turns degrees, -360 to 360: -120 for one step of the stalk seen from
  above), spin (a part seen from the side keeps turning until stop or the shot ends; rider: a molecule riding on it, such
  as H+ on the ring, or ""), stop, open (the site opens away from toward), loose (back to rest), tight (it closes onto
  toward with pressure: where a bond is pressed together), squeeze (the part is pressed and gives: it squashes, holds a
  moment and springs back, as a catalytic lobe pressed by the turning stalk), suck (the part's opening at toward pulls the
  rider in: a channel drawing H+ in), grab (the part closes on the rider at toward and holds it: a site gripping ADP),
  carry (the part grips the rider on its near side, squeezes it through and lets it go at toward on its far side: a
  proton pump taking H+ from the stroma into the lumen), stick (the part slides to toward and joins there, squashing a little on contact, with a glow at the joint: Pi joining
  ADP), leave (the part drifts to toward and is gone: ATP released), arrive (the part comes in from toward to its place),
  glow (the part lights up while it is named). toward is [x, y] in percent for open, tight, suck, grab, carry, stick,
  leave and arrive, else []; turns is 0 except for turn; rider (a molecule) is given for suck, grab and carry, may be
  given for spin, and is "" otherwise. Use the act that shows what the line says the part does to the thing, so the
  learner sees the press, the pull or the grip (Navin, 24 November 2026: "compress hone, suction, pakadne, chipakne ka
  effect"). A pump or carrier that moves something across a membrane is a listed part of its picture and carries it
  (carry) in the line that says so, so the learner sees it take hold and let go (Navin, 24 November 2026: "proton pump
  jeeta jaagta ... jaise proton ko pakadke lumen mein chhod rha ho"); that thing is not also sent through it as a move.
  At most {max_parts} parts on a picture and {max_acts} acts in a sentence; every listed part is acted on. A molecule
  that is not in the picture still comes as a move or a react. BIE keeps the living world moving by itself (membranes
  ripple slowly, the proteins in them sway with them, molecules wander a little as they travel); write nothing for it.
- MOLECULES MEETING (Navin, 21 November 2026: "achhe coordination ke saath, khichdi si na pake"). Where molecules meet
  (ADP + Pi → ATP at CF1's catalytic head; CO2 + RuBP → 3-PGA at Rubisco), show one meeting at a time: one react per
  sentence; every molecule that flies in or comes out is named in that sentence; the inputs come from where they really
  are and meet on the enzyme's site in the picture; besides the meeting, at most one other flow moves in that sentence.
  BIE times the flash to the moment the sentence names the product.
- ONE THING AT A TIME. At most {kinds} different molecules on screen at once (a swarm of one kind, such as many H+, counts
  as one); a step that needs more is split over sentences or shots, so the learner always sees what is happening. A
  wheel (cycles) with n stations is started by one sentence that names it and its stations, then keeps turning for n
  more sentences of its shot, each explaining one station (what comes in, what it makes, what leaves).
- A TEACHER TELLING WHAT HAPPENS, not a textbook read aloud. Speak in the present tense while it happens on screen
  ("Dekhiye, yeh CO2 andar aata hai...", "ab RuBP isse pakad leta hai..."), one step per sentence, naming each molecule or
  part as it appears; ask a small why or what-next before the answer at least once in every process shot; no textbook
  label lines ("CF0 membrane mein channel hai" becomes what the learner watches the channel do). It teaches like the best teacher: result first,
  then how and why, step by step, with an everyday example where it helps. Never "the book says", never a source name,
  never a caution line ("assume", "illustrative") on screen.
- A TEACHER EXPLAINING, NOT A MACHINE READING A PARAGRAPH. Navin, the teacher, rewrote a film's script on 20 November 2026;
  these are his ways:
  - Every sentence is complete and tied to the one before with joining words ("jisse ... ho jaati hai", "jiske kaaran
    ... ban jaata hai", "jiske andar"), never fragments strung on dashes.
  - A question and its answer are told apart: the question is asked, then a bridge opens the answer. Not "Proton
    gradient mein itni dilchaspi kyun—kyunki iske ghatne se energy milti hai" but "Par pehle, proton gradient mein itni
    dilchaspi kyun? Iski wajah jaan lete hain: aisa isliye hai kyunki iske ghatne se ATP banane ki energy milti hai."
    Every question after the film's opening one starts by saying that a question comes, in his words (Navin, 24
    November 2026; not in a film made from the chapter's script, which says its lines as written): "Ab sawaal uthta
    hai ki ...?", "Ab aap poochhenge ki ...?", "Ab aapke man mein sawaal utha hoga ki ...?", "Ek sawaal ab bhi banta hai
    ki ...?"; vary them. BIE writes
    the question on the screen and takes the camera to the part it asks about, so the question names that part; his
    answer openers: "Iska seedha sa jawab hai ...", "Aisa isliye hai kyunki ...", "Isme kaam aata hai ...", "Dekhiye,
    hota kya hai: ...".
  - In voice every question ends with ? and its answer starts a new sentence, so the voice pauses and the question sounds
    like a question.
  - He speaks with respect and takes the learner along: "aaiye", "chaliye", "dekhiye", "samajhiye", "pehchaan lete hain",
    "paas se dekhte hain", "aapko yaad rakhni hain"; never orders such as "dekho", "pehchaan lo", "yaad rakho". (A film
    made from the chapter's script keeps the script's own voice, "dekho" and "socho" included: Navin, 23 November 2026.)
  - After the opening question he invites: "Aaiye jaante hain." Between shots he builds a bridge ("ab isi chloroplast ke
    andar chalte hain aur cheezon ko aur detail mein samajhte hain"), and a new picture opens with where we are
    ("Chloroplast ke andar yeh thylakoid ek band chapti thaili jaisa dikhta hai").
  - Each hard idea gets an everyday picture: "Proton pump ko aap ek motor samajhiye"; a proton gradient is like water held
    behind a dam (baandh), or a battery's higher and lower potential; and he points the learner's attention: "Par gaur
    karne wali baat hai ...", "Dekhiye kaise ...".
  - The recap opens "Is video se aapko yeh baatein yaad rakhni hain: ...".
  - From his film A, which he judged the most natural (21 November 2026): every shot that shows a mechanism (molecules
    meeting, a turning machine, a wheel) asks a question before it happens, so the voice pauses there; an everyday
    picture comes every two or three shots, not once in the film; cause and effect stay in one flowing sentence
    ("jisse ...", "jiske kaaran ...") instead of short cut-up pieces.
- HOW GOOD TEACHERS OF THIS CHAPTER DRAW (BIE's teacher study, 22 November 2026; Navin's yes):
  - A PROCESS IS BUILT ON ONE PICTURE. A process of three or more steps (the Z scheme, the Calvin cycle, chemiosmosis, the
    C4 pathway) is told on ONE shot whose picture stays: each sentence adds only its own step on that same picture (an
    arrow, a pin, a move, a react) and sets "step" to its number (1, 2, 3, ... in order; 0 for a sentence that is not a
    step). BIE numbers the step on the picture; the new step glows and the earlier steps stay, quiet, so the learner sees
    the whole path grow and the last screen is never a khichdi. The picture leaves room for every step. The shot's last
    sentence may tell the whole path again over the finished picture (step 0). Such a stepped shot may have up to
    {step_sentences} sentences. Never a new picture for each step.
  - AMOUNTS ARE COUNTED. When a sentence counts (carbon atoms: 5 + 1 = 6, then 3 + 3; "teen CO2 ke liye nau ATP"), the
    count is seen: "count" puts beads on the picture at x, y (percent): groups (each n beads, 1 to {beads}, with a short
    label such as "RuBP" and a colour; the new atom in a different colour) and then, after "=", the groups they become
    ([] when nothing regroups); the beads before and after are the same number. A sentence that does not count has
    count {{"x": 50, "y": 86, "groups": [], "then": []}}.
  - AN ANALOGY GETS ITS OWN PICTURE. A shot with aside true is an everyday picture outside the film's world (a dam holding
    water, a classroom passing a book bench to bench): a photo, where the analogy is said and mapped in pins ("baandh =
    membrane", "paani = H+"); the film cuts to it and cuts back (both shots dive -1, -1), and these two cuts do not count
    as the film's one cut. aside is false for every other shot. The mapping is said in plain words; where it breaks is
    never said.
- Shots: {shots} shots for this film ({length}). Each shot has one visual and 2 to 6 short sentences spoken over it, about
  {shot_chars} characters of roman at most (about 40 seconds); a longer shot is split into a closer look (a stepped
  process shot: up to {step_sentences} sentences and {step_chars} characters, because each step changes the picture). A structure seen
  in two pictures keeps its side (left or right) in both: write its place into each image_prompt, and pin it there.
  shot.key is the one-line takeaway shown in the bottom band; shot.covers lists the indexes (0-based) of the question's
  points this shot teaches; together the shots cover every point.
- visual.type "photo": a photorealistic picture made by an image model. image_prompt describes it fully (place, subject,
  camera, light, 16:9) and must leave room for labels; svg is "". Use photo for real things, places, organisms, machines.
  A photo shows the real thing where it is, at its real size, in natural light (a real dam and its turbine, never a
  teaching model, a toy or a glossy render of them).
  No picture draws loose molecules, ions or a crowd of them (BIE moves a few over it): never "proton population",
  "dense H⁺" or "many tokens"; write that the space is left clear. Nor does a picture draw a checklist, a panel or
  empty boxes for what BIE draws over it (counts, lists, labels): leave that space clear too.
  visual.type "diagram": you draw it as one SVG illustration in the style of BIE's Pollen Lab (a calm background colour,
  gradients and soft shading, rounded natural shapes, depth, short labels with leader lines; at least one gradient and at
  least 12 drawn shapes; viewBox; no script, no images, no style element; give every part you will light up an id);
  image_prompt is "". Use diagram for graphs, cycles, flow charts and comparisons.
  visual.type "cutaway": an AI picture drawn as a transparent scientific cutaway or cross-section (glossy cells, soft
  volumetric light, depth, a calm dark background), for the inside of things a camera cannot see: the inside of a leaf,
  a chloroplast, an ovule, a root, a membrane and its proteins. image_prompt describes it fully like a photo prompt (what
  is where; BIE adds how it is rendered); svg is "".
- dive: {{"x": 0-100, "y": 0-100}} when this shot is a close-up INSIDE a point of the previous picture (the camera dives
  into that point, then this shot opens); {{"x": -1, "y": -1}} otherwise (and always for the first shot).
- place: what this shot's picture shows, as the narration calls it, 1 to 4 words ("Thylakoid", "ATP synthase", "CF₁ ka
  catalytic hissa", "Baandh"). GOING INSIDE (Navin, 24 November 2026: "kisi part ke molecular level par jaane ka effect
  yaani zoom in jaise patte ke andar karte the"): a dive goes one level deeper, into a part the previous picture shows
  (the organelle, its membrane, a protein, the protein's own site), and its picture shows that part big. BIE takes the
  camera onto the dive point first, then through it, and shows the path of places in a corner (Thylakoid › ATP synthase
  › CF₁), so the learner knows where they now are. A closer look at the same place is the camera's zoom on the same
  picture, not a new shot: a diving shot's place is a new place inside the one before.
- Every sentence says what appears WHILE it is spoken ("dikhaya = bola"): pins (a short label at x,y in percent of the
  picture, 3 to 97; the label's words must be spoken in that sentence), arrows (2 to 4 points in percent, a short label or
  ""), effects (rise for rising air or heat, rain, glow; a box x0,x1,y0,y1 in percent), focus (ids of SVG parts to light up;
  [] for photos) and zoom (x, y in percent and scale 1.0 to 1.3: where the camera moves for this sentence; 1.0 shows the
  whole picture, 1.2 to 1.3 leans towards one part while the rest stays in view, and BIE lights that part and dims the
  rest; BIE never goes closer than 1.3, so nothing the learner needs is cut off the screen).
- Motion, as in the approved Pollen-to-seed film: whatever travels in the story is SHOWN travelling while it is spoken.
  moves: things sent along a path over the picture: what (pollen, cell, dot, drop, molecule, light, spark, or a molecule
  from BIE's kit: {molecules}), colour (gold,
  green, blue, red, white, purple), label (1 to 3 spoken words, or ""), points (2 to 6 [x, y] in percent, the path in
  order), count (1 to 12 copies, one after another), ms (how long one trip takes, 800 to 8000) and loop (keep moving
  until the shot ends). A route or a flow (protons through a channel, electrons from carrier to carrier, water, sugar)
  is shown by the thing itself travelling on it (moves), never by a line drawn along the route (Navin, 23 November
  2026: "Cheez khud chale"). grows: only something that really grows (a pollen tube, a root tip), a living line along
  points (2 to 8), label, ms (1000 to 8000), in a sentence that says it grows. fuses: two parts become one at x, y, with label ("n + n → 2n", "glucose").
  reacts: a reaction seen happening: inputs (1 to 3, each what + from [x, y]) fly to "at" [x, y], a flash, and the outputs
  (1 to 3, each what + to [x, y]) appear there and travel to where they go, where they stay; label is the spoken equation
  ("CO2 + RuBP → 3-PGA") or ""; ms 1500 to 9000; loop true repeats it while the shot lasts (a steady process).
  cycles: a process that goes round (the Calvin cycle): an oval track at x, y with rx, ry (percent of width and of height,
  8 to 40; the whole oval inside the picture), carriers (1 to 4 molecules riding it), ms (one lap, 6000 to 30000), label (the
  cycle's spoken name or ""), and 2 to 5 stations: at (degrees, 0 = right, 90 = bottom, clockwise), label (spoken in this
  sentence), becomes (what a carrier turns into at this station), takes (molecules that fly in here, e.g. CO2, ATP, NADPH)
  and gives (molecules that leave here, e.g. ADP, NADP+, G3P). Example for the Calvin cycle: stations at 300 "fixation"
  (becomes 3-PGA, takes CO2), 90 "reduction" (becomes G3P, takes ATP and NADPH, gives ADP, NADP+ and G3P), 200
  "regeneration" (becomes RuBP, takes ATP, gives ADP).
  effects can also be spin (a turning rotor, such as the central stalk of ATP synthase; the box is where it turns).
  Use [] when nothing moves in that sentence. EVERY shot moves in at least one sentence, and in a long film at least half
  of all sentences move (moves, grows, fuses, reacts or cycles).
- At most 3 pins per sentence and at most {picture_pins} on a picture overall; labels of 1 to 3 words; two pins of one sentence are
  at least {pin_gap} percent apart (a part inside another, such as the lumen inside a thylakoid, is pinned in its own
  inner space). The picture names what the voice names, as it is said (Navin, 24 November 2026: "labelling itni use karo
  ki baat clear ho jaaye script ke bolne ke sath"): every structure, compartment or part a line speaks of gets its name
  in that line, as a pin, a move's label or the act of a listed part (BIE names a part as it acts); a name already on the
  picture is not pinned again.

Answer with the JSON object only."""

PROBLEMS_PROMPT = "BIE's code checked the film and found these problems. Send the whole corrected JSON again:\n- "


# what the maker is told about the pictures' look (the look itself is written into each picture prompt by image_prompt)
LOOK_RULES = {
    "glossy": "The pictures are glossy (Navin, 23 November 2026): never write matte, non-reflective or a muted sheen into "
              "the look or an image_prompt.",
    "mixed": "The pictures use Navin's hybrid look (22 November 2026): close-ups of proteins and molecular machinery are "
             "drawn like structural-biology figures with a light controlled sheen, and whole structures (a leaf, a cell, a "
             "chloroplast) matte in soft controlled light; BIE writes the look into every picture, so never write glossy, "
             "shiny or plastic, nor a light or render style, into the look or an image_prompt.",
    "asli": "The pictures show the inside of the chloroplast as electron micrographs show it (Navin, 24 November 2026): thin, "
            "curving membranes stacked into grana and crowded with proteins, and a granular stroma; BIE writes the look into "
            "every picture, so never write glossy, shiny or plastic, nor a light or render style, into the look or an "
            "image_prompt. The picture is busy, so the structure the narration talks about is drawn large, in front and "
            "clearly separate from the crowded membrane around it.",
    "asli_mixed": "Close-ups of proteins and molecular machinery are drawn clean like structural-biology figures with a light "
                  "controlled sheen, and every other picture shows the inside of the chloroplast as electron micrographs "
                  "show it: thin, curving membranes stacked into grana and crowded with proteins, and a granular stroma "
                  "(Navin, 24 November 2026); BIE writes the look into every picture, so never write glossy, shiny or "
                  "plastic, nor a light or render style, into the look or an image_prompt. In the busy pictures the "
                  "structure the narration talks about is drawn large, in front and clearly separate.",
}


def look_rule(look: str | None) -> str:
    look = look or FILM_STYLE
    return LOOK_RULES.get(look) or (f"The pictures are drawn in BIE's {look.replace('_', ' ')} look, which BIE writes into "
                                    "every picture: never write glossy, matte or a render style into the look or an image_prompt.")


def messages(question: dict, *, course: str, language: str, chapter: str = "", look: str | None = None) -> list:
    length = (question.get("film") or {}).get("length", "long")
    low, high = SHOTS.get(length, SHOTS["long"])
    points = "\n".join(f"{i}. ({p.get('kind')}) {p.get('point')}" for i, p in enumerate(question.get("points") or []))
    user = (f"Chapter: {chapter}\nQuestion {question.get('id')}: {question.get('question')}\nCuriosity: {question.get('hook')}\n"
            f"Showing moment planned: {(question.get('film') or {}).get('showing_moment', '')}\nPoints to teach:\n{points}\n"
            + _book_part(question))
    return [{"role": "system", "content": INSTRUCTIONS.format(course=course or "school", language=language or "Hinglish",
                                                              shots=f"{low} to {high}", length=length,
                                                              molecules=", ".join(MOLECULES),
                                                              kinds=MAX_KINDS, shot_chars=MAX_SHOT_CHARS,
                                                              pin_gap=PIN_GAP, step_sentences=STEP_SHOT_SENTENCES,
                                                              step_chars=STEP_SHOT_CHARS, beads=BEADS_MAX,
                                                              max_parts=MAX_PARTS, max_acts=MAX_ACTS, picture_pins=PICTURE_PINS,
                                                              look_rule=look_rule(look))
             + _aatma_part(course)},
            {"role": "user", "content": user + _overview_part(question) + _naksha_part(question) + _teacher_part(question)
             + _library_part(question)}]


def _aatma_part(course: str) -> str:
    """The ways of teaching and showing that films Navin passed used, as forms whose blanks this subject fills (the
    aatma ki almaari, ``bie/brain/aatma.py``); nothing while the almaari is empty."""
    from . import aatma
    return aatma.prompt_part(course)


NAKSHA_PART = """

THE CHAPTER'S NAKSHA (Navin, 21 November 2026: the whole chapter is planned before any film is written, so that the
progression never breaks, nothing is repeated and not everything looks the same). This film is {id}, section {section}.
- Open with: {opens_with}
- The story, step by step: {story}
- Tell first (prerequisite): {prerequisite}
- Its one analogy: {analogy} No other film of the chapter uses it; use no other analogy.
- Examples and real-world uses: {examples}
- Terms to open here, each at the moment it is first needed: {terms}
- From outside the book, welcome here: {outside}
- What the screen must show (saman ki list), made for this film: {saman}
  The first shot opens on {first}; the camera goes from there into what the story needs. Do not begin from the leaf
  unless that is this film's own opening.
- The learner already knows, from the films before this one (never teach these again; at most one sentence to remind):
{before}
- Coming in later films (do not teach them here; at most a one-line bridge to the next film at the end):
{after}"""


def _naksha_part(question: dict) -> str:
    plan = question.get("naksha")
    if not isinstance(plan, dict):
        return ""
    analogy = plan.get("analogy") or {}
    saman = plan.get("saman") or []
    before = "\n".join(f"  {b.get('id')} ({b.get('title')}): " + "; ".join(b.get("taught") or [])
                       + (f" · its analogy: {b['analogy']}" if b.get("analogy") else "")
                       + (f" · it opened on: {b['opening']}" if b.get("opening") else "")
                       for b in plan.get("before") or []) or "  (this is the first film)"
    return NAKSHA_PART.format(
        id=plan.get("id", ""), section=plan.get("section") or "the chapter's opening", opens_with=plan.get("opens_with", ""),
        story=" → ".join(plan.get("story") or []), prerequisite=plan.get("prerequisite") or "-",
        analogy=(f"{analogy.get('picture')} for {analogy.get('for')} ({analogy.get('why_it_fits')})." if analogy.get("picture")
                 else "none: this film needs no analogy."),
        examples="; ".join((plan.get("examples") or []) + (plan.get("real_world") or [])) or "-",
        terms=", ".join(plan.get("terms") or []) or "-",
        outside="; ".join(f"{o.get('what')} ({o.get('why')})" for o in plan.get("outside_book") or []) or "-",
        saman="; ".join(f"{s.get('id')} {s.get('kind')}: {s.get('shows')}" for s in saman) or "-",
        first=(saman[0].get("shows") if saman else "this film's own picture"),
        before=before, after="\n".join(f"  {a}" for a in plan.get("after") or []) or "  (this is the last film)")


OVERVIEW_PART = """

THE UNIT'S OVERVIEW. This is not a chapter question: it is the overview film of Unit {unit}{title}, made only from the
unit's opening page (Navin, 21 November 2026: "us unit ke sabhi chapters mein hum kya samjhenge jaisa overview mil
jaaye"). Its chapters: {chapters}. Show, in 2 to 4 shots, what this unit will help the learner understand, as the page
says it: its way of looking at life and what its chapters take up. Name each chapter by its number and title as the page
gives them. Teach nothing from inside the chapters that the page does not say (no light reaction, no Calvin cycle, no
Krebs cycle); the chapters' own films do that. End by leading into the first chapter."""


def _overview_part(question: dict) -> str:
    if not question.get("overview"):
        return ""
    unit = question.get("unit") or {}
    return OVERVIEW_PART.format(unit=unit.get("unit", ""), title=f" ({unit['title']})" if unit.get("title") else "",
                                chapters=", ".join(f"Chapter {c}" for c in unit.get("chapters") or []) or "as the page lists")


TEACHER_PART = """

THE TEACHER'S SCRIPT. Navin, the teacher, rewrote the narration of the earlier film of this question (its JSON is below).
Make the film again with HIS lines as the narration: the film's sentences are his lines, every one, in his order, and
nothing else is spoken. Keep his words; fix only spelling slips and broken spacing from typing on a tablet ("dekhte hsi"
is "dekhte hain"); his questions after the opening one get a question opener in front of his words ("Ab sawaal uthta
hai ki ...?", "Ab aap poochhenge ki ...?"; Navin, 24 November 2026). A NOTE under a line is his instruction to you, never
words to speak: follow it. Write each line's voice
in Devanagari, ending every question with ? and starting its answer as a new sentence. You may regroup his lines into
more shots (a long shot becomes a closer look) and change the pictures, their layout, the pins and the motion so that every
rule here holds; set teaches, beyond and part for his lines as for your own.

His lines:
{lines}

The earlier film (JSON):
{film}"""


LIBRARY_PART = """

THE PICTURE CUPBOARD (almaari). These pictures were made before and kept, each judged the best at its scale (Navin
approved keeping the best pictures, 21 November 2026). When a shot needs one of these scenes, use the kept picture: set
visual.library to its id, keep visual.type as given, and copy its description into visual.image_prompt; place pins,
moves, reacts and the rest on what it shows (its labelled places are listed). Draw a new picture (visual.library "")
only when no kept picture shows what the shot needs; a new picture keeps the kept pictures' colours and layout. Close-ups
of one structure in one film come from one set (the set is listed), so the machine keeps one look from shot to shot.

{entries}"""


def _library_part(question: dict) -> str:
    """The kept pictures the maker may use instead of drawing new ones (``visual.library``)."""
    entries = question.get("library") or []
    if not entries:
        return ""
    text = "\n".join(f"- {e.get('id')} ({e.get('type', 'cutaway')}, set {e.get('set') or '-'}, scale: {e.get('scale', '')}): {e.get('shows', '')}"
                     + (f"\n  labelled places: " + ", ".join(f"{p.get('label')} ({p.get('x')},{p.get('y')})" for p in e.get("places") or [])
                        if e.get("places") else "") for e in entries)
    return LIBRARY_PART.format(entries=text)


def missing_pictures(film: dict, images: dict) -> list:
    """The shots that need a picture (photo, cutaway) and have none in ``images``: each would play as a black screen with
    only its labels (11.6.2's gulel shot, film f3, 28 November 2026)."""
    return [s.get("id") for s in (film or {}).get("shots") or []
            if (s.get("visual") or {}).get("type") in ("photo", "cutaway") and not images.get(s.get("id"))]


def library_problems(film: dict, question: dict) -> list:
    """A shot that names a kept picture names one that is in the cupboard, of a type that is a picture."""
    kept = {e.get("id"): e for e in question.get("library") or []}
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        name = ((shot.get("visual") or {}).get("library") or "").strip()
        if not name:
            continue
        sid = shot.get("id") or f"shot {number}"
        if name not in kept:
            out.append(f"{sid}: no kept picture {name!r}; use one of {sorted(kept) or 'none'} or draw a new picture "
                       "(visual.library \"\")")
        elif (shot.get("visual") or {}).get("type") not in ("photo", "cutaway"):
            out.append(f"{sid}: a kept picture is a photo or cutaway visual, not {(shot.get('visual') or {}).get('type')!r}")
    used = {}
    for number, shot in enumerate(film.get("shots") or [], 1):
        e = kept.get(((shot.get("visual") or {}).get("library") or "").strip())
        if e and ":" in (e.get("scale") or "") and e.get("set"):
            group = e["scale"].split(":", 1)[0].strip().lower()
            first = used.setdefault(group, (shot.get("id") or f"shot {number}", e["set"]))
            if first[1] != e["set"]:
                out.append(f"{shot.get('id') or f'shot {number}'}: {group} comes from set {e['set']!r} here and from set "
                           f"{first[1]!r} in {first[0]}; close-ups of one structure in one film come from one set (one look)")
    return out


def without_empty_cupboard(film, question: dict):
    """With no kept pictures there is nothing to name: a visual.library is cleared and the picture is drawn from its
    image_prompt, as the films stage does anyway (the first heading films, 23 November 2026: the maker named a kept
    'motor' that never existed and spent its last round on it)."""
    if isinstance(film, dict) and not question.get("library"):
        for shot in film.get("shots") or []:
            if isinstance(shot.get("visual"), dict) and shot["visual"].get("library"):
                shot["visual"]["library"] = ""
    return film


SCRIPT_PART = """

THE CHAPTER'S SCRIPT. BIE wrote the whole chapter's script first (Navin, 22 November 2026: "script wo poora gyan hai jo
hume bache ko dena hai"); this film tells one heading of it. The film's sentences are the script's lines below, every
one, in their order, and nothing else is spoken (Navin, 26 November 2026: "koi chhut nahi"): keep their words and their
voice ("dekho", "socho" stay), fixing only a spelling slip, and leave no word out. Add nothing to a line: no answer
opener ("Iska seedha sa jawab hai ..."), no question opener ("Ab sawaal uthta hai ki ...", "Ab aap poochhenge ki ..."),
no invitation, no bridge between shots, no question of your own and no recap of your own: the film opens on the
script's first line and ends on its last. The rules above on the opening question, openers, invitations, bridges and the
closing recap are for films without a script; here the script's own lines do that work.
Where the script asks, the film asks. The screen shows what each line says while it is said (Navin, 26 November 2026: "jo script keh rahi hai wo hi visuals ke
madhyam se samajh mein aaye"): the picture, its pins and its motion follow the line, and nothing is shown that the line
does not speak of. A NOTE under a line is the script's instruction for the screen (the point's kind and what the screen
shows), never words to speak: follow it. A line of kind analogy is said on an aside shot (its own everyday picture); the
lines of a process are told on one picture, step by step. Write each line's voice in Devanagari, ending every question
with ? and starting its answer as a new sentence. Group the lines into shots so that every rule here holds; set teaches,
beyond and part for every line.

The script's lines:
{lines}"""


def _teacher_part(question: dict) -> str:
    lines = question.get("teacher_lines") or []
    if not lines:
        return ""
    text = "\n".join(f"L{n}: {line.get('roman', '').strip()}" + (f"\n    NOTE: {line['note'].strip()}" if (line.get("note") or "").strip()
                                                                   else "") for n, line in enumerate(lines, 1))
    if question.get("script_lines"):
        return SCRIPT_PART.format(lines=text)
    return TEACHER_PART.format(lines=text, film=json.dumps(question.get("earlier_film") or {}, ensure_ascii=False))


def _book_part(question: dict) -> str:
    lines = question.get("book_lines") or []
    if lines:
        part = "\nThe question's book lines (teach every one; list their numbers in teaches):\n" + "\n".join(
            f"B{line['n']} (page {line.get('page', '')}): {line['text']}" for line in lines)
    elif question.get("source_text"):
        part = "\nThe book's lines for these points:\n" + question["source_text"]
    else:
        part = ""
    others = question.get("other_questions") or []
    if others:
        part += "\n\nTaught in this course's other films (a bridge at most here):\n" + "\n".join(f"- {o}" for o in others)
    return part


def svg_problems(svg: str) -> list:
    if not svg.strip():
        return ["the diagram has no svg"]
    out = []
    if len(svg) > MAX_SVG:
        out.append(f"the svg is {len(svg)} characters; keep it under {MAX_SVG}")
    if SVG_BANNED.search(svg):
        out.append("the svg uses a banned element or attribute (script, foreignObject, image, use, style, on*, href)")
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        return out + [f"the svg is not valid XML ({exc})"]
    if not root.tag.endswith("svg") or not root.get("viewBox"):
        out.append("the svg needs an <svg> root with a viewBox")
    return out


SHAPES = ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line")
MIN_SHAPES = 12


def illustration_problems(svg: str) -> list:
    """An illustration in the Chapter 17 Pollen Lab style (Navin, 19 November 2026), not a bare sketch: at least one
    gradient and at least MIN_SHAPES drawn shapes."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return []
    tags = [el.tag.rsplit("}", 1)[-1] for el in root.iter()]
    out = []
    if not any(t in ("linearGradient", "radialGradient") for t in tags):
        out.append("the illustration has no gradient; draw it in the Pollen Lab style (gradients, soft shading, depth)")
    shapes = sum(1 for t in tags if t in SHAPES)
    if shapes < MIN_SHAPES:
        out.append(f"the illustration has {shapes} shapes; a bare sketch is not enough, draw at least {MIN_SHAPES}")
    return out


def svg_ids(svg: str) -> set:
    try:
        return {el.get("id") for el in ET.fromstring(svg).iter() if el.get("id")}
    except ET.ParseError:
        return set()


MOTION = ("moves", "grows", "fuses", "reacts", "cycles", "acts")


def moves(sentence: dict) -> bool:
    return any(sentence.get(key) for key in MOTION)


def _inside(points, low: int, high: int) -> bool:
    return isinstance(points, list) and low <= len(points) <= high and all(
        isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in p) for p in points)


# a sentence in which something really grows (a pollen tube, a root): only there may a line grow along points
GROWING = re.compile(r"\b(grow\w*|elongat\w*|ug(t|n|aa?)\w*|lamb\w*\s+ho\w*|nalika|nali|tubes?|roots?|jad(ein|en)?)\b", re.I)


def motion_problems(sentence: dict, spoken: set, where: str) -> list:
    """moves, grows and fuses: inside the picture, in time ranges a learner can follow, labels spoken (dikhaya = bola)."""
    out = []
    for move in sentence.get("moves") or []:
        if move.get("what") not in ACTORS:
            out.append(f"{where}: a move's what must be one of {', '.join(SPRITES)} or a kit molecule")
        if not _inside(move.get("points"), 2, 6):
            out.append(f"{where}: a move needs 2 to 6 points [x, y] in 0..100")
        if not 1 <= int(move.get("count") or 0) <= 12:
            out.append(f"{where}: a move's count is 1 to 12")
        if not 800 <= float(move.get("ms") or 0) <= 8000:
            out.append(f"{where}: a move's ms is 800 to 8000")
        if move.get("label") and not _tokens(move["label"]) & spoken:
            out.append(f"{where}: move label {move['label']!r} is not spoken in this sentence (dikhaya = bola)")
    if sentence.get("grows") and not GROWING.search(_plain(sentence.get("roman") or "")):
        out.append(f"{where}: a growing line shows a route here, but nothing grows in this line; show the moving thing "
                   "itself travelling on the route (moves), with no line (Navin, 23 November 2026: \"Cheez khud chale\")")
    for grow in sentence.get("grows") or []:
        if not _inside(grow.get("points"), 2, 8):
            out.append(f"{where}: a grow needs 2 to 8 points [x, y] in 0..100")
        if not 1000 <= float(grow.get("ms") or 0) <= 8000:
            out.append(f"{where}: a grow's ms is 1000 to 8000")
        if grow.get("label") and not _tokens(grow["label"]) & spoken:
            out.append(f"{where}: grow label {grow['label']!r} is not spoken in this sentence (dikhaya = bola)")
    for react in sentence.get("reacts") or []:
        ins, outs = react.get("inputs") or [], react.get("outputs") or []
        if not (1 <= len(ins) <= 3 and 1 <= len(outs) <= 3):
            out.append(f"{where}: a react has 1 to 3 inputs and 1 to 3 outputs")
        if any(x.get("what") not in ACTORS for x in ins + outs):
            out.append(f"{where}: a react's what must be a sprite or a kit molecule")
        if not _inside([react.get("at")] + [x.get("from") for x in ins] + [x.get("to") for x in outs], 2, 7):
            out.append(f"{where}: a react's at, from and to are [x, y] in 0..100")
        if not 1500 <= float(react.get("ms") or 0) <= 9000:
            out.append(f"{where}: a react's ms is 1500 to 9000")
        label = react.get("label") or ""
        if _tokens(label) and not _tokens(label) & spoken:
            out.append(f"{where}: react label {label!r} is not spoken in this sentence (dikhaya = bola)")
    for cycle in sentence.get("cycles") or []:
        x, y, rx, ry = (float(cycle.get(k) or 0) for k in ("x", "y", "rx", "ry"))
        if not (8 <= rx <= 40 and 8 <= ry <= 40 and x - rx >= 2 and x + rx <= 98 and y - ry >= 2 and y + ry <= 98):
            out.append(f"{where}: a cycle's oval (x, y, rx, ry: 8 to 40) must sit inside the picture")
        if not 1 <= int(cycle.get("carriers") or 0) <= 4:
            out.append(f"{where}: a cycle has 1 to 4 carriers")
        if not 6000 <= float(cycle.get("ms") or 0) <= 30000:
            out.append(f"{where}: a cycle's ms (one lap) is 6000 to 30000")
        stations = cycle.get("stations") or []
        if not 2 <= len(stations) <= 5:
            out.append(f"{where}: a cycle has 2 to 5 stations")
        for station in stations:
            if not 0 <= float(station.get("at", -1)) < 360:
                out.append(f"{where}: a station's at is 0 to 359 degrees")
            names = [station.get("becomes")] + list(station.get("takes") or []) + list(station.get("gives") or [])
            if any(n not in ACTORS for n in names):
                out.append(f"{where}: a station's becomes, takes and gives must be sprites or kit molecules")
            if station.get("label") and not _tokens(station["label"]) & spoken:
                out.append(f"{where}: station label {station['label']!r} is not spoken in this sentence (dikhaya = bola)")
        if cycle.get("label") and _tokens(cycle["label"]) and not _tokens(cycle["label"]) & spoken:
            out.append(f"{where}: cycle label {cycle['label']!r} is not spoken in this sentence (dikhaya = bola)")
    for fuse in sentence.get("fuses") or []:
        if not (0 <= float(fuse.get("x", -1)) <= 100 and 0 <= float(fuse.get("y", -1)) <= 100):
            out.append(f"{where}: a fuse is x, y in 0..100")
        label = fuse.get("label") or ""
        if not label.strip():
            out.append(f"{where}: a fuse needs its label (what the two parts become)")
        elif _tokens(label) and not _tokens(label) & spoken:
            out.append(f"{where}: fuse label {label!r} is not spoken in this sentence (dikhaya = bola)")
    return out


PLAIN = str.maketrans("\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079\u208A\u208B\u207A\u207B", "01234567890123456789+-+-")


def _plain(text: str) -> str:
    """Subscript and superscript digits and charges as plain ones, so a line that writes CO\u2082 or CF\u2080 names the CO2 or CF0
    of a label or a molecule (the first heading films, 23 November 2026: "CO\u2082 ... follow karo" was refused for not naming
    CO2, and a wheel station 'CF\u2080' was never found in the line that said it)."""
    return (text or "").translate(PLAIN)


def _words(text: str) -> set:
    return {w.lower() for w in WORD.findall(_plain(text))}


SHORT_STOP = {"a", "an", "as", "at", "be", "by", "do", "ek", "hi", "in", "is", "it", "ka", "ke", "ki", "ko", "me", "na", "of",
              "on", "or", "se", "to", "ya"}


def _tokens(text: str) -> set:
    """Words for "dikhaya = bola": the words of 3+ letters and the short names a label uses (H+, Pi, CO2, O2), plural
    and H+/proton folded together, so a moving 'H+' label is spoken by a sentence that says protons (Q14 remake,
    20 November 2026: every H+ label on a move was refused)."""
    out = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9]*|[\u0900-\u097F]{3,}", _plain(text)):
        low = w.lower()
        if len(low) >= 3 or low not in SHORT_STOP:
            out.add(_stem(low))
    return out


def problems(film, question: dict) -> list:
    if not isinstance(film, dict):
        return ["the answer is not a JSON object"]
    out = []
    length = (question.get("film") or {}).get("length", "long")
    low, high = SHOTS.get(length, SHOTS["long"])
    shots = film.get("shots") or []
    if not low <= len(shots) <= high:
        out.append(f"there are {len(shots)} shots; this {length} film needs {low} to {high}")
    covered, moving_shots, diagrams, cuts, moving, total = set(), set(), 0, 0, 0, 0
    for number, shot in enumerate(shots, 1):
        sid = shot.get("id") or f"shot {number}"
        covered.update(shot.get("covers") or [])
        visual = shot.get("visual") or {}
        if len((shot.get("key") or "").strip()) < 8:
            out.append(f"{sid}: key (the takeaway line) is missing")
        ids = set()
        if visual.get("type") in ("photo", "cutaway"):
            if len((visual.get("image_prompt") or "").strip()) < 60:
                out.append(f"{sid}: image_prompt needs a full description (at least 60 characters)")
        elif visual.get("type") == "diagram":
            diagrams += 1
            out += [f"{sid}: {p}" for p in svg_problems(visual.get("svg") or "") + illustration_problems(visual.get("svg") or "")]
            ids = svg_ids(visual.get("svg") or "")
        else:
            out.append(f"{sid}: visual.type must be photo, cutaway or diagram")
        dive = shot.get("dive") or {"x": -1, "y": -1}
        if not (dive.get("x") == -1 and dive.get("y") == -1) and not (0 <= float(dive.get("x", -5)) <= 100
                                                                    and 0 <= float(dive.get("y", -5)) <= 100):
            out.append(f"{sid}: dive is x, y in 0..100, or -1, -1 for no dive")
        if number == 1 and dive.get("x", -1) != -1:
            out.append(f"{sid}: the first shot cannot dive (there is no picture before it)")
        aside = bool(shot.get("aside")) or (number > 1 and bool(shots[number - 2].get("aside")))
        if number > 1 and dive.get("x", -1) == -1 and not aside:     # an analogy's own picture cuts out and back (F2)
            cuts += 1
        sentences = shot.get("sentences") or []
        stepped = stepped_shot(shot)
        most = STEP_SHOT_SENTENCES if stepped else 6
        if not 2 <= len(sentences) <= most:
            out.append(f"{sid}: {len(sentences)} sentences; write 2 to {most}")
        labels = set()
        for k, sentence in enumerate(sentences, 1):
            where = f"{sid} sentence {k}"
            roman, voice = sentence.get("roman") or "", sentence.get("voice") or ""
            if len(roman.strip()) < 15:
                out.append(f"{where}: roman is missing or too short")
            if not DEVANAGARI.search(voice):
                out.append(f"{where}: voice must be the same sentence in Devanagari")
            spoken = _tokens(roman) | _tokens(voice)
            pins = sentence.get("pins") or []
            if len(pins) > 3:
                out.append(f"{where}: {len(pins)} pins; at most 3 per sentence")
            marks = pins + [{"label": m.get("label"), "x": (m.get("points") or [[None]])[-1][0],
                             "y": (m.get("points") or [[None, None]])[-1][-1]}
                            for m in sentence.get("moves") or [] if (m.get("label") or "").strip()]
            for a, b in ((a, b) for i, a in enumerate(marks) for b in marks[i + 1:]):
                try:
                    apart = ((float(a["x"]) - float(b["x"])) ** 2 + (float(a["y"]) - float(b["y"])) ** 2) ** 0.5
                except (KeyError, TypeError, ValueError):
                    continue
                if apart < PIN_GAP and a.get("label") != b.get("label"):
                    out.append(f"{where}: labels {a.get('label')!r} and {b.get('label')!r} are {apart:.0f}% apart, on top of each "
                               f"other; keep two labels (pins, and the end of a labelled move) at least {PIN_GAP}% apart")
            for pin in pins:
                labels.add(pin.get("label"))
                if not (3 <= float(pin.get("x", -1)) <= 97 and 3 <= float(pin.get("y", -1)) <= 97):
                    out.append(f"{where}: pin {pin.get('label')!r} is outside 3..97")
                if not _tokens(pin.get("label")) & spoken:
                    out.append(f"{where}: pin {pin.get('label')!r} is not spoken in this sentence (dikhaya = bola)")
            for arrow in sentence.get("arrows") or []:
                pts = arrow.get("points") or []
                if not 2 <= len(pts) <= 4 or any(len(p) != 2 or not all(0 <= v <= 100 for v in p) for p in pts):
                    out.append(f"{where}: an arrow needs 2 to 4 points [x, y] in 0..100")
            missing = [f for f in sentence.get("focus") or [] if f not in ids]
            if missing:
                out.append(f"{where}: focus ids not in the svg: {', '.join(missing[:5])}")
            zoom = sentence.get("zoom") or {}
            if not 1.0 <= float(zoom.get("scale", 0)) <= ZOOM_MAX:
                out.append(f"{where}: zoom.scale must be 1.0 to {ZOOM_MAX}")
            found_motion = motion_problems(sentence, spoken, where)
            out += found_motion
            total += 1
            if moves(sentence):
                moving_shots.add(sid)
                moving += 1
            if SOURCE_WORDS.search(roman) or SOURCE_WORDS.search(voice):
                out.append(f"{where}: names the source; remove it")
        if len(labels) > PICTURE_PINS:
            out.append(f"{sid}: {len(labels)} different pins on one picture; at most {PICTURE_PINS}")
        chars = sum(len((sentence.get("roman") or "").strip()) for sentence in sentences)
        most_chars = STEP_SHOT_CHARS if stepped else MAX_SHOT_CHARS
        if chars > most_chars:
            out.append(f"{sid}: {chars} characters of narration (about {chars * 0.078:.0f} seconds) on one picture; at most "
                       f"{most_chars}: split it into two shots, the second a closer look")
    still = [shot.get("id") or f"shot {n}" for n, shot in enumerate(shots, 1)
             if (shot.get("id") or f"shot {n}") not in moving_shots]
    if shots and still:
        out.append(f"nothing moves in {', '.join(still)}: every shot shows its process happening (moves, grows, fuses, "
                   "reacts or cycles); show what travels travelling")
    if length == "long" and total and moving * 2 < total:
        out.append(f"only {moving} of {total} sentences move; in a long film at least half move (a still picture with a "
                   "voice over it is a slide)")
    if cuts > 1:
        out.append(f"{cuts} shots cut instead of diving; the film is one world: every shot after the first dives into a "
                   "point of the picture before it (at most one cut)")
    if diagrams > 1:
        out.append(f"{diagrams} diagram shots; at most one, for a comparison or a graph: show places and processes on AI "
                   "pictures (photo or cutaway)")
    opening = ((shots[0].get("sentences") or [{}])[0].get("roman") or "") if shots else ""
    if shots and "?" not in opening and not question.get("script_lines"):     # a script film opens on its own first line (B8)
        out.append("the film's first sentence must be the question that opens it (a learner's curiosity, ending with ?)")
    if not (film.get("look") or "").strip() or len(film.get("look", "").strip()) < 20:
        out.append("look is missing: one line of art direction every picture shares (palette, light, material, camera)")
    points = range(len(question.get("points") or []))
    missing_points = [i for i in points if i not in covered]
    if missing_points:
        out.append("no shot covers the question's points " + ", ".join(map(str, missing_points)))
    out += (picture_problems(film) + parts_problems(film) + photo_problems(film) + crowd_problems(film)
            + overlay_problems(film) + _aatma_problems(film))
    return (out + book_problems(film, question) + screen_problems(film, question) + layout_problems(film)
            + teacher_problems(film, question) + library_problems(film, question) + mechanism_problems(film, question)
            + teaching_problems(film, question) + question_problems(film, question) + carry_problems(film) + place_problems(film))


# --- Navin, 24 November 2026, on r3 of 11.6.3b (the hybrid look passed): questions said as questions and shown on the
# screen, a pump that grips and lets go, and dives that go inside. Films made before these rules (their shots have no
# "place", such as the passed Q14 of 21 November 2026) keep the rules they were passed under.
def newer_rules(film: dict) -> bool:
    shots = film.get("shots") or []
    return bool(shots) and all(isinstance(s, dict) and "place" in s for s in shots)


ASKING = re.compile(r"(?i)\b(sawaa?l\w*|savaa?l\w*|prashn\w*|prashan\w*|poochh\w*|puchh\w*|pooch\w*)\b|\bman mein\b")


def question_problems(film: dict, question: dict | None = None) -> list:
    """Every question after the film's opening one starts by saying that a question comes (Navin, 24 November 2026:
    "prashan ab sawal uthta hai, ya ab aap puchhenge, ya ab aapke man mein sawal utha hoga, jaise vakyo se shuru ho").
    Not in a film made from the chapter's script: it says the script's lines as written (Navin, 26 November 2026, B8)."""
    if not newer_rules(film) or (question or {}).get("script_lines"):
        return []
    out, first = [], True
    for where, shot, sentence in _sentences(film):
        roman = (sentence.get("roman") or "").strip()
        if first or sentence.get("part") == "hook":
            first = False
            continue
        if ASKING.search(" ".join(roman.split()[:6])) and not roman.endswith("?") and QUESTION_WORD.search(roman):
            out.append(f"{where}: the line says a question comes but does not end with ?; end the question with ? in roman "
                       f"and voice, so it is shown on the screen and the voice pauses: \"{roman[:70]}\"")
        if roman.endswith("?") and not ASKING.search(" ".join(roman.split()[:9])):
            out.append(f"{where}: a question in the film starts by saying a question comes (\"Ab sawaal uthta hai ki ...?\", "
                       f"\"Ab aap poochhenge ki ...?\", \"Ab aapke man mein sawaal utha hoga ki ...?\"), in roman and voice: "
                       f"\"{roman[:70]}\"")
    return out


PUMPING = re.compile(r"(?i)\b(pump\w*|carriers?|transporters?)\b[^.?!;]{0,60}?\b(le ja\w*|bhej\w*|pahunch\w*|accumulat\w*|"
                     r"pakad\w*|chhod\w*|daal\w*|across|andar|paar|into|moves?|carr(y|ies))\b")
PUMP_NAME = re.compile(r"(?i)\b(pump\w*|cytochrome\w*|b[6₆] ?f|carriers?|transporters?)")
NEGATION = re.compile(r"(?i)\b(nahi|nahin|na|bina|without|not|no)\b")


def carry_problems(film: dict) -> list:
    """A pump that moves something across a membrane is seen gripping it and letting it go (Navin, 24 November 2026:
    "proton pump jeeta jaagta sath mein aisa lage jaise proton ko pakdke lumen mein chhod rha ho"): a cutaway line whose
    moving thing passes a pinned pump, or (when no pump is pinned) that says a pump moves what travels in it, carries it
    (act carry on the pump)."""
    if not newer_rules(film):
        return []
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        visual = shot.get("visual") or {}
        if visual.get("type") != "cutaway":
            continue
        marks = [(p.get("label") or "", p.get("x"), p.get("y")) for s in shot.get("sentences") or []
                 for p in s.get("pins") or [] if isinstance(p, dict) and PUMP_NAME.search(p.get("label") or "")]
        for k, sentence in enumerate(shot.get("sentences") or [], 1):
            if any(a.get("do") == "carry" for a in sentence.get("acts") or []):
                continue
            roman = sentence.get("roman") or ""
            paths = [p for m in sentence.get("moves") or [] for p in m.get("points") or [] if _point(p)]
            if not paths:
                continue
            near = any(math.hypot(float(x) - p[0], float(y) - p[1]) < 10 for _, x, y in marks
                       if isinstance(x, (int, float)) and isinstance(y, (int, float)) for p in paths)
            said = not marks and PUMPING.search(roman) and not NEGATION.search(roman)   # no pump pinned: what the line says
            if near or said:
                out.append(f"{shot.get('id') or f'shot {number}'} sentence {k}: a pump moves what travels here; list the pump "
                           "as a part of this picture and show it carrying the thing across (carry: rider = what it moves, "
                           "toward = where it lets go on the far side), instead of a move through it")
    return out


def place_problems(film: dict) -> list:
    """Every shot names its place, and a dive goes inside something new that the picture before shows (Navin, 24
    November 2026: "kisi part ke molecular level par jaane ka effect yaani zoom in jaise patte ke andar karte the"; r3's
    five shots in a row were each a "closer look" at the same membrane, so going inside was never felt)."""
    if not newer_rules(film):
        return []
    out, shots = [], film.get("shots") or []
    for number, shot in enumerate(shots, 1):
        sid = shot.get("id") or f"shot {number}"
        place = str(shot.get("place") or "").strip()
        if not place or len(place.split()) > 5 or len(place) > 40:
            out.append(f"{sid}: place names what this picture shows in 1 to 4 words (\"Thylakoid\", \"ATP synthase\")")
            continue
        dive = shot.get("dive") or {}
        if number == 1 or dive.get("x", -1) == -1:
            continue
        before = shots[number - 2]
        if _plain(place).lower() == _plain(str(before.get("place") or "")).lower():
            out.append(f"{sid}: dives into {place!r} from a picture of the same place; a dive goes inside something new, and a "
                       "closer look at the same place is a zoom on the same picture")
            continue
        seen = " ".join([str(before.get("place") or ""), (before.get("visual") or {}).get("image_prompt") or ""]
                        + [f"{p.get('name') or ''} {p.get('looks') or ''}" for p in (before.get("visual") or {}).get("parts") or []
                           if isinstance(p, dict)]
                        + [f"{s.get('roman') or ''} " + " ".join(str(p.get("label") or "") for p in s.get("pins") or [])
                           for s in before.get("sentences") or []])
        if not (_tokens(place) - {"ka", "ki", "ke"}) & _tokens(seen):
            out.append(f"{sid}: dives into {place!r}, which the picture before does not show; a dive goes into a part that "
                       "picture shows")
    return out


def _turning_on(shot: dict, k: int) -> bool:
    """A part set spinning by an earlier sentence of this shot is still spinning at sentence ``k`` (1-based)."""
    on = set()
    for s in (shot.get("sentences") or [])[:k]:
        for a in s.get("acts") or []:
            if a.get("do") == "spin":
                on.add(a.get("part"))
            elif a.get("do") == "stop":
                on.discard(a.get("part"))
    return bool(on)


PART_ID = re.compile(r"^[a-z][a-z0-9_]{0,23}$")
TOUCHING = re.compile(r"\b(khul\w*|band ho\w*|band kar\w*|kas\w*|dab\w*|dabaa?v|pakad\w*|jud\w*|jod\w*|chipak\w*|nikal\w*|"
                      r"chhoot\w*|chhod\w*|ghoom\w*|ghuma\w*|opens?|clos\w*|grips?|squeez\w*|press\w*|binds?|releas\w*)\b", re.I)


def _point(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in value)


def parts_problems(film: dict) -> list:
    """Parts cut from an AI picture move as the narration says (Navin's routeS choice, 23 November 2026): every act names
    a listed part of its own picture, says what it does in a way the player can draw, and is spoken while it happens;
    every listed part is drawn in the picture and acted on; one thing at a time."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        sid = shot.get("id") or f"shot {number}"
        visual = shot.get("visual") or {}
        parts = [p for p in visual.get("parts") or [] if isinstance(p, dict)]
        sentences = shot.get("sentences") or []
        acted = [a for s in sentences for a in s.get("acts") or []]
        if parts and visual.get("type") not in ("photo", "cutaway"):
            out.append(f"{sid}: parts are cut from an AI picture (photo or cutaway); on a diagram light up its SVG ids (focus)")
            continue
        if len(parts) > MAX_PARTS:
            out.append(f"{sid}: {len(parts)} parts on one picture; at most {MAX_PARTS}")
        names, seen = {}, set()
        prompt = _content_words(visual.get("image_prompt") or "")
        for part in parts:
            pid = str(part.get("id") or "")
            if not PART_ID.match(pid) or pid in seen:
                out.append(f"{sid}: part id {pid!r} must be short, unique, a-z, digits and _")
            seen.add(pid)
            names[pid] = str(part.get("name") or "")
            if len((part.get("looks") or "").strip()) < 8:
                out.append(f"{sid}: part {pid!r} needs looks: how it looks in this picture (colour, shape, place)")
            if not (_content_words(f"{part.get('name') or ''} {part.get('looks') or ''}") & prompt):
                out.append(f"{sid}: part {pid!r} ({part.get('name')}) is not drawn by the image_prompt; describe it there as "
                           "its own clearly separate shape")
        for pid in names:
            if not any(a.get("part") == pid for a in acted):
                out.append(f"{sid}: part {pid!r} is listed but nothing happens to it; act on it or leave it out")
        for k, sentence in enumerate(sentences, 1):
            where = f"{sid} sentence {k}"
            acts = sentence.get("acts") or []
            if len(acts) > MAX_ACTS:
                out.append(f"{where}: {len(acts)} acts in one sentence; at most {MAX_ACTS}, one thing at a time")
            spoken = _spoken_words(f"{sentence.get('roman') or ''} {sentence.get('voice') or ''}")
            for act in acts:
                pid, do = act.get("part"), act.get("do")
                if pid not in names:
                    out.append(f"{where}: an act names part {pid!r}, which this shot's visual.parts does not list")
                    continue
                if do not in DOES:
                    out.append(f"{where}: act {do!r} on {pid!r}; it is one of {', '.join(DOES)}")
                    continue
                toward = act.get("toward") or []
                if do in TOWARD and not _point(toward):
                    out.append(f"{where}: {do} on {pid!r} needs toward [x, y] in 0..100 (where it closes, slides or goes)")
                if do not in TOWARD and toward:
                    out.append(f"{where}: {do} on {pid!r} takes no toward; write []")
                turns = act.get("turns") or 0
                if do == "turn" and not (isinstance(turns, (int, float)) and 5 <= abs(turns) <= 360):
                    out.append(f"{where}: turn on {pid!r} needs turns in degrees, 5 to 360 either way (-120 for one step)")
                if do != "turn" and turns:
                    out.append(f"{where}: {do} on {pid!r} takes turns 0")
                if do in ("suck", "grab", "carry") and not act.get("rider"):
                    what = {"suck": "pulls in", "grab": "holds", "carry": "carries across"}[do]
                    out.append(f"{where}: {do} on {pid!r} needs rider: the molecule it {what}")
                if act.get("rider") and do not in RIDES:
                    out.append(f"{where}: only {', '.join(RIDES)} take a rider; {do} on {pid!r} has rider \"\"")
                if do not in ("stop", "loose") and not (_spoken_words(names[pid]) & spoken):
                    out.append(f"{where}: part {names[pid]!r} {do}s here but the line does not name it (dikhaya = bola)")
            if parts and TOUCHING.search(sentence.get("roman") or "") and not acts and not moves(sentence) \
                    and sentence.get("part") not in ("hook", "recap"):
                out.append(f"{where}: the line says a part {TOUCHING.search(sentence.get('roman')).group(0)!r} but nothing "
                           "moves; show it on the part (acts)")
    return out


def picture_problems(film: dict) -> list:
    """A picture shows what its lines talk about: lines that name molecular machinery (ATP synthase, a photosystem, a
    pump) are not said over a whole-structure picture (a leaf, a cell, a chloroplast). The first heading film (11.6.3
    part b, 23 November 2026) dived leaf → cell → chloroplast while the voice already spoke of ATP synthase and H+, and
    Navin: "kheechdi si pak gayi ... wo kadi nhi ban paati". The opening question may ask before the journey."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        visual = shot.get("visual") or {}
        if shot.get("aside") or visual.get("type") not in ("photo", "cutaway") or style_for(shot) != "overview":
            continue
        named = [MACHINERY.search(_plain(s.get("roman") or "")) for s in shot.get("sentences") or [] if s.get("part") != "hook"]
        named = list(dict.fromkeys(m.group(0) for m in named if m))
        if named:
            out.append(f"{shot.get('id') or f'shot {number}'}: its lines talk about {', '.join(named[:3])} but its picture is a "
                       f"whole-structure view (\"{(visual.get('image_prompt') or '')[:70].strip()} ...\"); a picture shows what "
                       "its lines talk about: draw that part close up here, or say these lines on the shot that shows it")
    return out


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def stepped_shot(shot: dict) -> bool:
    """A shot that builds a process on its one picture: STEPS_FROM or more numbered steps (F1)."""
    return sum(1 for sentence in shot.get("sentences") or [] if _int(sentence.get("step")) > 0) >= STEPS_FROM


def _adds(sentence: dict) -> bool:
    return any(sentence.get(key) for key in ("arrows", "pins", "moves", "grows", "fuses", "reacts", "cycles", "effects",
                                              "focus")) or bool((sentence.get("count") or {}).get("groups"))


def answer_openers(sentences: list) -> list:
    """The first word of every answer: a sentence said right after a question, itself no question."""
    out = []
    for asked, said in zip(sentences, sentences[1:]):
        if asked.rstrip().endswith("?") and not said.rstrip().endswith("?"):
            words = re.findall(r"[^\W\d_]+", said.lower())
            if words:
                out.append(words[0])
    return out


def opener_habit(sentences: list):
    """(opener, times, answers) when one first word opens more than OPENER_SHARE of at least OPENERS_FROM answers."""
    openers = answer_openers(sentences)
    if len(openers) < OPENERS_FROM:
        return None
    word, times = Counter(openers).most_common(1)[0]
    return (word, times, len(openers)) if times > OPENER_SHARE * len(openers) else None


def teaching_problems(film: dict, question: dict) -> list:
    """The teacher study's ways of drawing (22 November 2026; Navin's yes to F1, F2 and F3, judged on a BIE video):
    a process built step by step on one picture, amounts counted with beads, an analogy on its own everyday picture."""
    out, shots = [], film.get("shots") or []
    for number, shot in enumerate(shots, 1):
        sid = shot.get("id") or f"shot {number}"
        expected = 1
        for k, sentence in enumerate(shot.get("sentences") or [], 1):
            where = f"{sid} sentence {k}"
            step = _int(sentence.get("step"))
            if step:
                if step != expected:
                    out.append(f"{where}: step {step} comes where step {expected} is due; number a shot's steps 1, 2, 3 in "
                               "order on its one picture")
                expected = step + 1
                if not _adds(sentence):
                    out.append(f"{where}: step {step} adds nothing to the picture; each step draws its own arrow, pin or "
                               "motion on it")
            count = sentence.get("count") or {}
            groups, then = list(count.get("groups") or []), list(count.get("then") or [])
            if groups:
                sizes = [_int(g.get("n")) for g in groups + then]
                if any(not 1 <= n <= BEADS_MAX for n in sizes):
                    out.append(f"{where}: a bead group has 1 to {BEADS_MAX} beads")
                if then and sum(_int(g.get("n")) for g in groups) != sum(_int(g.get("n")) for g in then):
                    out.append(f"{where}: the count has {sum(_int(g.get('n')) for g in groups)} beads before = and "
                               f"{sum(_int(g.get('n')) for g in then)} after; the same atoms regroup, so both are the same")
                try:
                    inside = 3 <= float(count.get("x")) <= 97 and 3 <= float(count.get("y")) <= 97
                except (TypeError, ValueError):
                    inside = False
                if not inside:
                    out.append(f"{where}: the count's x, y are in 3..97")
            elif COUNT_SAID.search(sentence.get("roman") or ""):
                before = (shot.get("sentences") or [])[k - 2] if k > 1 else {}
                if not ((before.get("count") or {}).get("groups")):
                    out.append(f"{where}: the sentence counts ({COUNT_SAID.search(sentence.get('roman') or '').group(0)}); "
                               "show the count with beads (count) while it is said")
        if shot.get("aside"):
            visual = shot.get("visual") or {}
            if visual.get("type") != "photo":
                out.append(f"{sid}: an aside is an everyday picture, a photo of the analogy's own thing")
            pins = [p.get("label") or "" for sentence in shot.get("sentences") or [] for p in sentence.get("pins") or []]
            if not any(MAPPING.search(label) for label in pins):
                out.append(f"{sid}: the aside maps the analogy in a pin (\"baandh = membrane\")")
            if (shot.get("dive") or {}).get("x", -1) != -1:
                out.append(f"{sid}: an aside cuts in (dive -1, -1); it is outside the film's world")
            if number < len(shots) and (shots[number].get("dive") or {}).get("x", -1) != -1:
                out.append(f"{shots[number].get('id') or f'shot {number + 1}'}: after an aside the film cuts back to its "
                           "world (dive -1, -1)")
    process = sum(1 for point in question.get("points") or [] if isinstance(point, dict) and point.get("kind") == "process")
    if shots and process >= PROCESS_FROM and not any(stepped_shot(shot) for shot in shots):
        out.append(f"the question has {process} process points; tell the process on one picture, step by step (at least "
                   f"{STEPS_FROM} sentences with step 1, 2, 3 on one shot)")
    lines = question.get("teacher_lines") or []
    if question.get("script_lines") and lines:
        found = list(_sentences(film))
        on_aside = {}
        for line, (_where, shot, _sentence) in zip(lines, found):
            if (line.get("kind") or "") == "analogy":
                on_aside.setdefault(line.get("point") or "", []).append(bool(shot.get("aside")))
        for point, placed in on_aside.items():
            if not any(placed):
                out.append(f"the script's analogy {point} is not on its own picture; say it on an aside shot")
    if not lines:                                    # his own lines and the script's lines are said as written (B8)
        spoken = [s for _where, _shot, sentence in _sentences(film)
                  for s in SENTENCE_END.split(sentence.get("roman") or "") if s.strip()]
        habit = opener_habit(spoken)
        if habit:
            out.append(f"{habit[1]} of the film's {habit[2]} answers open with \"{habit[0].capitalize()}\"; open some with "
                       f"another teacher's opener ({TEACHER_OPENERS}), no one opener for more than half")
    return out


QUESTION_WORD = re.compile(r"\b(kyun|kyon|kyu|kaise|kya|kab|kahan|kaun|kitna|kitne|kitni)\b", re.I)
BRIDGE = re.compile(r"\b(jawab|isliye|isiliye|aisa|wajah|dekhiye|chaliye|aaiye|aayiye|isme|ismein|iska|iski|hota|suniye|samajhiye|"
                    r"nahi|nahin|haan)\b", re.I)
ORDER = re.compile(r"\b(dekho|samjho|samajho|socho|suno|rakho|chalo|jaano|batao|padho|pehchaano)\b|"
                   r"\b(pehchaan|dekh|samajh|jaan|maan|sun|soch)\s+lo\b", re.I)
INVITE = re.compile(r"\b(aaiye|aayiye|aaie|chaliye)\b", re.I)
SEPARATOR = re.compile(r"\s*(?:—|–|;|:|\?|\s-\s)\s*")


def _asked_then(roman: str):
    """(question clause, what follows it) for every clause of a line that asks (a question word among its last six words)
    and is followed by more of the same line."""
    pieces = SEPARATOR.split(roman or "")
    for before, after in zip(pieces, pieces[1:]):
        if after.strip() and QUESTION_WORD.search(" ".join(before.split()[-6:])):
            yield before, after


def added_words(line: str, said: str) -> list:
    """The words of the film's sentence that its script line does not have, in the sentence's order (an opener put in
    front, "Ab sawaal uthta hai ki ...", is three or four of them)."""
    have, out = _tokens(line), []
    for w in re.findall(r"[A-Za-z][A-Za-z0-9]*|[\u0900-\u097F]{3,}", _plain(said)):
        low = w.lower()
        if (len(low) >= 3 or low not in SHORT_STOP) and _stem(low) not in have and w not in out:
            out.append(w)
    return out


def teacher_problems(film: dict, question: dict) -> list:
    """Navin's script edits (20 November 2026) as checks: a question and its answer told apart by a bridge, the voice
    ending a question with ?, the respectful "aap" voice, an invitation after the opening question, and, when the job
    carries the teacher's own lines, every film sentence being his line in his order."""
    out, teacher = [], question.get("teacher_lines") or []
    found = list(_sentences(film))
    for where, _shot, sentence in found:
        roman, voice = sentence.get("roman") or "", sentence.get("voice") or ""
        asks = "?" in roman or any(True for _ in _asked_then(roman))
        if asks and "?" not in voice:
            out.append(f"{where}: the line asks a question; in voice end the question with ? and start its answer as a new "
                       "sentence (the voice pauses there)")
        left = unsaid(voice or roman)
        if left:
            out.append(f"{where}: the voice cannot say {' '.join(left)}; write it in words in voice (\"per\", \"aur\", "
                       "\"guna\", \"se banta hai\"), the screen keeps the sign")
        if teacher:                               # the teacher's own words are his call
            continue
        for before, after in _asked_then(roman):
            if not BRIDGE.search(" ".join(after.split()[:5])):
                out.append(f"{where}: the question runs straight into its answer ({' '.join(before.split()[-4:])} → "
                           f"{' '.join(after.split()[:3])}); ask it, then open the answer with a bridge (\"Iska seedha sa "
                           "jawab hai ...\", \"Aisa isliye hai kyunki ...\", \"Dekhiye, hota kya hai: ...\")")
        order = ORDER.search(roman)
        if order:
            out.append(f"{where}: {order.group(0)!r} orders the learner; speak with respect and take them along (dekhiye, "
                       "chaliye dekhte hain, pehchaan lete hain, aapko yaad rakhni hain)")
    if found and not teacher:
        first = found[0][2].get("roman") or ""
        second = (found[1][2].get("roman") or "") if len(found) > 1 else ""
        if not (INVITE.search(first) or INVITE.search(" ".join(second.split()[:6]))):
            out.append(f"{found[0][0]}: after the opening question invite the learner (\"Aaiye jaante hain.\")")
    if teacher:
        if len(found) != len(teacher):
            out.append(f"the film has {len(found)} sentences and the teacher's script {len(teacher)} lines: the film's "
                       "sentences are his lines, every one, in his order")
        for n, (line, (where, _shot, sentence)) in enumerate(zip(teacher, found), 1):
            words = _tokens(line.get("roman") or "")
            kept = len(words & _tokens(sentence.get("roman") or "")) / max(1, len(words))
            if kept < TEACHER_MATCH:
                start = " ".join((line.get("roman") or "").split()[:6])
                out.append(f"{where} is not the teacher's line L{n} (\"{start} ...\"; {kept:.0%} of his words kept): keep "
                           "his words, fixing only spelling slips")
            elif question.get("script_lines"):      # the script's line as written, nothing put in front (B8)
                added = added_words(line.get("roman") or "", sentence.get("roman") or "")
                if len(added) >= ADDED_WORDS:
                    out.append(f"{where} adds words the script's line L{n} does not say ({' '.join(added[:6])}): say the "
                               "line as written, with no opener, question opener or bridge in front of it")
    return out


TURNING = re.compile(r"\b(ghoom\w*|ghuma\w*|rotor|rotate\w*|spin\w*)\b", re.I)
# "made again": regenerate, or again (dobara, phir se) with a making word close after it ("RuBP dobara banta hai",
# "acceptor dobara kaise milta hai"); a plain "dobara" is not a return ("dobara proton pumping ki energy": the first
# heading films, 23 November 2026, where it forced a wheel onto a proton's one-way trip)
AGAIN = re.compile(r"\bregenerat\w*|\b(?:dobara|phir se)\s+(?:\w+\s+){0,2}?(?:ban\w*|mil\w*|taiyaa?r\w*|restor\w*|renew\w*)\b",
                   re.I)
EVERYDAY = re.compile(r"\b(jaise|jaisa|jaisi|samajhiye|samjhiye|misaal|ki tarah|baandh|dam|motor|battery|turbine|conveyor)\b", re.I)


def mechanism_problems(film: dict, question: dict | None = None) -> list:
    """Navin's choice after comparing every Q14 film (21 November 2026): the whole mechanism shown (a turning machine
    turns, a returning process is a wheel), molecules meeting one at a time and named as they meet, a question before
    every mechanism, and everyday pictures through the film, as in his film A. An aside shot is an everyday picture; a
    film made from the chapter's script has the script's analogies and no others (its lines are the script's), so the
    count is the script's to keep, not the film's."""
    out, shots = [], film.get("shots") or []
    asked = 0
    # a film told in the chapter's script or the teacher's own lines asks where those lines ask: r4 of 11.6.3b (24
    # November 2026) spent two rounds and ended "needs_fix" because a question demanded per mechanism shot could not be
    # added without breaking "the film's sentences are the script's lines, every one"
    lined = bool((question or {}).get("teacher_lines"))
    for number, shot in enumerate(shots, 1):
        sid = shot.get("id") or f"shot {number}"
        sentences = shot.get("sentences") or []
        has_wheel = any(s.get("cycles") for s in sentences)
        mechanism = any((s.get("reacts") or s.get("cycles") or any((e.get("type") == "spin") for e in s.get("effects") or [])
                         or s.get("acts")) and s.get("part") != "recap" for s in sentences)
        has_question = any("?" in (s.get("voice") or "") for s in sentences)
        asked += has_question
        if mechanism and not has_question and not lined:
            out.append(f"{sid}: a mechanism is shown here but no question is asked before it; ask one (it ends with ? in "
                       "voice) so the voice pauses before the answer")
        for k, s in enumerate(sentences, 1):
            where, roman = f"{sid} sentence {k}", s.get("roman") or ""
            if TURNING.search(roman) and not s.get("cycles") and not any(e.get("type") == "spin" for e in s.get("effects") or []) \
                    and not any(a.get("do") in ("turn", "spin") for a in s.get("acts") or []) and not _turning_on(shot, k):
                out.append(f"{where}: the line says something turns ({TURNING.search(roman).group(0)!r}); show it turning: "
                           "the turning part of the picture turns (acts: turn or spin), or a spin effect on a diagram")
            if AGAIN.search(roman) and not has_wheel:
                out.append(f"{where}: the line says something is made again; show the return as a wheel (cycles) in this shot")
            reacts = s.get("reacts") or []
            if len(reacts) > 1:
                out.append(f"{where}: {len(reacts)} meetings in one sentence; one meeting at a time")
            if reacts and len(s.get("moves") or []) > 1:
                out.append(f"{where}: a meeting and {len(s.get('moves'))} other flows in one sentence; besides the meeting, "
                           "at most one flow moves")
            spoken = _tokens(roman) | _tokens(s.get("voice") or "")
            for r in reacts:
                for x in (r.get("inputs") or []) + (r.get("outputs") or []):
                    what = str(x.get("what") or "")
                    if KIT["molecules"].get(what) and not _tokens(KIT["molecules"][what].get("name") or what) & spoken \
                            and not _tokens(what) & spoken:
                        out.append(f"{where}: {what} takes part in the meeting but the line does not name it; name every "
                                   "molecule as it meets")
    if len(shots) >= 4:
        if asked * 2 < len(shots) and not lined:
            out.append(f"questions in {asked} of {len(shots)} shots; ask in at least half of them, as a teacher does")
        pictures = sum(1 if shot.get("aside") else sum(bool(EVERYDAY.search(s.get("roman") or "")) for s in shot.get("sentences") or [])
                       for shot in shots)
        if pictures < max(2, len(shots) // 3) and not (question or {}).get("script_lines"):
            out.append(f"{pictures} everyday picture(s) in the film; give one every two or three shots: an everyday "
                       "comparison in the line (jaise a dam, a motor, a battery, a turbine) or an aside shot")
    return out


def layout_problems(film: dict) -> list:
    """A structure pinned in two pictures stays on the same side of the other structures pinned with it (the Q14 review:
    the proton pump was left of ATP synthase in shot 4 and right of it in shot 6)."""
    places = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        xs = {}
        for sentence in shot.get("sentences") or []:
            for pin in sentence.get("pins") or []:
                try:
                    xs.setdefault((pin.get("label") or "").strip().lower(), []).append(float(pin["x"]))
                except (KeyError, TypeError, ValueError):
                    continue
        places.append((shot.get("id") or f"shot {number}", {k: sum(v) / len(v) for k, v in xs.items() if k}))
    out, told = [], set()
    for i, (first, a) in enumerate(places):
        for later, b in places[i + 1:]:
            both = sorted(set(a) & set(b))
            for one, two in ((one, two) for k, one in enumerate(both) for two in both[k + 1:]):
                da, db = a[one] - a[two], b[one] - b[two]
                if da * db < 0 and abs(da) > 10 and abs(db) > 10 and (one, two) not in told:
                    told.add((one, two))
                    left, right = (one, two) if da < 0 else (two, one)
                    out.append(f"{later}: {left!r} is left of {right!r} in {first} but right of it here; keep the same "
                               "left-right layout in every picture (write it into image_prompt and pin it there)")
    return out


def _sentences(film: dict):
    for number, shot in enumerate(film.get("shots") or [], 1):
        for k, sentence in enumerate(shot.get("sentences") or [], 1):
            yield f"{shot.get('id') or f'shot {number}'} sentence {k}", shot, sentence


ALIASES = {"h": "proton", "hydrogen": "proton", "electrons": "electron", "e": "electron"}


def _stem(word: str) -> str:
    word = word.lower()
    word = word[:-1] if len(word) > 4 and word.endswith("s") and not word.endswith("ss") else word
    return ALIASES.get(word, word)


def _content_words(text: str) -> set:
    """The words that carry a book line's meaning: English words of 4+ letters (not grammar words) and its terms, plural
    and H+/proton folded together."""
    text = _plain(text)
    words = {_stem(w) for w in re.findall(r"[A-Za-z]{4,}", text) if w.lower() not in STOP}
    return words | {_stem(studio_terms._norm_term(t)) for t in studio_terms.TERM.findall(text) if studio_terms.is_term(t)}


def _spoken_words(text: str) -> set:
    text = _plain(text)
    return {_stem(w) for w in re.findall(r"[A-Za-z]{4,}", text)} | {
        _stem(studio_terms._norm_term(t)) for t in studio_terms.TERM.findall(text) if studio_terms.is_term(t)}


def book_problems(film: dict, question: dict) -> list:
    """Every book line taught by a sentence that speaks its words, and the film's prerequisite and use sentences. Words
    are free: no word is refused for not being in the book (Navin, 20 November 2026)."""
    lines = question.get("book_lines") or []
    out, claims, parts = [], {}, set()
    for where, _shot, sentence in _sentences(film):
        if lines:
            teaches = sentence.get("teaches")
            if not isinstance(teaches, list):
                out.append(f"{where}: teaches is missing (the numbers of the book lines it teaches, [] for none)")
                teaches = []
            for n in teaches:
                if not isinstance(n, int) or not 1 <= n <= len(lines):
                    out.append(f"{where}: teaches B{n}, but the book lines are B1 to B{len(lines)}")
                else:
                    claims.setdefault(n, []).append(sentence.get("roman") or "")
        if "part" in sentence:
            parts.add(sentence.get("part"))
            if sentence.get("part") not in PARTS:
                out.append(f"{where}: part must be one of {', '.join(PARTS)}")
    for line in lines:
        said = claims.get(line["n"])
        words = _content_words(line["text"])
        if not said:
            out.append(f"book line B{line['n']} is not taught: {line['text'][:160]}")
        # a follow-up line with no key word of its own ("If yes, which one?", Photosynthesis q08, 21 November 2026) is
        # taught by the sentence that lists it; asking for its key words could never be met and spent 3 extra rounds
        elif words and not words & _spoken_words(" ".join(said)):
            out.append(f"book line B{line['n']} is listed in teaches, but none of its key words is spoken there: "
                       f"{line['text'][:120]}")
    if lines or parts:
        for part, what in (("prerequisite", "what the learner must know first"),
                           ("use", "where this concept is used next and the effect of what happened")):
            if part not in parts:
                out.append(f"no sentence is a {part} ({what}); every film has at least one")
    return out


def _molecules_of(sentence: dict) -> list:
    names = [m.get("what") for m in sentence.get("moves") or []]
    for react in sentence.get("reacts") or []:
        names += [x.get("what") for x in (react.get("inputs") or []) + (react.get("outputs") or [])]
    for cycle in sentence.get("cycles") or []:
        for station in cycle.get("stations") or []:
            names += [station.get("becomes")] + list(station.get("takes") or []) + list(station.get("gives") or [])
    return [n for n in dict.fromkeys(names) if n in KIT["molecules"]]


def _unexplained(stations: list, rest: list) -> list:
    """The stations that cannot each get a sentence of their own (a sentence that speaks the station's label or the
    molecule it makes), matched one sentence per station."""
    said = [_spoken_words((s.get("roman") or "") + " " + (s.get("voice") or "")) | _words(s.get("roman") or "")
            | _tokens(s.get("roman") or "") for s in rest]
    return _unmatched(stations, said, _station_names)


def _station_names(station: dict) -> set:
    """What names a wheel's station: the words of its label, short ones too (CF0, ATP), and the kit molecule it makes;
    a plain sprite (a dot, a drop) names nothing (the first heading films, 23 November 2026: a station that became a
    'dot' waited for a line to say "dot")."""
    label = station.get("label") or ""
    words = {_stem(w) for w in re.findall(r"[A-Za-z]{4,}", _plain(label))} | {t for t in _tokens(label) if t not in STOP}
    made = station.get("becomes") or ""
    if made in KIT["molecules"]:
        words |= {_stem(studio_terms._norm_term(t)) for t in studio_terms.TERM.findall(made) if studio_terms._norm_term(t)}
        words |= {made.lower()} | {t for t in _tokens(KIT["molecules"][made].get("name") or "") if t not in STOP}
    return words


def _unmatched(items: list, said: list, names) -> list:
    """The items that cannot each get a sentence of their own, matched one sentence per item."""
    options = [[i for i, words in enumerate(said) if names(item) & words] for item in items]
    owner = {}
    def place(j, seen):
        for i in options[j]:
            if i not in seen:
                seen.add(i)
                if i not in owner or place(owner[i], seen):
                    owner[i] = j
                    return True
        return False
    return [item for j, item in enumerate(items) if not place(j, set())]


def screen_problems(film: dict, question: dict) -> list:
    """One thing at a time: at most MAX_KINDS kit molecules on screen at once in a shot (what loops, what a reaction
    made and a turning wheel stay on screen until the shot ends); a wheel with n stations keeps turning for n more
    sentences after the one that starts it, one station explained per sentence (the Q14 ending told the whole cycle in
    one sentence)."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        sid = shot.get("id") or f"shot {number}"
        staying = set()
        for k, sentence in enumerate(shot.get("sentences") or [], 1):
            now = staying | set(_molecules_of(sentence))
            if len(now) > MAX_KINDS:
                out.append(f"{sid} sentence {k}: {len(now)} different molecules on screen at once "
                           f"({', '.join(sorted(now))}); at most {MAX_KINDS}: split the step over sentences or shots")
            staying |= {m.get("what") for m in sentence.get("moves") or [] if m.get("loop") and m.get("what") in KIT["molecules"]}
            for react in sentence.get("reacts") or []:
                staying |= {x.get("what") for x in react.get("outputs") or [] if x.get("what") in KIT["molecules"]}
            for cycle in sentence.get("cycles") or []:
                staying |= {n for st in cycle.get("stations") or [] for n in [st.get("becomes")] + list(st.get("takes") or [])
                            + list(st.get("gives") or []) if n in KIT["molecules"]}
            rest = (shot.get("sentences") or [])[k:]
            for cycle in sentence.get("cycles") or []:
                stations = cycle.get("stations") or []
                if len(stations) > len(rest):
                    out.append(f"{sid} sentence {k}: a wheel with {len(stations)} stations turns for only {len(rest)} "
                               f"sentence(s) after the one that starts it; keep it turning for {len(stations)} more "
                               "sentences, one station explained per sentence")
                else:
                    for station in _unexplained(stations, rest):
                        if not _station_names(station):
                            out.append(f"{sid} sentence {k}: a station of the wheel is a plain "
                                       f"{station.get('becomes') or 'dot'} with no label; label it with what happens there "
                                       "and say that in one of the sentences while the wheel turns")
                            continue
                        name = station.get("label") or station.get("becomes") or "a station"
                        out.append(f"{sid} sentence {k}: the wheel's station {name!r} is not explained in a sentence of "
                                   "its own (say its name or what it makes in one of the sentences while the wheel turns)")
    return out


def write(client, model: str, question: dict, *, course: str = "", language: str = "Hinglish", chapter: str = "",
          max_rounds: int = 3, look: str | None = None) -> dict:
    convo = messages(question, course=course, language=language, chapter=chapter, look=look)
    rounds, usage, film, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        try:
            reply = _ask(client, model, convo)
        except Exception as exc:
            if film is None or getattr(exc, "kind", None) == "plan_limit":
                raise
            # a later round's call failed twice: the film of the round before stands, with its findings and why it stopped
            found = list(found) + [f"round {number}: the maker's call failed ({str(exc)[:120]}); the film of round {number - 1} is kept"]
            rounds.append({"round": number, "problems": found, "failed": str(exc)[:200]})
            break
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        film = without_empty_cupboard(parse(reply.get("content", "")), question)
        found = problems(film, question)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
    return {"film": film, "problems": found, "rounds": rounds, "usage": usage}


def _ask(client, model: str, convo: list) -> dict:
    """One maker call, asked once more if it fails in a way a retry can help (a stuck or timed-out call): the first
    11.6 section job (23 November 2026) lost all three films to one codex call that did not finish in 30 minutes."""
    try:
        return client.chat(model=model, messages=convo, schema=SCHEMA)
    except Exception as exc:
        if not getattr(exc, "retryable", False):
            raise
        return client.chat(model=model, messages=convo, schema=SCHEMA)


IMAGE_SUFFIX = (" Photorealistic, natural colours, documentary quality, 16:9 landscape. No text, no letters, no numbers, "
                "no labels, no arrows or symbols, no logos, no watermark, no recognisable real person.")


CUTAWAY_SUFFIX = (" Scientific cutaway illustration: transparent cross-section, glossy cells, soft volumetric light, depth, "
                  "calm dark teal background, painterly 3D look, 16:9 landscape. No text, no letters, no numbers, no labels, "
                  "no arrows or symbols, no loose molecules or balls floating in the scene (BIE animates those over the "
                  "picture), no logos, no watermark.")
NO_MARKS = (" No text, no letters, no numbers, no labels, no arrows or symbols, no loose molecules or balls floating in the "
            "scene (BIE animates those over the picture), no logos, no watermark.")
# how a cutaway looks (Navin, 22 November 2026, on the 11.6 films: "visuals asli banane the, unki quality mein girawat aayi
# hai, ab cheezen zyada banawati lag rahi hain"; what he liked: where a thing binds and where it flows, "H⁺ ko membrane se
# paas karane wala receptor achhe se present kiya hai"). "glossy" is the look the films had; the look test puts the others
# beside it on the same shots, and Navin's eye chooses.
CUTAWAY_STYLES = {
    "glossy": CUTAWAY_SUFFIX,
    "matte": (" Realistic scientific render, not a cartoon: matte non-reflective surfaces with fine natural texture, true "
              "relative sizes, soft natural light with ambient occlusion in the creases, gentle depth of field, muted natural "
              "colours. No glossy or plastic sheen, no glow, no neon, no painterly haze, no volumetric light rays, whatever "
              "the words above say about light. 16:9 landscape." + NO_MARKS),
    "structure": (" Rendered like a structural-biology figure made from real atomic structures (cryo-EM and PDB models in a "
                  "physically based renderer): each protein a matte atomic-surface model with its real shape, the membrane as "
                  "densely packed lipid heads and tails, neutral studio light, strong ambient occlusion, photographic depth of "
                  "field, colours only as tints on the real shapes. No glossy plastic, no glow, no volumetric light rays, "
                  "whatever the words above say about light. 16:9 landscape." + NO_MARKS),
    # Navin's choice after the look test (22 November 2026, open ended: "baad mein mai apni choice badal bhi sakta hun"):
    # "proteins aur molecular machinery ke close-ups mein Structure; poore chloroplast jaise overview shots mein Matte.
    # Structure ki surface par halki, controlled sheen achhi rahegi ... chloroplast ke matte structure ko controlled chamak
    # deke achha kiya ja sakta hai"
    "close_up": (" Rendered like a structural-biology figure made from real atomic structures (cryo-EM and PDB models in a "
                 "physically based renderer): each protein a smooth atomic-surface model with its real shape and a light, "
                 "controlled satin sheen (never glossy plastic, never gritty or sandpaper-rough), the membrane as a real "
                 "lipid bilayer with visible thickness (two layers of densely packed lipid heads with their tails between "
                 "them, seen at the cut edge, a living, flexible sheet that curves and ripples a little along its length, "
                 "its lipid heads slightly uneven, never a ruler-straight row of identical beads, each protein sitting "
                 "through it at its true depth), soft "
                 "neutral studio light with ambient occlusion, photographic depth of "
                 "field, colours as tints on the real shapes. No glow, no volumetric light rays, whatever the words above "
                 "say about light. 16:9 landscape." + NO_MARKS),
    "overview": (" Realistic scientific render of the whole structure at this scale, not a cartoon: natural textures, true "
                 "relative sizes, soft natural light with ambient occlusion, a light controlled satin sheen on membranes "
                 "and envelopes (never glassy or plastic, no sparkle), every membrane with its real thickness (a double "
                 "layer where it is cut) and curving naturally like living tissue, never ruler-straight, gentle depth of "
                 "field, muted natural colours. Draw "
                 "no individual proteins or molecules at this scale unless the words above name them. No glow, no "
                 "volumetric light rays, whatever the words above say about light. 16:9 landscape." + NO_MARKS),
    # Navin, 24 November 2026, 14:41, after the real electron micrographs of thylakoids and stroma: "Iska alag se pehale yha
    # banwake dekhenge"; the trial pictures (VM job a1-asli-thylakoid-stroma) were drawn with these words, and he chose
    # to see r4 of 11.6.3b in this look, in "asli_mixed" (protein close-ups as close_up, the rest asli) and in "mixed"
    "asli": (" Rendered as the real inside of a chloroplast looks in electron micrographs and cryo-electron tomograms, given "
             "soft natural colour: thylakoid membranes are thin double-layered sheets that bend, curve and ripple, stacked "
             "like coins into grana and joined by thin unstacked stroma lamellae, never a thick band and never "
             "ruler-straight; where proteins are seen, the membrane is crowded with protein complexes packed side by side "
             "like cobblestones, each with its real atomic-surface shape and a light satin sheen, with little bare lipid "
             "between them; the stroma is a dense, finely granular, slightly cloudy fluid whose grain is a soft, "
             "out-of-focus texture of tiny ribosome-sized specks belonging to the fluid itself, with an occasional dark "
             "round plastoglobule or pale starch grain, never an empty smooth background. Soft controlled light with "
             "ambient occlusion, gentle depth of field, muted natural colours. No glow, no volumetric light rays, whatever "
             "the words above say about light. 16:9 landscape." + NO_MARKS),
}
# the films' cutaways: "mixed" draws a close-up of proteins and molecular machinery as "close_up" and a whole-structure
# view as "overview"; "glossy" brings back the look the films had until 22 November 2026
# Navin, 23 November 2026, after the first heading film: "Is baar matte with controlled roshni nhi pehale wale chamakdaar
# tarike se hi banao video" (his 22 November choice was open ended); Navin, 24 November 2026, after r3 of 11.6.3b in the
# hybrid look: "Behtar laga achha bana hai", so the hybrid look is the films' look again
FILM_STYLE = "mixed"
# the parts that move are solid, so they can be cut and so the mechanism reads (Navin, 23 November 2026, on routes A and B:
# "kuchh jyada hi transparent hai ... bahut hi transparent beta aur na dikhne wali dandi"): whatever the cutaway style
# says about transparency, these parts are opaque and fully in view; "solid, separate, clean edge" made toy shapes (the
# first parts film of 11.6.3b, Navin, 23 November 2026: "ekdum nakli"), so they stay as real as the rest of the picture
SOLID_PARTS = (" These parts are opaque and fully in view, not behind glass or a see-through layer and not covered by another "
               "part, and drawn exactly as real and detailed as everything else in the picture (their true structure and "
               "surface, never a simplified, cartoon or toy shape): {parts}.")
MACHINERY = re.compile(r"(?i)\b(proteins?|complex(es)?|enzymes?|ps ?ii?\b|photosystems?|atp synthase|cf[0₀1₁]|cytochromes?|"
                       r"plastoquinone|plastocyanin|ferredoxin|rubisco|reaction cent(re|er)|molecules?|molecular|carriers?|"
                       r"channels?|pumps?|antenna)")
NO_MACHINERY = re.compile(r"(?i)\bno (individual |molecular )?(proteins?|molecules)\b")


def style_for(shot: dict) -> str:
    """How a cutaway is drawn under FILM_STYLE "mixed": a close-up of proteins or molecular machinery as a structure, a
    whole-structure view (a chloroplast, a leaf, a cell) as an overview."""
    prompt = (shot.get("visual") or {}).get("image_prompt", "")
    if NO_MACHINERY.search(prompt):
        return "overview"
    return "close_up" if MACHINERY.search(prompt) else "overview"


CLOSE = re.compile(r"(?i)\b(close[- ]?ups?|closer|magnified|enlarged|zoom(ed)? in|macro)\b")


def close_view(shot: dict) -> bool:
    """A picture that shows proteins or molecular machinery from close by (Navin's "asli_mixed" look, 24 November 2026:
    these stay as clean as the hybrid's close-ups; grana, a thylakoid, the stroma and wide membrane views are drawn asli)."""
    prompt = (shot.get("visual") or {}).get("image_prompt", "")
    return bool(CLOSE.search(prompt) and MACHINERY.search(prompt) and not NO_MACHINERY.search(prompt))


COLOUR_WORDS = {"amber", "black", "blue", "bright", "brown", "copper", "cool", "dark", "deep", "emerald", "glow", "glowing",
                "gold", "golden", "gray", "green", "grey", "ivory", "jade", "light", "orange", "pale", "pink", "purple", "red",
                "sage", "silver", "teal", "translucent", "transparent", "turquoise", "violet", "warm", "white", "yellow"}
STYLE_WORDS = {"and", "aur", "camera", "cinematic", "colour", "colours", "color", "colors", "continuous", "depth", "every", "glossy",
               "har", "journey", "lighting", "look", "macro", "material", "palette", "par", "photoreal", "photorealistic",
               "realistic", "same", "scale", "scientific", "shadow", "shadows", "soft", "structural", "the", "volumetric", "with",
               # a surface or a style, never a structure (the first heading films, 23 November 2026: "matte" in the look's
               # workshop clause matched the chloroplast picture's "matte textures", and a motor was drawn in the stroma)
               "calm", "clean", "crisp", "detailed", "documentary", "everyday", "hydrated", "matte", "natural", "painterly",
               "photographic", "rich", "sharp", "texture", "textured", "textures"}


GENERIC_WORDS = {"above", "back", "behind", "below", "beside", "biological", "bottom", "center", "central", "centre", "consistent",
                 "facing", "far", "front", "inside", "large", "leave", "left", "lower", "many", "middle", "near", "one", "open",
                 "orientation", "outside", "previous", "right", "selected", "several", "side", "small", "target", "top", "two",
                 "upper", "all", "also", "any", "are", "both", "but", "each", "for", "from", "had", "has", "have", "its", "more",
                 "not", "only", "such", "than", "that", "then", "there", "this", "very", "was", "where", "while"}


def _structure_words(text: str) -> set:
    """The words that name structures: not colours, style, places in the frame or sizes (the second Q14 remake: "proton
    pump copper left" matched a cell picture's "upper left open", and ATP synthase was drawn on the cell again)."""
    return {_stem(w.lower()) for w in re.findall(r"[A-Za-z][A-Za-z0-9+]*", text or "")
            if w.lower() not in COLOUR_WORDS | STYLE_WORDS | GENERIC_WORDS
            and (len(w) >= 3 or "+" in w or w.lower() not in SHORT_STOP)}


EVERYDAY_LOOK = re.compile(r"\b(everyday|analogy|aside)\b", re.I)


def look_for(prompt: str, look: str, aside: bool | None = None) -> str:
    """The film's look for one picture: its light and palette always, and the colours of a structure only when this
    picture shows that structure. Q14 remake (20 November 2026): the shared look named 'ATP synthase: violet CF1 head',
    and the image model drew ATP synthase on the cell picture, one scale too early, though its prompt said no proteins.
    The look of the everyday world (an "everyday workshop ...") goes only to an aside's picture (``aside`` True), never
    to the film's own world (``aside`` False)."""
    shown = _structure_words(prompt)
    kept = []
    for clause in (c.strip() for c in re.split(r";|\.(?:\s|$)", look or "")):
        if not clause:
            continue
        if aside is False and EVERYDAY_LOOK.search(clause):
            continue
        name = clause.split(":", 1)[0] if ":" in clause else ""
        if _structure_words(name):            # "ATP synthase: violet head, amber channel" (not "16:9")
            if _structure_words(name) & shown:
                kept.append(clause)
            continue
        keep, last = [], None
        for part in (f.strip() for f in clause.split(",") if f.strip()):
            first = (re.findall(r"[A-Za-z]+", part) or [""])[0].lower()
            if last is not None and first in COLOUR_WORDS:      # "silver central stalk ..." describes the structure before it
                ok = last
            else:
                ok = not _structure_words(part) or bool(_structure_words(part) & shown)
            if ok:
                keep.append(part)
            last = ok
        if keep:
            kept.append(", ".join(keep))
    return "; ".join(kept)


UNGLOSSY = re.compile(r"(?i)\b(matte|non-reflective|muted|controlled (satin )?sheen|satin sheen)\b ?")
# a picture in another look is not asked to be glossy as well, and a photo is a real photograph, never glossy (Navin, 23
# November 2026, on the two 11.6.3b films: the first film's "photorealistic hydroelectric dam" read better than the
# second's "photoreal glossy hydroelectric teaching model")
GLOSSY_WORDS = re.compile(r"(?i)\b(high-gloss|glossy|glassy|shiny)\b ?")
# an everyday photo shows the real thing where it is, at its real size: a dam, not a model of one
PHOTO_MODEL = re.compile(r"(?i)(?<!ball-and-stick )(?<!space-filling )(?<!3d )(?<!atomic )(?<!structural )(?<!scientific )"
                         r"(?<!everyday )(?<!mental )\b(models?|miniatures?|toys?|dioramas?|replicas?)\b")


# a crowd word that sits on a structure ("curved crowded membrane", "packed proteins", "dense stroma") is about the
# structure, not loose molecules: the asli look asks for exactly that, and r4a lost a round to "Retain curved crowded
# membrane and clear ion approach space below" (24 November 2026)
_ON_STRUCTURE = (r"(?!\s+([\w-]+\s+){0,2}(membranes?|stroma|proteins?|protein\s+complexes|complexes|lipids?|grana|"
                 r"surfaces?|textures?|thylakoids?|interiors?|cytoplasm|matrix|bilayers?|sheets?|stacks?)\b)")
_SWARM = rf"(population|populations|dense|densely|sparse|crowd|crowded|many|packed|swarm|swarms)\b{_ON_STRUCTURE}"
_LOOSE = r"(protons?|h\+|h⁺|ions?|electrons?|molecules?|particles?|tokens?)"
CROWD = re.compile(rf"(?i)\b{_LOOSE}(?=[^.;,]{{0,30}}\b{_SWARM})|\b{_SWARM}(?=[^.;,]{{0,30}}{_LOOSE}(?![a-z]))")


def crowd_problems(film: dict) -> list:
    """A picture draws no crowd of loose molecules or ions: BIE animates a few over it. The second 11.6.3b film's
    "visibly higher proton population space" became a lumen carpeted with H⁺ beads, and Navin found that film the more
    khichdi of the two (23 November 2026)."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        if ((shot.get("visual") or {}).get("library") or "").strip():
            continue                          # a kept picture is already made and was chosen; its words stay
        prompt = (shot.get("visual") or {}).get("image_prompt") or ""
        found = CROWD.search(prompt)
        if found:
            out.append(f"{shot.get('id') or f'shot {number}'}: the image_prompt asks for a crowd of molecules or ions "
                       f"(\"...{prompt[max(0, found.start() - 20):found.end() + 30].strip()}...\"); the picture draws none, BIE "
                       "moves a few over it: write that the space is left clear")
    return out


OVERLAY_ASK = re.compile(r"(?i)\b(check-?lists?|(two|three|four|five|six)-item|list panels?|ui panels?|empty (bars|boxes|slots)|"
                         r"insets?|picture[- ]in[- ]picture)\b")


def overlay_problems(film: dict) -> list:
    """A picture leaves room for what BIE draws over it (a count, a checklist, labels) and never draws it itself: the
    second 11.6.3b film's "upper-center four-item checklist" came back as four empty bars painted into the picture, in
    both looks (look test, 23 November 2026)."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        if ((shot.get("visual") or {}).get("library") or "").strip():
            continue                          # a kept picture is already made and was chosen; its words stay
        found = OVERLAY_ASK.search((shot.get("visual") or {}).get("image_prompt") or "")
        if found and re.match(r"(?i)insets?|picture", found.group(0)):
            # r4 of 11.6.3b (24 November 2026): two pictures carried a small picture of another place in a corner
            out.append(f"{shot.get('id') or f'shot {number}'}: the image_prompt asks for a {found.group(0)!r}; a picture shows "
                       "one place, with no small picture of another place in it (BIE shows the path of places in a corner)")
        elif found:
            out.append(f"{shot.get('id') or f'shot {number}'}: the image_prompt asks the picture for a {found.group(0)!r}; BIE "
                       "draws counts and lists over the picture, so write only that the space is left clear")
    return out


def _aatma_problems(film: dict) -> list:
    """The film measured against the films Navin passed (``aatma.aatma_problems``); nothing while the almaari is empty."""
    from . import aatma
    return aatma.aatma_problems(film)


def photo_problems(film: dict) -> list:
    """An everyday photo (an analogy's dam, a field, a kitchen) shows the real thing at its real size, never a teaching
    model or a toy of it (the second 11.6.3b film's turbine, 23 November 2026)."""
    out = []
    for number, shot in enumerate(film.get("shots") or [], 1):
        visual = shot.get("visual") or {}
        if visual.get("type") != "photo" or (visual.get("library") or "").strip():
            continue
        found = PHOTO_MODEL.search(visual.get("image_prompt") or "")
        if found:
            out.append(f"{shot.get('id') or f'shot {number}'}: the photo asks for a {found.group(0)!r}; a photo shows the real "
                       "thing where it is, at its real size (a real dam and its turbine, not a model of them)")
    return out


def _where_in(point) -> str:
    x, y = float(point[0]), float(point[1])
    across = "left" if x < 34 else "right" if x > 66 else "centre"
    down = "upper" if y < 34 else "lower" if y > 66 else ""
    return f"{down} {across}".strip() if down or across != "centre" else "centre"


CARRIERS = re.compile(r"(?i)\b(channels?|pores?|pumps?|cf ?[0₀]|transmembrane|proteins?|complex(es)?|atp synthase|"
                      r"cytochromes?|photosystems?|ps ?ii?\b|carriers?|transporters?|ring|stalk|gates?)\b")


def route_clause(shot: dict) -> str:
    """The passages the shot's moving things go through a structure by, for its picture: each drawn as a real channel,
    open from entrance to exit (Navin, 24 November 2026, on r2 of 11.6.3b: "flow hone ke raaste ka structure sa bankar
    jaise glossy wale mein H+ ke liye bnaya hai"; 7-h11's picture had drawn the H+ channel through the membrane, and the H+
    visibly went through it). Only a route that passes a carrier (a channel, pump, protein or complex pinned near its
    middle) gets a passage: on r3 (24 November 2026) routes through the open stroma and lumen were drawn as invented tubes
    and ribbons between the proteins, which no cell has. Written by code from the film's own moves; "" when none."""
    visual = shot.get("visual") or {}
    if visual.get("type") != "cutaway":
        return ""
    marks = [(p.get("name") or p.get("label") or "", p.get("x"), p.get("y")) for p in visual.get("parts") or []
             if isinstance(p, dict) and p.get("x") is not None]
    marks += [(p.get("label") or "", p.get("x"), p.get("y")) for s in shot.get("sentences") or [] for p in s.get("pins") or []
              if isinstance(p, dict) and p.get("x") is not None]
    marks = [m for m in marks if CARRIERS.search(m[0] or "")]
    routes, seen = [], set()
    for sentence in shot.get("sentences") or []:
        for move in sentence.get("moves") or []:
            points = [p for p in move.get("points") or [] if _point(p)]
            what = str(move.get("label") or move.get("what") or "").strip()
            if len(points) < 2 or not what:
                continue
            middle = points[len(points) // 2]
            near = [(math.hypot(float(x) - middle[0], float(y) - middle[1]), name) for name, x, y in marks
                    if name and not _spoken_words(name) <= _spoken_words(what)]     # not the mover's own name
            if not near or min(near)[0] >= 14:
                continue
            through = min(near)[1]
            key = _plain(through).lower()                # one passage per structure (H⁺, "proton", "proton flow")
            if key in seen:
                continue
            seen.add(key)
            routes.append(f"the channel through the {through} that {what} pass through, from the {_where_in(points[0])} "
                          f"to the {_where_in(points[-1])}")
    if not routes:
        return ""
    return (" Draw each passage a moving thing takes through a structure as a real open channel in that structure, from its "
            "entrance to its exit and in clear view, empty of the travellers (BIE moves them over the picture): "
            + "; ".join(routes[:3]) + ". Things that move through open fluid (the stroma, the lumen) need no passage: draw "
            "no tube, pipe or ribbon between the structures.")


def image_prompt(shot: dict, look: str = "", style: str | None = None) -> str:
    """The shot's picture prompt; ``look`` (the film's shared art direction) keeps every picture in one world, with a
    structure's colours only on the pictures that show it (look_for); ``style`` is how a cutaway is rendered
    (CUTAWAY_STYLES, or "mixed"; FILM_STYLE when not given)."""
    visual = shot.get("visual") or {}
    style = style or FILM_STYLE
    if style == "mixed":
        style = style_for(shot)
    elif style == "asli_mixed":
        style = "close_up" if close_view(shot) else "asli"
    suffix = CUTAWAY_STYLES.get(style, CUTAWAY_SUFFIX) if visual.get("type") == "cutaway" else IMAGE_SUFFIX
    prompt = visual.get("image_prompt", "").strip()
    shared = look_for(prompt, look, aside=bool(shot.get("aside")))
    if visual.get("type") == "photo" or style != "glossy":   # a photo, or a cutaway in another look, is never glossy
        prompt, shared = (GLOSSY_WORDS.sub("", text) for text in (prompt, shared))
    elif style == "glossy":                  # a glossy picture is not asked to be matte as well (Navin, 23 November 2026)
        prompt, shared = (UNGLOSSY.sub("", text) for text in (prompt, shared))
    shared = f" Same look as the other pictures of this film: {shared.rstrip('.').strip(' ,;')}." if shared.strip(" ,;.") else ""
    moving = acted_parts(shot)
    if moving:                               # parts BIE cuts out and moves are solid (routeS, 23 November 2026)
        suffix = SOLID_PARTS.format(parts="; ".join(f"{p.get('name')} ({p.get('looks')})" for p in moving)) + suffix
    return prompt + shared + route_clause(shot) + suffix


def player_data(film: dict, *, images: dict, audio: dict, chapter: str, question: dict, tint: str = "#2c6e87",
                parts: dict | None = None) -> dict:
    """The JSON the film player reads: shots with their visual (image data URI or SVG) and timed sentences. A voiced
    sentence carries ``after``, the silence before the next one (``studio_voice.gaps``: the teacher study's pauses).
    ``parts`` ({shot id: [{id, img, box, centre}]}) are the parts cut from that shot's picture; the sentences' acts move
    them, and an act on a part that was not cut is left out."""
    from .studio_voice import gaps
    shots, lines = [], []
    for shot in film.get("shots") or []:
        dive = shot.get("dive") or {}
        for k, sentence in enumerate(shot.get("sentences") or []):
            clip = audio.get((shot.get("id"), k)) or {}
            lines.append({"text": sentence.get("voice") or sentence.get("roman") or "", "dur": clip.get("dur") or 0,
                          "shot_start": k == 0 and bool(lines), "dive": dive.get("x", -1) != -1})
    after = iter(gaps(lines))
    path = None
    for shot in film.get("shots") or []:
        visual = shot.get("visual") or {}
        # the path of places the camera has gone inside (Thylakoid › ATP synthase › CF₁): a dive adds its place, a cut
        # starts again, an analogy's own picture has none (Navin, 24 November 2026: "taaki pata lage ki hum is cheej ke
        # molecular level par jaa rahe hai")
        place = str(shot.get("place") or "").strip()
        diving = (shot.get("dive") or {}).get("x", -1) != -1
        path = None if (shot.get("aside") or not place) else (path + [place] if diving and path else [place])
        layers = [dict(p) for p in (parts or {}).get(shot.get("id")) or [] if p.get("img") and p.get("box")]
        cut = {p.get("id") for p in layers}
        names = {p.get("id"): p.get("name") or "" for p in visual.get("parts") or [] if isinstance(p, dict)}
        for layer in layers:                 # a part is named on screen as the voice names it (Navin, 24 November 2026)
            layer["name"] = names.get(layer.get("id"), "")
        sentences = []
        camera = steady_camera(shot.get("sentences") or [])
        for k, sentence in enumerate(shot.get("sentences") or []):
            clip = audio.get((shot.get("id"), k)) or {}
            text = sentence.get("roman", "")
            said = word_times(sentence, text, clip.get("dur") or max(2.5, 0.075 * len(text)))
            sentences.append({"text": text, "audio": clip.get("uri", ""),
                              "dur": clip.get("dur") or max(2.5, 0.075 * len(text)),
                              "pins": said["pins"],
                              "arrows": sentence.get("arrows") or [], "effects": sentence.get("effects") or [],
                              "focus": sentence.get("focus") or [], "zoom": camera[k],
                              "moves": held(said["moves"], clip.get("dur") or max(2.5, 0.075 * len(text))),
                              "grows": sentence.get("grows") or [],
                              "fuses": sentence.get("fuses") or [],
                              "reacts": timed(sentence.get("reacts") or [], text, clip.get("dur") or max(2.5, 0.075 * len(text))),
                              "cycles": sentence.get("cycles") or [],
                              "step": _int(sentence.get("step")), "count": sentence.get("count") or {},
                              "acts": act_times([{"part": a.get("part"), "do": a.get("do"), "toward": a.get("toward") or [],
                                                  "turns": a.get("turns") or 0, "rider": a.get("rider") or ""}
                                                 for a in sentence.get("acts") or [] if a.get("part") in cut],
                                                names, text, clip.get("dur") or max(2.5, 0.075 * len(text)))})
            if text.rstrip().endswith("?"):  # the question is on the screen while it is asked (Navin, 24 November 2026)
                sentences[-1]["ask"] = dict({"q": ask_card(text)}, **(question_subject(text, shot, layers) or {}))
            sentences[-1]["track"] = camera_track(sentences[-1], layers,
                                                  last=k == len(shot.get("sentences") or []) - 1,
                                                  question=text.rstrip().endswith("?"))
            gap = next(after, 0.0)
            if clip.get("uri"):
                sentences[-1]["after"] = gap
        dive = shot.get("dive") or {}
        shots.append({"id": shot.get("id"), "title": shot.get("title"), "key": shot.get("key"),
                      "light": lightness(images.get(shot.get("id"), "")),
                      "type": visual.get("type"), "img": images.get(shot.get("id"), ""),
                      "dive": dive if dive.get("x", -1) != -1 else None,
                      "place": place, "path": list(path) if path else None,
                      # the living world moves by itself: a membrane ripples, its proteins sway (Navin, 24 November 2026:
                      # "thoda hilti lage na jaise ek living organism ke andar cells wagarh aise hilti hai")
                      "alive": visual.get("type") == "cutaway",
                      "svg": visual.get("svg", "") if visual.get("type") == "diagram" else "", "sentences": sentences,
                      "parts": layers})
    return {"title": film.get("title") or question.get("question"), "question": question.get("question"),
            "qid": question.get("id"), "chapter": chapter, "tint": tint, "shots": shots, "kit": kit_for(shots)}


def joined(parts: list, *, qid: str, question: str, title: str = "") -> dict:
    """One heading's whole film from the player data of its parts, in order (Navin, 26 November 2026: "har heading ki ek
    poori film"): the parts are written one by one (at most studio_script.FILM_LINES lines each, so every line is kept),
    then played as one film, every shot id made unique with its part's id."""
    shots = []
    for data in parts:
        for shot in data.get("shots") or []:
            shots.append(dict(shot, id=f"{data.get('qid') or 'part'}-{shot.get('id')}"))
    first = parts[0] if parts else {}
    return {"title": title or question, "question": question, "qid": qid, "chapter": first.get("chapter", ""),
            "tint": first.get("tint", "#2c6e87"), "shots": shots, "kit": kit_for(shots),
            "parts": [data.get("qid") for data in parts]}


def lightness(uri: str) -> float | None:
    """How light a picture is, 0 (black) to 1 (white), from its data URI; None when it cannot be read. The spotlight dims
    the rest of a close-up; on r3's cream, matte pictures (24 November 2026) its dark edge turned the background a muddy
    grey, so a light picture is dimmed gently."""
    if not uri or not str(uri).startswith("data:image"):
        return None
    try:
        import base64
        import io
        from PIL import Image, ImageStat
        image = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))).convert("L")
        image.thumbnail((64, 64))
        return round(ImageStat.Stat(image).mean[0] / 255, 2)
    except Exception:
        return None


def timed(reacts: list, roman: str, seconds: float) -> list:
    """Each meeting's start, so its flash (at 45% of the meeting) comes when the line names its product, after the
    inputs are named (Navin, 21 November 2026: molecules meeting "achhe coordination ke saath"). ``delay`` is seconds
    after the sentence starts; without a product word the player keeps its own order."""
    low, out = (roman or "").lower(), []
    for r in reacts:
        r = dict(r)
        names = lambda xs: [str((KIT["molecules"].get(str(x.get("what"))) or {}).get("name") or x.get("what") or "").lower()
                            for x in xs]
        ins = [low.rfind(n) for n in names(r.get("inputs") or []) if n and low.rfind(n) >= 0]
        start = max(ins) if ins else 0
        found = [m.start() for n in names(r.get("outputs") or []) if n
                 for m in re.finditer(re.escape(n) + r"(?! synthase)", low) if m.start() >= start]
        if found and low:
            ms = max(1500, min(9000, float(r.get("ms") or 4000)))
            at = min(found) / len(low) * seconds
            r["delay"] = round(max(0.3, min(at - 0.45 * ms / 1000, seconds - 0.6 * ms / 1000)), 2)
        out.append(r)
    return out


# the closest the camera goes inside a picture: Navin, 24 November 2026, 19:21, on r4: "jiski baat ho rahi sirf use dikhane
# ke chakkar mein bahut kuchh screen ka hissa chhup jata hai, isme sudhar karo"; the camera leans in, the light points (a
# dive into the next place is apart from this: it goes inside)
CAM_MAX = 1.3


def _zoom(z: dict) -> tuple:
    z = z or {}
    return (50.0 if z.get("x") is None else float(z["x"]), 50.0 if z.get("y") is None else float(z["y"]),
            max(1.0, min(CAM_MAX, float(z.get("scale") or 1))))


def steady_camera(sentences: list) -> list:
    """Each sentence's camera (zoom), held still unless the line brings something new to look at. Navin, 23 November
    2026, on the two 11.6.3b films: the first, whose camera moved on 22 of 39 lines and stayed on a step while it was
    told, explained the mechanism better than the second (28 of 39). A question keeps the camera still; a line with nothing new (no pin, move, meeting, act, step or lit part) keeps the camera of the line before; a
    change smaller than 5% of the frame or 0.15 of zoom is no change."""
    out, last = [], (50.0, 50.0, 1.0)
    for sentence in sentences:
        want = _zoom(sentence.get("zoom"))
        new = any(sentence.get(k) for k in ("pins", "moves", "reacts", "acts", "focus", "cycles", "fuses")) or sentence.get("step")
        question = (sentence.get("roman") or "").rstrip().endswith("?")
        small = abs(want[2] - last[2]) < 0.15 and (want[2] <= 1.0 or math.hypot(want[0] - last[0], want[1] - last[1]) < 5)
        keep = last if (question or not new or small) else want
        out.append({"x": keep[0], "y": keep[1], "scale": keep[2]})
        last = keep
    return out


TRACK_MIN = 1.12       # how close the camera goes to what the voice names now (at most CAM_MAX; the light does the rest)
TRACK_MAX = CAM_MAX
FOLLOW_SCALE = 1.2     # the camera on a thing that travels
REACT_SCALE = 1.25     # the camera on a meeting
ASK_SCALE = 1.2        # how close the camera goes to what a question asks about


def ask_card(roman: str) -> str:
    """A question as the screen shows it: the words after its opener ("Ab sawaal uthta hai ki CF₁ ki shape kaise badalti
    hai?" shows "CF₁ ki shape kaise badalti hai?")."""
    text = " ".join((roman or "").split())
    found = re.match(r"^(.{0,90}?)(?:\bki\b|:)\s+(.+\?)$", text)
    if found and ASKING.search(found.group(1)):
        text = found.group(2)
    return text[:1].upper() + text[1:]


def _named_at(name: str, low: str):
    """Where in a plain, lower-case line ``name`` is first said, or None."""
    best = None
    for token in re.findall(r"[a-z0-9+\-]+", _plain(str(name or "")).lower()):
        if (len(token) < 3 and not re.search(r"[0-9+]", token)) or token in SHORT_STOP or token in STOP:
            continue
        stem = token[:5] if len(token) > 5 and token.isalpha() else token
        found = re.search((r"(?<![a-z0-9])" + re.escape(stem)) if stem[0].isalnum() else re.escape(stem), low)
        if found and (best is None or found.start() < best):
            best = found.start()
    return best


def question_subject(roman: str, shot: dict, layers: list) -> dict | None:
    """The point of the picture a question asks about, for the camera, the light and the "?" mark: the first part or pinned
    structure it names, or, when it names none, the first travelling thing it names (the middle of its way). None when it
    names nothing on the picture."""
    low = _plain(roman or "").lower()
    found = []
    for layer in layers:
        box = layer.get("box")
        at = _named_at(layer.get("name") or "", low)
        if box and at is not None:
            size = max(box[2] - box[0], (box[3] - box[1]) * 0.5625, 1.0)
            found.append((0, at, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, max(1.1, min(ASK_SCALE, 40 / size))))
    for sentence in shot.get("sentences") or []:
        for pin in sentence.get("pins") or []:
            at = _named_at(pin.get("label") or "", low) if isinstance(pin, dict) else None
            if at is not None and _point([pin.get("x"), pin.get("y")]):
                found.append((0, at, float(pin["x"]), float(pin["y"]), ASK_SCALE))
        for move in sentence.get("moves") or []:
            points = [p for p in move.get("points") or [] if _point(p)]
            at = _named_at(move.get("label") or move.get("what") or "", low)
            if points and at is not None:
                middle = points[len(points) // 2]
                found.append((1, at, float(middle[0]), float(middle[1]), 1.15))
    if not found:
        return None
    _, _, x, y, scale = min(found, key=lambda f: (f[0], f[1]))
    return {"x": round(x, 1), "y": round(y, 1), "scale": round(scale, 2)}


def camera_track(sentence: dict, layers: list, *, last: bool = False, question: bool = False) -> list:
    """Where the camera goes inside a sentence, timed to the words (Navin, 24 November 2026, on r2 of 11.6.3b: "zoom
    effects camera angles ka behtreen use krke taaki user ka dhyan script ke sath bandh jaaye"). As the voice names the
    first thing that happens (a part acting, a thing setting off, a meeting), the camera goes close to it; a thing that
    travels is followed to where it goes; the shot's last line ends on the whole picture, so the learner sees the step in
    its place. A question takes the camera, as it is asked, to the part it asks about and holds there (Navin, 24 November
    2026: "question par screen ke kis hisse par baat ho rhi ... wo thoda sa mehsoos ho camera effects ... se"); one that
    names no part keeps the camera still. At most three moves come in one line. Each move: at (seconds), x, y (percent),
    scale, ms."""
    if question:
        ask = sentence.get("ask") or {}
        if ask.get("x") is None:
            return []
        return [{"at": 0.15, "x": round(float(ask["x"]), 1), "y": round(float(ask["y"]), 1),
                 "scale": round(min(CAM_MAX, float(ask.get("scale") or ASK_SCALE)), 2), "ms": 1300}]
    dur = float(sentence.get("dur") or 0) or 3.0
    boxes = {p.get("id"): p.get("box") for p in layers if p.get("box")}
    events = []
    for act in sentence.get("acts") or []:
        box = boxes.get(act.get("part"))
        if not box or act.get("do") in ("stop", "loose"):
            continue
        size = max(box[2] - box[0], (box[3] - box[1]) * 0.5625, 1.0)
        if 40 / size < TRACK_MIN:            # a part that already fills much of the frame is seen without a push in (r3:
            continue                         # a 57% wide CF1 lobe at 1.35 cut the head and its labels off the screen)
        events.append((float(act.get("at") or 0.4), [(box[0] + box[2]) / 2, (box[1] + box[3]) / 2],
                       min(TRACK_MAX, 40 / size), None))
    for move in sentence.get("moves") or []:
        points = [p for p in move.get("points") or [] if _point(p)]
        if len(points) >= 2:
            events.append((float(move.get("at") if move.get("at") is not None else 0.3), list(points[0]), FOLLOW_SCALE,
                           (list(points[-1]), max(1.0, min(4.0, float(move.get("ms") or 3000) / 1000)))))
    for react in sentence.get("reacts") or []:
        if _point(react.get("at")):
            events.append((float(react.get("delay") or 0.3), list(react["at"]), REACT_SCALE, None))
    events.sort(key=lambda e: e[0])
    track = []
    if events:
        at, point, scale, follow = events[0]
        at = max(0.0, min(at - 0.3, dur - 1.0))
        track.append({"at": round(at, 2), "x": round(point[0], 1), "y": round(point[1], 1), "scale": round(scale, 2),
                      "ms": 1100})
        if follow and math.hypot(follow[0][0] - point[0], follow[0][1] - point[1]) > 8:
            track.append({"at": round(min(at + 0.6 * follow[1], dur - 0.8), 2), "x": round(follow[0][0], 1),
                          "y": round(follow[0][1], 1), "scale": round(scale, 2), "ms": round(follow[1] * 900)})
    if last:
        track.append({"at": round(max((track[-1]["at"] + 1.4) if track else 0.0, dur - 1.6), 2), "x": 50.0, "y": 50.0,
                      "scale": 1.0, "ms": 1400})
    return track[:3]


def said_at(names: list, roman: str, seconds: float) -> float | None:
    """The second of its sentence at which the voice first says one of ``names`` (a label, a molecule's name), from where
    the word sits in the line; None when the line never says it. Navin, 23 November 2026, on the two 11.6.3b films: the
    first explained the mechanism better because "bolte huye screen par wahi step par dhyan jata hai jo ho rha hai"."""
    low = _plain(roman or "").lower()
    if not low or seconds <= 0:
        return None
    found = []
    for name in names:
        for token in re.findall(r"[a-z0-9+\-]+", _plain(str(name or "")).lower()):
            if len(token) < 2 or token in SHORT_STOP:
                continue
            stem = token[:5] if len(token) > 5 and token.isalpha() else token
            pattern = (r"(?<![a-z0-9])" + re.escape(stem)) if stem[0].isalnum() else re.escape(stem)
            found += [m.start() for m in re.finditer(pattern, low)]
    if not found:
        return None
    return round(max(0.3, min(min(found) / len(low) * seconds - 0.2, seconds - 1.5)), 2)


def word_times(sentence: dict, roman: str, seconds: float) -> dict:
    """Each pin and each move of a sentence starts as the voice says its name (``at``, seconds); one the line never
    names keeps the player's own start."""
    pins, moves = [], []
    for pin in sentence.get("pins") or []:
        pin = {"t": pin["label"], "x": pin["x"], "y": pin["y"]}
        at = said_at([pin["t"]], roman, seconds)
        if at is not None:
            pin["at"] = at
        pins.append(pin)
    for move in sentence.get("moves") or []:
        move = dict(move)
        what = str(move.get("what") or "")
        at = said_at([move.get("label") or "", (KIT["molecules"].get(what) or {}).get("name") or "", what], roman, seconds)
        if at is not None:
            move["at"] = at
        moves.append(move)
    return {"pins": pins, "moves": moves}


def act_times(acts: list, names: dict, roman: str, seconds: float) -> list:
    """When each act starts, in seconds after its sentence starts: as the line names the part (a jaw closes as the voice
    says "beta kasta hai"), each act at least 1.2 s after the one before it (one thing at a time), and every act early
    enough to finish inside the sentence. Without the part's name in the line the acts are spread over the sentence."""
    low, out, last, cursor = _plain(roman or "").lower(), [], -1.2, 0
    n = max(1, len(acts))
    for i, act in enumerate(acts):
        act = dict(act)
        words = [w for w in _content_words(names.get(act.get("part")) or "") if len(w) > 2]
        found = [m.start() for w in words for m in re.finditer(re.escape(w), low) if m.start() >= cursor]
        guess = min(found) / max(1, len(low)) * seconds - 0.2 if found and low else seconds * (0.1 + 0.7 * i / n)
        if found:
            cursor = min(found) + 1
        at = min(max(0.3, guess, last + 1.2), max(0.3, seconds - 1.6))
        act["at"] = round(at, 2)
        last = at
        out.append(act)
    return out


def held(moves: list, seconds: float) -> list:
    """A move that would end long before its sentence does keeps flowing until the sentence ends (``hold``), then fades;
    it does not stay on into the next sentence the way ``loop`` does. The Q14 review: H+ flows of about 2 seconds stopped
    in sentences of 8 to 13 seconds, leaving a still picture."""
    out = []
    for move in moves:
        move = dict(move)
        count = max(1, min(12, int(move.get("count") or 1)))
        ms = max(800.0, float(move.get("ms") or 2400))
        if not move.get("loop") and ms * (1 + 0.85 * (count - 1) / count) < 0.6 * seconds * 1000:
            move["hold"] = True
        out.append(move)
    return out


def kit_for(shots: list) -> dict:
    """Only the kit molecules this film uses (the page stays small), with the element colours."""
    used = set()
    for shot in shots:
        for sentence in shot.get("sentences") or []:
            used.update(m.get("what") for m in sentence.get("moves") or [])
            for react in sentence.get("reacts") or []:
                used.update(x.get("what") for x in (react.get("inputs") or []) + (react.get("outputs") or []))
            for cycle in sentence.get("cycles") or []:
                for station in cycle.get("stations") or []:
                    used.update([station.get("becomes")] + list(station.get("takes") or []) + list(station.get("gives") or []))
            used.update(a.get("rider") for a in sentence.get("acts") or [] if a.get("rider"))
    return {"elements": KIT["elements"], "molecules": {k: v for k, v in KIT["molecules"].items() if k in used}}


def html(data: dict, template: str) -> str:
    from .studio_voice import with_player_voice
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return with_player_voice(template).replace("/*__FILM__*/null", blob, 1)


def coverage(film: dict, question: dict) -> dict:
    """Which film sentences teach each book line, what goes beyond the book, and the sentences that only join the story."""
    lines = question.get("book_lines") or []
    taught, beyond, bridges = {line["n"]: [] for line in lines}, [], []
    for _where, shot, sentence in _sentences(film if isinstance(film, dict) else {}):
        said = {"shot": shot.get("title") or shot.get("id") or "", "roman": sentence.get("roman") or "",
                "part": sentence.get("part") or ""}
        ns = [n for n in sentence.get("teaches") or [] if n in taught]
        for n in ns:
            taught[n].append(said)
        if (sentence.get("beyond") or "").strip():
            beyond.append(dict(said, note=sentence["beyond"].strip()))
        if not ns:
            bridges.append(said)
    unknown = []
    if question.get("chapter_terms"):
        for _where, _shot, sentence in _sentences(film if isinstance(film, dict) else {}):
            unknown += [t for t in studio_terms.unknown_terms(sentence.get("roman") or "", question["chapter_terms"])
                        if t not in unknown]
    rows = [{"n": line["n"], "page": line.get("page", ""), "text": line["text"], "film": taught[line["n"]]} for line in lines]
    parts = {}
    for _where, _shot, sentence in _sentences(film if isinstance(film, dict) else {}):
        if sentence.get("part") in PARTS:
            parts[sentence["part"]] = parts.get(sentence["part"], 0) + 1
    return {"rows": rows, "taught": sum(1 for r in rows if r["film"]), "total": len(rows), "beyond": beyond,
            "bridges": bridges, "unknown_terms": unknown, "parts": parts}


def coverage_page(film: dict, question: dict, *, chapter: str = "") -> str:
    """The NCERT-to-film page for Navin (a review page: it never reaches the learner's screen). Each book line with its
    printed page and the film sentences that teach it, then what the film says beyond the book."""
    import html as _h
    c = coverage(film, question)
    e = _h.escape
    pages = sorted({r["page"] for r in c["rows"] if r["page"]}, key=lambda p: (len(p), p))
    rows = []
    for r in c["rows"]:
        said = "".join(f'<li><span class="shot">{e(s["shot"])}</span> {e(s["roman"])}</li>' for s in r["film"])
        mark = '<b class="ok">✓</b>' if r["film"] else '<b class="no">✗ nahi padhaya</b>'
        rows.append(f'<tr><td class="pg">{e(r["page"])}</td><td class="book">{e(r["text"])}</td>'
                    f'<td>{mark}<ul>{said}</ul></td></tr>')
    tag = lambda s: f'<span class="part">{e(PART_NAMES.get(s.get("part"), ""))}</span> ' if s.get("part") in PART_NAMES else ""
    extra = "".join(f'<li>{tag(b)}{e(b["roman"])}<div class="note">{e(b["note"])}</div></li>' for b in c["beyond"]) or "<li>Kuch nahi.</li>"
    joins = "".join(f'<li>{tag(b)}<span class="shot">{e(b["shot"])}</span> {e(b["roman"])}</li>' for b in c["bridges"]) or "<li>Kuch nahi.</li>"
    shape = " · ".join(f"{PART_NAMES[p]}: {c['parts'][p]}" for p in PARTS if c["parts"].get(p))
    shape = f'<p class="sum">Film ka dhaancha: {e(shape)}</p>' if shape else ""
    terms = (f'<p class="sum">Kitab se bahar ke shabd (sirf jaankari, film inse rukti nahi): '
             f'{e(", ".join(c["unknown_terms"]))}</p>' if c["unknown_terms"] else "")
    title = f'{question.get("id", "")} · {question.get("question", "")}'
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCERT aur film</title><style>
:root{{--bg:#f7f5ef;--ink:#1d2326;--soft:#5d676b;--line:#ddd8cc;--ok:#1d7a46;--no:#b3261e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111719;--ink:#e8ecea;--soft:#9aa6a8;--line:#2a3538;--ok:#5cc98a;--no:#ff8a80;--card:#182023}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}main{{max-width:980px;margin:0 auto;padding:16px}}
h1{{font-size:1.25rem;margin:.2em 0}}h2{{font-size:1.05rem;margin:1.4em 0 .4em}}.sum{{color:var(--soft)}}
table{{width:100%;border-collapse:collapse;background:var(--card)}}td{{border-top:1px solid var(--line);padding:8px;vertical-align:top}}
td.pg{{white-space:nowrap;color:var(--soft);width:3em}}td.book{{width:45%}}ul{{margin:.3em 0 0;padding-left:1.1em}}.shot{{color:var(--soft);font-size:.85em}}
.ok{{color:var(--ok)}}.no{{color:var(--no)}}.note{{color:var(--soft);font-size:.9em}}.warn{{color:var(--no)}}
.part{{display:inline-block;font-size:.75em;border:1px solid var(--line);border-radius:6px;padding:0 5px;color:var(--soft)}}
@media (max-width:640px){{td{{display:block;width:auto!important;border-top:none}}tr{{display:block;border-top:1px solid var(--line);padding:6px 0}}}}
</style></head><body><main>
<p class="sum">BIE · {e(chapter)} · review page (learner ko nahi dikhta)</p>
<h1>{e(title)}</h1>
<p><b>{c["taught"]} / {c["total"]}</b> NCERT lines film mein padhayi gayi · NCERT page {e(", ".join(pages))}</p>{shape}{terms}
<table>{"".join(rows)}</table>
<h2>NCERT se bahar ki baat (BIE ne samjhane ke liye joda)</h2><ul>{extra}</ul>
<h2>Baaki lines (sawaal, pehle ki baat, kahan kaam aata hai; inmein koi NCERT line nahi)</h2><ul>{joins}</ul>
</main></body></html>"""


# --- labels placed on the picture they label (Navin's Q14 review, 20 November 2026: "stroma aur lumen dono pins left ke
# green granum stack par lag gaye", "facilitated diffusion pin right lipid bilayer par hai"). The maker writes every point
# before the picture exists, so the image model draws structures elsewhere. After each picture is made, a vision call sees
# it and moves each point onto the structure or route it names; the labels and the story do not change.

PLACE_INSTRUCTIONS = """You are BIE's layout checker for a teaching film. You see ONE picture of the film and the list of
things BIE will draw over it while the narration plays: labels (each with one point), arrows and moving paths (several
points in order), reactions (where they happen, where the inputs come from, where the products go), wheels (their
centre), camera targets and the point the next shot dives into. BIE wrote these points before the picture existed, so
some sit on the wrong structure. For every item give the points where it really belongs in THIS picture, x and y in
percent of the picture's width and height (0, 0 = top left): a label's point on the very structure it names (not on a
neighbour), a path along the real route through the real structures with the same number of points, a reaction where
the named part is, a camera target on the part the sentence talks about, the dive point on the structure the next shot
shows close up. Keep a point that is already right; keep labels 3 to 97; two labels of one sentence never point at the
same spot (a part inside another, such as the lumen inside a thylakoid, gets its own inner space). visible is false only
when the named structure is not in the picture at all.
BIE will also cut some parts out of the picture and move them (listed under "parts", with their name and how they were
meant to look). For each part give: inside, 2 to 5 points well inside the part itself (on its body, not on its edge,
spread over it; for a molecule drawn as separate balls, one point on each ball or group); outside, 1 to 3 points on the
neighbours that touch the part but are not it ([] when nothing touches it); box, [x0, y0, x1, y1] tight around the part
alone; visible false (and inside, outside, box []) when the part is not in the picture. Answer with the JSON object only."""

PLACE_SCHEMA = _obj({"items": _arr(_obj({"id": S, "points": _arr(_arr(N)), "visible": B})),
                     "parts": _arr(_obj({"id": S, "inside": _arr(_arr(N)), "outside": _arr(_arr(N)), "box": _arr(N),
                                         "visible": B}))})


def place_items(shot: dict, next_shot: dict | None = None) -> list:
    """Every point drawn over this shot's picture, as {id, what, said, points, set}; ``set`` writes corrected points back."""
    items = []

    def add(iid, what, said, points, setter):
        items.append({"id": iid, "what": what, "said": said, "points": [list(map(float, p)) for p in points], "set": setter})

    for k, s in enumerate(shot.get("sentences") or []):
        said = s.get("roman") or ""
        for j, p in enumerate(s.get("pins") or []):
            add(f"s{k}.pin{j}", f"label '{p.get('label')}'", said, [[p.get("x", 50), p.get("y", 50)]],
                lambda pts, p=p: p.update(x=pts[0][0], y=pts[0][1]))
        for j, a in enumerate(s.get("arrows") or []):
            add(f"s{k}.arrow{j}", f"arrow {a.get('label') or ''}".strip(), said, a.get("points") or [],
                lambda pts, a=a: a.update(points=pts))
        for j, m in enumerate(s.get("moves") or []):
            add(f"s{k}.move{j}", f"path of the moving {m.get('what')}", said, m.get("points") or [],
                lambda pts, m=m: m.update(points=pts))
        for j, g in enumerate(s.get("grows") or []):
            add(f"s{k}.grow{j}", f"growing line {g.get('label') or ''}".strip(), said, g.get("points") or [],
                lambda pts, g=g: g.update(points=pts))
        for j, r in enumerate(s.get("reacts") or []):
            add(f"s{k}.react{j}.at", f"where the reaction {r.get('label') or ''} happens".replace("  ", " "), said,
                [r.get("at") or [50, 50]], lambda pts, r=r: r.update(at=pts[0]))
            for i, x in enumerate(r.get("inputs") or []):
                add(f"s{k}.react{j}.in{i}", f"where {x.get('what')} comes from", said, [x.get("from") or [10, 50]],
                    lambda pts, x=x: x.update({"from": pts[0]}))
            for i, x in enumerate(r.get("outputs") or []):
                add(f"s{k}.react{j}.out{i}", f"where the product {x.get('what')} goes", said, [x.get("to") or [90, 50]],
                    lambda pts, x=x: x.update(to=pts[0]))
        for j, c in enumerate(s.get("cycles") or []):
            add(f"s{k}.cycle{j}", f"centre of the wheel {c.get('label') or ''}".strip(), said, [[c.get("x", 50), c.get("y", 50)]],
                lambda pts, c=c: c.update(x=_within(pts[0][0], c.get("rx")), y=_within(pts[0][1], c.get("ry"))))
        for j, f in enumerate(s.get("fuses") or []):
            add(f"s{k}.fuse{j}", f"where two parts become {f.get('label')}", said, [[f.get("x", 50), f.get("y", 50)]],
                lambda pts, f=f: f.update(x=pts[0][0], y=pts[0][1]))
        for j, e in enumerate(s.get("effects") or []):
            if e.get("type") in ("glow", "spin") and all(k in e for k in ("x0", "x1", "y0", "y1")):
                kind = "the turning part (a spin)" if e["type"] == "spin" else "the glowing part"
                add(f"s{k}.effect{j}", f"centre of {kind} this sentence talks about", said,
                    [[(e["x0"] + e["x1"]) / 2, (e["y0"] + e["y1"]) / 2]],
                    lambda pts, e=e: e.update(x0=e["x0"] + pts[0][0] - (e["x0"] + e["x1"]) / 2,
                                              x1=e["x1"] + pts[0][0] - (e["x0"] + e["x1"]) / 2,
                                              y0=e["y0"] + pts[0][1] - (e["y0"] + e["y1"]) / 2,
                                              y1=e["y1"] + pts[0][1] - (e["y0"] + e["y1"]) / 2))
        names = {p.get("id"): p.get("name") for p in (shot.get("visual") or {}).get("parts") or [] if isinstance(p, dict)}
        for j, a in enumerate(s.get("acts") or []):
            if a.get("do") in TOWARD and _point(a.get("toward")):
                where = {"open": "the point the part opens away from (the centre it closes onto)",
                         "tight": "the point the part closes onto", "stick": "the point the part slides to and joins",
                         "suck": "the part's opening that pulls the molecule in",
                         "grab": "the point where the part closes on the molecule it holds",
                         "carry": "where the part lets the molecule go, just past its far side (the side the molecule "
                                  "is carried to, such as the lumen below a proton pump)",
                         "leave": "where the part goes as it leaves", "arrive": "where the part comes in from"}[a["do"]]
                add(f"s{k}.act{j}", f"{where}: part '{names.get(a.get('part'), a.get('part'))}'", said, [a["toward"]],
                    lambda pts, a=a: a.update(toward=pts[0]))
        z = s.get("zoom") or {}
        if float(z.get("scale") or 1) > 1.05:
            add(f"s{k}.zoom", "camera target: the part this sentence talks about", said, [[z.get("x", 50), z.get("y", 50)]],
                lambda pts, z=z: z.update(x=pts[0][0], y=pts[0][1]))
    dive = (next_shot or {}).get("dive") or {}
    if next_shot and dive.get("x", -1) != -1:
        what = f"the point the next shot dives into: {next_shot.get('place') or next_shot.get('title') or ''}: " + \
               ((next_shot.get("visual") or {}).get("image_prompt") or "")[:220]
        add("dive", what, "", [[dive.get("x", 50), dive.get("y", 50)]], lambda pts, d=dive: d.update(x=pts[0][0], y=pts[0][1]))
    return items


def acted_parts(shot: dict) -> list:
    """The parts of this shot's picture that some sentence acts on: the ones worth cutting."""
    acted = {a.get("part") for s in shot.get("sentences") or [] for a in s.get("acts") or []}
    if (shot.get("visual") or {}).get("type") not in ("photo", "cutaway"):
        return []
    return [p for p in (shot.get("visual") or {}).get("parts") or [] if isinstance(p, dict) and p.get("id") in acted]


def place_messages(items: list, image_part: dict, parts: list = ()) -> list:
    listed = [{k: v for k, v in it.items() if k != "set"} for it in items]
    text = ("The picture is attached. The items BIE will draw over it, with the points BIE guessed:\n"
            + json.dumps(listed, ensure_ascii=False))
    if parts:
        text += ("\nThe parts BIE will cut out and move:\n"
                 + json.dumps([{"id": p.get("id"), "name": p.get("name"), "looks": p.get("looks")} for p in parts],
                              ensure_ascii=False))
    return [{"role": "system", "content": PLACE_INSTRUCTIONS},
            {"role": "user", "content": [{"type": "text", "text": text}, image_part]}]


def _within(centre, radius) -> float:
    """A wheel's centre moved by looking keeps its whole oval inside the picture (the first heading films, 23 November
    2026: the CF0 wheel was moved to x 80 with rx 20, off the picture's edge)."""
    r = float(radius or 0)
    return round(min(98.0 - r, max(2.0 + r, float(centre))), 1)


def apply_places(items: list, answer) -> dict:
    """Write the checker's points back where they are sound (same count, inside the picture); labels stay 3..97."""
    known = {it["id"]: it for it in items}
    moved, missing, refused = 0, [], 0
    for got in (answer or {}).get("items") or []:
        it = known.get(got.get("id"))
        pts = got.get("points")
        if not it or not isinstance(pts, list) or len(pts) != len(it["points"]) or not all(
                isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in p) for p in pts):
            refused += 1
            continue
        if ".pin" in it["id"]:
            pts = [[min(97.0, max(3.0, float(p[0]))), min(97.0, max(3.0, float(p[1])))] for p in pts]
        if [list(map(float, p)) for p in pts] != it["points"]:
            it["set"]([[round(float(v), 1) for v in p] for p in pts])
            moved += 1
        if got.get("visible") is False:
            missing.append(it["what"])
    return {"items": len(items), "moved": moved, "refused": refused, "missing": missing}


def pointed_parts(parts: list, answer) -> dict:
    """The checker's points for each part to cut, where they are sound: {id: {inside, outside, box}}; a part it could
    not see, or pointed at with no point inside the picture, is left out (the film plays it uncut)."""
    wanted = {p.get("id") for p in parts}
    found = {}
    for got in (answer or {}).get("parts") or []:
        pid = got.get("id")
        if pid not in wanted or got.get("visible") is False:
            continue
        inside = [list(map(float, q)) for q in got.get("inside") or [] if _point(q)][:6]
        outside = [list(map(float, q)) for q in got.get("outside") or [] if _point(q)][:4]
        box = got.get("box") or []
        box = [float(v) for v in box] if isinstance(box, list) and len(box) == 4 and all(
            isinstance(v, (int, float)) and 0 <= v <= 100 for v in box) and box[0] < box[2] and box[1] < box[3] else []
        if inside or box:
            found[pid] = {"inside": inside, "outside": outside, "box": box}
    return found


MOLECULE_WORDS = re.compile(r"\b(molecules?|ions?|atoms?|phosphates?)\b", re.I)


def _molecule_part(part: dict) -> bool:
    """A part that is a molecule (ADP + Pi, an ATP, an H+): cut from its points alone (bie/brain/picture_parts.py)."""
    words = {w.lower() for w in re.findall(r"[A-Za-z0-9+\-]+", _plain(f"{part.get('id') or ''} {part.get('name') or ''}"))}
    kit = {m.lower() for m in MOLECULES}
    return bool(words & kit) or bool(MOLECULE_WORDS.search(part.get("name") or ""))


def part_requests(shot: dict, pointed: dict) -> list:
    """What the cutter needs for each acted part the checker found: its points and box, whether it moves away from its
    place (so the picture needs a plate under it) and whether it is a molecule."""
    out = []
    for part in acted_parts(shot):
        got = (pointed or {}).get(part.get("id"))
        if not got:
            continue
        does = {a.get("do") for s in shot.get("sentences") or [] for a in s.get("acts") or [] if a.get("part") == part.get("id")}
        out.append({"id": part["id"], "inside": got.get("inside") or [], "outside": got.get("outside") or [],
                    "box": got.get("box") or [], "moves": bool(does & set(UNCOVERS)), "molecule": _molecule_part(part)})
    return out


def place(client, model: str, shot: dict, next_shot: dict | None, image_part: dict) -> dict:
    """One vision call: move this shot's points onto its picture, and point at the parts to cut. A failed call keeps the
    maker's points (and cuts no part)."""
    items = place_items(shot, next_shot)
    parts = acted_parts(shot)
    if not items and not parts:
        return {"items": 0, "moved": 0, "refused": 0, "missing": [], "usage": {}}
    try:
        reply = client.chat(model=model, messages=place_messages(items, image_part, parts), schema=PLACE_SCHEMA)
        answer = parse(reply.get("content", ""))
        result = apply_places(items, answer)
        if parts:
            result["parts"] = pointed_parts(parts, answer)
        result["usage"] = reply.get("usage") or {}
    except Exception as exc:                          # the film still plays with the maker's points; the report says so
        result = {"items": len(items), "moved": 0, "refused": 0, "missing": [], "error": str(exc)[:160], "usage": {}}
    return result


ACT_WORDS = {"turn": "ghoomta hai", "spin": "ghoomta rehta hai", "stop": "rukta hai", "open": "khulta hai",
             "loose": "dheela hota hai", "tight": "kasta hai (dabaav)", "squeeze": "dabta hai (sikudta, phir lautta)",
             "suck": "molecule ko andar kheenchta hai", "grab": "molecule ko pakad leta hai",
             "carry": "molecule ko pakadkar us paar chhodta hai",
             "stick": "khisak kar judta hai (jod par chamak)",
             "leave": "bahar nikal jaata hai", "arrive": "andar aata hai", "glow": "chamakta hai"}


def acts_page(film: dict, report: dict | None = None, *, question: dict | None = None, chapter: str = "") -> str:
    """Navin's review page of the parts that move (routeS, 23 November 2026: "har film ke har asar ki suchi"): for every
    picture with parts, each part and whether BIE cut it, then each line with what happens to which part while it is
    said. A review page: it never reaches the learner's screen."""
    import html as _h
    e = _h.escape
    report = report or {}
    cut = report.get("parts") or {}
    blocks, total, shown = [], 0, 0
    for number, shot in enumerate(film.get("shots") or [], 1):
        sid = shot.get("id") or f"shot {number}"
        parts = [p for p in (shot.get("visual") or {}).get("parts") or [] if isinstance(p, dict)]
        if not parts:
            continue
        names = {p.get("id"): p.get("name") or p.get("id") for p in parts}
        rows = []
        for p in parts:
            got = cut.get(f"{sid}.{p.get('id')}")
            if got is None:
                state = '<b class="no">nahi kata (tasveer mein nahi mila)</b>' if report else '<span class="sum">—</span>'
            elif got.get("problems"):
                state = f'<b class="no">saaf nahi kata: {e("; ".join(got["problems"]))}</b>'
            else:
                state = f'<b class="ok">kata</b> <span class="sum">{got.get("area")}% tasveer</span>'
                shown += 1
            total += 1
            rows.append(f'<li><b>{e(str(p.get("name")))}</b> <span class="sum">({e(str(p.get("looks") or ""))})</span> · {state}</li>')
        lines = []
        for k, sentence in enumerate(shot.get("sentences") or [], 1):
            acts = sentence.get("acts") or []
            what = "; ".join(f"{names.get(a.get('part'), a.get('part'))} {ACT_WORDS.get(a.get('do'), a.get('do'))}"
                             + (f" ({a.get('turns'):+g}°)" if a.get("do") == "turn" else "")
                             + (f", savaar {a.get('rider')}" if a.get("rider") else "") for a in acts)
            lines.append(f'<tr><td class="pg">{k}</td><td>{e(sentence.get("roman") or "")}</td>'
                         f'<td>{e(what) if what else "<span class=sum>—</span>"}</td></tr>')
        blocks.append(f'<h2>{e(sid)} · {e(shot.get("title") or "")}</h2><ul>{"".join(rows)}</ul>'
                      f'<table><tr><td class="pg">#</td><td><b>Line</b></td><td><b>Kya hilta hai</b></td></tr>{"".join(lines)}</table>')
    body = "".join(blocks) or "<p>Is film mein koi hissa nahi hilta.</p>"
    title = f'{(question or {}).get("id", "")} · {(question or {}).get("question", film.get("title", ""))}'
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hilte hisse</title><style>
:root{{--bg:#f7f5ef;--ink:#1d2326;--soft:#5d676b;--line:#ddd8cc;--ok:#1d7a46;--no:#b3261e;--card:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111719;--ink:#e8ecea;--soft:#9aa6a8;--line:#2a3538;--ok:#5cc98a;--no:#ff8a80;--card:#182023}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}main{{max-width:980px;margin:0 auto;padding:16px}}
h1{{font-size:1.25rem;margin:.2em 0}}h2{{font-size:1.05rem;margin:1.4em 0 .4em}}.sum{{color:var(--soft)}}
table{{width:100%;border-collapse:collapse;background:var(--card)}}td{{border-top:1px solid var(--line);padding:8px;vertical-align:top}}
td.pg{{white-space:nowrap;color:var(--soft);width:2em}}.ok{{color:var(--ok)}}.no{{color:var(--no)}}ul{{padding-left:1.1em}}
</style></head><body><main><p class="sum">{e(chapter)} · review page (learner ko nahi dikhta)</p><h1>Hilte hisse: {e(title)}</h1>
<p class="sum">Tasveeron se kate hisse: {shown} / {total}</p>{body}</main></body></html>"""

