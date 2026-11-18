"""The course studio, stage 3 (Navin, 18 November 2026): one game stage per question, every choice visibly does something,
checked by code (scene ids, mechanics, coverage) and turned into the chapter's phone game. Offline: fake maker."""
from __future__ import annotations

import copy
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
from bie.brain import studio, studio_game  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

QUESTION = {"id": "q01", "pillar": "p1", "question": "Ek hi hawa kahin baadh aur kahin sookha kyun laati hai?",
            "hook": "Mumbai bheega, Pune sookha.",
            "points": [{"block_ids": ["p0001-b0002"], "point": "Hawa pahaad par chadhkar barasti hai", "kind": "process"},
                       {"block_ids": ["p0001-b0003"], "point": "Doosri taraf vrishti chhaya", "kind": "cause_effect"}],
            "film": {"length": "short", "showing_moment": "Hawa ka gola Ghat par chadhta hai"},
            "game_stage": {"mechanic": "drag_to_target", "idea": "Gole ko Ghat par kheencho"}}
PLAN = {"chapter_title": "Monsoon", "big_question": "Ek hi hawa poore Bharat ko kaise bhigoti hai?",
        "pillars": [{"id": "p1", "title": "Ghat", "line": "Pahaad aur baarish"}], "questions": [QUESTION]}
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450"><rect id="sea" x="0" y="300" width="250" height="150"/>'
       '<path id="ghat" d="M250 450 L420 160 L560 450Z"/><circle id="parcel" cx="120" cy="260" r="26"/>'
       '<g id="cloud"><ellipse cx="400" cy="140" rx="60" ry="26"/></g><path id="rain" d="M380 170 L370 230"/>'
       '<rect id="pune" x="600" y="400" width="60" height="30"/><text x="610" y="395">Pune</text></svg>')


def act(target, do, **kw):
    return {"target": target, "do": do, "x": kw.get("x", 0), "y": kw.get("y", 0), "scale": kw.get("scale", 1),
            "color": kw.get("color", ""), "ms": kw.get("ms", 700)}


def opt(label, correct=True, *, group="", order=0, target="", actions=None):
    return {"label": label, "correct": correct, "group": group, "order": order, "target": target,
            "feedback": f"{label}: yeh isliye kyunki hawa ka raasta yahi hai.", "actions": actions or [act("parcel", "pulse")]}


def stage():
    return {"title": "Hawa ko Ghat par chadhao", "intro": "Samudra ki geeli hawa ko pahaad tak le jaao aur dekho kya hota hai.",
            "scene_svg": SVG, "start_hidden": ["cloud", "rain"],
            "rounds": [
                {"id": "r1", "mechanic": "drag_to_target", "covers": [0], "prompt": "Hawa ke gole ko Ghat ki dhalaan par chhodo.",
                 "groups": [], "options": [opt("Geeli hawa", target="ghat", actions=[act("parcel", "move", x=260, y=-110),
                                                                                       act("cloud", "show"), act("rain", "draw")]),
                                           opt("Sookhi ret", correct=False, actions=[act("parcel", "shake")])],
                 "success_actions": [act("cloud", "glow")], "explain": "Hawa chadhi, thandi hui, aur baadal ban kar barsi."},
                {"id": "r2", "mechanic": "choose_and_see", "covers": [1], "prompt": "Ab Pune mein kya hoga? Chuno.",
                 "groups": [], "options": [opt("Kam baarish, kyunki hawa utar kar sookhi hai", actions=[act("pune", "color", color="#e8c26a")]),
                                           opt("Baadh aayegi", correct=False, actions=[act("pune", "shake")])],
                 "success_actions": [], "explain": "Utarti hawa garam hoti hai, isliye Pune vrishti chhaya mein hai."},
                {"id": "r3", "mechanic": "build_sequence", "covers": [0, 1], "prompt": "Kram lagao: pehle kya, phir kya?",
                 "groups": [], "options": [opt("Hawa samudra se uthti hai", order=1), opt("Ghat par chadhti hai", order=2),
                                           opt("Barasti hai", order=3)],
                 "success_actions": [], "explain": "Yahi kram har saal Konkan ko bhigota hai."},
                {"id": "r4", "mechanic": "sort_groups", "covers": [1], "prompt": "Shahron ko sahi samooh mein rakho.",
                 "groups": ["Zyada baarish", "Kam baarish"],
                 "options": [opt("Mumbai", group="Zyada baarish"), opt("Mahabaleshwar", group="Zyada baarish"),
                             opt("Pune", group="Kam baarish"), opt("Satara", group="Kam baarish")],
                 "success_actions": [], "explain": "Hawa ki taraf wale shahar bheegte hain, peeche wale sookhe rehte hain."}]}


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def chat(self, *, model, messages, schema=None):
        self.calls.append(messages)
        return {"content": json.dumps(self.answers.pop(0), ensure_ascii=False), "usage": {"input_tokens": 10, "output_tokens": 5}}


