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
import codex_vm  # noqa: E402
import studio_revoice  # noqa: E402
import voice_tone  # noqa: E402
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

    def test_a_machine_without_the_tamil_engine_makes_the_film_without_voice(self):
        with tempfile.TemporaryDirectory() as folder:
            import os
            old = os.environ.get("BIE_INDIC_TTS_DIR")
            os.environ["BIE_INDIC_TTS_DIR"] = folder
            try:
                voice, why = studio_voice.make(fetch=False, language="ta")
            finally:
                os.environ.pop("BIE_INDIC_TTS_DIR") if old is None else os.environ.__setitem__("BIE_INDIC_TTS_DIR", old)
        self.assertIsNone(voice)
        self.assertIn("best_model.pth is missing", why)
        self.assertEqual(studio_voice.name("ta"), "indic-tts ta female")
        voice, why = studio_voice.make(fetch=False, language="xx")
        self.assertIn("no voice engine for 'xx'", why)


class TeacherVoice(unittest.TestCase):
    """BIE's teacher rules for saying a line, and the tone colour step, with a fake engine (no models offline)."""

    def test_a_question_then_a_breath_at_each_clause(self):
        self.assertEqual(studio_voice.parts("Band membrane kyun chahiye? Iska seedha sa jawab hai: jamav; aur kuch nahi."),
                         [("Band membrane kyun chahiye?", studio_voice.QUESTION_PAUSE),
                          ("Iska seedha sa jawab hai", studio_voice.CLAUSE_PAUSE), ("jamav", studio_voice.CLAUSE_PAUSE),
                          ("aur kuch nahi.", 0.0)])
        self.assertLess(studio_voice.speed("Kyun?"), studio_voice.speed("Isliye."))

    def test_each_sentence_on_its_own_and_a_longer_pause_after_an_invitation(self):
        # Navin's Q14 verdict: "aayiye jaante hai ... thoda ruko, pehle yaad kijiye bolo"
        self.assertEqual(studio_voice.parts("आइए जानते हैं। पहले याद कीजिए कि पत्ते में आती लाइट की एनर्जी काम करती है।"),
                         [("आइए जानते हैं।", studio_voice.INVITE_PAUSE),
                          ("पहले याद कीजिए कि पत्ते में आती लाइट की एनर्जी काम करती है।", 0.0)])
        self.assertEqual(studio_voice.parts("Yeh CO2 3.5 guna hai. Ab aage chalte hain."),
                         [("Yeh CO2 3.5 guna hai.", studio_voice.SENTENCE_PAUSE), ("Ab aage chalte hain.", 0.0)])
        self.assertGreater(studio_voice.INVITE_PAUSE, studio_voice.SENTENCE_PAUSE)

    def test_an_invitation_before_a_semicolon_gets_the_same_pause(self):
        # Photosynthesis films q01, q02, q04, q05 (21 November 2026) all wrote "आइए जानते हैं;", which got only a breath
        self.assertEqual(studio_voice.parts("आइए जानते हैं; रोटी के पीछे गेहूँ का पौधा मिलता है।"),
                         [("आइए जानते हैं", studio_voice.INVITE_PAUSE), ("रोटी के पीछे गेहूँ का पौधा मिलता है।", 0.0)])
        # a long clause that only starts with an invitation word is a statement: a breath, not the invitation pause
        self.assertEqual(studio_voice.parts("देखिए, ब्लू और रेड रीजन्स से ज़्यादा O2 निकलती है; इसलिए बैक्टीरिया वहीं जमा होते हैं।"),
                         [("देखिए, ब्लू और रेड रीजन्स से ज़्यादा O2 निकलती है", studio_voice.CLAUSE_PAUSE),
                          ("इसलिए बैक्टीरिया वहीं जमा होते हैं।", 0.0)])

    def test_the_passed_q14_film_is_said_as_before(self):
        # the invitation rule must not change how any line of Navin's passed Q14 film is said
        import gzip
        film = json.load(gzip.open(ROOT / "tests" / "fixtures" / "passed_outputs" / "studio" / "photosynthesis-q14.json.gz"))["film"]
        for shot in film["shots"]:
            for sentence in shot["sentences"]:
                for bit, pause in studio_voice.parts(sentence["voice"]):
                    if pause == studio_voice.INVITE_PAUSE:          # only after a full stop, as when Navin passed it
                        self.assertRegex(bit, r"[.।!]$", sentence["voice"])

    def test_a_think_question_waits_longer_than_one_answered_at_once(self):
        # teacher study and Navin's ear (22 November 2026): "Naye wala sahi hai"
        self.assertEqual(studio_voice.parts("Oxygen aati kahan se hai? Woh aati hai paani se."),
                         [("Oxygen aati kahan se hai?", studio_voice.QUESTION_PAUSE), ("Woh aati hai paani se.", 0.0)])
        self.assertEqual(studio_voice.parts("Ruko, pehle khud socho: paani na ho to kya hoga? Dekho, kuch bacteria H2S lete hain."),
                         [("Ruko, pehle khud socho: paani na ho to kya hoga?", studio_voice.THINK_PAUSE),
                          ("Dekho, kuch bacteria H2S lete hain.", 0.0)])
        self.assertEqual(studio_voice.parts("रुको, पहले खुद सोचो, पानी न हो तो क्या होगा?")[0][1], studio_voice.THINK_PAUSE)
        self.assertEqual((studio_voice.QUESTION_PAUSE, studio_voice.THINK_PAUSE), (0.30, 0.90))

    def test_the_pace_is_one_and_a_copy_can_be_faster(self):
        # Navin, 22 November 2026: "Mujhe 1.00 wala shi lga abhi ke liye isko use krenge"; a 1.05 copy for his ear
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {studio_voice.PACE_ENV: ""}):
            self.assertEqual(studio_voice.pace(), 1.00)
            self.assertEqual(studio_voice.speed("Isliye."), 1.00)
            self.assertEqual(studio_voice.speed("Kyun?"), 0.97)
        with mock.patch.dict(os.environ, {studio_voice.PACE_ENV: "1.05"}):
            self.assertEqual(studio_voice.pace(), 1.05)
            self.assertEqual(studio_voice.speed("Kyun?"), round(1.05 * 0.97, 3))
            self.assertIn("raftaar 1.05", studio_voice.name("hi"))
        for wrong in ("fast", "3"):
            with mock.patch.dict(os.environ, {studio_voice.PACE_ENV: wrong}):
                self.assertEqual(studio_voice.pace(), 1.00)
        self.assertEqual(studio_voice.speed("Isliye.", 1.05), 1.05)

    def test_the_gaps_between_lines(self):
        line = lambda text, dur=4.0, **kw: dict({"text": text, "dur": dur}, **kw)
        found = studio_voice.gaps([line("Oxygen aati kahan se hai?"), line("Woh aati hai paani se."),
                                   line("Paani tootta hai."), line("Ab dekhte hain yeh kahan hota hai."),
                                   line("Thylakoid ke andar."), line("Ab is H+ ko dekhiye."),
                                   line("Naya chitra.", shot_start=True, dive=True), line("Aur ek.", shot_start=True),
                                   line("Aakhri baat.")])
        # the question stays on the screen a second after it is asked (Navin, 24 November 2026, 19:21); part of that
        # second is already in its own voice
        self.assertEqual(found[0], round(studio_voice.ASK_PAUSE - studio_voice.QUESTION_PAUSE, 2))
        self.assertEqual(found[1], studio_voice.SENTENCE_PAUSE)
        self.assertEqual(found[2], studio_voice.REVEAL_PAUSE)             # a new idea, the film's first long pause
        self.assertEqual(found[4], studio_voice.SENTENCE_PAUSE)           # another new idea 8 s later: no long pause
        self.assertEqual(found[5], studio_voice.SENTENCE_PAUSE)           # a dive already waits 1.6 s
        self.assertEqual(found[6], round(studio_voice.REVEAL_PAUSE - studio_voice.SHOT_WAIT["fade"], 2))
        self.assertEqual(found[-1], 0.0)
        later = studio_voice.gaps([line("Paani tootta hai.", 31.0), line("Ab dekhte hain aage.")])
        self.assertEqual(later[0], studio_voice.REVEAL_PAUSE)

    def test_units_and_signs_are_said_in_words_and_the_rest_refused(self):
        self.assertEqual(studio_voice.spoken("680 nm par, 25°C aur 360 µL/L; 3:2; ADP → ATP; ~10 guna; 3 × 6"),
                         "680 नैनोमीटर par, 25 डिग्री सेल्सियस aur 360 माइक्रोलीटर प्रति लीटर; 3 अनुपात 2; ए डी पी से ए टी पी; "
                         "लगभग 10 guna; 3 गुणा 6")
        self.assertEqual(studio_voice.spoken("680 nm; 35 °C; 3:2; ADP → ATP", "en"),
                         "680 nanometres; 35 degrees Celsius; 3 to 2; A D P gives A T P")
        self.assertEqual(studio_voice.spoken("Jawab hai: 3 cheezein"), "Jawab hai: 3 cheezein")   # a clause, not a ratio
        self.assertEqual(studio_voice.unsaid("कार्बन की गिनती 5 + 1 = 3 + 3 रहती है।"), [])
        self.assertEqual(studio_voice.unsaid("[CH2O] प्लस O2; H+ ions, 1% light"), [])
        self.assertEqual(studio_voice.unsaid("ATP/NADPH * 10⁶"), ["/", "*", "⁶"])
        self.assertEqual(studio_voice.unsaid("ATP/NADPH", "ta"), [])        # the Indic engines read their own script

        class Engine:
            label = "fake"

            def speak(self, text, pace):
                import numpy as np
                return np.ones(10, dtype="float32"), 1000
        voice = studio_voice.Voice.__new__(studio_voice.Voice)
        voice.engine, voice.tone, voice.language, voice.who, voice.pace = Engine(), None, "hi", "female", 1.0
        with self.assertRaisesRegex(ValueError, "cannot say /"):
            voice.say("3 ATP/2 NADPH")

    def test_the_spelling_list_is_for_the_voice_only(self):
        self.assertEqual(studio_voice.spoken("थायलाकोइड के अंदर फियोफाइटिन"), "थायलाकॉइड के अंदर फ़ियोफ़ाइटिन")
        # Navin, 25 November 2026: "cf0 ko safe bolna" -- CF said as two letters
        self.assertEqual(studio_voice.spoken("सीएफ़ ज़ीरो और सीएफ वन"), "सी एफ़ ज़ीरो और सी एफ़ वन")
        self.assertEqual(studio_voice.spoken("CF₀ से"), studio_voice.spoken("सीएफ़ ज़ीरो से"))
        self.assertEqual(studio_voice.spoken("थायलाकोइड्स", "en"), "थायलाकोइड्स")
        for written, better in studio_voice.SPELLING:
            self.assertNotEqual(written, better)
            self.assertEqual(studio_voice.spoken(better), better)           # a respelled word stays as it is

    def test_the_passed_q14_film_is_never_refused(self):
        import gzip
        film = json.load(gzip.open(ROOT / "tests" / "fixtures" / "passed_outputs" / "studio" / "photosynthesis-q14.json.gz"))["film"]
        for shot in film["shots"]:
            for sentence in shot["sentences"]:
                self.assertEqual(studio_voice.unsaid(sentence["voice"]), [], sentence["voice"])

    def test_the_line_is_said_part_by_part_then_turned_to_his_tone(self):
        import numpy as np

        class Engine:
            label = "fake"
            said = []

            def speak(self, text, pace):
                self.said.append((text, pace))
                return np.ones(1000, dtype="float32"), 1000

        class Tone:
            calls = 0

            def convert(self, samples, rate, key, sample):
                Tone.calls += 1
                return samples * 0.5, rate
        voice = studio_voice.Voice.__new__(studio_voice.Voice)
        voice.engine, voice.tone, voice.language, voice.who = Engine(), Tone(), "hi", "navin"
        made = voice.say("Kyun chahiye? Jawab hai: jamav.")
        # 3 parts of 1 s, a question pause and one clause breath
        self.assertAlmostEqual(made["dur"], 3 + studio_voice.QUESTION_PAUSE + studio_voice.CLAUSE_PAUSE, places=2)
        self.assertEqual([p for _, p in Engine.said], [studio_voice.QUESTION_SPEED, studio_voice.SPEED, studio_voice.SPEED])
        self.assertEqual(Tone.calls, 1)
        self.assertTrue(made["uri"].startswith("data:audio/"))

    def test_the_indic_config_names_its_speaker_file_where_it_is(self):
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / "ta" / "fastpitch"
            model.mkdir(parents=True)
            (model / "config.json").write_text(json.dumps({"model": "fast_pitch", "speakers_file": "models/v1/ta/fastpitch/speakers.pth",
                                                           "model_args": {"speakers_file": "models/v1/ta/fastpitch/speakers.pth"}}))
            fixed = json.loads(studio_voice.local_config(model).read_text(encoding="utf-8"))
            where = str((model / "speakers.pth").resolve())
            self.assertEqual((fixed["speakers_file"], fixed["model_args"]["speakers_file"]), (where, where))

    def test_navin_narrator_needs_his_private_tone_file(self):
        import os
        old = {k: os.environ.get(k) for k in ("BIE_NARRATOR", "BIE_VOICE_TONE")}
        os.environ["BIE_NARRATOR"], os.environ["BIE_VOICE_TONE"] = "navin", "/nonexistent/tone.npy"
        try:
            self.assertEqual(studio_voice.narrator(), "navin")
            self.assertEqual(studio_voice.name("hi"), "kokoro hm_omega")
            with self.assertRaises(FileNotFoundError):
                studio_voice._tone_from_env()
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


