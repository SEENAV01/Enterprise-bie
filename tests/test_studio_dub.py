"""Autodub (Navin, 21 November 2026): a finished studio film said again in another language mix, technical terms in
English, checked by code line by line. Offline: fake maker, fake pictures, no voice engine."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import vm_studio  # noqa: E402
from bie.brain import studio_dub, studio_voice  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

KNOWN = frozenset({"thylakoid", "lumen", "channel", "atp", "synthase", "stroma"})
QUESTION = {"id": "q01", "question": "Jama protons ki waapsi se ATP kaise banta hai?", "points": []}


def film():
    return {"title": "Jama protons ki waapsi se ATP", "look": "glossy cutaway", "shots": [
        {"id": "s1", "title": "Patta", "key": "H+ lautte hain", "visual": {"type": "cutaway", "image_prompt": "x", "svg": ""},
         "sentences": [
             {"roman": "Patte ke andar jama H+ wapas niklein, toh ATP kaise ban jaata hai?",
              "pins": [{"label": "Patta", "x": 30, "y": 40}],
              "moves": [{"what": "dot", "colour": "red", "label": "H+", "points": [[10, 10], [60, 60]], "count": 3, "ms": 2400}]},
             {"roman": "Thylakoid ke andar lumen hai; CF0 channel deta hai.",
              "pins": [{"label": "Thylakoid", "x": 55, "y": 35}, {"label": "ATP synthase", "x": 70, "y": 60}]}]}]}


def tamil():
    return {"title": "சேர்ந்த protons திரும்புவதால் ATP", "question": "சேர்ந்த protons திரும்பும்போது ATP எப்படி உருவாகிறது?",
            "shots": [{"id": "s1", "title": "இலை", "key": "H+ திரும்புகின்றன"}],
            "lines": [{"id": "s1.0", "screen": "இலைக்குள் சேர்ந்த H+ திரும்ப வெளியேறினால், ATP எப்படி உருவாகிறது?",
                       "voice": "இலைக்குள் சேர்ந்த எச் பிளஸ் திரும்ப வெளியேறினால், ஏ டி பி எப்படி உருவாகிறது?"},
                      {"id": "s1.1", "screen": "Thylakoid உள்ளே lumen இருக்கிறது; CF0 ஒரு channel தருகிறது.",
                       "voice": "தைலகாய்டு உள்ளே லூமன் இருக்கிறது; சி எஃப் சீரோ ஒரு சேனல் தருகிறது."}],
            "labels": [{"from": "Patta", "to": "இலை"}, {"from": "H+", "to": "H+"}, {"from": "Thylakoid", "to": "Thylakoid"},
                       {"from": "ATP synthase", "to": "ATP synthase"}]}


def line(answer, lid):
    return next(x for x in answer["lines"] if x["id"] == lid)


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def chat(self, *, model, messages, schema=None):
        self.calls.append(messages)
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 10, "output_tokens": 5}}


class DubChecks(unittest.TestCase):
    def test_schema_strict(self):
        self.assertTrue(strict_ready(studio_dub.SCHEMA))

    def test_a_good_tamil_dub_passes(self):
        self.assertEqual(studio_dub.problems(tamil(), film(), "ta", known=KNOWN), [])

    def test_terms_to_keep(self):
        kept = studio_dub.kept_terms(film()["shots"][0]["sentences"][1]["roman"], studio_dub.labels(film()), KNOWN)
        self.assertEqual(kept, ["CF0", "Thylakoid"])
        self.assertTrue(studio_dub.technical("ADP + Pi → ATP"))
        self.assertFalse(studio_dub.technical("Patta", KNOWN))

    def test_a_question_must_stay_a_question(self):
        a = tamil()
        line(a, "s1.0")["screen"] = line(a, "s1.0")["screen"].replace("?", ".")
        self.assertTrue(any("question" in p for p in studio_dub.problems(a, film(), "ta", known=KNOWN)))

    def test_an_english_term_must_stay_english(self):
        a = tamil()
        line(a, "s1.0")["screen"] = line(a, "s1.0")["screen"].replace("ATP", "ஏடிபி")
        self.assertIn('s1.0: keep "ATP" in English on the screen line', studio_dub.problems(a, film(), "ta", known=KNOWN))

    def test_no_latin_in_the_voice_line_and_no_invented_english(self):
        a = tamil()
        line(a, "s1.1")["voice"] = line(a, "s1.1")["voice"].replace("சேனல்", "channel")
        line(a, "s1.0")["screen"] = line(a, "s1.0")["screen"].replace("திரும்ப", "energy")
        found = studio_dub.problems(a, film(), "ta", known=KNOWN)
        self.assertTrue(any(p.startswith("s1.1: the voice line must have no Latin") for p in found), found)
        self.assertTrue(any("does not have: energy" in p for p in found), found)

    def test_technical_labels_stay_and_lines_are_all_there(self):
        a = tamil()
        a["labels"][2]["to"] = "தைலகாய்டு"
        a["lines"] = a["lines"][:1]
        found = studio_dub.problems(a, film(), "ta", known=KNOWN)
        self.assertIn('label "Thylakoid" is technical: keep it exactly as "Thylakoid"', found)
        self.assertTrue(any("lines missing: s1.1" in p for p in found))

    def test_marathi_without_hindi_and_tamil_without_devanagari(self):
        a = tamil()
        line(a, "s1.1")["screen"] = "Thylakoid के अंदर lumen है; CF0 channel देता है."
        line(a, "s1.1")["voice"] = "थायलाकॉइड के अंदर ल्यूमन है; सी एफ झिरो चॅनल देता है."
        self.assertTrue(any("Devanagari letters in a Tamil line" in p for p in studio_dub.problems(a, film(), "ta", known=KNOWN)))
        found = studio_dub.problems(a, film(), "mr", known=KNOWN)
        self.assertTrue(any("Hindi words in the Marathi line" in p and "है" in p for p in found), found)

    def test_english_dub_is_plain_english(self):
        a = {"title": "ATP from returning protons", "question": "How is ATP made when the stored protons return?",
             "shots": [{"id": "s1", "title": "Leaf", "key": "H+ return"}],
             "lines": [{"id": "s1.0", "screen": "When the H+ stored inside the leaf comes back out, how is ATP made?",
                        "voice": "When the H plus stored inside the leaf comes back out, how is A T P made?"},
                       {"id": "s1.1", "screen": "Inside the Thylakoid is the lumen; CF0 gives a channel hai.",
                        "voice": "Inside the thylakoid is the lumen; C F 0 gives H+ a channel."}],
             "labels": [{"from": "Patta", "to": "Leaf"}, {"from": "H+", "to": "H+"}, {"from": "Thylakoid", "to": "Thylakoid"},
                        {"from": "ATP synthase", "to": "ATP synthase"}]}
        found = studio_dub.problems(a, film(), "en", known=KNOWN)
        self.assertTrue(any("Hinglish words left" in p and "hai" in p for p in found), found)
        self.assertTrue(any("say the formula signs in words" in p for p in found), found)

    def test_the_dubbed_film_keeps_places_and_motion(self):
        out = studio_dub.dubbed(film(), tamil())
        first = out["shots"][0]["sentences"][0]
        self.assertEqual(first["roman"], line(tamil(), "s1.0")["screen"])
        self.assertEqual(first["voice"], line(tamil(), "s1.0")["voice"])
        self.assertEqual(first["hinglish"], film()["shots"][0]["sentences"][0]["roman"])
        self.assertEqual((first["pins"][0]["label"], first["pins"][0]["x"]), ("இலை", 30))
        self.assertEqual(first["moves"][0]["points"], [[10, 10], [60, 60]])
        self.assertEqual(out["shots"][0]["title"], "இலை")
        self.assertEqual(out["shots"][0]["sentences"][1]["pins"][0]["label"], "Thylakoid")

    def test_the_maker_is_told_its_problems_and_tries_again(self):
        bad = tamil()
        line(bad, "s1.0")["screen"] = line(bad, "s1.0")["screen"].replace("ATP", "ஏடிபி")
        client = FakeClient([bad, tamil()])
        record = studio_dub.dub(client, "m", film(), QUESTION, "ta", known=KNOWN)
        self.assertEqual(record["problems"], [])
        self.assertEqual(len(record["rounds"]), 2)
        self.assertIn('keep "ATP" in English', client.calls[1][-1]["content"])
        prompt = client.calls[0][0]["content"] + client.calls[0][1]["content"]
        for rule in ("Tanglish", "a question stays a question", "no Latin letters", "Patta (everyday: say it in Tamil)",
                     "Thylakoid (technical: keep)"):
            self.assertIn(rule, prompt)
        with self.assertRaises(ValueError):
            studio_dub.dub(client, "m", film(), QUESTION, "xx")

    def test_no_voice_engine_yet_for_tamil(self):
        voice, why = studio_voice.make(fetch=False, language="ta")
        self.assertIsNone(voice)
        self.assertIn("no voice engine for 'ta'", why)
        self.assertEqual(studio_voice.name("ta"), "none")


class DubStage(unittest.TestCase):
    def test_the_stage_dubs_a_finished_film(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / "films-run"
            (run / "films" / "img").mkdir(parents=True)
            (run / "questions.json").write_text(json.dumps({"chapter_title": "Photosynthesis", "questions": [QUESTION]}),
                                                encoding="utf-8")
            (run / "films" / "q01.json").write_text(json.dumps({"film": film(), "images": {"s1": "q01-s1.png"}}), encoding="utf-8")
            buffer = io.BytesIO()
            Image.new("RGB", (32, 18), (40, 120, 60)).save(buffer, "PNG")
            (run / "films" / "img" / "q01-s1.png").write_bytes(buffer.getvalue())
            args = SimpleNamespace(stage="dub", source="", from_run=str(run), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="NEET", language="ta", model="", max_rounds=2)
            summary = vm_studio.run(args, client=FakeClient([tamil()]), load=None,
                                    voice_maker=lambda language="hi": (None, "no engine"))
            out = Path(folder) / "out"
            # no chapter given here, so "Thylakoid" is not known as a chapter word: the check still asks for CF0, H+, ATP
            self.assertIn(summary["status"], ("ok", "needs_fix"), summary)
            page = (out / "dub" / "ta" / "q01.html").read_text(encoding="utf-8")
            self.assertIn("data:image/webp;base64,", page)
            self.assertIn("எப்படி உருவாகிறது", page)
            record = json.loads((out / "dub" / "ta" / "q01.json").read_text(encoding="utf-8"))
            self.assertEqual(record["language"], "ta")
            self.assertIn("Tamil", (out / "DUB.md").read_text(encoding="utf-8"))
            self.assertEqual(summary["voice"], {"ta": "no voice (no engine)"})

    def test_the_stage_needs_language_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(stage="dub", source="", from_run=folder, videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=1)
            summary = vm_studio.run(args, client=FakeClient([]), load=None, voice_maker=lambda language="hi": (None, "x"))
            self.assertIn("--language for dub", summary["error"])


if __name__ == "__main__":
    unittest.main()
