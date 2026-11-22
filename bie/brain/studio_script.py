"""The chapter's script: the whole chapter taught once, in one teacher's own words, before any video, note or game is
made (Navin, 22 November 2026).

Navin: "maan lo maine chapter ko poora padh liya hai, mai BIE hun ... mai apni ek script banaunga poore chapter par kyunki
mujhe poora chapter yaad hai; kitab mein jo cheezen hain unhe aapas mein jodke poore chapter ko kaise progress karna hai
link karke poore ek chapter ki script banaunga; phir video maker us script ke hisab se poore chapter ko video ke tukdon
mein baantega". And: "script wo poora gyan hai jo hume bache ko dena hai; notes us gyan ko behtar dhang se organise karke
present karne ka tarika hai" (the script is the knowledge; video, notes and games each present it in their own way and
never write their own story); "chapter 11 ki saari cheezen bache ko samajh aa jaayein, aage wo koi is par based deep book
bhi padhe to wo book use samajh aa jaaye". Card, 22 November 2026: "Poora chapter ek saath".

Input: Section 1's chapter map (``chapter_map.json``), given whole as the chapter file (``chapter_file.markdown``), and,
when the from-run is a naksha run, its two plans (``naksha.json``) as ideas for each heading (not the cut into videos).

How: the script is written heading by heading in the book's order (the opening, 11.1, 11.2 ... 11.10.4). Every call gets
the whole chapter file, the whole script written so far, the terms, analogies and examples already used, this heading's
items and the plan ideas, so one teacher with one memory writes the whole chapter. Each heading's part is checked by code
before the next is written (problems go back, at most ``max_rounds``):

* NCERT line by line: every teachable body item of the heading is in the "teaches" of exactly one point, and the point
  speaks at least one of its key words; no item of another heading, no unknown id.
* Terms: every short form or formula the chapter opens (★) in this heading's items is opened here with its meaning, and
  every other first term is at least said where its line is taught; a term opened earlier is never defined again; a short
  form of a later heading is not used before it is opened (a pointer such as "aage dekhenge" is fine).
* No repetition: no sentence says again what an earlier sentence of the script said; an analogy or an example is used
  once in the chapter; a real-world use is a thing in life, not a study task.
* The teacher's voice: Roman script, sentences under 40 words, a screen line per point (what explains the words), never a
  caution line, never the book named to the learner; knowledge points of at most 8 sentences.
* Examples, analogies, real world (round 1 of Chapter 11 had 0 analogies and 1 real-world use in 154 points): a worked
  example in every heading of three or more items; an analogy and a real-world use wherever the plan offered one.
* Code repairs what it can before checking (the section, a recall that names an item id).
* The teacher study (Navin, 22 November 2026, after four YouTube teachers of Chapter 11 were read line by line and
  measured: their sentences are questions 18-35 % of the time, BIE's round 1 4 %; every process is told as steps first,
  then each step, then the whole again; card "Haan, isi kram se"): every heading opens with its goal, about one sentence
  in five asks the learner something (at least one "kyun"), a process heading has an overview and a retell and says the
  counts that change, a misconception the chapter file marks is said and corrected, the bridge names the link to the next
  heading, no known teacher slip is said, and no sentence is a fragment of three words or fewer (Navin, 22 November 2026,
  after hearing "पानी से।" said alone: "chhote vakya se baat tooti tooti lagegi"; an answer repeats its subject and a
  thinking question's answer flows from cause to conclusion in one sentence).

Output: ``script.json`` (the parts, each point with its id "11.6.1-k3": the knowledge points that video, notes and games
will account for), ``SCRIPT.md`` and ``SCRIPT.html`` (Navin's script page: each heading's script beside the NCERT lines
it teaches), ``record.json`` (rounds and problems per heading).
"""
from __future__ import annotations

import html as html_module
import json
import math
import re

from . import chapter_file, studio_naksha
from .studio import parse
from .studio_book import CAUTION
from .studio_film import _content_words, _spoken_words

KINDS = ("explain", "question", "checkpoint", "example", "analogy", "real_world", "recall", "activity", "story", "figure",
         "summary", "overview", "retell")
RECAP = "recap"                # the chapter's closing heading, from the summary's items (ChatGPT's audit of round 1)
CHECKPOINT_FROM = 3            # a heading with this many items stops once for the learner to think (predict, then reason)
MAX_WORDS = 40                 # words in one spoken sentence (Navin's Hinglish rule, Task 045)
SAME_SENTENCE = 0.6            # share of shared words above which a sentence says again what another said
SAME_ANALOGY = studio_naksha.SAME_ANALOGY
SAME_EXAMPLE = 0.6
WORDS_PER_MINUTE = 130         # spoken Hinglish
MAX_SENTENCES = 8              # sentences in one knowledge point (round 1 of Chapter 11: up to 16 in one point)
EXAMPLE_FROM = 3               # a heading with this many items needs at least one worked example
# the book named on the learner's screen (round 1 of Chapter 11: 24 lines such as "Book ise ... kehti hai")
BOOK_NAMED = re.compile(r"(?i)\b(book|books|textbook|ncert|kitab|kitaab|lekhak|campbell|according to the (text|author))\b")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
FORWARD = re.compile(r"\b(aage|baad mein|baad me|agle|aane wale|later|next)\b", re.I)
WORD = re.compile(r"[A-Za-z]{3,}")
FILLER = studio_naksha.FILLER | {"hum", "hai", "hain", "toh", "tho", "yeh", "woh", "kya", "nahi", "bhi", "kar", "karta",
                                 "karte", "karti", "hota", "hoti", "hote", "this", "that", "here"}
# The teacher study of Chapter 11 (22 November 2026): four teachers' sentences were questions 18-35 % of the time
# (Roshni 35 %, 31 %, Vipin 18 %); BIE's round 1 was 4 %.
QUESTION_SHARE = 0.15          # at least this share of a heading's sentences asks the learner something
QUESTIONS_FROM = 8             # ... in a heading of at least this many sentences
WHY = re.compile(r"\b(kyun|kyon|kyu|kyoon|why)\b", re.I)
FRAGMENT = 3                   # a sentence of this many words or fewer is a fragment (Navin, 22 Nov: "tooti tooti lagegi")
PROCESS_FROM = 3               # a heading with this many teachable process items is a process heading: overview, retell
SENTENCE = re.compile(r"(?<=[.?!])(?<!\b[A-Z]\.)\s+")   # never after an initial ("J.A. Bassham", "T.W. Engelmann")
COUNT = re.compile(r"\d|\b(ek|teen|chaar|char|paanch|panch|chhe|chhah|chheh|saat|aath|nau|das|baarah|barah|athaarah|"
                   r"atharah|one|two|three|four|five|six|seven|eight|nine|ten|twelve|eighteen|dono|teeno|chaaron)\b", re.I)
MISCONCEPTION = re.compile(r"\b(log|aksar|zyadatar|bahut se|kai)\b.{0,60}\b(sochte|samajhte|maante|lagta)\b|galat ?fa?h?e?mi|"
                           r"galat samajh|aisa nahi|asal mein|asli baat|confus|misconception", re.I)
