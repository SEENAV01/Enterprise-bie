"""The studio's narrator voice, per language, with BIE's teacher pauses and (when it is set up) Navin's own tone colour.

Engines (all free, all on the machine's CPU):

- **Kokoro** (kokoro-onnx, MIT; Kokoro-82M weights, Apache-2.0) for Hindi/Hinglish and English. Hindi voice ``hf_alpha``
  is the voice Navin heard in the approved Monsoon film (18 November 2026); its known limit (weak aspirated sounds such as
  kh and gh) was told to him. Files are fetched once to ``$BIE_HOME/models/kokoro`` (or ``BIE_KOKORO_DIR``).
- **AI4Bharat Indic-TTS** (FastPitch + HiFi-GAN; code and checkpoints MIT, trained on the IIT Madras Indic TTS database,
  royalty-free licence) for Tamil, Telugu, Malayalam and Marathi, read through Coqui TTS (``coqui-tts``, MPL-2.0, used
  unmodified as a library). Autodub (Navin, 21 November 2026). Checkpoints in ``$BIE_HOME/models/indic-tts/<lang>/``
  (``fastpitch/`` and ``hifigan/``, as AI4Bharat releases them). These engines read only their own script.
- **Navin's tone colour** (Navin, 21 November 2026: "Kokoro + OpenVoice"): OpenVoice V2's tone-colour converter (MyShell,
  MIT) turns the base voice into his timbre in any language. Only his timbre is taken from his recording; how a line is
  said (pauses, pace) is BIE's teacher rule below, because his recording has slips he asked BIE not to learn. The tone
  file and every audio made with it are private: never in the repository or a public run folder
  (``docs/roadmap/VOICE_CLIP_METHOD.md``). Set ``BIE_NARRATOR=navin`` and ``BIE_VOICE_TONE=<tone .npy>``; the base voice
  is then a male one, which converts best to his.

When an engine or its files are missing the studio still makes the film, timed by text length and marked "no voice".
"""
from __future__ import annotations

import base64
import io
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

FILES = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
         "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
# pace (Navin, 22 November 2026, after hearing 0.95, 1.00, 1.05 and 1.15 of the same lines: "Mujhe 1.00 wala shi lga abhi
# ke liye isko use krenge"; a 1.05 copy of the next films for his ear: ``BIE_VOICE_PACE`` or ``Voice(pace=...)``)
VOICE, SPEED, LANG = "hf_alpha", 1.00, "hi"
PACE_ENV = "BIE_VOICE_PACE"
PACE_RANGE = (0.8, 1.25)
# narrator -> language -> (Kokoro voice, Kokoro language). "navin" uses male base voices for his tone colour.
KOKORO_VOICES = {"female": {"hi": (VOICE, LANG), "en": ("bf_emma", "en-gb")},
                 "navin": {"hi": ("hm_omega", "hi"), "en": ("bm_george", "en-gb")}}
INDIC = ("ta", "te", "ml", "mr")                      # AI4Bharat Indic-TTS; speakers "female" and "male"
INDIC_SPEAKER = {"female": "female", "navin": "male"}

# BIE's teacher rules for saying a line (Navin, 20, 21 and 22 November 2026), not taken from any recording. The numbers of
# 22 November come from the teacher study (four Chapter 11 teachers, measured: a question that is answered at once is
# followed by about a quarter second, a full stop by about 0.38 s, and a pause of a second or more comes once or twice a
# minute); Navin heard them on the same lines ("Naye wala sahi hai", "Hmm yeh sahi baitha"):
QUESTION_PAUSE = 0.30     # after a question that is answered at once ("...aati kahan se hai?" "Woh aati hai paani se.")
THINK_PAUSE = 0.90        # after a question the learner is asked to think about first ("Ruko, pehle khud socho: ...?")
CLAUSE_PAUSE = 0.22       # a short breath at ";", ":" and "—" inside a statement (one long flow sounded like a paragraph)
QUESTION_SPEED = 0.97     # a question is asked a little slower than the answer is told (0.92 at the old pace 0.95)
CLAUSE = re.compile(r"\s*(?:;|:|—|–)\s*")
THINK = re.compile(r"\b(?:ruko|rukiye|ruk kar|socho|sochiye|sochie|sochein|sochen|soch kar|andaza|andaaza|anuman|guess|"
                   r"think|predict)\b|(?:रुको|रुकिए|रुकिये|रुककर|सोचो|सोचिए|सोचिये|सोचें|सोचकर|अंदाज़ा|अंदाजा|अनुमान)", re.I)