class FormulasAreSaidByName(unittest.TestCase):
    """Navin, 21 November 2026: "co2 kehne ki bajaye carbon dioxide bol de"; the screen keeps the book's spelling."""

    def test_a_molecule_is_said_by_its_name(self):
        say = studio_voice.spoken
        self.assertEqual(say("इसका जवाब है सीओ₂, जो एन्ज़ाइम्स तक पहुँचती है"), "इसका जवाब है कार्बन डाइऑक्साइड, जो एन्ज़ाइम्स तक पहुँचती है")
        self.assertEqual(say("CO2 प्लस H2O से [CH2O] प्लस O2"), "कार्बन डाइऑक्साइड प्लस पानी से सी एच टू ओ प्लस ऑक्सीजन")
        self.assertEqual(say("Plants take in CO₂ and give out O₂.", "en"), "Plants take in carbon dioxide and give out oxygen.")

    def test_right_after_the_word_formula_it_is_spelled(self):
        self.assertEqual(studio_voice.spoken("जिसका फ़ॉर्मूला C6H12O6 है"), "जिसका फ़ॉर्मूला सी सिक्स एच ट्वेल्व ओ सिक्स है")

    def test_a_reaction_centre_written_out_in_hindi_is_said_the_teachers_way(self):
        # films a13 and a14 (22 November 2026) wrote "पी छह सौ अस्सी" and "पी सात सौ" in their voice lines
        say = studio_voice.spoken
        self.assertEqual(say("पी छह सौ अस्सी का इलेक्ट्रॉन निकल गया"), "पी सिक्स एटी का इलेक्ट्रॉन निकल गया")
        self.assertEqual(say("फिर पी सात सौ को दूसरा boost मिलता है"), "फिर पी सेवन हंड्रेड को दूसरा boost मिलता है")
        self.assertEqual(say("पी सात सौ बीस नहीं"), "पी सात सौ बीस नहीं")          # another number is left alone

    def test_short_forms_are_said_the_way_a_teacher_says_them(self):
        say = studio_voice.spoken
        self.assertEqual(say("PSII से PSI तक, फिर NADP+ से NADPH"), "पी एस टू से पी एस वन तक, फिर एन ए डी पी प्लस से एन ए डी पी एच")
        self.assertEqual(say("C3 और C₄ पौधे, सी₃ एसिड"), "सी थ्री और सी फ़ोर पौधे, सी थ्री एसिड")
        self.assertEqual(say("RuBisCO पर RuBP, फिर 2H+ और P680"), "रूबिस्को पर आर यू बी पी, फिर 2 एच प्लस और पी सिक्स एटी")
        self.assertEqual(say("मेज़ोफ़िल की PEPकेस"), "मेज़ोफ़िल की पी ई पी केस")

    def test_other_languages_keep_their_own_lines(self):
        self.assertEqual(studio_voice.spoken("ஒளிச்சேர்க்கையில் CO2 தேவை", "ta"), "ஒளிச்சேர்க்கையில் CO2 தேவை")

    def test_ordinary_words_are_left_alone(self):
        for line in ("पौधा खाना खाता नहीं, तो हमारी थाली का खाना आता कहाँ से है?", "Calvin ने chlorophyll a देखा।",
                     "Aaiye jaante hain."):
            self.assertEqual(studio_voice.spoken(line), line)

    def test_the_voice_says_the_spoken_form(self):
        class Engine:
            label = "fake"
            said = []

            def speak(self, text, pace):
                import numpy as np
                self.said.append(text)
                return np.zeros(240, dtype="float32"), 24000

        voice = studio_voice.Voice.__new__(studio_voice.Voice)
        voice.engine, voice.language, voice.who, voice.tone, voice.label = Engine(), "hi", "female", None, "fake"
        voice.render("पत्ता CO2 लेता है।")
        self.assertEqual(Engine.said, ["पत्ता कार्बन डाइऑक्साइड लेता है।"])


