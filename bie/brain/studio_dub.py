"""Autodub: a finished studio film said again in another language mix (Navin, 21 November 2026).

In his words: "video ke neeche chalne wali script, bolne wali voice autodub ho jaaye dusri bhasha ke mix mein: wo bhasha
plus technical terms in English, jaise hum Hinglish ke liye karte hain", at no cost. The maker (Codex on the ChatGPT plan,
Rs 0) re-says every line of the film the way a teacher of that language explains it on video; code checks every line:

- every short form and formula (ATP, CF0, H+, CO2) and every technical word of the film's labels stays in English, in
  Latin letters, on the screen line;
- no English word is invented: a Latin word on the screen line is one the Hinglish line already had;
- the screen line is in the language's own script (Tamil, Telugu, Malayalam; Marathi in Devanagari without Hindi words);
- the voice line (``voice``, what the voice engine reads) is wholly in that script, because the Indian-language voice
  engines read only their own letters; for English it is plain English with formulas spoken ("H plus");
- a question stays a question (same number of "?"), numbers stay the same, and nothing is added or dropped
  (length within a band of the Hinglish line).

The dubbed film keeps the shots, pictures, labels' places, moves and timings of the original; only its words change, so
the player plays it as it is. Labels that are technical stay English; everyday labels (Patta, Dhoop) are translated.
"""
from __future__ import annotations

import copy
import json
import re

from . import studio
from .studio import is_term, parse

S = {"type": "string"}

# language code -> (name, script name, letters of the script, how its teachers mix English)
LANGUAGES = {
    "ta": ("Tamil", "Tamil", r"[஀-௿]", "a Tamil Nadu coaching teacher (Tanglish: Tamil sentences, English science terms)"),
    "te": ("Telugu", "Telugu", r"[ఀ-౿]", "an Andhra/Telangana coaching teacher (Telugu sentences, English science terms)"),
    "ml": ("Malayalam", "Malayalam", r"[ഀ-ൿ]", "a Kerala coaching teacher (Malayalam sentences, English science terms)"),
    "mr": ("Marathi", "Devanagari", r"[ऀ-ॿ]", "a Maharashtra coaching teacher (Marathi sentences, English science terms)"),
    "en": ("English", "Latin", r"[A-Za-z]", "an Indian English-medium coaching teacher (simple spoken Indian English)"),
}
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z0-9+\-]*")
NUMBER = re.compile(r"\d+")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
# Hindi words that are not Marathi: a Marathi line holding them was said in Hindi
HINDI_ONLY = {"है", "हैं", "और", "में", "नहीं", "क्यों", "कैसे", "यह", "वह", "लेकिन", "इसलिए", "इसका", "इसकी"}
# Hinglish words that are not English: an English line holding them was not translated
HINGLISH = {"hai", "hain", "ke", "ki", "ka", "ko", "mein", "aur", "toh", "yeh", "ye", "woh", "kya", "kyun", "kaise", "nahi",
            "nahin", "hota", "hoti", "jaata", "jaati", "isliye", "aaiye", "chaliye", "dekhiye", "yahaan", "ab", "par", "se"}
LENGTH_BAND = (0.45, 2.6)        # characters of the dubbed voice line per character of the Hinglish line
LABEL_KEYS = ("moves", "grows", "fuses", "reacts", "cycles", "arrows")

LINE = {"type": "object", "additionalProperties": False, "required": ["id", "screen", "voice"],
        "properties": {"id": S, "screen": S, "voice": S}}
SHOT = {"type": "object", "additionalProperties": False, "required": ["id", "title", "key"],
        "properties": {"id": S, "title": S, "key": S}}
LABEL = {"type": "object", "additionalProperties": False, "required": ["from", "to"], "properties": {"from": S, "to": S}}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["title", "question", "shots", "lines", "labels"],
          "properties": {"title": S, "question": S, "shots": {"type": "array", "items": SHOT},
                         "lines": {"type": "array", "items": LINE}, "labels": {"type": "array", "items": LABEL}}}