NEGATION = re.compile(r"\b(nahi|nahin|na|not|never|galat|stable|sthir)\b", re.I)
# slips the four teachers made that BIE must never make (the teacher study): (name, pattern, flagged only when the
# sentence has no negation, the correct form)
TRAPS = (
    ("oxygen-18 called radioactive", re.compile(r"(o-?18|oxygen-?18|18o|¹⁸o|o¹⁸).{0,60}radioactiv|radioactiv.{0,40}(o-?18|"
                                                 r"oxygen-?18|¹⁸o|o¹⁸)", re.I), True,
     "oxygen-18 is a heavy, stable isotope, not radioactive"),
    ("the dark reaction put at night", re.compile(r"\b(dark reaction|biosynthetic phase)\b.{0,60}\b(raat|night)\b", re.I), True,
     "it does not need darkness; it runs on the light reaction's ATP and NADPH"),
    ("the Calvin cycle releasing CO2", re.compile(r"\bcalvin\b.{0,80}\b(co2|co₂|carbon dioxide)\b.{0,30}\b(nikal|release|chhod)",
                                                  re.I), True,
     "the Calvin cycle releases no CO2; the fixed carbon leaves as a triose phosphate sugar"),
    ("pigments separated by weight", re.compile(r"\b(chromatograph\w*|pigment\w*)\b.{0,80}\b(bhaari|bhari|heavy|heavier|weight|"
                                                 r"wazan|vazan)\b", re.I), True,
     "they separate by how they dissolve in the solvent and stick to the paper, not by weight"),
    ("C4 plants storing CO2 and opening stomata once", re.compile(r"\bc4\b.{0,80}\b(store|jama karke|jamaa)\b.{0,40}\b(co2|co₂)|"
                                                                  r"\bc4\b.{0,80}\bstomata\b.{0,40}\b(ek baar|once)\b", re.I),
     True, "that is CAM; C4 plants concentrate CO2 around RuBisCO in the bundle sheath"),
    ("light saturation at 1 % of sunlight", re.compile(r"\b1 ?(?:%|percent\b|pratishat\b)", re.I), True,
     "light saturates at about 10 per cent of full sunlight"),
    ("temperature not affecting the light reaction", re.compile(r"\blight reactions?\b.{0,60}\b(temperature|taapmaan|tapman)\b"
                                                                 r".{0,40}\b(asar nahi|farak nahi|fark nahi|affect nahi|no effect)",
                                                                 re.I), False,
     "the light reaction is temperature sensitive too, only much less than the enzyme reactions"),
    ("360 and 450 called compensation points", re.compile(r"compensation.{0,60}\b(360|450)\b|\b(360|450)\b.{0,60}compensation",
                                                          re.I), False,
     "360 and 450 µL/L are where C4 and C3 photosynthesis saturate"),
    ("pheophytin called a protein", re.compile(r"\bpheophytin\b.{0,40}\b(protein|chlorophyll b)\b", re.I), True,
     "pheophytin is chlorophyll a without its magnesium"),
    ("NADP reductase giving the electron", re.compile(r"\bnadp\+? reductase\b.{0,40}\belectrons?\b.{0,20}\b(deta|deti|de deta|"
                                                      r"donate)", re.I), True,
     "the electron comes from ferredoxin; the enzyme only makes the reaction go"),
)

S = {"type": "string"}


