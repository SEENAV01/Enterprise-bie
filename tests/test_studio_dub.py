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