# Navin's Q14 verdict (21 November 2026): "aayiye jaante hai ... thoda ruko, pehle yaad kijiye bolo": every sentence of a
# line is said on its own, with a pause after its full stop, a longer one after an invitation
SENTENCE_PAUSE = 0.35
INVITE_PAUSE = 0.55
SENTENCE_END = re.compile(r"(?<=[.।!])\s+(?=[^\s\d])")
INVITE = re.compile(r"^(?:aaiye|aayiye|aaie|chaliye|dekhiye|आइए|आइये|आईए|आइयें|चलिए|चलिये|देखिए|देखिये|let's|let us)\b"
                    r"|^(?:आइए|आइये|आईए|चलिए|चलिये)", re.I)
INVITE_WORDS = 4          # "आइए जानते हैं", "चलिए पास से देखते हैं": an invitation, not a whole statement
CONVERT_TAU = 0.3         # OpenVoice's strength of the tone change (its default)
# the silence between two lines of a film (the player waits ``after`` seconds once a line's voice ends; 0.45 before this):
# a full stop's pause between lines, about a second before a new idea, and the shot change's own wait counted in
REVEAL_PAUSE = 1.0        # before a new idea inside a shot ("Ab dekhte hain ...") and, with the picture's own move, a new shot
REVEAL_EVERY = 30.0       # seconds of film between two long pauses at most once (teachers: one or two a minute)
SHOT_WAIT = {"dive": 1.6, "fade": 0.2}   # how long the player itself waits before a new shot's first line (studio_player)
NEW_IDEA = re.compile(r"^(?:ab\s+(?:dekh|jaan|samajh|samjh|baat|chal|aage|agl|is\b|yeh\b|ye\b)|aaiye|aayiye|chaliye|"
                      r"to\s+ab\b|next\b|now\s+(?:let|we)|let'?s\b)"
                      r"|^(?:अब\s+(?:देख|जान|समझ|बात|चल|आगे|अगल|इस|यह|ये)|आइए|आइये|आईए|चलिए|चलिये|तो\s+अब)", re.I)