def _obj(properties: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


POINT = _obj({
    "id": S,
    "kind": {"type": "string", "enum": list(KINDS)},
    "teaches": _arr(S),
    "recalls": _arr(S),
    "says": _arr(S),
    "screen": S,
    "terms": _arr(_obj({"term": S, "meaning": S})),
    "outside_book": S,
    "prepares": _arr(S),
    "answer": S,
    "watch_out": S,
})
SCHEMA = _obj({"section": S, "goal": S, "points": _arr(POINT), "bridge": S})

RULES = """You are BIE's teacher: the best {subject} teacher for {learners} ({exam}). You have read the whole chapter and
you now write its script: everything the learner must come to know, taught once, in your own words, in the book's order,
each idea linked to what came before. Videos, notes and games are made from this script later (each presents the same
knowledge in its own way), so the script holds the knowledge fully; never write shot directions or "is video mein" in what
you say.

Navin's words for the script (22 November 2026): the teacher explains every single thing of the chapter in his own words,
in the right order, so that the whole chapter makes sense to the learner, and the base is so sound that a deeper book on
the same topic would make sense to them later.

You write the script one heading at a time; this message asks for one heading. You see the whole chapter file (every item
with its id, role, terms, why steps and what comes first), the script written so far, and ideas from the teaching plan.
Continue as the same teacher: same voice, never repeating what the script already said.

Rules:
- NCERT line by line: every item id listed for this heading is in the "teaches" of exactly one point. Teach each line by
  what it does: an in_text_question is posed and answered; reader_talk ("Let us see how this happens") is said in your own
  words; an activity is a task the learner can do or watch; a biography is a short story moment; a figure is walked
  through, label by label (kind "figure"). Use the book's key words when you teach its line.
- Explain, do not restate: the why steps, cause and effect, what must come first. When an earlier point taught what is
  needed, remind in one short sentence and name it in "recalls": the id of a point of an earlier heading as THE SCRIPT SO
  FAR shows it (like 11.5-k4), never an item id; when nothing earlier taught it, teach it briefly and say so in
  outside_book.
- Terms: open each term marked ★ in this heading's items at its first use, with its meaning in simple words ("terms").
  Never define again a term the script already opened: remind in a few words. Do not use a technical term of a later
  heading before it is opened, except as a pointer ("isko aage dekhenge").
- Examples (kind "example"): a concrete case worked through: a named plant or experiment, a number, one molecule followed.
  Every heading with three or more items has at least one. Analogies (kind "analogy"): an everyday picture for a hard
  idea, never one the script already used; when the plan's ideas for this heading offer an analogy, the heading has one
  (that one or a better one). Real-world uses (kind "real_world"): a real thing, place or happening in food, farming,
  health, weather or technology; never a study task or an exam trap; when the plan's ideas offer one, the heading has
  one; otherwise leave it out rather than invent one.
  An analogy is told fully and vividly, the way a good teacher tells it, for the hard ideas (not in every point), and it
  says its mapping in plain words as part of the telling ("H⁺ ions yahan paani hain, aur membrane hamara baandh");
  that is enough for the learner (Navin, 22 November 2026: "analogy ko sahi tarike se bolna hi kaafi hai"). "answer"
  records the mapping; "watch_out" records where the picture stops being true, for notes, games and checks only: it is
  never said in the telling.
- Checkpoints (kind "checkpoint"): every heading with three or more items stops at least once for the learner to think:
  ask what will happen or why ("socho, phir aage badhenge"), then reason it out; "answer" holds the reasoning the learner
  should reach and "watch_out" a common wrong idea and why it is wrong. Videos pause there, games ask it, notes keep the
  wrong idea. At least one per such heading, not many: the video should not stop all the time.
- Exercises (THE CHAPTER'S EXERCISES below): the script does not solve them (games and notes do), but it holds the
  knowledge to answer every one of them. When a point gives that knowledge, list the exercise ids in "prepares"; when an
  exercise needs something the body of the book never teaches (why a leaf kept in the dark turns yellow, why a shade leaf
  is darker green), teach it in the heading where it belongs and mark it in outside_book.
- An activity or a table the book asks the learner to do or fill is done and filled here, with the reason for each
  answer; the game turns it into a task later.
- A cycle or pathway is accounted for in matter as well as energy: what goes in, what comes out, what is regenerated
  (carbon by carbon), as a worked ledger.
- A figure is taught by its teaching labels; never describe decoration, clothing or how a portrait looks.
- The book's slips are not copied (for example NAD/NADH where the chapter means NADP/NADPH): teach the correct form.
- Knowledge points are small: one idea each, at most {max_sentences} sentences; split a long explanation into several
  points.
- Never name the book, NCERT or an author to the learner ("book kehti hai", "NCERT mein likha hai"): say it as your own
  teaching.
- Depth: NEET depth where the chapter file marks exam high or deep; a sound base everywhere.
- Outside the book is welcome where it makes the concept clearer; name what you added in outside_book.
- "screen": for every point, what the screen shows while it is said (a photo, a diagram, a table, an equation): what
  explains the words. A process or cycle taught over several points is built on the same realistic picture step by
  step, as it is followed: each point adds only its own step and the earlier steps stay quiet, never a finished
  crowded picture first (Navin, 22 November 2026: the Calvin cycle drawn as it is followed, on the photorealistic
  picture, not a flat 2D diagram, so the last screen is never a khichdi of molecules). Never a caution line ("assume", "illustrative", "the source does not say") in says or screen.
- Voice: {language} in Roman script with the book's English terms; a warm spoken teacher (questions, "socho", "dekho");
  every sentence under {max_words} words.
- How good teachers of this chapter teach (Navin, 22 November 2026, after four teachers were studied line by line):
  - "goal": the line this heading opens with: what we want to find or make here, and how it follows from what came
    before. Say it as the first sentence of the first point.
  - Ask the learner: about one sentence in five is a question, at least one a "kyun"; answer it at once, or after
    "socho" when the learner should think first. Voice the learner's own doubt ("ab aap sochoge, phir NADPH ka kya?").
  - A process (several steps): first an "overview" point that names the steps with their count ("yahan teen kaam hote
    hain: …"), then the steps, then a "retell" point that tells the whole process again in order, in a few sentences.
    Say the counts that change (carbons, electrons, protons, ATP and NADPH) before and after.
  - Open a compound name by its parts when the parts help the learner (photo + lysis = light + splitting; Kranz =
    wreath).
  - Where the chapter file marks a line "deep: misconception", say the common wrong idea and correct it in your words
    ("aksar log sochte hain ki …, par asal mein …").
  - An experiment is a story: the question the scientist asked, the setup, what was seen, what it proved. Before the
    experiments, say what will count as proof (oxygen bubbles, starch turning blue-black).
  - For an idea about amounts (a limiting factor, a ratio), choose an everyday analogy with numbers (a factory where
    the scarcest part decides how many finished pieces come out).
  - Flowing answers (Navin, 22 November 2026, on hearing "Paani se." said alone: "chhote vakya se baat tooti tooti
    lagegi"): never a sentence of three words or fewer. An answer repeats its subject ("Woh aati hai paani se", not
    "Paani se."). The answer to a thinking question starts with "Dekho," and joins cause to conclusion in one sentence
    ("…, aur woh oxygen chhodte hi nahi, jiska matlab hai ki oxygen paani se hi aati hai").
  - Never say these slips, which teachers of this chapter make: oxygen-18 is radioactive; the dark reaction happens at
    night; the Calvin cycle releases CO2; pigments separate by weight; C4 plants store CO2 and open their stomata once;
    light saturates at 1 % of sunlight; temperature does not affect the light reaction; 360 and 450 are compensation
    points; pheophytin is a protein; NADP reductase gives the electron.
- "bridge": one line that leads into the next heading and names the link: a problem and its cure, a need and what meets
  it (empty only for the last heading).
- The last heading, "recap", is the chapter's closing: it teaches the summary's lines as one connected picture (energy,
  electrons, protons and carbon, each traced end to end), recalls the points it rests on, and prepares every exercise no
  earlier point prepared.

Ids: points {tag}-k1, {tag}-k2 ... in order. Answer with the JSON object only."""

PROBLEMS_PROMPT = ("BIE's code checked this heading's script and found these problems. Send the whole corrected JSON object "
                   "for this heading again, changing only what the problems need:\n- ")


def tag(section: str) -> str:
    return section or "0"           # the recap heading's points are recap-k1, recap-k2 ...


def headings(chapter: dict) -> list:
    """The body headings in the book's order that have items to teach: [{"number", "title", "items": [ids]}]."""
    wanted = set(studio_naksha.coverable(chapter))
    out = []
    for section in chapter_file.build(chapter)["sections"]:
        if section["zone"] != "body":
            continue
        ids = [row["id"] for row in section["items"] if row["id"] in wanted]
        if ids:
            out.append({"number": section["number"], "title": section["title"] or ("Opening" if not section["number"] else ""),
                        "items": ids, "rows": section["items"]})
    summary = studio_naksha.zone_items(chapter, "summary")
    if summary:
        rows = [row for section in chapter_file.build(chapter)["sections"] if section["zone"] == "summary"
                for row in section["items"] if row["id"] in summary]
        out.append({"number": RECAP, "title": "Poore chapter ki tasveer (summary)", "items": summary, "rows": rows})
    return out


def exercises(chapter: dict) -> list:
    """The chapter's exercise items, the knowledge for which the script must hold."""
    return studio_naksha.zone_items(chapter, "exercise")


def first_terms(heading: dict) -> list:
    """The terms the chapter opens (★) in this heading's items: [(term, item id)]."""
    return [(t["term"], row["id"]) for row in heading["rows"] for t in row.get("terms") or [] if t.get("first_here")]


def _technical(term: str) -> bool:
    """A short form or formula (PS II, ATP, RuBP, 3-PGA, CO₂, H⁺) in a term of at most three words: it must be opened
    with its meaning and never used before. Section 1 also marks plain words as first terms ("regenerated", "turn"); those
    only need to be said where their line is taught (the Chapter 11 map, 22 November 2026: 39 marked terms in the opening)."""
    term = term.strip()
    return 0 < len(term.split()) <= 3 and (sum(c.isupper() for c in term) >= 2 or any(c.isdigit() or c in "+⁺₀₁₂₃₄₅₆₇₈₉"
                                                                                      for c in term))


def _words(text: str) -> set:
    return {w for w in WORD.findall((text or "").lower()) if w not in FILLER}


def _same(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b))


def _overlap(a: set, b: set) -> float:
    return len(a & b) / max(1, min(len(a), len(b)))


def _term_in(term: str, text: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(_plain(term)) + r"(?![a-z0-9])", _plain(text)))


PLAIN = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "01234567890123456789+-")


def _plain(term: str) -> str:
    """CO₂ and CO2, H⁺ and H+ are one term."""
    return " ".join((term or "").translate(PLAIN).casefold().split())


def _same_term(a: str, b: str) -> bool:
    a, b = _plain(a), _plain(b)
    return bool(a) and bool(b) and (a == b or (len(a) >= 4 and len(b) >= 4 and (a in b or b in a)))


def unprepared(chapter: dict, parts: list) -> list:
    """The exercises no point of ``parts`` prepares."""
    done = {x for part in parts for p in part.get("points") or [] for x in p.get("prepares") or []}
    return [x for x in exercises(chapter) if x not in done]