INSTRUCTIONS = """You are BIE's dubbing teacher for {name}. A finished Hinglish video lesson ({course}) must now be said in
{name} by {teacher}, to students watching the same pictures. Re-say EVERY line as that teacher would explain it on video:

- natural spoken {name} of a classroom, not a word-for-word translation and not a textbook; the same meaning, the same
  order, nothing added, nothing dropped, no caution lines, no source or book names;
- a question stays a question at the same place and ends with "?"; an invitation ("aaiye", "chaliye", "dekhiye") becomes
  the natural invitation of {name}; an everyday comparison (baandh, motor, battery) stays that comparison;
- keep every technical term, short form and formula in English exactly as the Hinglish line writes it (ATP synthase, CF0,
  H+, proton gradient, thylakoid membrane, stroma, NADPH, CO2), the way {name} students really mix English terms;
  never use an English word the Hinglish line does not have;
- numbers stay digits.

For every line give two forms:
- "screen": the subtitle, in {script} script, with the English terms in Latin letters inside it;
- "voice": the same words for the voice engine{voice_rule}.

Also give the film title, the question and every shot's title and key in {name} (English terms kept), and every label:
a technical label stays exactly as it is ("to" = "from"); an everyday label (Patta, Dhoop) is said in {name}.
Answer with JSON only: {{"title", "question", "shots": [{{"id","title","key"}}], "lines": [{{"id","screen","voice"}}],
"labels": [{{"from","to"}}]}}, one line for every line id below, in the same order."""

VOICE_RULE = {"en": ": plain English with every formula and sign spoken as said aloud (H+ as \"H plus\", CO2 as \"C O 2\", "
                    "ADP + Pi as \"ADP and P i\"), no other symbols",
              "mr": ", wholly in Devanagari letters: English terms written as a Marathi teacher pronounces them, no Latin "
                    "letters, no symbols other than . , ? !",
              "other": ", wholly in {script} letters: English terms written as a {name} teacher pronounces them (ATP as the "
                       "three letters, H+ as \"H plus\"), no Latin letters, no symbols other than . , ? !"}

PROBLEMS_PROMPT = "BIE's code checked the dub and found these problems. Send the whole corrected JSON again:\n- "


def line_ids(film: dict) -> list:
    """[(line id "s1.0", Hinglish line)] in film order."""
    return [(f"{shot.get('id')}.{k}", sentence.get("roman") or "")
            for shot in film.get("shots") or [] for k, sentence in enumerate(shot.get("sentences") or [])]


def labels(film: dict) -> list:
    """Every distinct label text on the film's screen: pins and the labels of moves, reacts, cycles and their stations."""
    out = []

    def add(text):
        text = (text or "").strip()
        if text and text not in out:
            out.append(text)
    for shot in film.get("shots") or []:
        for sentence in shot.get("sentences") or []:
            for pin in sentence.get("pins") or []:
                add(pin.get("label"))
            for key in LABEL_KEYS:
                for item in sentence.get(key) or []:
                    add(item.get("label"))
                    for station in item.get("stations") or []:
                        add(station.get("label"))
    return out


def technical(text: str, known=frozenset()) -> bool:
    """A label that stays English: it has a short form or formula, or every word of it is a word of the English chapter."""
    words = LATIN_WORD.findall(text or "")
    if not words:
        return False
    if any(is_term(w) for w in words):
        return True
    return bool(known) and all(studio._norm_term(w) in known for w in words)


def kept_terms(roman: str, film_labels: list, known=frozenset()) -> list:
    """The English the dubbed line must keep: every short form and formula of the Hinglish line, and every technical
    label that the line says."""
    out = []
    for token in LATIN_WORD.findall(roman or ""):
        if is_term(token) and token not in out:
            out.append(token)
    low = (roman or "").casefold()
    for label in film_labels:
        if technical(label, known) and re.search(r"(?<![a-z])" + re.escape(label.casefold()) + r"(?![a-z])", low) \
                and label not in out and not any(label in o for o in out):
            out.append(label)
    return out