def folder() -> Path:
    return Path(os.environ.get("BIE_KOKORO_DIR") or Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" / "kokoro")


def indic_folder(language: str) -> Path:
    return Path(os.environ.get("BIE_INDIC_TTS_DIR") or Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" /
                "indic-tts") / language


def narrator() -> str:
    return "navin" if os.environ.get("BIE_NARRATOR", "").strip().lower() == "navin" else "female"


# --- what the voice says for a formula or a short form (Navin, 21 November 2026: "teacher ki voice jo video mein aati hai
# wo molecules ke formula bolti hai usme galti karti hai co2 kehne ki bajaye carbon diaoxide bol de"). Measured with
# Kokoro's own phonemizer the same day: "सीओ₂" was said "सीओ दो", PSII "साई", NADPH "नाड्फ", H2O "एच दो ओ". The screen
# keeps the book's spelling; only the voice changes. A molecule with a name is said by its name, except right after the
# word formula ("jiska formula C6H12O6 hai"), where it is spelled; every other short form is spelled letter by letter.
LETTERS = {"A": "ए", "B": "बी", "C": "सी", "D": "डी", "E": "ई", "F": "एफ़", "G": "जी", "H": "एच", "I": "आई", "J": "जे",
           "K": "के", "L": "एल", "M": "एम", "N": "एन", "O": "ओ", "P": "पी", "Q": "क्यू", "R": "आर", "S": "एस", "T": "टी",
           "U": "यू", "V": "वी", "W": "डब्ल्यू", "X": "एक्स", "Y": "वाई", "Z": "ज़ेड"}
NUMBER_WORDS = {"0": "ज़ीरो", "1": "वन", "2": "टू", "3": "थ्री", "4": "फ़ोर", "5": "फ़ाइव", "6": "सिक्स", "7": "सेवन",
                "8": "एट", "9": "नाइन", "10": "टेन", "11": "इलेवन", "12": "ट्वेल्व", "14": "फ़ोर्टीन", "16": "सिक्सटीन",
                "18": "एटीन"}
SCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹₊₋⁺⁻", "01234567890123456789+-+-")
# named molecules: (the formula as written, without sub- or superscripts) -> (Hindi name, English name)
NAMED = {"CO2": ("कार्बन डाइऑक्साइड", "carbon dioxide"), "O2": ("ऑक्सीजन", "oxygen"), "H2O": ("पानी", "water"),
         "C6H12O6": ("ग्लूकोज़", "glucose"), "H2S": ("हाइड्रोजन सल्फ़ाइड", "hydrogen sulphide"),
         "NH3": ("अमोनिया", "ammonia"), "CH4": ("मीथेन", "methane"), "HCO3-": ("बाइकार्बोनेट", "bicarbonate"),
         "N2": ("नाइट्रोजन", "nitrogen"), "H2": ("हाइड्रोजन", "hydrogen")}
# short forms a teacher says in their own way (the rest are spelled)
SAID = {"PSII": ("पी एस टू", "P S two"), "PSI": ("पी एस वन", "P S one"), "PS II": ("पी एस टू", "P S two"),
        "PS I": ("पी एस वन", "P S one"), "RuBisCO": ("रूबिस्को", "rubisco"), "RuBisCo": ("रूबिस्को", "rubisco"),
        "Rubisco": ("रूबिस्को", "rubisco"), "RUBISCO": ("रूबिस्को", "rubisco"), "P680": ("पी सिक्स एटी", "P six eighty"),
        "P700": ("पी सेवन हंड्रेड", "P seven hundred"), "NEET": ("नीट", "NEET"), "Pi": ("पी आई", "P i"),
        "PEPcase": ("पेप केस", "pep case"), "PEPCase": ("पेप केस", "pep case")}
FORMULA_WORD = re.compile(r"(?:फ़ॉर्मूला|फार्मूला|फ़ार्मूला|फॉर्मूला|formula)\s*$", re.I)
DEVANAGARI_FORMULA = {"सीओ₂": "CO2", "सीओ2": "CO2", "सीओ टू": "CO2", "सीओटू": "CO2", "एच₂ओ": "H2O", "ओ₂": "O2",
                      "सी₃": "C3", "सी₄": "C4"}
# the film maker sometimes writes a reaction centre's number out in Hindi (films a13, a14, 22 November 2026: "पी छह सौ
# अस्सी", "पी सात सौ"); a teacher says "पी सिक्स एटी", so the name goes back to its short form before SAID reads it
DEVANAGARI_SAID = ((re.compile(r"पी\s*(?:छह सौ अस्सी|६८०|680)(?![०-९0-9])"), "P680"),
                   (re.compile(r"पी\s*(?:सात सौ|७००|700)(?![०-९0-9])(?!\s*(?:एक|दो|तीन|चार|पाँच|पांच|छह|सात|आठ|नौ|दस|बीस|तीस|चालीस|पचास|साठ|सत्तर|अस्सी|नब्बे))"),
                    "P700"))
TOKEN = re.compile(r"(?<![A-Za-z])(?:PS ?II|PS ?I(?![A-Za-z])|\[?[A-Z][A-Za-z]{0,6}(?:[0-9₀-₉⁰-⁹+⁺\-⁻]*[A-Za-z]*)*\]?)"
                   r"(?![A-Za-z])")
DEVANAGARI_LETTER = re.compile(r"[ऀ-ॿ]")
# units and signs said in words (teacher study, 22 November 2026; measured with Kokoro's own phonemizer that day: "680 nm"
# was said "en em", "25°C" lost its degree, "360 µL/L" was "micro L slash L", "3 × 6" and an arrow were dropped and "~"
# was "tilde"). "+", "=" and "%" it already says as plus, barabar and pratishat.
UNITS = ((r"[µμu][Ll]\s?/\s?[Ll]", "माइक्रोलीटर प्रति लीटर", "microlitres per litre"),
         (r"°\s?C|ºC|℃", "डिग्री सेल्सियस", "degrees Celsius"), (r"°\s?F", "डिग्री फ़ारेनहाइट", "degrees Fahrenheit"),
         (r"°|º", "डिग्री", "degrees"), (r"nm", "नैनोमीटर", "nanometres"), (r"[µμ]m", "माइक्रोमीटर", "micrometres"),
         (r"mm", "मिलीमीटर", "millimetres"), (r"cm", "सेंटीमीटर", "centimetres"), (r"km", "किलोमीटर", "kilometres"),
         (r"mg", "मिलीग्राम", "milligrams"), (r"kg", "किलोग्राम", "kilograms"), (r"m[Ll]", "मिलीलीटर", "millilitres"),
         (r"ppm", "पी पी एम", "parts per million"), (r"kJ", "किलोजूल", "kilojoules"), (r"kcal", "किलोकैलोरी", "kilocalories"))
UNIT = [(re.compile(r"(?<=\d)\s?(?:" + pattern + r")(?![A-Za-z])"), hi, en) for pattern, hi, en in UNITS]
SIGNS = ((re.compile(r"(?<=\d)\s?:\s?(?=\d)"), " अनुपात ", " to "),                 # 3:2, a ratio (not a clause's colon)
         (re.compile(r"\s*(?:→|⟶|->|⇒|➝)\s*"), " से ", " gives "),
         (re.compile(r"(?:≈|~|∼)\s*(?=\d)"), "लगभग ", "about "),
         (re.compile(r"\s*×\s*"), " गुणा ", " times "), (re.compile(r"\s*÷\s*"), " भाग ", " divided by "),
         (re.compile(r"\s*±\s*"), " प्लस माइनस ", " plus or minus "))
# Devanagari spellings Kokoro says better (A6; Navin's yes, 22 November 2026): the same word as the film maker writes it,
# respelled so the vowel or sound comes out as a teacher says it (phonemizer: "थायलाकोइड" ends "koːɪɖ", "थायलाकॉइड" ends
# "kɔɪɖ" as in thylakoid; "फियो" starts with an aspirated p, "फ़ियो" with f). The screen keeps the maker's spelling.
SPELLING = (("थाइलाकोइड", "थायलाकॉइड"), ("थायलाकोइड", "थायलाकॉइड"), ("थायलेकोइड", "थायलाकॉइड"), ("थाइलेकोइड", "थायलाकॉइड"),
            ("थायलाकोयड", "थायलाकॉइड"), ("कैरोटिनोइड", "कैरोटिनॉइड"), ("कैरोटेनोइड", "कैरोटिनॉइड"),
            ("कैरोटीनोइड", "कैरोटिनॉइड"), ("फियोफाइटिन", "फ़ियोफ़ाइटिन"), ("फ़ियोफाइटिन", "फ़ियोफ़ाइटिन"),
            ("फियोफ़ाइटिन", "फ़ियोफ़ाइटिन"), ("फेओफाइटिन", "फ़ियोफ़ाइटिन"), ("फ़ेओफ़ाइटिन", "फ़ियोफ़ाइटिन"),
            ("फैरेडॉक्सिन", "फ़ेरेडॉक्सिन"), ("फेरेडॉक्सिन", "फ़ेरेडॉक्सिन"), ("फेरेडोक्सिन", "फ़ेरेडॉक्सिन"),
            ("केमिओस्मोसिस", "केमिऑस्मोसिस"), ("कीमिओस्मोसिस", "केमिऑस्मोसिस"), ("ज़ैंथोफिल", "ज़ैंथोफ़िल"),
            ("जैंथोफिल", "ज़ैंथोफ़िल"), ("ऑक्सैलोएसिटिक", "ऑक्ज़ैलोएसिटिक"), ("ऑक्सालोएसिटिक", "ऑक्ज़ैलोएसिटिक"))
# what the voice may still meet once ``spoken`` has said a line: letters and marks of any script, digits, spaces, and the
# signs the engine says or pauses on. Anything else (a leftover arrow, slash, star, superscript ...) is skipped or misread.
SAYABLE = set(".,;:!?'\"()[]-–—।॥…‘’“”+=%")


def _spell(token: str, english: bool) -> str:
    """C6H12O6 -> "सी सिक्स एच ट्वेल्व ओ सिक्स"; NADP+ -> "एन ए डी पी प्लस"; 3-PGA -> handled by the caller."""
    out = []
    for piece in re.findall(r"[A-Z][a-z]?|[a-z]|\d+|\+|-", token):
        if piece.isdigit():
            out.append(piece if english else NUMBER_WORDS.get(piece, piece))
        elif piece == "+":
            out.append("plus" if english else "प्लस")
        elif piece == "-":
            out.append("minus" if english else "माइनस")
        else:
            out.append(" ".join(piece.upper()) if english else " ".join(LETTERS.get(c.upper(), c) for c in piece))
    return " ".join(out)


def spoken(text: str, language: str = "hi") -> str:
    """The line as the voice should say it: formulas by their names, short forms the way a teacher says them. Hindi and
    English only: a Tamil, Telugu, Malayalam or Marathi line is said by its own engine as the dub wrote it."""
    if language not in ("hi", "en"):
        return text
    english = language == "en"
    if not english:
        for written, better in SPELLING:
            text = text.replace(written, better)
    for pattern, hi, en in UNIT:
        text = pattern.sub(" " + (en if english else hi), text)
    for pattern, hi, en in SIGNS:
        text = pattern.sub(en if english else hi, text)
    for written, formula in DEVANAGARI_FORMULA.items():
        text = text.replace(written, formula)
    for pattern, short in DEVANAGARI_SAID:
        text = pattern.sub(short, text)

    def say(match):
        raw = match.group(0)
        after = text[match.end():match.end() + 1]
        joiner = raw.endswith("-") and after.isalpha()          # "H-कैरियर": a hyphen, not a minus
        said = _say(raw[:-1] if joiner else raw, match.start())
        if said == raw:
            return raw
        if joiner or DEVANAGARI_LETTER.match(after):
            said += " "
        if match.start() and text[match.start() - 1].isdigit():  # "2H+": the count, then the formula
            said = " " + said
        return said

    def _say(raw, start):
        token = raw.strip("[]").translate(SCRIPTS)
        before = text[:start]
        if token in SAID or raw in SAID:
            return SAID.get(token, SAID.get(raw))[1 if english else 0]
        bare = token.rstrip("+-")
        if token in NAMED and not FORMULA_WORD.search(before):
            return NAMED[token][1 if english else 0]
        if bare in NAMED and token.endswith(("+", "-")) and not FORMULA_WORD.search(before):
            return NAMED[bare][1 if english else 0] + (" आयन" if not english else " ion")
        uppers = sum(c.isupper() for c in token)
        if uppers >= 2 or (uppers == 1 and any(c.isdigit() or c in "+-" for c in token)):
            return _spell(token, english)
        return raw

    return TOKEN.sub(say, text)


def unsaid(text: str, language: str = "hi") -> list:
    """The signs of a line the voice cannot say (A5, Navin's yes, 22 November 2026: "bacha nishaan mila to voice step ruk
    jaaye"): what is left once ``spoken`` has put formulas, units and signs into words. Hindi and English only."""
    if language not in ("hi", "en"):
        return []
    import unicodedata
    left = []
    for char in spoken(text or "", language):
        kind = unicodedata.category(char)
        if kind[0] in "LMZ" or kind == "Nd" or char in SAYABLE or char.isspace():
            continue
        if char not in left:
            left.append(char)
    return left


def _clause_pause(bit: str) -> float:
    """The breath after a clause. A short invitation ("आइए जानते हैं;", "Chaliye dekhte hain:") gets INVITE_PAUSE whatever
    mark ends it: the makers write "Aaiye jaante hain;" as often as "Aaiye jaante hain." (Photosynthesis films q01, q02,
    q04 and q05, 21 November 2026), and Navin's Q14 verdict asks for the pause either way."""
    return INVITE_PAUSE if INVITE.search(bit) and len(bit.split()) <= INVITE_WORDS else CLAUSE_PAUSE


def parts(text: str) -> list:
    """The pieces a line is spoken in, with the silence after each: a question on its own with QUESTION_PAUSE after it;
    a statement in one flow, with a short breath (CLAUSE_PAUSE) at ";", ":" and "—"; every sentence on its own, with
    SENTENCE_PAUSE after its full stop (INVITE_PAUSE after an invitation: "Aaiye jaante hain." or "Aaiye jaante hain;").
    A question the learner is asked to think about first ("Ruko, pehle khud socho: ...?") gets THINK_PAUSE.
    "Band membrane kyun chahiye? Iska seedha sa jawab hai: jamav." -> [("Band membrane kyun chahiye?", 0.30),
    ("Iska seedha sa jawab hai", 0.22), ("jamav.", 0.0)]. A line that ends with its question keeps the question's pause
    at its end; ``gaps`` then adds nothing after it."""
    out = []
    for piece in [p.strip() for p in re.split(r"(?<=\?)\s*", (text or "").strip()) if p.strip()]:
        if piece.endswith("?"):
            out.append((piece, THINK_PAUSE if THINK.search(piece) else QUESTION_PAUSE))
            continue
        sentences = [x.strip() for x in SENTENCE_END.split(piece) if x.strip()]
        for n, sentence in enumerate(sentences):
            bits = [b.strip() for b in CLAUSE.split(sentence) if b.strip()]
            out.extend((b, _clause_pause(b)) for b in bits[:-1])
            last = n == len(sentences) - 1
            out.append((bits[-1], 0.0 if last else (INVITE_PAUSE if INVITE.search(sentence) else SENTENCE_PAUSE)))
    if out and out[-1][1] and not (text or "").strip().endswith("?"):
        out[-1] = (out[-1][0], 0.0)
    return out or [((text or "").strip() or ".", 0.0)]


def pace() -> float:
    """The voice's base pace: ``BIE_VOICE_PACE`` when it is set to a number in PACE_RANGE (a 1.05 copy for Navin's ear),
    else SPEED (1.00, his choice of 22 November 2026)."""
    try:
        value = float(os.environ.get(PACE_ENV, "") or SPEED)
    except ValueError:
        return SPEED
    return value if PACE_RANGE[0] <= value <= PACE_RANGE[1] else SPEED


def speed(part: str, base: float | None = None) -> float:
    """The pace a part is said at: the base pace, a question a little slower (QUESTION_SPEED / SPEED of it)."""
    base = base or pace()
    return round(base * QUESTION_SPEED / SPEED, 3) if part.endswith("?") else base


def gaps(lines: list) -> list:
    """The silence after each line of a film before the next line starts (the player's ``after``), from the lines in
    order: [{"text": the voice line, "dur": seconds, "shot_start": the first line of a shot, "dive": that shot opens by a
    dive}]. After a question nothing more (its pause is at the end of its own voice); before a new shot, what makes about a
    second with the shot's own wait (SHOT_WAIT), never less than a full stop's pause; before a new idea inside a shot
    ("Ab dekhte hain ...", "Aaiye ..."), REVEAL_PAUSE, but at most once in REVEAL_EVERY seconds; else SENTENCE_PAUSE."""
    out, since = [], REVEAL_EVERY                        # the film's opening counts as a long pause
    for n, line in enumerate(lines):
        text = (line.get("text") or "").strip()
        since += float(line.get("dur") or 0)
        nxt = lines[n + 1] if n + 1 < len(lines) else None
        if nxt is None:
            out.append(0.0)
            continue
        if text.endswith("?"):
            gap = 0.0
            if THINK.search(text):                       # a think question's pause is a long one too
                since = 0.0
        elif nxt.get("shot_start"):
            wait = SHOT_WAIT["dive" if nxt.get("dive") else "fade"]
            gap = max(SENTENCE_PAUSE, round(REVEAL_PAUSE - wait, 2))
            since = 0.0
        elif NEW_IDEA.search((nxt.get("text") or "").strip()) and since >= REVEAL_EVERY:
            gap, since = REVEAL_PAUSE, 0.0
        else:
            gap = SENTENCE_PAUSE
        since += gap
        out.append(gap)
    return out


class KokoroEngine:
    def __init__(self, language: str, who: str, *, fetch: bool = True, path: Path | None = None):
        if language not in KOKORO_VOICES[who]:
            raise LookupError(f"no Kokoro voice for {language!r}")
        self.voice, self.lang = KOKORO_VOICES[who][language]
        from kokoro_onnx import Kokoro            # optional: ImportError means "no voice"
        path = path or folder()
        path.mkdir(parents=True, exist_ok=True)
        for name, url in FILES.items():
            target = path / name
            if not target.exists():
                if not fetch:
                    raise FileNotFoundError(f"{target} is missing")
                with urllib.request.urlopen(url, timeout=600) as response, tempfile.NamedTemporaryFile(dir=path, delete=False) as tmp:
                    shutil.copyfileobj(response, tmp)
                Path(tmp.name).replace(target)
        self.engine = Kokoro(str(path / "kokoro-v1.0.onnx"), str(path / "voices-v1.0.bin"))
        self.label = f"kokoro {self.voice}"

    def speak(self, text: str, pace: float):
        import numpy as np
        made, rate = self.engine.create(text, voice=self.voice, speed=pace, lang=self.lang)
        return np.asarray(made, dtype="float32"), rate


def local_config(model: Path) -> Path:
    """AI4Bharat's configs name their speaker file by the path it had on their machine ("models/v1/ta/fastpitch/
    speakers.pth"); a copy beside the original names the file where it really is."""
    import json
    config = json.loads((model / "config.json").read_text(encoding="utf-8"))
    speakers = str((model / "speakers.pth").resolve())

    def fix(node):
        if isinstance(node, dict):
            return {k: (speakers if k == "speakers_file" and v else fix(v)) for k, v in node.items()}
        return [fix(x) for x in node] if isinstance(node, list) else node
    fixed = model / "config.bie.json"
    text = json.dumps(fix(config), ensure_ascii=False, indent=1)
    if not fixed.exists() or fixed.read_text(encoding="utf-8") != text:
        fixed.write_text(text, encoding="utf-8")
    return fixed


class IndicEngine:
    def __init__(self, language: str, who: str):
        base = indic_folder(language)
        model, vocoder = base / "fastpitch", base / "hifigan"
        for need in (model / "best_model.pth", model / "config.json", vocoder / "best_model.pth", vocoder / "config.json"):
            if not need.exists():
                raise FileNotFoundError(f"{need} is missing")
        from TTS.utils.synthesizer import Synthesizer     # optional: coqui-tts
        speakers = model / "speakers.pth"
        self.engine = Synthesizer(tts_checkpoint=str(model / "best_model.pth"), tts_config_path=str(local_config(model)),
                                  tts_speakers_file=str(speakers) if speakers.exists() else None,
                                  vocoder_checkpoint=str(vocoder / "best_model.pth"), vocoder_config=str(vocoder / "config.json"),
                                  use_cuda=False)
        self.speaker = INDIC_SPEAKER[who]
        self.label = f"indic-tts {language} {self.speaker}"

    def speak(self, text: str, pace: float):
        import numpy as np
        made = self.engine.tts(text, speaker_name=self.speaker, split_sentences=False)
        samples = np.asarray(made, dtype="float32")
        if abs(pace - 1.0) > 0.01:                          # FastPitch has no speed knob here: stretch without pitch change
            import librosa
            samples = librosa.effects.time_stretch(samples, rate=pace)
        return samples, self.engine.output_sample_rate


class Tone:
    """OpenVoice V2's tone-colour converter: the base voice's line in Navin's timbre (``BIE_VOICE_TONE``)."""

    def __init__(self, tone_file: Path | None = None, model_dir: Path | None = None):
        import numpy as np
        import torch
        from openvoice import utils
        from openvoice.models import SynthesizerTrn
        model_dir = model_dir or Path(os.environ.get("BIE_OPENVOICE_DIR") or
                                      Path(os.environ.get("BIE_HOME", "/var/lib/bie")) / "models" / "openvoice" / "converter")
        self.torch = torch
        self.hps = utils.get_hparams_from_file(str(model_dir / "config.json"))
        self.model = SynthesizerTrn(len(getattr(self.hps, "symbols", [])), self.hps.data.filter_length // 2 + 1,
                                    n_speakers=self.hps.data.n_speakers, **self.hps.model).eval()
        self.model.load_state_dict(torch.load(str(model_dir / "checkpoint.pth"), map_location="cpu")["model"], strict=False)
        self.rate = self.hps.data.sampling_rate
        self.target = torch.from_numpy(np.load(str(tone_file)).astype("float32")) if tone_file else None
        self.sources = {}

    def _spec(self, samples):
        from openvoice.mel_processing import spectrogram_torch
        d = self.hps.data
        return spectrogram_torch(self.torch.FloatTensor(samples).unsqueeze(0), d.filter_length, d.sampling_rate,
                                 d.hop_length, d.win_length, center=False)

    def tone_of(self, clips) -> "object":
        """The mean tone-colour vector of clips of one voice (each a few seconds of steady speech at ``self.rate``)."""
        with self.torch.no_grad():
            found = [self.model.ref_enc(self._spec(c).transpose(1, 2)).unsqueeze(-1) for c in clips if len(c) > self.rate]
        return self.torch.stack(found).mean(0)

    def convert(self, samples, rate: int, source_key: str, source_sample):
        """``source_sample`` () -> (samples, rate): a steady stretch of the base voice, asked for once per base voice."""
        import numpy as np
        samples = resample(samples, rate, self.rate)
        if source_key not in self.sources:                    # the base voice's own tone, once per base voice
            ref, ref_rate = source_sample()
            ref = resample(ref, ref_rate, self.rate)
            step = 8 * self.rate
            self.sources[source_key] = self.tone_of([ref[i:i + step] for i in range(0, len(ref), step)])
        with self.torch.no_grad():
            spec = self._spec(samples)
            out = self.model.voice_conversion(spec, self.torch.LongTensor([spec.size(-1)]), sid_src=self.sources[source_key],
                                              sid_tgt=self.target, tau=CONVERT_TAU)
        return np.asarray(out[0][0, 0].cpu().float().numpy(), dtype="float32"), self.rate


def resample(samples, rate: int, target: int):
    if rate == target:
        return samples
    import librosa
    return librosa.resample(samples, orig_sr=rate, target_sr=target)


# a steady stretch of each base voice for its own tone colour (said once per voice, never shown)
TONE_SAMPLE = {"hi": "Aaiye, aaj hum dekhte hain ki patte ke andar energy kaise banti hai, aur yeh kaam kaun karta hai.",
               "en": "Today we will see how a leaf turns sunlight into chemical energy, and which parts do the work.",
               "ta": "இன்று ஒரு இலை சூரிய ஒளியை எப்படி ஆற்றலாக மாற்றுகிறது என்று பார்ப்போம்.",
               "te": "ఈ రోజు ఒక ఆకు సూర్యకాంతిని ఎలా శక్తిగా మారుస్తుందో చూద్దాం.",
               "ml": "ഇന്ന് ഒരു ഇല സൂര്യപ്രകാശത്തെ എങ്ങനെ ഊർജമാക്കി മാറ്റുന്നു എന്ന് നോക്കാം.",
               "mr": "आज आपण पाहूया की एक पान सूर्यप्रकाशाचे ऊर्जेत कसे रूपांतर करते."}


def _tone_from_env() -> "Tone":
    tone_file = os.environ.get("BIE_VOICE_TONE", "")
    if not tone_file or not Path(tone_file).exists():
        raise FileNotFoundError("BIE_NARRATOR=navin needs BIE_VOICE_TONE (Navin's private tone file)")
    return Tone(Path(tone_file))


class Voice:
    def __init__(self, path: Path | None = None, *, fetch: bool = True, language: str = "hi", who: str | None = None,
                 tone: "Tone | None" = None, base_only: bool = False, pace: float | None = None):
        who = who or narrator()
        self.pace = pace if pace and PACE_RANGE[0] <= pace <= PACE_RANGE[1] else globals()["pace"]()
        if language in INDIC:
            self.engine = IndicEngine(language, who)
        elif language in KOKORO_VOICES[who]:
            self.engine = KokoroEngine(language, who, fetch=fetch, path=path)
        else:
            raise LookupError(f"no voice engine for {language!r} on this machine yet")
        self.language, self.who = language, who
        # base_only: the base voice alone (its timbre is changed later in one batch, ``tools/studio_revoice.py``)
        self.tone = None if base_only else (tone if tone is not None or who != "navin" else _tone_from_env())
        self.label = self.engine.label + (" · Navin ki tone" if self.tone else "") + \
            (f" · raftaar {self.pace:.2f}" if abs(self.pace - SPEED) > 0.001 else "")

    def say(self, text: str) -> dict:
        """{"uri": data URI (mp3 when ffmpeg is here, else wav), "dur": seconds}, said by BIE's teacher rules (``parts``).
        A line with a sign the voice cannot say is refused (``unsaid``), never said wrong; the film step reports it."""
        left = unsaid(text, self.language)
        if left:
            raise ValueError(f"the voice cannot say {' '.join(left)}")
        samples, rate = self.render(text)
        return clip(samples, rate)

    def render(self, text: str):
        """(samples, rate) of the line, said by BIE's teacher rules, in Navin's tone when a tone is set."""
        import numpy as np
        chunks, rate = [], 24000
        base = getattr(self, "pace", None) or pace()
        for part, pause in parts(spoken(text, self.language)):
            made, rate = self.engine.speak(part, speed(part, base))
            chunks.append(made)
            if pause:
                chunks.append(np.zeros(int(rate * pause), dtype="float32"))
        samples = np.concatenate(chunks) if chunks else np.zeros(1, dtype="float32")
        if self.tone is not None and len(samples) > rate // 2:
            samples, rate = self.tone.convert(samples, rate, self.engine.label,
                                              lambda: self.engine.speak(TONE_SAMPLE.get(self.language, TONE_SAMPLE["en"]), SPEED))
        return samples, rate


def clip(samples, rate: int) -> dict:
    """{"uri": data URI (mp3 when ffmpeg is here, else wav), "dur": seconds} for the film player."""
    wav = wav_bytes(samples, rate)
    mp3 = to_mp3(wav)
    data, mime = (mp3, "audio/mpeg") if mp3 else (wav, "audio/wav")
    return {"uri": f"data:{mime};base64," + base64.b64encode(data).decode("ascii"), "dur": round(len(samples) / rate, 3)}


def wav_bytes(samples, rate: int) -> bytes:
    """16-bit mono WAV through the standard library (no audio library needed to write it)."""
    import wave
    import numpy as np
    pcm = (np.clip(np.asarray(samples, dtype="float32"), -1.0, 1.0) * 32767).astype("<i2").tobytes()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(int(rate))
        out.writeframes(pcm)
    return buffer.getvalue()


def to_mp3(wav: bytes) -> bytes | None:
    if not shutil.which("ffmpeg"):
        return None
    done = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-b:a", "48k", "-f", "mp3", "pipe:1"],
                          input=wav, capture_output=True, timeout=120)
    return done.stdout if done.returncode == 0 and done.stdout else None


PLAYER_JS = Path(__file__).with_name("studio_voice_player.js")
VOICE_SLOT = "/*__VOICE__*/"


def with_player_voice(page: str) -> str:
    """The page with BIE's voice script (``studio_voice_player.js``) in its slot: the audio element with a data: URI first,
    Web Audio when the viewer refuses media loads, and a visible notice when neither can sound (Navin, 20 November 2026:
    the first films played silently)."""
    return page.replace(VOICE_SLOT, PLAYER_JS.read_text(encoding="utf-8"), 1)


def name(language: str = "hi") -> str:
    who = narrator()
    if language in INDIC:
        return f"indic-tts {language} {INDIC_SPEAKER[who]}"
    voice = KOKORO_VOICES[who].get(language)
    at = pace()
    return (f"kokoro {voice[0]}" + (f" · raftaar {at:.2f}" if abs(at - SPEED) > 0.001 else "")) if voice else "none"


def make(fetch: bool = True, language: str = "hi"):
    """A Voice, or None with the reason when this machine cannot speak yet (or not in this language)."""
    try:
        return Voice(fetch=fetch, language=language), None
    except Exception as exc:              # missing library, files or network: the film is still made, without voice
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"
