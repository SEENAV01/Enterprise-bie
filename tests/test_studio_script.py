"""The chapter's script (bie/brain/studio_script.py; Navin, 22 November 2026: one script for the whole chapter in one
teacher's words, then video, notes and games made from it; card "Poora chapter ek saath").

The small chapter map of tests/test_studio_naksha.py stands in for Section 1's output: the opening, 11.6 and 11.6.1.
"""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from bie.brain import studio_script
from bie.model_gateway.live.messages import strict_ready
from tests.test_studio_naksha import chapter, good


def point(pid, kind, teaches, says, *, terms=(), recalls=(), screen="a picture that explains it", outside=""):
    return {"id": pid, "kind": kind, "teaches": list(teaches), "recalls": list(recalls), "says": list(says),
            "screen": screen, "terms": [{"term": t, "meaning": f"{t} ka matlab"} for t in terms], "outside_book": outside}


def parts():
    return [
        {"section": "", "bridge": "Ab dekhte hain electrons ka safar.", "points": [
            point("0-k1", "explain", ["p001-i1"], ["Plants apna food khud banate hain, dhoop ki madad se."]),
            point("0-k2", "real_world", [], ["Hum jo chawal aur dal khate hain, uski shuruaat bhi ek patti se hoti hai."])]},
        {"section": "11.6", "bridge": "Ab sawaal: electrons ki kami kaun bharta hai?", "points": [
            point("11.6-k1", "explain", ["p001-i3"], ["Electrons PS II se PS I ki taraf move karte hain, ek line mein."],
                  terms=["PS II"], recalls=["0-k1"]),
            point("11.6-k2", "question", ["p001-i4"], ["Yeh kaise happens hota hai? Chaliye ek-ek kadam dekhte hain."]),
            point("11.6-k3", "analogy", [], ["Socho ek seedhi hai jis par gend neeche ludhakti hai, har kadam par thodi energy deti hai."])]},
        {"section": "11.6.1", "bridge": "", "points": [
            point("11.6.1-k1", "explain", ["p002-i1"], ["Water split hota hai aur PS II ke khoye electrons replace hote hain."],
                  terms=["lumen"]),
            point("11.6.1-k2", "question", ["p002-i2"], ["Protons kahan released hote hain? Thylakoid ke andar, lumen mein."]),
            point("11.6.1-k3", "figure", ["p002-i5"], ["Ab Z scheme figure dekho: har label ek station hai."])]},
    ]


class Client:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def chat(self, *, model, messages, schema=None):
        self.calls.append(messages)
        return {"content": json.dumps(self.answers.pop(0)), "usage": {"input_tokens": 100, "output_tokens": 20}}

    def plan_usage(self):
        return None


def check(index, part, written=None):
    ch = chapter()
    heads = studio_script.headings(ch)
    later = [t for h in heads[index + 1:] for t, _ in studio_script.first_terms(h) if studio_script._technical(t)]
    return " | ".join(studio_script.problems(part, heads[index], ch, written if written is not None else parts()[:index], later))