class ToneFromHisRecording(unittest.TestCase):
    """Only the clean stretches of Navin's reading make his tone colour (his slips are left out)."""

    @staticmethod
    def words(spec):
        out, t = [], 0.0
        for word, gap, p in spec:
            t += gap
            out.append({"w": word, "s": t, "e": t + 0.4, "p": p})
            t += 0.4
        return out

    def test_pauses_restarts_and_unsure_words_end_a_stretch(self):
        steady = [(f"shabd{i}", 0.05, 0.9) for i in range(12)]          # 12 words, about 5.4 s
        spec = steady + [("ruk", 2.0, 0.9)] + [("phir", 0.05, 0.9), ("phir", 0.05, 0.9)] + steady + [("hmm", 0.05, 0.2)] \
            + [(f"chhota{i}", 0.05, 0.9) for i in range(3)]
        clean = voice_tone.stretches(self.words(spec))
        self.assertEqual(len(clean), 2)                                 # the short tail and the restart are left out
        for c in clean:
            self.assertGreaterEqual(c["e"] - c["s"], voice_tone.LO)
        found = voice_tone.report(self.words(spec), 20.0, clean)
        self.assertEqual((found["pauses_over_0_8s"], found["restarts"], found["unsure_words"]), (1, 1, 1))
        self.assertEqual(found["clean_stretches"], 2)

    def test_a_long_run_is_cut_into_stretches(self):
        clean = voice_tone.stretches(self.words([(f"shabd{i}", 0.05, 0.9) for i in range(60)]))
        self.assertGreaterEqual(len(clean), 2)
        self.assertTrue(all(c["e"] - c["s"] <= voice_tone.HI + 1 for c in clean))

    def test_the_tone_never_goes_into_the_repository(self):
        with self.assertRaises(SystemExit):
            voice_tone.main(["--recording", "x.m4a", "--out", str(ROOT / "docs" / "tone")])