def memory(parts: list) -> dict:
    """What the script so far has used: terms opened, sentences said, analogies and examples, point ids."""
    out = {"terms": {}, "sentences": [], "analogies": [], "examples": [], "points": set()}
    for part in parts:
        for point in part.get("points") or []:
            pid = point.get("id")
            out["points"].add(pid)
            for t in point.get("terms") or []:
                out["terms"].setdefault(_plain(t.get("term") or ""), pid)
            for sentence in point.get("says") or []:
                out["sentences"].append((pid, _words(sentence)))
            if point.get("kind") == "analogy":
                out["analogies"].append((pid, _words(" ".join(point.get("says") or []))))
            if point.get("kind") == "example":
                out["examples"].append((pid, _words(" ".join(point.get("says") or []))))
    return out


def repair(answer, heading: dict, earlier: list):
    """What code can put right without asking again (round 1 of Chapter 11: every heading went back once, 136 times for a
    recall naming an item id and 20 times for the section's own number): the section is set to the heading, a recall of
    an item id becomes the earlier point that taught that item, and a recall of this heading's own point is dropped."""
    if not isinstance(answer, dict):
        return answer
    taught_by = {i: p.get("id") for part in earlier for p in part.get("points") or [] for i in p.get("teaches") or []}
    earlier_points = memory(earlier)["points"]
    own = f"{tag(heading['number'])}-k"
    for p in answer.get("points") or []:
        if not isinstance(p, dict):
            continue
        fixed = []
        for r in p.get("recalls") or []:
            r = taught_by.get(r, r) if r not in earlier_points else r
            if isinstance(r, str) and r.startswith(own):
                continue
            if r not in fixed:
                fixed.append(r)
        p["recalls"] = fixed
    return dict(answer, section=heading["number"])


def sentences(point: dict) -> list:
    """The spoken sentences of a point: a "says" line may hold more than one ("Protons kahan jaate hain? Lumen mein.")."""
    return [s.strip() for line in point.get("says") or [] for s in SENTENCE.split(line or "") if s.strip()]


def process_items(heading: dict, chapter: dict) -> list:
    items = chapter.get("items") or {}
    return [i for i in heading["items"] if (items.get(i) or {}).get("content_type") == "process"]


def teacher_problems(answer: dict, heading: dict, chapter: dict, points: list) -> list:
    """The teacher study's rules (Navin, 22 November 2026): goal first, questions, a process told as overview, steps and
    retell with its counts, a marked misconception said and corrected, a bridge that names the link, no fragment, no
    known teacher slip."""
    out = []
    items = chapter.get("items") or {}
    number = heading["number"]
    goal = (answer.get("goal") or "").strip()
    if not goal:
        out.append("\"goal\" is empty: the line this heading opens with (what we find or make here and how it follows "
                   "from what came before)")
    elif _words(goal) and len(_words(goal) & _words(" ".join(points[0].get("says") or []))) < 0.6 * len(_words(goal)):
        out.append(f"{points[0].get('id')}: open the heading with its goal (say \"{goal[:90]}\" as the first sentence)")
    said = [(p.get("id"), k, s) for p in points for k, s in enumerate(sentences(p), 1)]
    if len(said) >= QUESTIONS_FROM:
        asked = [s for _, _, s in said if s.endswith("?")]
        if len(asked) < QUESTION_SHARE * len(said):
            out.append(f"{len(asked)} of {len(said)} sentences ask the learner something; a teacher asks about one in five "
                       f"(at least {math.ceil(QUESTION_SHARE * len(said))} here): pose the learner's question, then "
                       "answer it")
        if not any(WHY.search(s) for s in asked):
            out.append("no \"kyun\" question in this heading: ask why at least once, then reason it out")
    for pid, k, s in said:
        if len(s.split()) <= FRAGMENT and not s.rstrip().endswith("?"):      # "Kyun?" is a teacher's question
            out.append(f"{pid} sentence {k}: {s!r} is a fragment; say a full sentence (an answer repeats its subject: "
                       "\"Woh aati hai paani se\", not \"Paani se.\")")
        for name, pattern, plain_only, right in TRAPS:
            if pattern.search(s) and not (plain_only and NEGATION.search(s)):
                out.append(f"{pid} sentence {k}: this says a known slip ({name}); correct: {right}")
    steps = process_items(heading, chapter)
    at = [n for n, p in enumerate(points) if set(p.get("teaches") or []) & set(steps)]
    if number != RECAP and len(steps) >= PROCESS_FROM and at:
        kinds = [p.get("kind") for p in points]
        if "overview" not in kinds or kinds.index("overview") > min(at):
            out.append("this heading teaches a process: before its steps, an \"overview\" point names the steps with their "
                       "count")
        if "retell" not in kinds or len(kinds) - 1 - kinds[::-1].index("retell") < max(at):
            out.append("this heading teaches a process: after its steps, a \"retell\" point tells the whole of it again in "
                       "order, in a few sentences")
        if not any(COUNT.search(s) for _, _, s in said):
            out.append("this process heading says no count: say what changes, before and after (carbons, electrons, "
                       "protons, ATP and NADPH)")
    marked = [i for i in heading["items"] if (items.get(i) or {}).get("teach_depth") == "deep"
              and (items.get(i) or {}).get("deep_why") == "misconception"]
    if marked and not any(MISCONCEPTION.search(s) for _, _, s in said):
        out.append(f"the chapter file marks a common wrong idea here ({', '.join(marked[:4])}); say it and correct it "
                   "(\"aksar log sochte hain ki …, par asal mein …\")")
    last = headings(chapter)[-1]["number"]
    if number != last and not (answer.get("bridge") or "").strip():
        out.append("\"bridge\" is empty: one line into the next heading that names the link (a problem and its cure, a need "
                   "and what meets it)")
    return out


