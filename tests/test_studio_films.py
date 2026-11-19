"""The course studio, stage 2 (Navin, 18 November 2026): one film per approved question, checked by code (said = shown,
safe SVG, coverage of the question's points) and turned into a phone film. Offline: fake maker, fake pictures, fake voice."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import codex_vm  # noqa: E402
import vm_studio  # noqa: E402
from bie.brain import studio_film  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

def png_bytes():
    import io
    from PIL import Image
    buffer = io.BytesIO()
    Image.new("RGB", (32, 18), (40, 120, 60)).save(buffer, "PNG")
    return buffer.getvalue()
QUESTION = {"id": "q01", "question": "Ek hi hawa kahin baadh aur kahin sookha kyun laati hai?", "hook": "Mumbai bheega, Pune sookha.",
            "points": [{"block_ids": ["p0001-b0002"], "point": "Hawa pahaad par chadhkar barasti hai", "kind": "process"},
                       {"block_ids": ["p0001-b0003"], "point": "Doosri taraf vrishti chhaya", "kind": "cause_effect"}],
            "film": {"length": "short", "showing_moment": "Hawa ka gola Ghat par chadhta hai"},
            "game_stage": {"mechanic": "drag_to_target", "idea": "Gole ko Ghat par kheencho"}}
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 56"><defs><linearGradient id="g"><stop offset="0"/>'
       '</linearGradient></defs><rect width="100" height="56" fill="#eef"/><path id="slope" d="M0 50 L50 10 L100 50"/>'
       '<circle id="cloud" cx="40" cy="12" r="6"/>' + "".join(f'<circle cx="{5 + i * 9}" cy="52" r="2"/>' for i in range(10))
       + '</svg>')


def sentence(roman, voice, pins=(), focus=(), moves=(), grows=(), fuses=(), scale=1.1):
    return {"roman": roman, "voice": voice, "pins": [{"label": p, "x": 40, "y": 30} for p in pins],
            "arrows": [{"points": [[10, 60], [40, 30]], "label": "hawa"}], "effects": [],
            "focus": list(focus), "zoom": {"x": 50, "y": 50, "scale": scale},
            "moves": list(moves), "grows": list(grows), "fuses": list(fuses)}


CLOUDS = {"what": "drop", "colour": "blue", "label": "hawa", "points": [[10, 80], [35, 45], [55, 25]], "count": 6,
          "ms": 2600, "loop": True}


def film():
    return {"title": "Ghat aur baarish", "shots": [
        {"id": "s1", "title": "Ghat ki deewar", "key": "Hawa chadhti hai, baarish hoti hai", "covers": [0],
         "visual": {"type": "photo", "image_prompt": "Photorealistic wide view of the green Western Ghats escarpment in the "
                    "July monsoon with dark clouds on the windward slope and waterfalls", "svg": ""},
         "dive": {"x": -1, "y": -1},
         "sentences": [sentence("Dekhiye, yeh Ghat ki deewar hai.", "देखिए, यह घाट की दीवार है।", ["Ghat"]),
                       sentence("Hawa yahan chadhkar thandi hoti hai aur barasti hai.", "हवा यहाँ चढ़कर ठंडी होती है और बरसती है।",
                                moves=[CLOUDS], scale=1.8)]},
        {"id": "s2", "title": "Kaat", "key": "Doosri taraf sookha", "covers": [1],
         "visual": {"type": "diagram", "image_prompt": "", "svg": SVG},
         "dive": {"x": 55, "y": 25},
         "sentences": [sentence("Ab pahaad ka kaat dekhiye, baadal upar.", "अब पहाड़ का काट देखिए, बादल ऊपर।", ["baadal"], ["cloud"]),
                       sentence("Doosri taraf utarti hawa sookhi rehti hai.", "दूसरी तरफ़ उतरती हवा सूखी रहती है।", [], ["slope"])]}]}


class FakeClient:
    def __init__(self, answers):
        self.answers = list(answers)
        self.images = 0

    def chat(self, *, model, messages, schema=None):
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 10, "output_tokens": 5}}

    def generate_image(self, prompt, out, model=None):
        assert "No text" in prompt
        self.images += 1
        Path(out).write_bytes(png_bytes())
        return {"file": Path(out).name}


class FakeVoice:
    def say(self, text):
        return {"uri": "data:audio/mpeg;base64,AAAA", "dur": 2.0}


class FilmChecks(unittest.TestCase):
    def test_schema_strict(self):
        self.assertTrue(strict_ready(studio_film.SCHEMA))

    def test_good_film_passes(self):
        self.assertEqual(studio_film.problems(film(), QUESTION), [])

    def test_pin_not_spoken_and_bad_svg_and_coverage(self):
        bad = film()
        bad["shots"][0]["sentences"][0]["pins"][0]["label"] = "Thar"
        bad["shots"][1]["visual"]["svg"] = '<svg viewBox="0 0 1 1"><script>alert(1)</script></svg>'
        bad["shots"][1]["covers"] = []
        found = " | ".join(studio_film.problems(bad, QUESTION))
        self.assertIn("not spoken", found)
        self.assertIn("banned element", found)
        self.assertIn("points 1", found)

    def test_devanagari_voice_needed(self):
        bad = film()
        bad["shots"][0]["sentences"][1]["voice"] = "Hawa chadhti hai"
        self.assertIn("Devanagari", " ".join(studio_film.problems(bad, QUESTION)))


class FilmMotion(unittest.TestCase):
    """Navin, 19 November 2026: the Campbell 17 film's motion (what travels is shown travelling, the camera pushes in)."""

    def test_motion_is_checked(self):
        bad = film()
        first = bad["shots"][0]["sentences"][1]
        first["moves"] = [dict(CLOUDS, points=[[10, 180]], count=40, ms=50, label="Thar")]
        first["grows"] = [{"points": [[5, 5]], "label": "", "ms": 100}]
        first["fuses"] = [{"x": 50, "y": 50, "label": ""}]
        first["zoom"]["scale"] = 3
        bad["shots"][0]["dive"] = {"x": 20, "y": 20}
        found = " | ".join(studio_film.problems(bad, QUESTION))
        for text in ("2 to 6 points", "count is 1 to 12", "ms is 800 to 8000", "'Thar' is not spoken", "2 to 8 points",
                     "grow's ms", "needs its label", "zoom.scale must be 1.0 to 2.2", "first shot cannot dive"):
            self.assertIn(text, found)

    def test_a_film_without_motion_is_sent_back(self):
        still = film()
        for shot in still["shots"]:
            for line in shot["sentences"]:
                line["moves"], line["grows"], line["fuses"] = [], [], []
        self.assertIn("show what travels travelling", " ".join(studio_film.problems(still, QUESTION)))

    def test_player_plays_motion(self):
        page = Path(ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        for hook in ("addMove", "addGrow", "addFuse", "camTo", "toScreen", "s.dive", "SPRITE_SCALE", "/*__FILM__*/null"):
            self.assertIn(hook, page)

    def test_player_keeps_diagram_words_readable(self):
        """The first Photosynthesis films (19 Nov 2026) showed three faults on diagram shots: a zoom cut words at the frame
        edge, highlighted words got a thick red outline, and moving sprites passed over words. The player now keeps the
        diagram's words on their own top layer, fades a word the frame cuts, and highlights words without an outline."""
        page = Path(ROOT / "bie" / "brain" / "studio_player.html").read_text(encoding="utf-8")
        self.assertIn(".svg text.lit,.svg .lit text{stroke:none!important", page)
        self.assertNotIn(".svg .lit{filter:drop-shadow(0 0 6px #e8a93a);stroke", page)
        self.assertIn(".svg.base svg text{visibility:hidden}", page)
        self.assertIn(".svg.tl svg text.cut{opacity:0}", page)
        build = page[page.index("function build(i)"):page.index("function show(i,k,viaDive)")]
        self.assertIn("'svg base'", build)
        self.assertLess(build.index("worldLayers()"), build.index("textLayer()"))   # words go above the sprite layer
        layer = page[page.index("function textLayer()"):page.index("function edgeCut(now)")]
        self.assertIn("e.dataset.oid=e.id;e.removeAttribute('id')", layer)          # ids stay unique in the page
        self.assertIn("[data-oid=", page)                                           # a highlight reaches the top words
        self.assertIn("function tick(now){camStep(now);edgeCut(now);", page)
        self.assertIn("words:texts.length,cut:", page)

    def test_cutaway_is_an_ai_picture_in_cutaway_style(self):
        shot = {"visual": {"type": "cutaway", "image_prompt": "The inside of a mature ovule", "svg": ""}}
        self.assertIn("transparent cross-section", studio_film.image_prompt(shot))
        data = studio_film.player_data(film(), images={}, audio={}, chapter="Monsoon", question=QUESTION)
        self.assertEqual(data["shots"][1]["dive"], {"x": 55, "y": 25})
        self.assertIsNone(data["shots"][0]["dive"])
        self.assertEqual(data["shots"][0]["sentences"][1]["moves"][0]["what"], "drop")


class FilmStage(unittest.TestCase):
    def test_films_stage_makes_a_phone_film(self):
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "qrun"
            run_dir.mkdir()
            (run_dir / "questions.json").write_text(json.dumps({"chapter_title": "Monsoon", "questions": [QUESTION]}), encoding="utf-8")
            args = SimpleNamespace(stage="films", source="", from_run=str(run_dir), videos="q01", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9", language="Hinglish", model="", max_rounds=2)
            client = FakeClient([film()])
            summary = vm_studio.run(args, client=client, load=None, voice_maker=lambda: (FakeVoice(), None))
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual(client.images, 1)
            page = (out / "films" / "q01.html").read_text(encoding="utf-8")
            self.assertNotIn("/*__FILM__*/null", page)
            self.assertIn("data:image/webp;base64,", page)
            self.assertIn("घाट की दीवार", (out / "films" / "q01.json").read_text(encoding="utf-8"))
            self.assertTrue((out / "FILMS.md").exists())

    def test_job_for_films(self):
        job = codex_vm.validate({"job": "bie.vm-job/1", "id": "studio-films-test", "section": "studio", "stage": "films",
                                 "from_run": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/x",
                                 "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/chapters/x.pdf",
                                 "videos": "q01,q02"})
        cmd = codex_vm.argv(job, Path("/tmp/o"), "python")
        self.assertEqual(cmd[cmd.index("--from-run") + 1], job["from_run"])
        self.assertEqual(cmd[cmd.index("--videos") + 1], "q01,q02")
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({"job": "bie.vm-job/1", "id": "studio-films-x", "section": "studio", "stage": "films"})


if __name__ == "__main__":
    unittest.main()