class Revoice(unittest.TestCase):
    def test_a_finished_page_is_said_again_and_its_timing_follows(self):
        from bie.brain import studio_film
        template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        dubbed = studio_dub.dubbed(film(), tamil())
        old = studio_film.player_data(dubbed, images={"s1": "data:image/webp;base64,AAAA"}, audio={}, chapter="Photosynthesis",
                                      question=QUESTION, tint="#3f7d4e")
        page = studio_film.html(old, template)

        class Voice:
            label = "fake"
            lines = []

            def say(self, text):
                self.lines.append(text)
                return {"uri": "data:audio/mpeg;base64,BBBB", "dur": 7.5}
        voice = Voice()
        new_page, report = studio_revoice.revoice(page, {"film": dubbed}, voice, template=template)
        data = studio_revoice.page_data(new_page)
        self.assertEqual(voice.lines[0], line(tamil(), "s1.0")["voice"])          # the voice line, not the subtitle
        self.assertEqual(data["shots"][0]["img"], "data:image/webp;base64,AAAA")
        self.assertEqual([s["dur"] for s in data["shots"][0]["sentences"]], [7.5, 7.5])
        self.assertEqual((data["chapter"], data["tint"], data["qid"]), ("Photosynthesis", "#3f7d4e", "q01"))
        self.assertEqual((report["lines"], report["voice_seconds"]), (2, 15.0))

    def test_his_voice_comes_from_one_batch_conversion_of_the_base_lines(self):
        from bie.brain import studio_film
        import numpy as np
        template = (ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        dubbed = studio_dub.dubbed(film(), tamil())
        page = studio_film.html(studio_film.player_data(dubbed, images={}, audio={}, chapter="P", question=QUESTION), template)

        class Base:
            label = "base"

            def render(self, text):
                return np.zeros(8000, dtype="float32"), 8000          # 1 s each

        fake = Path(tempfile.mkdtemp())
        worker = fake / "worker.py"
        # a stand-in for the voice environment's worker: "converts" by doubling each line's length
        worker.write_text("import json,sys,wave\nfrom pathlib import Path\na=sys.argv\nreq=json.load(open(a[2]))\n"
                          "out=Path(req['audio_dir']);out.mkdir(parents=True,exist_ok=True)\nrows=[]\n"
                          "for it in req['convert']:\n"
                          "    r=wave.open(it['wav']);fr=r.readframes(r.getnframes());rate=r.getframerate();r.close()\n"
                          "    w=wave.open(str(out/(it['key']+'.wav')),'wb');w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)\n"
                          "    w.writeframes(fr+fr);w.close();rows.append({'key':it['key'],'compute_s':0.5})\n"
                          "json.dump({'status':'ok','converted':rows,'target':req['target']},open(a[4],'w'))\n")
        private = fake / "private"
        private.mkdir()

        def convert(files):
            return studio_revoice.chatterbox_convert(files, target=fake / "his.wav", private=private, python=sys.executable,
                                                     worker=worker, revision="pinned")
        new_page, report = studio_revoice.revoice(page, {"film": dubbed}, Base(), template=template, convert=convert,
                                                  private=private)
        data = studio_revoice.page_data(new_page)
        self.assertEqual([s["dur"] for s in data["shots"][0]["sentences"]], [2.0, 2.0])
        self.assertEqual(report["not_converted"], [])
        self.assertEqual(report["convert_seconds"], 1.0)
        request = json.loads((private / "request.json").read_text(encoding="utf-8"))
        self.assertEqual((request["model_revision"], [x["key"] for x in request["convert"]]), ("pinned", ["s1-0", "s1-1"]))

    def test_his_copy_can_keep_the_female_voices_way_of_speaking(self):
        """Navin, 23 November 2026: "female voice ... uske pattern ko pakdo wo meri aawaj par lagao": with --base female
        the female voice says the lines and Chatterbox turns them into his timbre; the default stays the male base."""
        from unittest import mock
        from bie.brain import studio_voice
        seen = []

        class FakeVoice:
            label = "fake"

            def __init__(self, **kw):
                seen.append((kw.get("who"), kw.get("base_only")))

        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder)
            for name in ("p.html", "f.json", "his.wav"):
                (f / name).write_text("{}", encoding="utf-8")
            args = ["--page", str(f / "p.html"), "--film", str(f / "f.json"), "--language", "hi", "--narrator", "navin",
                    "--target", str(f / "his.wav"), "--voice-python", sys.executable, "--private", str(f / "work"),
                    "--out", str(f / "out.html")]
            with mock.patch.object(studio_voice, "Voice", FakeVoice), \
                    mock.patch.object(studio_revoice, "revoice", return_value=("<html></html>", {"lines": 0})):
                studio_revoice.main(args + ["--base", "female"])
                studio_revoice.main(args)
        self.assertEqual(seen, [("female", True), ("navin", True)])

    def test_navin_pages_stay_out_of_the_repository(self):
        for extra in (["--narrator", "navin", "--tone", "/nonexistent.npy", "--out", str(ROOT / "x.html")],
                      ["--narrator", "navin", "--converter", "openvoice", "--out", "/tmp/x.html"],
                      ["--narrator", "navin", "--out", "/tmp/x.html", "--private", str(ROOT / "work")],
                      ["--narrator", "navin", "--out", "/tmp/x.html"]):
            with self.assertRaises(SystemExit):
                studio_revoice.main(["--page", "p.html", "--film", "f.json", "--language", "hi"] + extra)


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

    def test_language_codes_may_be_separated_by_spaces(self):
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(stage="dub", source="", from_run=folder, videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="ta te", model="", max_rounds=1)
            (Path(folder) / "questions.json").write_text(json.dumps({"questions": []}), encoding="utf-8")
            summary = vm_studio.run(args, client=FakeClient([]), load=None, voice_maker=lambda language="hi": (None, "x"))
            self.assertEqual(summary["voice"], {"ta": "no voice (x)", "te": "no voice (x)"})

    def test_the_vm_accepts_a_dub_job_and_runs_the_fixed_tool(self):
        job = {"job": "bie.vm-job/1", "id": "studio-dub-test", "section": "studio", "stage": "dub",
               "from_run": "https://raw.githubusercontent.com/x/y/z/run", "language": "ta te ml mr en", "videos": "q14",
               "maker": "codex", "reviewer": "codex", "max_inr": 1, "max_rounds": 3}
        cmd = codex_vm.argv(codex_vm.validate(dict(job)), Path("/tmp/out"), "python")
        self.assertEqual(cmd[cmd.index("--stage") + 1], "dub")
        self.assertEqual(cmd[cmd.index("--language") + 1], "ta te ml mr en")
        for missing in ("from_run", "language"):
            with self.assertRaises(codex_vm.JobError):
                codex_vm.validate({k: v for k, v in job.items() if k != missing})
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, language="ta,te"))         # only letters and spaces reach the machine

    def test_the_stage_needs_language_codes(self):
        with tempfile.TemporaryDirectory() as folder:
            args = SimpleNamespace(stage="dub", source="", from_run=folder, videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=1)
            summary = vm_studio.run(args, client=FakeClient([]), load=None, voice_maker=lambda language="hi": (None, "x"))
            self.assertIn("--language for dub", summary["error"])


if __name__ == "__main__":
    unittest.main()