def problems(answer, heading: dict, chapter: dict, earlier: list, later_terms: list, ideas: dict | None = None,
             open_exercises: list | None = None) -> list:
    """What this heading's part gets wrong, in words the maker can act on. ``earlier``: the parts already written;
    ``later_terms``: the technical terms the chapter opens in later headings; ``ideas``: what the plan offered for this
    heading ({"analogy": bool, "real_world": bool}); ``open_exercises``: for the recap, the exercises no earlier point
    prepared."""
    if not isinstance(answer, dict):
        return ["the answer is not one JSON object"]
    items = chapter.get("items") or {}
    number = heading["number"]
    points = [p for p in answer.get("points") or [] if isinstance(p, dict)]
    out = []
    if not points:
        return out + ["no points"]
    ids = [p.get("id") for p in points]
    if ids != [f"{tag(number)}-k{n}" for n in range(1, len(points) + 1)]:
        out.append(f"point ids must be {tag(number)}-k1, {tag(number)}-k2 ... in order")
    before = memory(earlier)
    exercise_ids = set(exercises(chapter))
    taught = {}
    for p in points:
        pid = p.get("id")
        for iid in p.get("teaches") or []:
            if iid not in items:
                out.append(f"{pid}: teaches {iid!r}, which is not an item of the chapter file")
            elif iid not in heading["items"]:
                out.append(f"{pid}: teaches {iid}, which is not an item of this heading ({number or 'the opening'}); "
                           "teach only this heading's items")
            elif iid in taught:
                out.append(f"{iid} is taught twice ({taught[iid]} and {pid}); teach it once")
            else:
                taught[iid] = pid
                words = _content_words(items[iid].get("content", ""))
                if words and not words & _spoken_words(" ".join(p.get("says") or [])):
                    out.append(f"{pid}: teaches {iid}, but none of its key words is said there: "
                               f"{items[iid].get('content', '')[:110]}")
        if not p.get("says"):
            out.append(f"{pid}: says nothing")
        if len(p.get("says") or []) > MAX_SENTENCES:
            out.append(f"{pid}: {len(p['says'])} sentences; a knowledge point holds one idea in at most {MAX_SENTENCES}: "
                       "split it into several points")
        for k, sentence in enumerate(p.get("says") or [], 1):
            if BOOK_NAMED.search(sentence or ""):
                out.append(f"{pid} sentence {k}: names the book ({BOOK_NAMED.search(sentence).group(0)!r}); say it as your "
                           "own teaching")
            if DEVANAGARI.search(sentence or ""):
                out.append(f"{pid} sentence {k}: write it in Roman script")
            if len((sentence or "").split()) > MAX_WORDS:
                out.append(f"{pid} sentence {k}: {len(sentence.split())} words; keep every sentence under {MAX_WORDS}")
            if CAUTION.search(sentence or ""):
                out.append(f"{pid} sentence {k}: a caution line never reaches the learner; say it as a teacher")
        if not (p.get("screen") or "").strip():
            out.append(f"{pid}: needs its screen line (what the screen shows while this is said)")
        elif CAUTION.search(p.get("screen") or ""):
            out.append(f"{pid}: the screen line has a caution line; show what explains the words")
        for r in p.get("recalls") or []:
            if r not in before["points"]:
                out.append(f"{pid}: recalls {r!r}, which is not a point of an earlier heading")
        bad = [x for x in p.get("prepares") or [] if x not in exercise_ids]
        if bad:
            out.append(f"{pid}: prepares {bad}, which are not exercise items of the chapter")
        if p.get("kind") in ("checkpoint", "analogy"):
            what = ("the reasoning the learner should reach" if p.get("kind") == "checkpoint" else "what maps to what")
            limit = ("a common wrong idea and why it is wrong" if p.get("kind") == "checkpoint"
                     else "where the picture stops being true")
            if not (p.get("answer") or "").strip():
                out.append(f"{pid}: a {p.get('kind')} needs \"answer\": {what}")
            if not (p.get("watch_out") or "").strip():
                out.append(f"{pid}: a {p.get('kind')} needs \"watch_out\": {limit}")
        if p.get("kind") == "real_world":
            task = studio_naksha.STUDY_TASK.search(" ".join(p.get("says") or []))
            if task:
                out.append(f"{pid}: this real-world point is a study task ({task.group(0)!r}); name where the learner meets "
                           "it in life, or leave the point out")
    missing = [iid for iid in heading["items"] if iid not in taught]
    if missing:
        out.append(f"{len(missing)} items of this heading are in no point's teaches: " + ", ".join(missing))
    out += teacher_problems(answer, heading, chapter, points)
    kinds = {p.get("kind") for p in points}
    if number == RECAP:
        prepared = {x for p in points for x in p.get("prepares") or []}
        left = [x for x in open_exercises or [] if x not in prepared]
        if left:
            out.append(f"{len(left)} exercises are prepared by no point of the script: {', '.join(left)}; give each the "
                       "knowledge it needs here (outside_book where the book's body never teaches it) and list it in prepares")
    elif len(heading["items"]) >= CHECKPOINT_FROM and "checkpoint" not in kinds:
        out.append("this heading needs at least one checkpoint (kind checkpoint): ask the learner to predict or reason, "
                   "then reason it out, with answer and watch_out")
    if number != RECAP and len(heading["items"]) >= EXAMPLE_FROM and "example" not in kinds:
        out.append("this heading needs at least one worked example (kind example): a named plant or experiment, a number, "
                   "one molecule followed")
    if (ideas or {}).get("analogy") and "analogy" not in kinds:
        out.append("the plan offers an analogy for this heading; give the heading one (that one or a better one, kind "
                   "analogy), never one the script already used")
    if (ideas or {}).get("real_world") and "real_world" not in kinds:
        out.append("the plan offers a real-world use for this heading; give the heading one (kind real_world): where the "
                   "learner meets it in life")
    # terms: opened here when the chapter opens them here; never defined twice; not used before they are opened
    opened_here = {}
    for p in points:
        for t in p.get("terms") or []:
            key = _plain(t.get("term") or "")
            if not key:
                continue
            if key in before["terms"]:
                out.append(f"{p.get('id')}: the term {t.get('term')!r} was opened in {before['terms'][key]}; remind in a few "
                           "words, do not define it again")
            opened_here.setdefault(key, p.get("id"))
    said_by = {p.get("id"): " ".join(p.get("says") or []) for p in points}
    for term, iid in first_terms(heading):
        if iid not in taught or any(_same_term(term, k) for k in opened_here) or any(_same_term(term, k) for k in before["terms"]):
            continue
        if _technical(term):
            out.append(f"{taught[iid]}: open the term {term!r} (first met in {iid}) with its meaning in terms")
        elif not _term_in(term, said_by.get(taught[iid], "")):
            out.append(f"{taught[iid]}: the book's term {term!r} (first met in {iid}) is neither said nor opened; use it "
                       "where you teach that line (open it in terms when the learner needs its meaning)")
    seen_terms = set(before["terms"]) | set()
    for p in points:
        seen_terms |= {_plain(t.get("term") or "") for t in p.get("terms") or []}
        for sentence in p.get("says") or []:
            if FORWARD.search(sentence or ""):
                continue
            for term in later_terms:
                if _term_in(term, sentence) and not any(_same_term(term, k) for k in seen_terms):
                    out.append(f"{p.get('id')}: uses {term!r} before the chapter opens it (a later heading); explain without "
                               "it, or point ahead (\"isko aage dekhenge\")")
                    break
    # no repetition: sentences, analogies, examples
    said = list(before["sentences"])
    for p in points:
        for k, sentence in enumerate(p.get("says") or [], 1):
            words = _words(sentence)
            if len(words) >= 6:
                for other, other_words in said:
                    if len(other_words) >= 6 and _same(words, other_words) >= SAME_SENTENCE:
                        out.append(f"{p.get('id')} sentence {k} says again what {other} said; say something new or "
                                   "remind in a few words")
                        break
            said.append((p.get("id"), words))
    for kind, used, limit in (("analogy", before["analogies"], SAME_ANALOGY), ("example", before["examples"], SAME_EXAMPLE)):
        used = list(used)
        for p in points:
            if p.get("kind") != kind:
                continue
            words = _words(" ".join(p.get("says") or []))
            for other, other_words in used:
                if words and other_words and _overlap(words, other_words) >= limit:
                    out.append(f"{p.get('id')}: this {kind} repeats {other}'s; choose another")
                    break
            used.append((p.get("id"), words))
    return out