class Script(unittest.TestCase):
    def test_schema_is_strict_ready(self):
        self.assertTrue(strict_ready(studio_script.SCHEMA))

    def test_the_headings_follow_the_book_and_hold_only_teachable_body_items(self):
        heads = studio_script.headings(chapter())
        self.assertEqual([(h["number"], h["items"]) for h in heads],
                         [("", ["p001-i1"]), ("11.6", ["p001-i3", "p001-i4"]), ("11.6.1", ["p002-i1", "p002-i2", "p002-i5"])])
        self.assertEqual(studio_script.first_terms(heads[1]), [("PS II", "p001-i3")])

    def test_a_good_script_passes_and_covers_every_line(self):
        client = Client(parts())
        saved = []
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"], on_part=lambda r: saved.append(len(r["parts"])))
        self.assertEqual(record["problems"], {})
        self.assertEqual(saved, [1, 2, 3])                       # saved after every heading
        counts = studio_script.counts(chapter(), record["parts"])
        self.assertEqual((counts["covered"], counts["coverable"]), (6, 6))
        self.assertEqual((counts["analogies"], counts["real_world"]), (1, 1))

    def test_every_call_sees_the_whole_chapter_and_the_script_so_far(self):
        client = Client(parts())
        studio_script.write(client, "fake", chapter(), course=chapter()["course"], naksha={"A": good("A")})
        third = client.calls[2][1]["content"]
        self.assertIn("## 11.6.1 Splitting of Water", third)                      # the whole chapter file
        self.assertIn("Electrons PS II se PS I ki taraf move karte hain", third)  # the script so far
        self.assertIn("Terms already opened: ps ii", third)
        self.assertIn("plan A · question", third)                                # the plan's ideas for this heading
        self.assertIn("not the cut into videos", third)
        self.assertIn("NOW WRITE THE SCRIPT OF THIS HEADING: 11.6.1 Splitting of Water", third)
        self.assertIn("one heading at a time", client.calls[0][0]["content"])

    def test_ncert_line_by_line(self):
        part = copy.deepcopy(parts()[2])
        part["points"][0]["teaches"] = ["p001-i3"]
        part["points"][2]["teaches"] = ["p002-i2", "p002-i5"]
        found = check(2, part)
        self.assertIn("teaches p001-i3, which is not an item of this heading", found)
        self.assertIn("p002-i2 is taught twice", found)
        self.assertIn("1 items of this heading are in no point's teaches: p002-i1", found)
        part = copy.deepcopy(parts()[2])
        part["points"][0]["says"] = ["Ab ek naya kadam aata hai jo bahut zaroori hai."]
        self.assertIn("teaches p002-i1, but none of its key words is said there", check(2, part))

    def test_terms_open_once_at_first_use_and_never_early(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["terms"] = []
        self.assertIn("open the term 'PS II' (first met in p001-i3)", check(1, part))
        part = copy.deepcopy(parts()[2])
        part["points"][0]["terms"].append({"term": "PS II", "meaning": "again"})
        self.assertIn("the term 'PS II' was opened in 11.6-k1; remind in a few words", check(2, part))
        part = copy.deepcopy(parts()[0])
        part["points"][0]["says"] = ["Plants apna food khud banate hain, aur PS II isme kaam karta hai."]
        self.assertIn("uses 'PS II' before the chapter opens it", check(0, part))
        part["points"][0]["says"] = ["Plants apna food khud banate hain; PS II ko hum aage dekhenge."]
        self.assertNotIn("before the chapter opens it", check(0, part))
        self.assertTrue(studio_script._same_term("CO₂", "co2"))                 # one term, however it is typed
        self.assertFalse(studio_script._technical("regenerated"))               # a plain word only needs to be said

    def test_nothing_is_said_twice(self):
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"] = ["Socho ek seedhi hai jis par gend neeche ludhakti hai, har kadam par thodi energy deti hai.",
                                     "Protons kahan released hote hain? Lumen mein."]
        self.assertIn("11.6.1-k2 sentence 1 says again what 11.6-k3 said", check(2, part))
        part = copy.deepcopy(parts()[2])
        part["points"].append(point("11.6.1-k4", "analogy", [], ["Socho ek seedhi par gend neeche ludhakti hai aur energy deti hai."]))
        self.assertIn("11.6.1-k4: this analogy repeats 11.6-k3's", check(2, part))

    def test_a_teachers_voice_on_screen_without_caution_lines(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["says"].append("पानी टूटता है")
        part["points"][1]["says"].append(" ".join(["shabd"] * 45))
        part["points"][2]["says"].append("This is illustrative only.")
        part["points"][2]["screen"] = ""
        found = check(1, part)
        self.assertIn("11.6-k1 sentence 2: write it in Roman script", found)
        self.assertIn("11.6-k2 sentence 2: 45 words", found)
        self.assertIn("11.6-k3 sentence 2: a caution line never reaches the learner", found)
        self.assertIn("11.6-k3: needs its screen line", found)

    def test_real_world_is_life_not_a_study_task(self):
        part = copy.deepcopy(parts()[0])
        part["points"][1]["says"] = ["NEET numerical traps mein yeh diagram identify karna hota hai."]
        self.assertIn("0-k2: this real-world point is a study task", check(0, part))

    def test_recalls_only_point_back(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["recalls"] = ["11.6.1-k1"]
        self.assertIn("recalls '11.6.1-k1', which is not a point of an earlier heading", check(1, part))

    def test_navins_script_page(self):
        record = {"parts": [dict(p, title=t) for p, t in zip(parts(), ("Opening", "THE ELECTRON TRANSPORT", "Splitting of Water"))],
                  "problems": {"11.6.1": ["one left"]}}
        page = studio_script.html(chapter(), record)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("review page", page)
        self.assertIn("NCERT items 6/6", page)
        self.assertIn("Water is split to replace the electrons.", page)       # the NCERT line beside the script
        self.assertIn("1 kamiyan bachi", page)
        text = studio_script.markdown(chapter(), record)
        self.assertIn("## 11.6.1 Splitting of Water", text)
        self.assertIn("**11.6-k1** · samjhana · Electrons PS II se PS I", text)


class Stage(unittest.TestCase):
    def test_the_vm_stage_writes_the_script_from_a_naksha_run(self):
        import tools.vm_studio as vm_studio
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "naksha"
            run_dir.mkdir()
            (run_dir / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
            (run_dir / "naksha.json").write_text(json.dumps({"A": good("A"), "B": good("B")}), encoding="utf-8")
            args = SimpleNamespace(stage="script", source="", from_run=str(run_dir), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=2, pyqs="")
            summary = vm_studio.run(args, client=Client(parts()), load=None)
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual(summary["script"]["covered"], 6)
            for name in ("script.json", "SCRIPT.md", "SCRIPT.html", "record.json"):
                self.assertTrue((out / name).exists(), name)
            data = json.loads((out / "script.json").read_text(encoding="utf-8"))
            self.assertEqual([p["section"] for p in data["parts"]], ["", "11.6", "11.6.1"])

    def test_a_heading_left_with_problems_is_kept_and_reported(self):
        import tools.vm_studio as vm_studio
        bad = copy.deepcopy(parts()[1])
        bad["points"][0]["terms"] = []
        answers = [parts()[0], bad, bad, parts()[2]]
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "naksha"
            run_dir.mkdir()
            (run_dir / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
            args = SimpleNamespace(stage="script", source="", from_run=str(run_dir), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=2, pyqs="")
            summary = vm_studio.run(args, client=Client(answers), load=None)
            self.assertEqual(summary["status"], "needs_fix")
            self.assertEqual(summary["rounds"], {"opening": 1, "11.6": 2, "11.6.1": 1})
            self.assertIn("11.6", summary["problems"])

    def test_the_vm_runner_accepts_the_script_stage(self):
        import tools.codex_vm as codex_vm
        job = {"job": codex_vm.JOB_SCHEMA, "id": "script-test", "section": "studio", "stage": "script", "maker": "codex",
               "reviewer": "codex", "from_run": "https://raw.githubusercontent.com/x/y/z"}
        self.assertIn("--stage", codex_vm.argv(codex_vm.validate(job), Path("/tmp/out")))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, from_run=""))