def messages(film: dict, question: dict, language: str, *, course: str = "", known=frozenset()) -> list:
    name, script, _, teacher = LANGUAGES[language]
    rule = VOICE_RULE.get(language, VOICE_RULE["other"]).format(name=name, script=script)
    system = INSTRUCTIONS.format(name=name, script=script, teacher=teacher, course=course or "school", voice_rule=rule)
    film_labels = labels(film)
    lines = "\n".join(f"{lid}: {roman}" for lid, roman in line_ids(film))
    shots = "\n".join(f"{s.get('id')}: title \"{s.get('title') or ''}\" · key \"{s.get('key') or ''}\"" for s in film.get("shots") or [])
    tags = "\n".join(f"- {x} ({'technical: keep' if technical(x, known) else 'everyday: say it in ' + name})" for x in film_labels)
    user = (f"Film title: {film.get('title') or ''}\nQuestion: {question.get('question') or ''}\n\nShots:\n{shots}\n\n"
            f"Lines:\n{lines}\n\nLabels:\n{tags}\n")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _letters(text: str) -> str:
    return re.sub(r"[\W\d_]", "", text or "")


def problems(answer, film: dict, language: str, *, known=frozenset()) -> list:
    if not isinstance(answer, dict):
        return ["the answer is not one JSON object"]
    name, _, letters, _ = LANGUAGES[language]
    script = re.compile(letters)
    out = []
    want = line_ids(film)
    got = {str(x.get("id")): x for x in answer.get("lines") or [] if isinstance(x, dict)}
    missing = [lid for lid, _ in want if lid not in got]
    if missing:
        out.append(f"lines missing: {', '.join(missing)} (send every line id)")
    extra = [i for i in got if i not in dict(want)]
    if extra:
        out.append(f"unknown line ids: {', '.join(extra)}")
    film_labels = labels(film)
    for lid, roman in want:
        line = got.get(lid)
        if not line:
            continue
        screen, voice = str(line.get("screen") or "").strip(), str(line.get("voice") or "").strip()
        if not screen or not voice:
            out.append(f"{lid}: screen and voice are both needed")
            continue
        if roman.count("?") != screen.count("?") or roman.count("?") != voice.count("?"):
            out.append(f"{lid}: the Hinglish line has {roman.count('?')} question(s); keep each as a question with \"?\" "
                       f"(screen has {screen.count('?')}, voice has {voice.count('?')})")
        if sorted(NUMBER.findall(roman)) != sorted(NUMBER.findall(screen)):
            out.append(f"{lid}: the numbers must stay the same as in the Hinglish line ({' '.join(NUMBER.findall(roman)) or 'none'})")
        for term in kept_terms(roman, film_labels, known):
            if term.casefold() not in screen.casefold():
                out.append(f"{lid}: keep \"{term}\" in English on the screen line")
        source_words = {w.casefold() for w in LATIN_WORD.findall(roman)}
        if language != "en":
            invented = [w for w in LATIN_WORD.findall(screen) if w.casefold() not in source_words]
            if invented:
                out.append(f"{lid}: the screen line uses English the Hinglish line does not have: {', '.join(invented[:5])}")
            native = re.sub(LATIN_WORD, "", screen)
            if len(script.findall(native)) < 0.8 * max(1, len(_letters(native))) or not script.search(native):
                out.append(f"{lid}: write the screen line in {name} script (English only for the kept terms)")
            if LATIN_WORD.search(voice):
                out.append(f"{lid}: the voice line must have no Latin letters; write the English terms in {name} letters")
            if len(script.findall(voice)) < 0.9 * max(1, len(_letters(voice))):
                out.append(f"{lid}: write the voice line wholly in {name} letters")
            if language != "mr" and (DEVANAGARI.search(screen) or DEVANAGARI.search(voice)):
                out.append(f"{lid}: Devanagari letters in a {name} line")
            if language == "mr":
                hindi = sorted({w for w in re.findall(r"[ऀ-ॿ]+", screen + " " + voice) if w in HINDI_ONLY})
                if hindi:
                    out.append(f"{lid}: Hindi words in the Marathi line: {', '.join(hindi)} (say it in Marathi)")
        else:
            left = sorted({w for w in LATIN_WORD.findall(screen + " " + voice) if w.casefold() in HINGLISH})
            if left:
                out.append(f"{lid}: Hinglish words left in the English line: {', '.join(left)}")
            if re.search(r"[^\x00-\x7F’‘“”—–…·]", voice):
                out.append(f"{lid}: the English voice line must be plain English letters")
            if re.search(r"[+=→]", voice):
                out.append(f"{lid}: say the formula signs in words in the voice line (H plus, gives)")
        ratio = len(voice) / max(1, len(roman))
        if not LENGTH_BAND[0] <= ratio <= LENGTH_BAND[1]:
            out.append(f"{lid}: the voice line is {ratio:.1f} times the Hinglish line's length; say the same, no more, no less")
    shots = {str(x.get("id")): x for x in answer.get("shots") or [] if isinstance(x, dict)}
    for shot in film.get("shots") or []:
        if shot.get("id") not in shots:
            out.append(f"shot {shot.get('id')}: title and key missing")
    told = {str(x.get("from")): str(x.get("to") or "") for x in answer.get("labels") or [] if isinstance(x, dict)}
    for label in film_labels:
        if label not in told:
            out.append(f"label \"{label}\" missing (a technical label stays as it is)")
        elif technical(label, known) and told[label] != label:
            out.append(f"label \"{label}\" is technical: keep it exactly as \"{label}\"")
        elif not told[label].strip():
            out.append(f"label \"{label}\": empty")
    if not str(answer.get("title") or "").strip() or not str(answer.get("question") or "").strip():
        out.append("the film title and the question are both needed")
    for shot in film.get("shots") or []:
        if (shot.get("visual") or {}).get("type") == "diagram" and re.search(r"<text\b", (shot.get("visual") or {}).get("svg") or ""):
            out.append(f"shot {shot.get('id')}: its diagram has words that the dub does not change yet")
            break
    return out