class GameChecks(unittest.TestCase):
    def test_schema_strict_and_mechanics_mapped(self):
        self.assertTrue(strict_ready(studio_game.SCHEMA))
        self.assertEqual(set(studio_game.CHOOSE + studio_game.DRAG + studio_game.ORDER + studio_game.SORT),
                         set(studio.MECHANICS))

    def test_good_stage_passes(self):
        self.assertEqual(studio_game.problems(stage(), QUESTION), [])

    def test_every_choice_must_do_something(self):
        bad = stage()
        bad["rounds"][1]["options"][1]["actions"] = []
        bad["rounds"][1]["options"][1]["feedback"] = "galat"
        found = " | ".join(studio_game.problems(bad, QUESTION))
        self.assertIn("no action; every choice must visibly do something", found)
        self.assertIn("feedback must say why", found)

    def test_scene_ids_and_mechanic_rules(self):
        bad = stage()
        bad["start_hidden"] = ["ghost"]
        bad["rounds"][0]["options"][0]["target"] = "nowhere"
        bad["rounds"][1]["options"][1]["correct"] = True
        bad["rounds"][2]["options"][2]["order"] = 5
        bad["rounds"][3]["options"][3]["group"] = "Beech mein"
        bad["rounds"][3]["options"][0]["actions"] = [act("missing", "spin")]
        found = " | ".join(studio_game.problems(bad, QUESTION))
        for text in ("start_hidden 'ghost'", "drop target 'nowhere'", "exactly one correct", "order exactly 1..n",
                     "groups not listed: Beech mein", "action target 'missing'", "action do 'spin'"):
            self.assertIn(text, found)

    def test_coverage_svg_and_source_words(self):
        bad = stage()
        for r in bad["rounds"]:
            r["covers"] = [0]
        bad["scene_svg"] = bad["scene_svg"].replace("<rect id=\"sea\"", "<script>x</script><rect id=\"sea\"")
        bad["rounds"][0]["explain"] = "NCERT ke hisaab se hawa chadhti hai aur barasti hai."
        found = " | ".join(studio_game.problems(bad, QUESTION))
        self.assertIn("no round revises the question's points 1", found)
        self.assertIn("banned element", found)
        self.assertIn("names the source", found)

    def test_problems_go_back_and_are_fixed(self):
        broken = copy.deepcopy(stage())
        broken["rounds"][0]["options"][0]["target"] = "nowhere"
        client = FakeClient([broken, stage()])
        record = studio_game.write(client, "fake", QUESTION, course="Class 9 Geography")
        self.assertEqual(record["problems"], [])
        self.assertEqual(len(record["rounds"]), 2)
        self.assertIn("nowhere", client.calls[1][-1]["content"])
        self.assertIn("drag_to_target", client.calls[0][0]["content"])


class GameRun(unittest.TestCase):
    def test_games_stage_writes_the_chapter_game(self):
        import io
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            films = Path(folder) / "films_run"
            (films / "films" / "img").mkdir(parents=True)
            (films / "questions.json").write_text(json.dumps(PLAN, ensure_ascii=False), encoding="utf-8")
            (films / "films" / "q01.json").write_text(json.dumps(
                {"film": {"shots": [{"key": "Hawa chadhti hai, baarish hoti hai"}]}, "images": {"s1": "q01-s1.png"}}),
                encoding="utf-8")
            buffer = io.BytesIO()
            Image.new("RGB", (64, 36), (40, 120, 60)).save(buffer, "PNG")
            (films / "films" / "img" / "q01-s1.png").write_bytes(buffer.getvalue())
            client = FakeClient([stage()])
            args = SimpleNamespace(stage="games", source="", from_run=str(films), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="Class 9 Geography", language="Hinglish", model="", max_rounds=2)
            summary = vm_studio.run(args, client=client, load=None)
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary.get("error"))
            self.assertEqual(summary["stages"], 1)
            self.assertIn("Hawa chadhti hai, baarish hoti hai", client.calls[0][1]["content"])
            page = (out / "GAME.html").read_text(encoding="utf-8")
            self.assertNotIn("/*__GAME__*/null", page)
            self.assertIn("data:image/webp;base64,", page)
            self.assertIn(studio.subject_tint("Class 9 Geography"), page)
            for name in ("GAMES.md", "games/q01.json", "questions.json", "SUMMARY.json"):
                self.assertTrue((out / name).exists(), name)

    def test_games_job_needs_the_earlier_run(self):
        job = {"job": "bie.vm-job/1", "id": "studio-g-test", "section": "studio", "stage": "games",
               "from_run": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-results/runs/x"}
        cmd = codex_vm.argv(codex_vm.validate(dict(job)), Path("/tmp/out"), "python")
        self.assertEqual(cmd[cmd.index("--stage") + 1], "games")
        self.assertEqual(cmd[cmd.index("--from-run") + 1], job["from_run"])
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({k: v for k, v in job.items() if k != "from_run"})

    def test_subject_tints(self):
        self.assertEqual(studio.subject_tint("Class 11 Biology"), "#3f7d4e")
        self.assertEqual(studio.subject_tint("UPSC Indian Economy"), "#9a6b1f")
        self.assertEqual(studio.subject_tint(""), "#2c6e87")


if __name__ == "__main__":
    unittest.main()