def script_so_far(parts: list, chapter: dict) -> str:
    """The script written so far, as the next call reads it."""
    if not parts:
        return "(nothing yet: this is the first heading)"
    out = []
    for part in parts:
        out.append(f"### {part.get('section') or 'Opening'}")
        if part.get("goal"):
            out.append(f"(goal) {part['goal']}")
        for p in part.get("points") or []:
            terms = "; ".join(f"{t.get('term')} = {t.get('meaning')}" for t in p.get("terms") or [])
            out.append(f"[{p.get('id')} · {p.get('kind')}] " + " ".join(p.get("says") or [])
                       + (f"  (terms: {terms})" if terms else ""))
        if part.get("bridge"):
            out.append(f"(bridge) {part['bridge']}")
    used = memory(parts)
    out += ["", "Terms already opened: " + ", ".join(sorted(used["terms"])) if used["terms"] else ""]
    return "\n".join(out)


def ideas(naksha: dict | None, number: str) -> dict:
    """Whether the plan offers an analogy or a real-world use for this heading (in either shape)."""
    films = [f for plan in (naksha or {}).values() if isinstance(plan, dict) for f in plan.get("films") or []
             if isinstance(f, dict) and (f.get("section") or "") == number]
    return {"analogy": any((f.get("analogy") or {}).get("picture") for f in films),
            "real_world": any(f.get("real_world") for f in films)}


def plan_ideas(naksha: dict | None, number: str) -> str:
    """The teaching plan's ideas for one heading (both shapes when both exist): student questions, openings, analogies,
    examples, real-world uses and pictures. Ideas only: the cut into videos comes later."""
    rows = []
    for shape, plan in sorted((naksha or {}).items()):
        for f in (plan or {}).get("films") or [] if isinstance(plan, dict) else []:
            if (f.get("section") or "") != number:
                continue
            rows.append(f"- plan {shape} · question: {f.get('question')} · opens with: {f.get('opens_with')} · story: "
                        + " → ".join(f.get("story") or [])
                        + (f" · analogy: {(f.get('analogy') or {}).get('picture')}" if (f.get("analogy") or {}).get("picture") else "")
                        + (f" · examples: {'; '.join(f.get('examples') or [])}" if f.get("examples") else "")
                        + (f" · real world: {'; '.join(f.get('real_world') or [])}" if f.get("real_world") else "")
                        + (" · pictures: " + "; ".join(s.get("shows", "") for s in f.get("saman") or []) if f.get("saman") else ""))
    return "\n".join(rows) if rows else "(no plan ideas for this heading)"


