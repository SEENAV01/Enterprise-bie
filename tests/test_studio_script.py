"""The chapter's script (bie/brain/studio_script.py; Navin, 22 November 2026: one script for the whole chapter in one
teacher's words, then video, notes and games made from it; card "Poora chapter ek saath").

The small chapter map of tests/test_studio_naksha.py stands in for Section 1's output: the opening, 11.6 and 11.6.1.
"""
from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from bie.brain import studio_script
from bie.model_gateway.live.messages import strict_ready
from tests.test_studio_naksha import chapter, good


def point(pid, kind, teaches, says, *, terms=(), recalls=(), screen="a picture that explains it", outside="", prepares=(),
          answer=None, watch_out=None):
    thinking = kind in ("analogy", "checkpoint")
    return {"id": pid, "kind": kind, "teaches": list(teaches), "recalls": list(recalls), "says": list(says),
            "screen": screen, "terms": [{"term": t, "meaning": f"{t} ka matlab"} for t in terms], "outside_book": outside,
            "prepares": list(prepares), "answer": answer if answer is not None else ("the reasoning" if thinking else ""),
            "watch_out": watch_out if watch_out is not None else ("a common wrong idea" if thinking else "")}


def parts():
    return [
        {"section": "", "goal": "Plants apna food khud banate hain, dhoop ki madad se.",
         "bridge": "Ab dekhte hain electrons ka safar.", "points": [
            point("0-k1", "explain", ["p001-i1"], ["Plants apna food khud banate hain, dhoop ki madad se."]),
            point("0-k2", "real_world", [], ["Hum jo chawal aur dal khate hain, uski shuruaat bhi ek patti se hoti hai."]),
            point("0-k3", "analogy", [], ["Socho patti ek chhoti rasoi hai jahan dhoop se khana pakta hai."])]},
        {"section": "11.6", "goal": "Electrons PS II se PS I ki taraf move karte hain.",
         "bridge": "Ab sawaal: electrons ki kami kaun bharta hai?", "points": [
            point("11.6-k1", "explain", ["p001-i3"], ["Electrons PS II se PS I ki taraf move karte hain, ek line mein."],
                  terms=["PS II"], recalls=["0-k1"]),
            point("11.6-k2", "question", ["p001-i4"], ["Yeh kaise happens hota hai? Chaliye ek-ek kadam dekhte hain."]),
            point("11.6-k3", "analogy", [], ["Socho ek seedhi hai jis par gend neeche ludhakti hai, har kadam par thodi energy deti hai."]),
            point("11.6-k4", "real_world", [], ["Kheton mein subah dhoop milte hi fasal ki pattiyan kaam shuru kar deti hain."])]},
        {"section": "11.6.1", "goal": "Ab dekhenge ki PS II ke khoye electrons ki kami kaun bharta hai.",
         "bridge": "Ab dekhte hain yeh sab milkar aage kya banata hai.", "points": [
            point("11.6.1-k1", "overview", [], ["Ab dekhenge ki PS II ke khoye electrons ki kami kaun bharta hai.",
                                                "Pani kyun tootta hai, aur usse teen cheezein kya milti hain?"]),
            point("11.6.1-k2", "explain", ["p002-i1"], ["Water split hota hai aur PS II ke khoye electrons replace hote hain."],
                  terms=["lumen"]),
            point("11.6.1-k3", "question", ["p002-i2"], ["Protons kahan released hote hain? Thylakoid ke andar, lumen mein."]),
            point("11.6.1-k4", "figure", ["p002-i5"], ["Ab Z scheme figure dekho: har label ek station hai."],
                  prepares=["p002-i4"]),
            point("11.6.1-k5", "example", [], ["Do water molecules gino: inse chaar protons, chaar electrons aur ek oxygen milti hai."]),
            point("11.6.1-k6", "real_world", [], ["Hum jo oxygen saans mein lete hain, uska bada hissa paudhon ke pani todne se aata hai."]),
            point("11.6.1-k7", "checkpoint", [], ["Socho: agar pani tootna band ho jaye, to PS II ka kya hoga?"],
                  answer="PS II ki khali jagah nahi bharegi, aur electron ka safar ruk jayega",
                  watch_out="PS I pani se seedha electron nahi leta"),
            point("11.6.1-k8", "retell", [], ["Poori baat ek saath: roshni PS II ka electron uchhalti hai, pani tootkar uski "
                                              "kami bharta hai, protons lumen mein jama hote hain aur oxygen bahar jaati hai."])]},
        {"section": "recap", "goal": "Light reactions ATP aur NADPH banati hain.", "bridge": "", "points": [
            point("recap-k1", "summary", ["p002-i3"], ["Ant mein yaad rakho: light reactions ATP aur NADPH banati hain, "
                                                        "jo aage sugar banane mein kaam aate hain."], recalls=["11.6-k1"])]},
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
                         [("", ["p001-i1"]), ("11.6", ["p001-i3", "p001-i4"]), ("11.6.1", ["p002-i1", "p002-i2", "p002-i5"]),
                          ("recap", ["p002-i3"])])                                     # the summary closes the chapter
        self.assertEqual(studio_script.exercises(chapter()), ["p002-i4"])
        self.assertEqual(studio_script.first_terms(heads[1]), [("PS II", "p001-i3")])

    def test_a_good_script_passes_and_covers_every_line(self):
        client = Client(parts())
        saved = []
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"], on_part=lambda r: saved.append(len(r["parts"])))
        self.assertEqual(record["problems"], {})
        self.assertEqual(saved, [1, 2, 3, 4])                    # saved after every heading
        counts = studio_script.counts(chapter(), record["parts"])
        self.assertEqual((counts["covered"], counts["coverable"]), (6, 6))
        self.assertEqual((counts["summary_taught"], counts["summary"], counts["exercises_prepared"], counts["exercises"]),
                         (1, 1, 1, 1))
        self.assertEqual(counts["checkpoints"], 1)
        self.assertEqual((counts["analogies"], counts["real_world"]), (2, 3))

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
        part["points"][1]["teaches"] = ["p001-i3"]
        part["points"][3]["teaches"] = ["p002-i2", "p002-i5"]
        found = check(2, part)
        self.assertIn("teaches p001-i3, which is not an item of this heading", found)
        self.assertIn("p002-i2 is taught twice", found)
        self.assertIn("1 items of this heading are in no point's teaches: p002-i1", found)
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"] = ["Ab ek naya kadam aata hai jo bahut zaroori hai."]
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

    def test_round_two_rules_from_the_first_chapter_11_script(self):
        # round 1 of Chapter 11 (22 Nov 2026): 0 analogies, 24 lines naming the book, points of up to 16 sentences
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"].append("Book ise water splitting kehti hai.")
        part["points"][2]["says"] += [f"Protons ka ek aur pehlu number {n} dekho." for n in range(8)]
        part["points"] = [p for p in part["points"] if p["kind"] != "example"]
        found = check(2, part)
        self.assertIn("11.6.1-k2 sentence 2: names the book ('Book')", found)
        self.assertIn("11.6.1-k3: 9 sentences; a knowledge point holds one idea in at most 8", found)
        self.assertIn("this heading needs at least one worked example", found)
        ch = chapter()
        heads = studio_script.headings(ch)
        part = copy.deepcopy(parts()[1])
        part["points"] = [p for p in part["points"] if p["kind"] not in ("analogy", "real_world")]
        found = " | ".join(studio_script.problems(part, heads[1], ch, parts()[:1], [], {"analogy": True, "real_world": True}))
        self.assertIn("the plan offers an analogy for this heading", found)
        self.assertIn("the plan offers a real-world use for this heading", found)
        self.assertEqual(studio_script.ideas({"A": good("A")}, "11.6"), {"analogy": True, "real_world": True})

    def test_final_round_rules_from_the_teacher_audit(self):
        # ChatGPT's audit of round 1 (22 Nov 2026), filtered with Navin: the knowledge for every exercise, a closing recap,
        # a stop for the learner to think, an analogy that says what maps to what and where it breaks
        part = copy.deepcopy(parts()[2])
        part["points"] = [p for p in part["points"] if p["kind"] != "checkpoint"]
        part["points"][2]["prepares"] = ["p002-i9"]
        self.assertIn("this heading needs at least one checkpoint", check(2, part))
        self.assertIn("prepares ['p002-i9'], which are not exercise items", check(2, part))
        part = copy.deepcopy(parts()[1])
        part["points"][2]["answer"] = ""
        part["points"][2]["watch_out"] = ""
        found = check(1, part)
        self.assertIn('11.6-k3: a analogy needs "answer": what maps to what', found)
        self.assertIn('11.6-k3: a analogy needs "watch_out": where the picture stops being true', found)
        ch = chapter()
        heads = studio_script.headings(ch)
        written = copy.deepcopy(parts()[:3])
        written[2]["points"][3]["prepares"] = []
        self.assertEqual(studio_script.unprepared(ch, written), ["p002-i4"])
        found = " | ".join(studio_script.problems(parts()[3], heads[3], ch, written, [], None, ["p002-i4"]))
        self.assertIn("1 exercises are prepared by no point of the script: p002-i4", found)
        self.assertEqual(studio_script.problems(parts()[3], heads[3], ch, parts()[:3], [], None, []), [])
        user = studio_script.messages(ch, heads[3], written, course=ch["course"])[1]["content"]
        self.assertIn("THE CHAPTER'S EXERCISES", user)
        self.assertIn("Not yet prepared by any point: p002-i4", user)
        rules = studio_script.messages(ch, heads[0], [], course=ch["course"])[0]["content"]
        for words in ("never describe decoration", "carbon by carbon", "NAD/NADH", "done and filled here",
                      "told fully and vividly", "never said in the telling", "built on the same realistic picture step by"):
            self.assertIn(words, rules)

    def test_teacher_study_rules(self):
        # four teachers of Chapter 11 read line by line (Navin, 22 Nov 2026, card "Haan, isi kram se"): goal first,
        # questions about one in five with a "kyun", a process told as overview, steps and retell with its counts
        part = copy.deepcopy(parts()[2])
        part["goal"] = ""
        self.assertIn('"goal" is empty', check(2, part))
        part["goal"] = "Chloroplast ke andar ribosomes ki ginti samjhenge."
        self.assertIn("11.6.1-k1: open the heading with its goal", check(2, part))
        part = copy.deepcopy(parts()[2])
        for p in part["points"]:
            p["says"] = [s.replace("?", ".") for s in p["says"]]
        found = check(2, part)
        self.assertIn("0 of 10 sentences ask the learner something", found)
        self.assertIn('no "kyun" question in this heading', found)
        part = copy.deepcopy(parts()[2])
        part["points"] = [p for p in part["points"] if p["kind"] not in ("overview", "retell")]
        part["points"][0]["says"] = [part["goal"]] + part["points"][0]["says"]
        part["points"] = [dict(p, says=[re.sub(r"\b(chaar|ek)\b", "kuch", s) for s in p["says"]]) for p in part["points"]]
        found = check(2, part)
        self.assertIn('an "overview" point names the steps', found)
        self.assertIn('a "retell" point tells the whole of it again', found)
        self.assertIn("this process heading says no count", found)
        part = copy.deepcopy(parts()[2])
        part["points"] = part["points"][1:] + part["points"][:1]               # the overview after the steps
        self.assertIn('before its steps, an "overview" point', check(2, part))

    def test_flowing_answers_and_no_teacher_slip(self):
        # Navin heard "पानी से।" said alone (22 Nov 2026): "chhote vakya se baat tooti tooti lagegi"
        part = copy.deepcopy(parts()[2])
        part["points"][2]["says"] = ["Protons kahan released hote hain? Lumen mein."]
        self.assertIn("11.6.1-k3 sentence 2: 'Lumen mein.' is a fragment", check(2, part))
        # round 1 (22 Nov 2026): an initial is not a sentence end, and a teacher's one-word question is not a fragment
        self.assertEqual(studio_script.sentences({"says": ["Calvin ne J.A. Bassham ke saath reactions dhoondhi. Kyun?"]}),
                         ["Calvin ne J.A. Bassham ke saath reactions dhoondhi.", "Kyun?"])
        part["points"][2]["says"] = ["Protons kahan released hote hain? Kyun? Woh lumen mein release hote hain, jahan "
                                     "unki ginti badhti hai."]
        self.assertNotIn("is a fragment", check(2, part))
        part = copy.deepcopy(parts()[2])
        part["points"][4]["says"].append("Is experiment mein oxygen-18 radioactive tracer tha.")
        self.assertIn("this says a known slip (oxygen-18 called radioactive)", check(2, part))
        part["points"][4]["says"][-1] = "Is experiment mein oxygen-18 tha, jo radioactive nahi hai."
        self.assertNotIn("known slip", check(2, part))                          # BIE's round 1 said it right
        part["points"][4]["says"][-1] = "Calvin cycle har chakkar mein ek CO2 nikalta hai, isliye yeh yaad rakho."
        self.assertIn("the Calvin cycle releasing CO2", check(2, part))
        part["points"][4]["says"][-1] = "Light reaction par temperature ka koi asar nahi hota, yeh pakka hai."
        self.assertIn("temperature not affecting the light reaction", check(2, part))   # here the negation is the slip

    def test_answers_do_not_all_open_with_dekho(self):
        # the final round (22 Nov 2026): "Dekho," opened nearly every answer, as the old rule told the writer; Navin,
        # 23 Nov 2026, card "Tum wali chalegi": the voice ("dekho", "socho") stays, the openers vary
        part = copy.deepcopy(parts()[2])
        extra = [f"Yeh kadam {n} kyun zaroori hai? Dekho, iske bina electron ka raasta ruk jaata hai aur kaam band hota hai."
                 for n in range(4)]
        part["points"][1]["says"] = part["points"][1]["says"] + extra[:2]
        part["points"][5]["says"] = part["points"][5]["says"] + extra[2:]
        found = check(2, part)
        self.assertIn('4 of 7 answers open with "Dekho"; vary the opener as a teacher does', found)
        part["points"][5]["says"][-1] = part["points"][5]["says"][-1].replace("Dekho,", "Iska seedha sa jawab hai ki")
        part["points"][5]["says"][-2] = part["points"][5]["says"][-2].replace("Dekho,", "Aisa isliye hai kyunki")
        self.assertNotIn("answers open with", check(2, part))
        self.assertIn("no one opener for more than half the answers", studio_script.messages(
            chapter(), studio_script.headings(chapter())[2], parts()[:2], course={})[0]["content"])

    def test_a_marked_misconception_is_said_and_the_bridge_names_the_link(self):
        ch = chapter()
        ch["items"]["p002-i1"].update(teach_depth="deep", deep_why="misconception")
        heads = studio_script.headings(ch)
        found = " | ".join(studio_script.problems(parts()[2], heads[2], ch, parts()[:2], []))
        self.assertIn("the chapter file marks a common wrong idea here (p002-i1)", found)
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"].append("Aksar log sochte hain ki oxygen CO2 se aati hai, par asal mein woh pani se aati hai.")
        self.assertEqual(studio_script.problems(part, heads[2], ch, parts()[:2], []), [])
        part["bridge"] = ""
        self.assertIn('"bridge" is empty', " | ".join(studio_script.problems(part, heads[2], ch, parts()[:2], [])))
        self.assertEqual(studio_script.problems(parts()[3], heads[3], ch, parts()[:3], [], None, []), [])   # last heading
        counts = studio_script.counts(ch, parts())
        self.assertEqual((counts["retells"], counts["fragments"], counts["goals"]), (1, 0, 4))
        self.assertGreater(counts["question_share"], 0.15)
        rules = studio_script.messages(ch, heads[0], [], course=ch["course"])[0]["content"]
        for words in ("about one sentence in five is a question", '"overview" point', '"retell" point',
                      "never a sentence of three words or fewer", "oxygen-18 is radioactive", "names the link"):
            self.assertIn(words, rules)

    def test_code_repairs_the_section_and_a_recall_of_an_item(self):
        heads = studio_script.headings(chapter())
        part = copy.deepcopy(parts()[2])
        part["section"] = "11.6.1 Splitting of Water"
        part["points"][0]["recalls"] = ["p001-i3", "11.6.1-k2", "11.6-k3"]
        fixed = studio_script.repair(part, heads[2], parts()[:2])
        self.assertEqual(fixed["section"], "11.6.1")
        self.assertEqual(fixed["points"][0]["recalls"], ["11.6-k1", "11.6-k3"])   # item -> the point that taught it
        self.assertEqual(check(2, fixed), "")

    def test_navins_script_page(self):
        record = {"parts": [dict(p, title=t) for p, t in zip(parts(), ("Opening", "THE ELECTRON TRANSPORT", "Splitting of Water",
                                                                         "Poore chapter ki tasveer"))],
                  "problems": {"11.6.1": ["one left"]}}
        page = studio_script.html(chapter(), record)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("review page", page)
        self.assertIn("padhai ki NCERT lines 6/6", page)
        self.assertIn("exercises ka gyan\n1/1", page)
        self.assertIn("Aam galti:", page)
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
            self.assertEqual([p["section"] for p in data["parts"]], ["", "11.6", "11.6.1", "recap"])

    def test_a_heading_left_with_problems_is_kept_and_reported(self):
        import tools.vm_studio as vm_studio
        bad = copy.deepcopy(parts()[1])
        bad["points"][0]["terms"] = []
        answers = [parts()[0], bad, bad, parts()[2], parts()[3]]
        with tempfile.TemporaryDirectory() as folder:
            run_dir = Path(folder) / "naksha"
            run_dir.mkdir()
            (run_dir / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
            args = SimpleNamespace(stage="script", source="", from_run=str(run_dir), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="", language="Hinglish", model="", max_rounds=2, pyqs="")
            summary = vm_studio.run(args, client=Client(answers), load=None)
            self.assertEqual(summary["status"], "needs_fix")
            self.assertEqual(summary["rounds"], {"opening": 1, "11.6": 2, "11.6.1": 1, "recap": 1})
            self.assertIn("11.6", summary["problems"])

    def test_the_vm_runner_accepts_the_script_stage(self):
        import tools.codex_vm as codex_vm
        job = {"job": codex_vm.JOB_SCHEMA, "id": "script-test", "section": "studio", "stage": "script", "maker": "codex",
               "reviewer": "codex", "from_run": "https://raw.githubusercontent.com/x/y/z"}
        self.assertIn("--stage", codex_vm.argv(codex_vm.validate(job), Path("/tmp/out")))
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate(dict(job, from_run=""))