def dubbed(film: dict, answer: dict) -> dict:
    """The film with its words in the new language: shots, pictures, places, moves and timings unchanged."""
    film = copy.deepcopy(film)
    lines = {str(x.get("id")): x for x in answer.get("lines") or [] if isinstance(x, dict)}
    shots = {str(x.get("id")): x for x in answer.get("shots") or [] if isinstance(x, dict)}
    told = {str(x.get("from")): str(x.get("to") or "") for x in answer.get("labels") or [] if isinstance(x, dict)}

    def relabel(item):
        if item.get("label") in told and told[item["label"]].strip():
            item["label"] = told[item["label"]]
    film["title"] = answer.get("title") or film.get("title")
    for shot in film.get("shots") or []:
        said = shots.get(str(shot.get("id"))) or {}
        shot["title"], shot["key"] = said.get("title") or shot.get("title"), said.get("key") or shot.get("key")
        for k, sentence in enumerate(shot.get("sentences") or []):
            line = lines.get(f"{shot.get('id')}.{k}") or {}
            sentence["hinglish"] = sentence.get("roman") or ""
            sentence["roman"] = line.get("screen") or sentence.get("roman")
            sentence["voice"] = line.get("voice") or sentence["roman"]
            for pin in sentence.get("pins") or []:
                relabel(pin)
            for key in LABEL_KEYS:
                for item in sentence.get(key) or []:
                    relabel(item)
                    for station in item.get("stations") or []:
                        relabel(station)
    return film


def dub(client, model: str, film: dict, question: dict, language: str, *, course: str = "", known=frozenset(),
        max_rounds: int = 3) -> dict:
    """Ask, check, send the problems back; at most ``max_rounds`` maker calls."""
    if language not in LANGUAGES:
        raise ValueError(f"unknown dub language {language!r}; one of {', '.join(LANGUAGES)}")
    convo = messages(film, question, language, course=course, known=known)
    rounds, usage, answer, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        reply = client.chat(model=model, messages=convo, schema=SCHEMA)
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        answer = parse(reply.get("content", ""))
        found = problems(answer, film, language, known=known)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
    film_out = dubbed(film, answer) if isinstance(answer, dict) else None
    question_out = dict(question, question=(answer or {}).get("question") or question.get("question")) if isinstance(answer, dict) else question
    return {"language": language, "film": film_out, "question": question_out, "answer": answer, "problems": found,
            "rounds": rounds, "usage": usage}


def markdown(rows: list) -> str:
    lines = ["# Autodub", ""]
    for row in rows:
        lines.append(f"- **{row['qid']} · {LANGUAGES[row['language']][0]}** · {row['lines']} lines · rounds {row['rounds']}"
                     f" · awaaz: {row['voice']}" + (f" · kamiyan: {len(row['problems'])}" if row["problems"] else " · sab sahi"))
    return "\n".join(lines) + "\n"


def to_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1)