def messages(chapter: dict, heading: dict, parts: list, *, course: dict, naksha: dict | None = None,
             language: str = "Hinglish", next_title: str = "") -> list:
    system = RULES.format(subject=course.get("subject") or "the subject", learners=course.get("learners") or "the learners",
                          exam=course.get("exam") or "their exam", language=language or "Hinglish", max_words=MAX_WORDS,
                          max_sentences=MAX_SENTENCES, tag=tag(heading["number"]))
    items = chapter.get("items") or {}
    stars = [f"{term} (in {iid})" for term, iid in first_terms(heading)]
    lines = "\n".join(f"- {iid}: {items[iid].get('content', '')[:300]}" for iid in heading["items"])
    exercise_lines = "\n".join(f"- {iid}: {items[iid].get('content', '')[:240]}" for iid in exercises(chapter)) or "(none)"
    user = (f"THE CHAPTER FILE\n\n{chapter_file.markdown(chapter)}\n\nTHE SCRIPT SO FAR\n\n{script_so_far(parts, chapter)}\n\n"
            f"IDEAS FROM THE TEACHING PLAN FOR THIS HEADING (use what serves; not the cut into videos)\n\n"
            f"{plan_ideas(naksha, heading['number'])}\n\n"
            f"THE CHAPTER'S EXERCISES (the script holds the knowledge for each; list a point's in prepares)\n{exercise_lines}\n"
            f"Not yet prepared by any point: {', '.join(unprepared(chapter, parts)) or '(none)'}\n\n"
            f"NOW WRITE THE SCRIPT OF THIS HEADING: {heading['number'] or 'the opening'} {heading['title']}\n"
            f"Its items (each in exactly one point's teaches):\n{lines}\n"
            f"Terms the chapter opens here: {', '.join(stars) if stars else '(none)'}\n"
            f"The next heading: {next_title or '(none: this is the last heading)'}")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def write(client, model: str, chapter: dict, *, course: dict, naksha: dict | None = None, language: str = "Hinglish",
          max_rounds: int = 3, on_part=None) -> dict:
    """The whole chapter's script, heading by heading; ``on_part(record)`` is called after each heading (to save it)."""
    heads = headings(chapter)
    later = {}
    for n, heading in enumerate(heads):
        later[n] = [t for h in heads[n + 1:] for t, _ in first_terms(h) if _technical(t)]
    parts, rounds, usage, left = [], [], {"input_tokens": 0, "output_tokens": 0}, {}
    for n, heading in enumerate(heads):
        nxt = heads[n + 1] if n + 1 < len(heads) else None
        convo = messages(chapter, heading, parts, course=course, naksha=naksha, language=language,
                         next_title=f"{nxt['number']} {nxt['title']}" if nxt else "")
        answer, found, these = None, ["no answer yet"], []
        for number in range(1, max_rounds + 1):
            reply = client.chat(model=model, messages=convo, schema=SCHEMA)
            for key in usage:
                usage[key] += int((reply.get("usage") or {}).get(key) or 0)
            answer = repair(parse(reply.get("content", "")), heading, parts)
            found = problems(answer, heading, chapter, parts, later[n], ideas(naksha, heading["number"]),
                             unprepared(chapter, parts) if heading["number"] == RECAP else None)
            these.append({"round": number, "problems": found})
            if not found:
                break
            convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                             {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
        part = answer if isinstance(answer, dict) else {"section": heading["number"], "points": [], "bridge": ""}
        part = dict(part, section=heading["number"], title=heading["title"])
        parts.append(part)
        rounds.append({"section": heading["number"], "rounds": these})
        if found:
            left[heading["number"] or "opening"] = found
        record = {"parts": parts, "rounds": rounds, "usage": usage, "problems": left}
        if on_part:
            on_part(record)
    return {"parts": parts, "rounds": rounds, "usage": usage, "problems": left}


FILM_LINES = 48               # script lines in one film at most (about 8 shots); a longer heading is cut into films


def film_id(section: str, part: int = 0, parts: int = 1) -> str:
    """A heading's film id, as a VM job's videos field can carry it: "11.6.1" -> "h11-6-1", the opening "h0"; a heading cut
    into several films: "h11-2a", "h11-2b" ..."""
    return "h" + (section or "0").replace(".", "-") + ("abcdefghijklmnopqrstuvwxyz"[part] if parts > 1 else "")


def _cut(points: list) -> list:
    """The heading's points in films of at most FILM_LINES lines, cut only between points, the parts as even as they can be."""
    sizes = [len(sentences(p)) for p in points]
    total = sum(sizes)
    count = max(1, -(-total // FILM_LINES))
    target = total / count
    out, current, size = [], [], 0
    for point, n in zip(points, sizes):
        if current and (size + n > FILM_LINES or (size >= target and len(out) < count - 1)):
            out.append(current)
            current, size = [], 0
        current.append(point)
        size += n
    return out + ([current] if current else [])


def film_questions(script: dict, chapter: dict, naksha: dict | None = None, wanted: list | None = None) -> dict:
    """The script cut into films, first slice (Navin, 22 November 2026: "phir video maker us script ke hisab se poore
    chapter ko video ke tukdon mein baantega"): one film per heading, its narration the heading's script lines in order
    (the films stage's teacher lines, with each point's kind and screen line as the note), its points the heading's items
    (their blocks give the book lines). A film opens on a question: the plan's question for the heading (shape B, one
    heading one film; else shape A's first) when the script's first line is not one. ``wanted``: film ids or headings."""
    items = chapter.get("items") or {}
    shape_a, shape_b = {}, {}
    for f in ((naksha or {}).get("A") or {}).get("films") or []:              # shape A: question-wise films in a heading
        if isinstance(f, dict) and f.get("question"):
            shape_a.setdefault(f.get("section") or "", []).append(f)
    for f in ((naksha or {}).get("B") or {}).get("films") or []:              # shape B: one heading, one film
        if isinstance(f, dict) and f.get("question"):
            shape_b.setdefault(f.get("section") or "", f)
    wanted = {w.strip() for w in wanted or [] if w.strip()}
    out = []
    for part in script.get("parts") or []:
        section = part.get("section") or ""
        pieces = _cut([p for p in part.get("points") or [] if sentences(p)])
        for number, chunk in enumerate(pieces):
            fid = film_id(section, number, len(pieces))
            if wanted and fid not in wanted and section not in wanted and film_id(section) not in wanted:
                continue
            lines = []
            for point in chunk:
                kind, screen = point.get("kind") or "explain", (point.get("screen") or "").strip()
                for n, said in enumerate(sentences(point)):
                    lines.append({"roman": said, "note": f"{kind} · screen: {screen}" if n == 0 and screen else kind,
                                  "kind": kind, "point": point.get("id") or ""})
            taught = list(dict.fromkeys(i for point in chunk for i in point.get("teaches") or [] if i in items))
            # the plan's film that teaches most of this film's items (shape B when the heading is one film)
            planned = sorted(shape_a.get(section) or [], key=lambda f: -len(set(f.get("teaches") or []) & set(taught)))
            plan = (shape_b.get(section) if len(pieces) == 1 else None) or (planned[0] if planned else None) or \
                shape_b.get(section) or {}
            question = (plan.get("question") or "").strip()
            if not lines[0]["roman"].rstrip().endswith("?"):
                opening = question if question.endswith("?") else next(
                    (x["roman"] for x in lines if x["roman"].rstrip().endswith("?")), (part.get("title") or section) + "?")
                lines.insert(0, {"roman": opening, "note": "the film's opening question", "kind": "question", "point": ""})
            if number == len(pieces) - 1 and (part.get("bridge") or "").strip():
                lines.append({"roman": part["bridge"].strip(), "note": "bridge to the next heading's film", "kind": "bridge",
                              "point": ""})
            points = [{"block_ids": list(items[i].get("block_ids") or []), "point": items[i].get("content", "")[:200],
                       "kind": items[i].get("content_type") or "facts_numbers", "item_id": i} for i in taught]
            out.append({"id": fid, "pillar": section or "opening", "question": lines[0]["roman"],
                        "hook": plan.get("opens_with", ""), "points": points,
                        "film": {"length": "long",
                                 "showing_moment": next((x.get("shows") for x in plan.get("saman") or []), "")},
                        "game_stage": {"mechanic": "choose_and_see", "idea": ""}, "naksha": True, "script_lines": True,
                        "teacher_lines": lines, "heading": {"section": section, "title": part.get("title") or "",
                                                            "film": number + 1, "films": len(pieces)}})
    return {"chapter_title": script.get("chapter_title") or (chapter.get("map") or {}).get("chapter_title", ""),
            "naksha": True, "script": True, "questions": out}


def counts(chapter: dict, parts: list) -> dict:
    wanted = studio_naksha.coverable(chapter)
    taught = {i for part in parts for p in part.get("points") or [] for i in p.get("teaches") or []}
    lines = [s for part in parts for p in part.get("points") or [] for s in p.get("says") or []]
    words = sum(len(s.split()) for s in lines)
    spoken = [s for part in parts for p in part.get("points") or [] for s in sentences(p)]
    summary = studio_naksha.zone_items(chapter, "summary")
    prepared = {x for part in parts for p in part.get("points") or [] for x in p.get("prepares") or []}
    return {"headings": len(parts), "points": sum(len(part.get("points") or []) for part in parts),
            "summary_taught": sum(1 for i in summary if i in taught), "summary": len(summary),
            "exercises_prepared": sum(1 for i in exercises(chapter) if i in prepared), "exercises": len(exercises(chapter)),
            "checkpoints": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "checkpoint"),
            "sentences": len(lines), "words": words, "minutes": round(words / WORDS_PER_MINUTE),
            "covered": sum(1 for i in wanted if i in taught), "coverable": len(wanted),
            "analogies": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "analogy"),
            "examples": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "example"),
            "real_world": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "real_world"),
            "outside_book": sum(1 for part in parts for p in part.get("points") or [] if (p.get("outside_book") or "").strip()),
            "questions": sum(1 for s in spoken if s.endswith("?")),
            "question_share": round(sum(1 for s in spoken if s.endswith("?")) / max(1, len(spoken)), 3),
            "fragments": sum(1 for s in spoken if len(s.split()) <= FRAGMENT and not s.rstrip().endswith("?")),
            "retells": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "retell"),
            "goals": sum(1 for part in parts if (part.get("goal") or "").strip())}


KIND_WORDS = {"explain": "samjhana", "question": "sawaal", "checkpoint": "ruko, socho", "example": "example", "analogy": "analogy",
              "real_world": "asli duniya", "recall": "yaad", "activity": "activity", "story": "kahani", "figure": "figure",
              "summary": "saar", "overview": "pehle poori jhalak", "retell": "poori kahani dobara"}


