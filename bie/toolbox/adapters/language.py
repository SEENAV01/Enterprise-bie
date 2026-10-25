"""Languages and literature: a sentence in an Indian script cut into words and aksharas for BIE's kinetic text block
(Task 046a, batch 3).

- ``sentence``: Indic NLP Library tokenises the sentence and splits every word into orthographic syllables (aksharas);
  a lone visarga, anusvara or candrabindu joins the akshara before it, as a reader sees it; indic_transliteration
  writes each word in Roman (IAST by default, or ISO 15919). A gloss may be given per word; the punctuation (danda)
  stays with the word before it.
"""
from __future__ import annotations

from .base import need

JOINERS = {"ः", "ं", "ँ"}           # visarga, anusvara, candrabindu
PUNCTUATION = {"।", "॥", ",", ".", "?", "!"}


def _setup():
    from .. import sources
    need("indic-nlp")
    from indicnlp import common
    common.set_resources_path(str(sources.indic_nlp_resources()))
    from indicnlp.script import indic_scripts
    indic_scripts.init()


def sentence(text: str, *, lang: str = "sa", scheme: str = "iast", glosses=None) -> dict:
    _setup()
    sanscript = need("indic-transliteration")
    from indicnlp.syllable import syllabifier
    from indicnlp.tokenize import indic_tokenize
    import importlib.metadata
    target = {"iast": sanscript.IAST, "iso": sanscript.ISO}[scheme]
    words = []
    for token in indic_tokenize.trivial_tokenize(text, lang=lang):
        if token in PUNCTUATION and words:
            words[-1]["punct"] = token
            continue
        units = []
        for unit in syllabifier.orthographic_syllabify(token, lang):
            if units and unit in JOINERS:
                units[-1] += unit
            else:
                units.append(unit)
        words.append({"text": token, "aksharas": units, "roman": sanscript.transliterate(token, sanscript.DEVANAGARI, target)})
    if glosses is not None:
        if len(glosses) != len(words):
            raise ValueError(f"{len(glosses)} glosses for {len(words)} words")
        for word, gloss in zip(words, glosses):
            word["gloss"] = gloss
    return {"text": text, "lang": lang, "scheme": scheme.upper(), "words": words,
            "made_by": f"Indic NLP Library {importlib.metadata.version('indic-nlp-library')} (tokenise, syllabify) · "
                       f"indic_transliteration {importlib.metadata.version('indic-transliteration')} ({scheme.upper()})"}