def markdown(chapter: dict, record: dict) -> str:
    items = chapter.get("items") or {}
    title = (chapter.get("map") or {}).get("chapter_title") or (chapter.get("course") or {}).get("title", "")
    c = counts(chapter, record.get("parts") or [])
    out = [f"# Chapter ki script · {title}", "",
           f"{c['headings']} headings · {c['points']} gyan-bindu · {c['sentences']} lines · lagbhag {c['minutes']} minute bolna · "
           f"padhai ki NCERT lines {c['covered']}/{c['coverable']} · summary {c['summary_taught']}/{c['summary']} · "
           f"exercises ka gyan {c['exercises_prepared']}/{c['exercises']} · ruko-socho {c['checkpoints']} · "
           f"sawaal {round(100 * c['question_share'])}% · poori kahani dobara {c['retells']} · tukde {c['fragments']}", ""]
    for part in record.get("parts") or []:
        out += [f"## {part.get('section') or 'Shuruaat'} {part.get('title') or ''}".rstrip(), ""]
        if part.get("goal"):
            out += [f"_Maqsad: {part['goal']}_", ""]
        for p in part.get("points") or []:
            out.append(f"**{p.get('id')}** · {KIND_WORDS.get(p.get('kind'), p.get('kind'))} · " + " ".join(p.get("says") or []))
            if p.get("terms"):
                out.append("  - terms: " + "; ".join(f"{t.get('term')} = {t.get('meaning')}" for t in p["terms"]))
            out.append(f"  - screen: {p.get('screen')}")
            if p.get("teaches"):
                out.append("  - NCERT: " + "; ".join(f"{i} {items.get(i, {}).get('content', '')[:80]}" for i in p["teaches"]))
            if (p.get("outside_book") or "").strip():
                out.append(f"  - kitaab se bahar: {p['outside_book']}")
            if (p.get("answer") or "").strip():
                out.append(f"  - {'jawab' if p.get('kind') == 'checkpoint' else 'kya kis jaisa'}: {p['answer']}")
            if (p.get("watch_out") or "").strip():
                out.append(f"  - {'aam galti' if p.get('kind') == 'checkpoint' else 'kahan tootti hai'}: {p['watch_out']}")
            if p.get("prepares"):
                out.append(f"  - exercise ke liye: {', '.join(p['prepares'])}")
        if part.get("bridge"):
            out += ["", f"_→ {part['bridge']}_"]
        left = (record.get("problems") or {}).get(part.get("section") or "opening")
        if left:
            out += ["", f"Code ki kamiyan bachi: {len(left)}"]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def html(chapter: dict, record: dict) -> str:
    """SCRIPT.html, Navin's script page (a review page, never the learner's): each heading's script beside the NCERT lines
    it teaches, readable on his tablet."""
    e = html_module.escape
    items = chapter.get("items") or {}
    title = (chapter.get("map") or {}).get("chapter_title") or (chapter.get("course") or {}).get("title", "")
    c = counts(chapter, record.get("parts") or [])
    left_total = sum(len(v) for v in (record.get("problems") or {}).values())
    parts = [f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chapter ki script · {e(title)}</title><style>
body{{font:16px/1.6 system-ui,sans-serif;margin:0;padding:16px;background:#faf8f3;color:#222}}main{{max-width:1100px;margin:auto}}
h1{{font-size:22px;margin:.2em 0}}.sum{{color:#555}}details.h{{background:#fff;border:1px solid #ddd6c8;border-radius:10px;margin:8px 0;
padding:6px 12px}}details.h>summary{{cursor:pointer;font-weight:600}}.pt{{display:grid;grid-template-columns:3fr 2fr;gap:12px;
border-top:1px solid #eee;padding:10px 0}}@media (max-width:720px){{.pt{{grid-template-columns:1fr}}}}
.tag{{display:inline-block;font-size:12px;border-radius:6px;padding:0 6px;margin-right:6px;background:#eef2e8;color:#2f4d1f}}
.k-analogy,.k-example,.k-real_world{{background:#fbf3df;color:#6b4a07}}.k-question{{background:#e7eefb;color:#1d3d7a}}
.k-recall{{background:#f1f1f1;color:#555}}.k-overview,.k-retell{{background:#e8f3f1;color:#1f5a4e}}.k-checkpoint{{background:#fde7ea;color:#7a1f2b}}.says{{margin:4px 0}}.k{{color:#555;font-size:14px}}.k b{{color:#333}}
.book{{background:#f6f3ec;border-radius:8px;padding:6px 10px;font-size:14px;color:#444}}.book div{{margin:3px 0}}
.left{{color:#7a3413;font-size:14px}}.bridge{{color:#2f4d1f;font-style:italic;margin:6px 0}}.id{{color:#888;font-size:12px}}
</style></head><body><main>
<p class="sum">BIE · chapter ki script (review page, learner ko nahi dikhta)</p><h1>{e(title)}</h1>
<p>{c['headings']} headings · {c['points']} gyan-bindu · {c['sentences']} lines · lagbhag {c['minutes']} minute bolna<br>
padhai ki NCERT lines {c['covered']}/{c['coverable']} · summary {c['summary_taught']}/{c['summary']} · exercises ka gyan
{c['exercises_prepared']}/{c['exercises']}<br>analogy {c['analogies']} · example {c['examples']} · asli duniya {c['real_world']} ·
ruko-socho {c['checkpoints']} · kitaab se bahar {c['outside_book']} · code ki kamiyan {left_total}<br>
sawaal {round(100 * c['question_share'])}% vaakya · poori kahani dobara {c['retells']} · chhote tukde {c['fragments']}</p>"""]
    for part in record.get("parts") or []:
        points = part.get("points") or []
        left = (record.get("problems") or {}).get(part.get("section") or "opening") or []
        words = sum(len(s.split()) for p in points for s in p.get("says") or [])
        parts.append(f'<details class="h"><summary>{e(part.get("section") or "Shuruaat")} {e(part.get("title") or "")} · '
                     f'{len(points)} gyan-bindu · lagbhag {round(words / WORDS_PER_MINUTE)} min'
                     + (f' · <span class="left">{len(left)} kamiyan bachi</span>' if left else "") + "</summary>")
        if part.get("goal"):
            parts.append(f'<div class="bridge">Maqsad: {e(part["goal"])}</div>')
        for p in points:
            terms = "; ".join(f"<b>{e(t.get('term') or '')}</b> = {e(t.get('meaning') or '')}" for t in p.get("terms") or [])
            book = "".join(f'<div><span class="id">{e(i)}</span> {e(items.get(i, {}).get("content", ""))}</div>'
                           for i in p.get("teaches") or [])
            parts.append(
                f'<div class="pt"><div><span class="tag k-{e(p.get("kind") or "")}">{e(KIND_WORDS.get(p.get("kind"), p.get("kind") or ""))}</span>'
                f'<span class="id">{e(p.get("id") or "")}</span>'
                f'<div class="says">{e(" ".join(p.get("says") or []))}</div>'
                f'<div class="k"><b>Screen par:</b> {e(p.get("screen") or "")}</div>'
                + (f'<div class="k"><b>Terms:</b> {terms}</div>' if terms else "")
                + (f'<div class="k"><b>Kitaab se bahar:</b> {e(p.get("outside_book"))}</div>' if (p.get("outside_book") or "").strip() else "")
                + (f'<div class="k"><b>Yaad:</b> {e(", ".join(p.get("recalls") or []))}</div>' if p.get("recalls") else "")
                + (f'<div class="k"><b>{"Jawab" if p.get("kind") == "checkpoint" else "Kya kis jaisa"}:</b> {e(p.get("answer"))}</div>'
                   if (p.get("answer") or "").strip() else "")
                + (f'<div class="k"><b>{"Aam galti" if p.get("kind") == "checkpoint" else "Kahan tootti hai"}:</b> '
                   f'{e(p.get("watch_out"))}</div>' if (p.get("watch_out") or "").strip() else "")
                + (f'<div class="k"><b>Exercise ke liye:</b> {e(", ".join(p.get("prepares") or []))}</div>' if p.get("prepares") else "")
                + f'</div><div class="book">{book or "<span class=k>(NCERT line nahi: jodne wali baat)</span>"}</div></div>')
        if part.get("bridge"):
            parts.append(f'<div class="bridge">→ {e(part["bridge"])}</div>')
        if left:
            parts.append('<div class="left">Code ki kamiyan: ' + e(" | ".join(left[:8])) + "</div>")
        parts.append("</details>")
    parts.append("</main></body></html>")
    return "\n".join(parts)


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1)
