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
          answer=None, watch_out=None, roles=None):
    thinking = kind in ("analogy", "checkpoint")
    return {"id": pid, "kind": kind, "teaches": list(teaches), "recalls": list(recalls), "says": list(says),
            "screen": screen, "terms": [{"term": t, "meaning": f"{t} ka matlab"} for t in terms], "outside_book": outside,
            "prepares": list(prepares), "answer": answer if answer is not None else ("the reasoning" if thinking else ""),
            "watch_out": watch_out if watch_out is not None else ("a common wrong idea" if thinking else ""),
            "uses": [], "roles": list(roles) if roles is not None else ["ask" if line.rstrip().endswith("?") else "plain"
                                                                         for line in says]}


def with_facts(heads):
    """Each heading's facts and each point's uses, as the teacher's way asks (25 Nov 2026), by kind as padhai pehle asks
    (25 Nov 2026): a book fact per item it teaches, a word fact per term the chapter opens there, a base fact for what
    its items need first, a label fact for what a figure shows by name."""
    ch = chapter()
    items = ch["items"]
    by_number = {h["number"]: h for h in studio_script.headings(ch)}
    for part in heads:
        part["facts"] = []

        def add(item, kind, term, fact, point):
            fid = f"f{len(part['facts']) + 1}"
            part["facts"].append({"id": fid, "item": item, "kind": kind, "term": term, "fact": fact})
            point["uses"].append(fid)

        for p in part["points"]:
            for iid in p["teaches"]:
                add(iid, "book", "", items[iid]["content"], p)
        heading = by_number.get(part["section"])
        if not heading or part["section"] == "recap":
            continue
        add(heading["items"][0], "base", "", "Roshni ek energy hai (light is energy).", part["points"][0])
        for term, iid in studio_script.first_terms(heading):
            said = next((p for p in part["points"] if studio_script._term_in(term, " ".join(p["says"]))), part["points"][0])
            add(iid, "word", term, f"{term} ka matlab", said)
        rows = {r["id"]: r for r in heading["rows"]}
        for iid in heading["items"]:
            if items[iid].get("kind") == "diagram":
                teacher = next(p for p in part["points"] if iid in p["teaches"])
                for label in studio_script.label_candidates(rows[iid], items):
                    add(iid, "label", label, f"{label} figure mein ek station hai", teacher)
    return heads


def parts():
    return with_facts([
        {"section": "", "goal": "Plants apna food khud kaise banate hain?",
         "bridge": "Ab dekhte hain electrons ka safar.", "points": [
            point("0-k1", "explain", ["p001-i1"], ["Plants apna food khud kaise banate hain?",
                                                   "Plants apna food khud dhoop se banate hain, kyunki patti dhoop ki energy ko "
                                                   "khane mein badal deti hai."],
                  roles=["link", "why"]),
            point("0-k2", "real_world", [], ["Hum jo chawal aur dal khate hain, uski shuruaat bhi ek patti se hoti hai."]),
            point("0-k3", "analogy", [], ["Socho patti ek chhoti rasoi hai jahan dhoop se khana pakta hai."])]},
        {"section": "11.6", "goal": "Roshni se uchhla electron aage kis taraf move karta hai?",
         "bridge": "Ab sawaal: electrons ki kami kaun bharta hai?", "points": [
            point("11.6-k1", "explain", ["p001-i3"], ["Roshni se uchhla electron aage kis taraf move karta hai, aur kyun?",
                                                       "Roshni se uchhla electron aage isliye move karta hai kyunki roshni "
                                                       "use dhakka deti hai.",
                                                       "Electrons PS II se PS I ki taraf move karte hain, ek line mein.",
                                                       "Yeh isliye hota hai kyunki har agla station electron ko thoda neeche "
                                                       "kheenchta hai."],
                  terms=["PS II"], recalls=["0-k1"], roles=["link", "plain", "term", "why"]),
            point("11.6-k2", "question", ["p001-i4"], ["Electron aage kaise badhta hai? Electron aage aise badhta hai ki har "
                                                        "station use agle station tak deta hai."]),
            point("11.6-k3", "analogy", [], ["Socho ek seedhi hai jis par gend neeche ludhakti hai, har kadam par thodi energy deti hai."]),
            point("11.6-k4", "real_world", [], ["Kheton mein subah dhoop milte hi fasal ki pattiyan kaam shuru kar deti hain."])]},
        {"section": "11.6.1", "goal": "PS II ke khoye electrons ki kami kaun bharta hai?",
         "bridge": "Ab dekhte hain yeh sab milkar aage kya banata hai.", "points": [
            point("11.6.1-k1", "overview", [], ["PS II ke khoye electrons ki kami kaun bharta hai?",
                                                "Pani kyun tootta hai, aur usse teen cheezein kya milti hain?"]),
            point("11.6.1-k2", "explain", ["p002-i1"], ["Paani tootta hai aur PS II ke khoye electrons ki jagah bharta hai.",
                                                         "Aisa isliye hota hai kyunki PS II ko apne electrons wapas chahiye."],
                  terms=["lumen"], roles=["plain", "why"]),
            point("11.6.1-k3", "question", ["p002-i2"], ["Protons kahan chhode jaate hain? Protons thylakoid ke andar, lumen "
                                                          "mein chhode jaate hain."]),
            point("11.6.1-k4", "figure", ["p002-i5"], ["Ab Z scheme figure dekho: Photosystem II se shuru karke har "
                                                        "label ek station hai."],
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
    ])


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
        self.assertIn("11.6-k1 sentence 5: write it in Roman script", found)
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
        part["points"][2]["says"] += [f"Protons ka ek aur pehlu number {n} dekho." for n in range(24)]
        part["points"] = [p for p in part["points"] if p["kind"] != "example"]
        found = check(2, part)
        self.assertIn("11.6.1-k2 sentence 3: names the book ('Book')", found)
        # a point is one book line in one flow (Navin, 26 Nov 2026: the passed c2 is 23 lines), at most 24 lines
        self.assertIn("11.6.1-k3: 25 lines; a point teaches one book line in at most 24", found)
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
        self.assertIn("0 of 11 sentences ask the learner something: ask at the turns of the teaching", found)
        self.assertNotIn('no "kyun"', found)                      # its why lines give the kyun
        for p in part["points"]:
            p["roles"] = ["plain" if r == "why" else r for r in p.get("roles") or []]
        self.assertIn('no "kyun" in this heading: give the why of what matters', check(2, part))
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
        part["points"][1]["roles"].append("plain")
        self.assertEqual(studio_script.problems(part, heads[2], ch, parts()[:2], []), [])
        part["bridge"] = ""
        self.assertIn('"bridge" is empty', " | ".join(studio_script.problems(part, heads[2], ch, parts()[:2], [])))
        # rule B3 (Navin, 27 November 2026): a last line that leaves the next question open needs no bridge
        part["points"][-1]["says"].append("Electron ki kami kaun bharta hai, yeh aage hum dekhenge.")
        part["points"][-1]["roles"].append("link")
        self.assertTrue(studio_script.ends_open(part))
        self.assertNotIn('"bridge"', " | ".join(studio_script.problems(part, heads[2], ch, parts()[:2], [])))
        self.assertEqual(studio_script.problems(parts()[3], heads[3], ch, parts()[:3], [], None, []), [])   # last heading
        counts = studio_script.counts(ch, parts())
        self.assertEqual((counts["retells"], counts["fragments"], counts["goals"]), (1, 0, 4))
        self.assertGreater(counts["question_share"], 0.15)
        rules = studio_script.messages(ch, heads[0], [], course=ch["course"])[0]["content"]
        for words in ("Ask the learner at the turns of the teaching", '"overview" point', '"retell" point',
                      "never a sentence of three words or fewer", "oxygen-18 is radioactive", "leaving its question open"):
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
        self.assertIn("**11.6-k1** · samjhana · Roshni se uchhla electron aage kis taraf move karta hai", text)
        self.assertIn("- f4 · shabd ka matlab · PS II · PS II ka matlab", text)        # padhai pehle: the facts by kind
        self.assertIn("Kitab ki baatein (6): kitab kehti hai 3 · shabd ka matlab 1 · pehle ki zaroori baat 1 · figure ka "
                      "nishaan 1", page)


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


class TeacherWay(unittest.TestCase):
    """Rule B1 (Navin, 25 November 2026): "vaad anuvaad nahi; ek padha likha teacher use kaise samjhata hai bachon ko";
    Claude's worked example of the CF₁ line, "bilkul yahi tha". The facts first and locked, then the teacher's order:
    known, picture, plain, why, term, fact."""

    def test_the_answer_carries_facts_uses_and_roles(self):
        self.assertTrue(strict_ready(studio_script.SCHEMA))
        self.assertEqual(list(studio_script.SCHEMA["properties"]), ["section", "goal", "misaal", "facts", "points", "bridge"])
        self.assertIn("roles", studio_script.POINT["properties"])
        self.assertIn("uses", studio_script.POINT["properties"])

    def test_every_item_has_its_facts_and_every_fact_is_taught(self):
        part = copy.deepcopy(parts()[2])
        part["facts"] = []
        self.assertIn('"facts" is empty', check(2, part))
        part = copy.deepcopy(parts()[2])
        part["facts"] = [f for f in part["facts"] if f["item"] != "p002-i2"]
        self.assertIn("no book fact is listed for p002-i2", check(2, part))
        part = copy.deepcopy(parts()[2])
        part["facts"].append({"id": "f9", "item": "p002-i1", "fact": "Oxygen is released."})
        self.assertIn("facts f9 are used by no point", check(2, part))
        part["points"][0]["uses"] = ["f42"]
        self.assertIn("11.6.1-k1: uses ['f42'], which are not ids", check(2, part))
        ch = chapter()
        ch["items"]["p002-i1"]["content"] = "Water is split to give several protons."
        heads = studio_script.headings(ch)
        found = " | ".join(studio_script.problems(parts()[2], heads[2], ch, parts()[:2], []))
        self.assertIn("the facts of p002-i1 leave out the book's 'several'", found)
        ch["items"]["p002-i1"]["content"] = "Water is split (Figure 11.5) to replace the electrons."
        found = " | ".join(studio_script.problems(parts()[2], heads[2], ch, parts()[:2], []))
        self.assertNotIn("leave out the book's", found)                  # a figure number is not a fact

    def test_each_line_has_a_job(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["roles"] = ["plain"]
        self.assertIn("11.6-k1: roles must give each of its 4 lines of says its job", check(1, part))
        part["points"][0]["roles"] = ["link", "plain", "teaching", "why"]
        self.assertIn("11.6-k1: roles must give each", check(1, part))

    def test_a_term_is_named_after_the_idea_is_told(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["says"] = ["Electrons PS II se PS I ki taraf move karte hain, ek line mein.",
                                     "Yeh isliye hota hai kyunki har agla station electron ko thoda neeche kheenchta hai."]
        part["points"][0]["roles"] = ["term", "why"]
        self.assertIn("11.6-k1 line 1: names 'PS II' before the idea is told", check(1, part))
        part["points"][0]["roles"] = ["ask", "why"]                       # a question may name it
        self.assertNotIn("before the idea is told", check(1, part))
        self.assertEqual(check(1, parts()[1]), "")                        # the plain idea first, then the term

    def test_a_cause_is_explained(self):
        part = copy.deepcopy(parts()[1])
        part["points"][0]["roles"] = ["link", "plain", "term", "plain"]
        self.assertIn("11.6-k1: teaches a cause (p001-i3) but no line says why", check(1, part))

    def test_a_line_that_says_the_books_line_again_is_counted_not_sent_back(self):
        # the 11.6.3 rewrite (25 Nov 2026): all four lines the word overlap flagged were questions, answers and recalls
        ch = chapter()
        self.assertTrue(studio_script.restates("Water split hota hai to replace the electrons, yahi hota hai.",
                                               [ch["items"]["p002-i1"]["content"]], ch))
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"] = ["Water split hota hai to replace the electrons, yahi hota hai.",
                                     "Aisa isliye hota hai kyunki PS II ko apne electrons wapas chahiye."]
        self.assertNotIn("says the book's line again", check(2, part))

    def test_ordinary_words_are_said_in_hindi(self):
        ch = chapter()
        heavy = "Plants apna food make karte hain, aur light reactions protons released karti hain."
        found, words = studio_script.english_words(heavy, ch)
        self.assertEqual(found, ["plants", "food", "make", "light", "reactions", "protons", "released"])
        self.assertEqual(studio_script.english_words("Paudhe apna khana khud banate hain, roshni ki madad se.", ch)[0], [])
        self.assertEqual(studio_script.english_words("PS II se electron aage jaata hai.", ch)[0], [])   # the terms stay
        part = copy.deepcopy(parts()[1])
        part["points"][0]["says"][2] = heavy
        self.assertIn("11.6-k1 line 3: 7 of its 13 words are English (plants, food, make, light, reactions, protons)",
                      check(1, part))
        counts = studio_script.counts(ch, parts())
        self.assertEqual((counts["facts"], counts["english_heavy"]), (13, 0))   # 6 lines, the summary, 3 bases, 2 words, a label
        self.assertEqual(counts["baatein"], {"book": 7, "word": 2, "base": 3, "label": 1, "extra": 0})

    def test_an_answer_opens_with_its_questions_words(self):
        # rules A4 and C2, Navin's card of 25 November 2026: "Sawaal ke shabdon se"
        part = copy.deepcopy(parts()[2])
        part["points"][2]["says"] = ["Protons kahan chhode jaate hain? Thylakoid ke andar, lumen mein."]
        self.assertIn("11.6.1-k3: the answer to 'Protons kahan chhode jaate hain?' does not open with its question's words",
                      check(2, part))
        part["points"][2]["says"] = ["Protons kahan chhode jaate hain? Dekho, protons thylakoid ke andar chhode jaate hain."]
        self.assertNotIn("does not open with its question's words", check(2, part))
        part["points"][2]["says"] = ["Ruko, pehle khud socho: protons kahan chhode jaate hain?",
                                     "Aapne socha hoga ki thylakoid ke andar, aur aapne sahi socha."]
        part["points"][2]["roles"] = ["ask", "answer"]
        self.assertNotIn("does not open with its question's words", check(2, part))
        rules = studio_script.messages(chapter(), studio_script.headings(chapter())[1], [], course=chapter()["course"])[0]["content"]
        for words in ("a question never comes alone", "Aapne socha", "An answer opens with its question's own words"):
            self.assertIn(words, rules)

    def test_the_rules_teach_the_teachers_way(self):
        ch = chapter()
        rules = studio_script.messages(ch, studio_script.headings(ch)[1], [], course=ch["course"])[0]["content"]
        for words in ("PADHAI PEHLE", "vaad anuvaad nahi", "Never say the book's line again",
                      "known (start from what the learner already knows", "term (only now the book's term",
                      "never copy its words", "a few words recalling an earlier one", '"lautna", not "return"'):
            self.assertIn(words, rules)

    def test_the_facts_are_locked_after_the_first_answer(self):
        first = copy.deepcopy(parts()[1])
        first["points"][0]["roles"] = ["link", "plain", "term", "plain"]   # a problem that is not about facts
        second = copy.deepcopy(first)
        second["facts"][0]["fact"] = "Electrons jump about."
        client = Client([parts()[0], first, second, parts()[2], parts()[3]])
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"], max_rounds=2)
        rounds = next(r for r in record["rounds"] if r["section"] == "11.6")["rounds"]
        self.assertIn(studio_script.LOCKED, rounds[1]["problems"])
        self.assertNotIn(studio_script.LOCKED, rounds[0]["problems"])

    def test_one_heading_is_written_again_in_its_place(self):
        old = parts()
        new = copy.deepcopy(parts()[1])
        new["points"][3]["says"] = ["Subah dhoop milte hi dhaan ke kheton ki pattiyan kaam shuru kar deti hain."]
        client = Client([new])
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"], only=["h11-6"], earlier=old)
        self.assertEqual(len(client.calls), 1)
        self.assertIn("NOW WRITE THE SCRIPT OF THIS HEADING: 11.6 THE ELECTRON TRANSPORT", client.calls[0][1]["content"])
        self.assertIn("Plants apna food khud kaise banate hain", client.calls[0][1]["content"])  # the script so far is the old
        self.assertEqual([p["section"] for p in record["parts"]], ["", "11.6", "11.6.1", "recap"])
        self.assertEqual(record["parts"][1]["points"][3]["says"], new["points"][3]["says"])
        self.assertEqual(record["parts"][2], old[2])
        self.assertEqual(record["problems"], {})

    def test_the_vm_stage_writes_one_heading_again(self):
        import tools.vm_studio as vm_studio
        with tempfile.TemporaryDirectory() as folder:
            naksha, earlier = Path(folder) / "naksha", Path(folder) / "script"
            naksha.mkdir()
            earlier.mkdir()
            (naksha / "chapter_map.json").write_text(json.dumps(chapter()), encoding="utf-8")
            (earlier / "script.json").write_text(json.dumps({"parts": parts()}), encoding="utf-8")
            args = SimpleNamespace(stage="script", source="", from_run=str(earlier), chapter_map=str(naksha), videos="h11-6",
                                   out=str(Path(folder) / "out"), pages="", course="", language="Hinglish", model="",
                                   max_rounds=2, pyqs="")
            client = Client([parts()[1]])
            summary = vm_studio.run(args, client=client, load=None)
            self.assertEqual(summary["status"], "ok", summary)
            self.assertEqual(summary["rewritten"], ["h11-6"])
            self.assertEqual(len(client.calls), 1)
            data = json.loads((Path(folder) / "out" / "script.json").read_text(encoding="utf-8"))
            self.assertEqual([p["section"] for p in data["parts"]], ["", "11.6", "11.6.1", "recap"])
            args.chapter_map = ""
            failed = vm_studio.run(args, client=Client([parts()[1]]), load=None)
            self.assertEqual(failed["status"], "failed")


TARGET = Path(__file__).resolve().parent / "fixtures" / "teacher_target" / "11.6.3_first_try.json"


def target():
    """Three book lines of 11.6.3 (with Figure 11.7), Claude's first cut script of them, and the rewrite Navin passed."""
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    passed = studio_script.namunas()[0]
    ch = {"items": {iid: dict(it, ncert_section="11.6.3") for iid, it in data["items"].items()},
          "source_sha256": passed["withheld_for"]["source_sha256"]}
    heading = {"number": "11.6.3", "title": "Chemiosmotic Hypothesis", "items": list(data["items"]),
               "rows": [{"id": iid, "terms": it["terms"], "parts": []} for iid, it in data["items"].items()]}
    return data, passed, ch, heading


class PadhaiPehle(unittest.TestCase):
    """Padhai pehle (Navin, 25 November 2026: "maksad kitab ki complex bhasha ko asan shabdon mein samjhane ka hai na ki
    terms hi kha jaane ka"): the facts list what the learner must take, by kind (book, word, base, label, extra), and the
    script teaches all of it; a book word is never cut to keep English low. The yardstick: Claude's first 11.6.3 script,
    which cut what the book teaches, and the rewrite Navin passed ("bilkul passed hai meri taraf se")."""

    def test_the_facts_carry_a_kind_and_a_term(self):
        self.assertEqual(list(studio_script.FACT["properties"]), ["id", "item", "kind", "term", "fact"])
        self.assertEqual(studio_script.FACT["properties"]["kind"]["enum"], ["book", "word", "base", "label", "extra"])
        self.assertTrue(strict_ready(studio_script.SCHEMA))
        part = copy.deepcopy(parts()[2])
        part["facts"][0]["kind"] = "fact"
        self.assertIn("fact f1: kind 'fact' is not one of book, word, base, label, extra", check(2, part))
        word = next(f for f in part["facts"] if f["kind"] == "word")
        word["term"] = ""
        self.assertIn(f"fact {word['id']}: a word fact names in \"term\" the book's word it is about", check(2, part))

    def test_a_term_the_chapter_opens_here_has_its_meaning(self):
        part = copy.deepcopy(parts()[2])
        part["facts"] = [f for f in part["facts"] if f["kind"] != "word"]
        self.assertIn("no word fact tells what 'lumen' (first met in p002-i1) means", check(2, part))
        # PS II was opened in 11.6, so 11.6.1 does not open it again
        self.assertNotIn("what 'PS II'", check(2, part))

    def test_what_the_items_need_first_is_recalled(self):
        part = copy.deepcopy(parts()[1])
        part["facts"] = [f for f in part["facts"] if f["kind"] != "base"]
        for p in part["points"]:
            p["uses"] = [u for u in p["uses"] if any(f["id"] == u for f in part["facts"])]
        self.assertIn("no base fact recalls them: 'light is energy' (p001-i3)", check(1, part))
        part = copy.deepcopy(parts()[1])
        base = next(f for f in part["facts"] if f["kind"] == "base")
        base["fact"] = "Pattiyan hari hoti hain."                       # recalls something else
        self.assertIn("'light is energy' (p001-i3)", check(1, part))

    def test_a_figure_is_walked_by_the_labels_it_has(self):
        part = copy.deepcopy(parts()[2])
        label = next(f for f in part["facts"] if f["kind"] == "label")
        label["term"] = "Photosystem IX"
        self.assertIn(f"fact {label['id']}: the figure p002-i5 has no label 'Photosystem IX'", check(2, part))
        part["facts"] = [f for f in part["facts"] if f["kind"] != "label"]
        for p in part["points"]:
            p["uses"] = [u for u in p["uses"] if any(f["id"] == u for f in part["facts"])]
        self.assertIn("the figure p002-i5 is walked by 0 label facts; list at least 1 of what it shows by name "
                      "(Photosystem II)", check(2, part))

    def test_a_word_or_label_is_said_where_it_is_taught(self):
        part = copy.deepcopy(parts()[2])
        part["points"][3]["says"] = ["Ab Z scheme figure dekho: har label ek station hai."]
        label = next(f for f in part["facts"] if f["kind"] == "label")
        self.assertIn(f"fact {label['id']}: 'Photosystem II' is never said in 11.6.1-k4, which teaches it", check(2, part))

    def test_the_books_short_forms_are_all_said(self):
        self.assertEqual(studio_script.book_names("Light reaches P680 PS II and P700 PS I, then Fd and FNR to NADP⁺; "
                                                  "water releases ½O₂; CF₀–CF₁ ATP synthase, ADP + Pᵢ, cytochrome B6f, "
                                                  "H⁺ (Chapter 12, Figure 11.7)."),
                         ["P680", "PS", "P700", "FNR", "NADP⁺", "½O₂", "CF₀", "CF₁", "ATP", "ADP", "Pᵢ", "B6f", "H⁺"])
        ch = chapter()
        ch["items"]["p001-i3"]["content"] = "Electrons move from PS II to PS I and make ATP."
        heads = studio_script.headings(ch)
        found = " | ".join(studio_script.problems(parts()[1], heads[1], ch, parts()[:1], []))
        self.assertIn("the book writes these here and no line says them: ATP (p001-i3)", found)

    def test_book_words_are_never_counted_as_everyday_english(self):
        ch = chapter()
        line = "Plants apna food make karte hain, aur light reactions protons released karti hain."
        self.assertIn("protons", studio_script.english_words(line, ch)[0])
        self.assertNotIn("protons", studio_script.english_words(line, ch, frozenset({"protons"}))[0])
        part = copy.deepcopy(parts()[2])
        part["facts"].append({"id": "f99", "item": "p002-i1", "kind": "word", "term": "released protons", "fact": "..."})
        self.assertTrue({"released", "protons", "lumen"} <= studio_script.book_words(part, studio_script.headings(ch)[2], ch))

    def test_a_base_may_be_recalled_but_not_copied(self):
        written = parts()[:2]
        part = copy.deepcopy(parts()[2])
        earlier = "Roshni ek electron ko dhakka deti hai aur woh PS II se aage chal padta hai."
        written[1]["points"][0]["says"][1] = earlier
        part["points"][1]["says"].insert(0, "Yaad karo, roshni electron ko dhakka deti hai aur woh PS II se aage chalta hai.")
        part["points"][1]["roles"].insert(0, "known")
        self.assertNotIn("11.6.1-k2 sentence 1 says again", check(2, part, written))
        part["points"][1]["says"][0] = earlier                           # the same sentence copied
        self.assertIn("11.6.1-k2 sentence 1 says again", check(2, part, written))

    def test_a_galat_line_says_the_wrong_idea_and_breaks_it(self):
        part = copy.deepcopy(parts()[2])
        part["points"][1]["says"].append("Paani hi electrons deta hai.")
        part["points"][1]["roles"].append("galat")
        self.assertIn("11.6.1-k2: the galat line 'Paani hi electrons deta hai.' must say the wrong idea and break it",
                      check(2, part))
        part["points"][1]["says"][-1] = "Aksar hum sochte hain ki PS I paani se electron leta hai, par aisa nahi hai."
        self.assertNotIn("galat line", check(2, part))
        for _ in range(2):
            part["points"][1]["says"].append("Aksar log sochte hain ki oxygen CO₂ se aati hai, par asal mein paani se aati hai.")
            part["points"][1]["roles"].append("galat")
        self.assertIn("3 galat lines; at most 2 in a heading", check(2, part))

    def test_the_goal_is_todays_question(self):
        part = copy.deepcopy(parts()[2])
        part["goal"] = "Ab dekhenge ki PS II ke khoye electrons ki kami kaun bharta hai."
        part["points"][0]["says"][0] = part["goal"]
        self.assertIn("\"goal\" is today's question (rule A4)", check(2, part))

    def test_a_long_heading_hangs_on_one_running_picture(self):
        part = copy.deepcopy(parts()[2])
        extra = [point(f"11.6.1-k{n}", "explain", [], [f"Paani ka anu {n} ki baat aage badhti hai, kyunki electron chahiye."],
                       roles=["why"]) for n in (9, 10, 11)]
        part["points"] += extra
        self.assertIn("\"misaal\" is empty", check(2, part))
        part["misaal"] = "seedhi: electron har kadam par neeche utarta hai"
        self.assertIn("the heading's misaal 'seedhi: electron har kadam par neeche utarta hai' is pictured in 0 point(s)",
                      check(2, part))
        for p in extra[:2]:
            p["says"].append("Jaise seedhi par gend ek kadam aur neeche aati hai.")
            p["roles"].append("picture")
        self.assertNotIn("misaal", check(2, part))

    def test_the_rules_put_teaching_first(self):
        ch = chapter()
        rules = studio_script.messages(ch, studio_script.headings(ch)[1], [], course=ch["course"])[0]["content"]
        for words in ("PADHAI PEHLE", "terms hi kha jaane ka", "no rule of voice, length or repetition is ever a reason",
                      "A book word is never dropped", "a base the learner has lost", "walked as a story with a finger",
                      "today's question (aaj ka sawaal, rule A4)", "\"misaal\": the heading's one running picture"):
            self.assertIn(words, rules)

    def test_the_passed_example_is_shown_except_while_its_own_heading_is_written(self):
        ch = chapter()
        user = studio_script.messages(ch, studio_script.headings(ch)[2], [], course=ch["course"])[1]["content"]
        self.assertIn("A WORKED EXAMPLE OF THE WAY: 11.6.3 Chemiosmotic Hypothesis", user)
        self.assertIn("Never copy its words, pictures or examples", user)
        self.assertIn("- known · f5: Pehle jagah pakki kar lo.", user)                   # a line with its job and fact
        self.assertIn("[word: chemiosmotic hypothesis]", user)
        self.assertIn("shows by name (label facts): Photosystem II", user)              # the figure's labels, named
        _, passed, own, heading = target()
        self.assertEqual(studio_script.namuna(own, heading), "")                       # 11.6.3 of its own book
        self.assertNotEqual(studio_script.namuna(dict(own, source_sha256="another book"), heading), "")

    def test_the_yardstick_catches_the_cut_script_and_passes_the_passed_one(self):
        data, passed, ch, heading = target()
        first = [{"id": f"11.6.3-{k}", "says": p["says"]} for k, p in data["first_try"].items()]
        cut = [n for n, _ in studio_script.unsaid_names(heading, ch, first)]
        for name in ("ETS", "P680", "P700", "B6f", "½O₂", "Pᵢ"):           # never said by the first script
            self.assertIn(name, cut)
        points = [{"id": f"11.6.3-{p['id']}", "kind": p["kind"], "teaches": p["teaches"],
                   "says": [line["says"] for line in p["lines"]], "roles": [line["role"] for line in p["lines"]],
                   "uses": sorted({u for line in p["lines"] for u in line["uses"]})} for p in passed["points"]]
        answer = {"goal": passed["goal"], "misaal": passed["misaal"], "facts": passed["facts"], "points": points}
        self.assertEqual([n for n, _ in studio_script.unsaid_names(heading, ch, points)], ["FNR", "CF₀", "CF₁"])
        found = studio_script.padhai_problems(answer, heading, ch, points)
        # only what the passed steps leave to the heading's later steps (CF₀, CF₁, the ATP synthase and chemiosmosis are
        # taught in c9 to c11 of the whole script), and one small thing the checks found in it: the figure's FNR is never named
        self.assertEqual(len(found), 3, found)
        self.assertIn("'chemiosmosis' (first met in p011-i1)", found[0])
        self.assertIn("FNR (p011-i1), CF₀ (p011-i1), CF₁ (p011-i1)", found[1])
        self.assertIn("the book writes 'synthase' here and no sentence opens it by itself", found[2])
        # the hard words: the passed steps open hypothesis, chemi + osmotic, gradient and electro + chemical; the cut
        # script opened none of them
        self.assertEqual([w for w, _ in studio_script.unopened_words(heading, ch, points)], ["synthase"])
        self.assertEqual([w for w, _ in studio_script.unopened_words(heading, ch, first)],
                         ["hypothesis", "chemiosmotic", "gradient", "electrochemical", "synthase"])
        self.assertEqual(sum(1 for p in points for line in p["says"] if studio_script.bolchaal(line)), 0)
        kinds = {k: sum(1 for f in passed["facts"] if f["kind"] == k) for k in studio_script.BAAT_KINDS}
        self.assertEqual(kinds, {"book": 7, "word": 7, "base": 5, "label": 8, "extra": 1})


class BolchaalAurKholo(unittest.TestCase):
    """Seekh from BIE s8 (25 November 2026), its 11.6.3 beside the passed rewrite: 28 of its 96 lines said an
    accountant's words ("Ledger ki pehli row mein lumen ke khaate mein H⁺ judte hain"), and it never opened the hard words
    inside the book's terms (what a hypothesis is, "chemi" + "osmotic", a gradient as a slope); and the passed example,
    withheld for its own heading, had leaked into the rules as their examples."""

    def test_an_accountants_words_are_found_unless_they_are_book_words(self):
        line = "Ledger ki pehli row mein lumen ke khaate mein H⁺ judte hain, yeh pehla contribution hai."
        self.assertEqual([w for w, _ in studio_script.bolchaal(line)], ["ledger", "khaata", "contribution"])
        for eating in ("Sher hiran ko khaata hai.", "Hum roti khaate hain.", "Jo hum khaate the, woh paudhon se aaya.",
                       "Gaay ghaas khaate waqt jugaali karti hai."):
            self.assertEqual(studio_script.bolchaal(eating), [], eating)              # eating, not an account (job k1)
        self.assertEqual([w for w, _ in studio_script.bolchaal("H⁺ lumen ke khaate mein jaate hain.")], ["khaata"])
        self.assertEqual(studio_script.bolchaal("Inner-side electron handover par H⁺ lumen mein chhoot jaata hai.")[0][0],
                         "handover")
        self.assertEqual(studio_script.bolchaal("Paani ka tootna pehla kaam hai, aur carrier H⁺ utha leta hai."), [])
        self.assertEqual(studio_script.bolchaal("C4 pathway mein pehle CO₂ pakdi jaati hai.", frozenset({"pathway"})), [])
        self.assertEqual(studio_script.bolchaal("Raaste ka pathway dekho.")[0], ("pathway", "raasta"))

    def test_every_point_is_checked_for_them_a_figure_walk_too(self):
        _, passed, ch, heading = target()
        answer = {"facts": passed["facts"]}
        points = [{"id": "11.6.3-k1", "kind": "figure", "teaches": [], "uses": [],
                   "says": ["Ab green proton arrows follow karo.", "Ledger ki pehli row lumen ki hai."],
                   "roles": ["link", "fact"]}]
        found = " | ".join(studio_script.explain_problems(answer, heading, ch, points))
        self.assertIn("11.6.3-k1: a teacher does not say an accountant's or office's words to children: 'follow' (line 1)",
                      found)
        self.assertIn("'ledger' (line 2): say hisaab, ginti", found)

    def test_a_hard_word_inside_a_term_is_opened_by_itself(self):
        _, _, ch, heading = target()
        def unopened(*says, opened=frozenset()):
            points = [{"id": "11.6.3-k1", "says": list(says)}]
            return [w for w, _ in studio_script.unopened_words(heading, ch, points, opened)]
        named = unopened("Isi ko chemiosmotic hypothesis kehte hain.")
        self.assertIn("hypothesis", named)
        self.assertIn("chemiosmotic", named)
        told = unopened("Kisi baat ko samjhane ka aisa vichaar, jise prayogon se parkha jaata hai, hypothesis kehlata hai.",
                        "Chemi yaani rasayanik kaam. Osmotic yaani membrane ke aar-paar bahna.",
                        "Isi dhalaan ko proton gradient kehte hain; gradient ka matlab hi dhalaan hai.")
        self.assertNotIn("hypothesis", told)
        self.assertNotIn("chemiosmotic", told)
        self.assertNotIn("gradient", told)
        self.assertIn("gradient", unopened("Dono processes mein gradient ki jagah alag hai."))      # said, never opened
        self.assertNotIn("gradient", unopened("Kuch nahi.", opened=frozenset({"concentration gradient"})))
        self.assertIn("hypothesis", unopened("Kuch nahi.", opened=frozenset({"hypothesised"})))     # another word
        answer = {"facts": []}
        found = " | ".join(studio_script.padhai_problems(answer, heading, ch, [{"id": "11.6.3-k1", "says": ["Kuch nahi."]}]))
        self.assertIn("the book writes 'chemiosmotic' here and no sentence opens it by itself: where it is first needed, "
                      "break it into its parts inside the teaching", found)
        self.assertIn("the book writes 'hypothesis' here and no sentence opens it by itself: where it is first needed, tell "
                      "what it means inside the teaching, joined to the line it serves, in your own words", found)
        self.assertIn("(for you, not to copy: it means an explanation put forward first and then tested", found)

    def test_the_rules_quote_no_line_of_the_withheld_example(self):
        _, passed, ch, heading = target()
        rules = studio_script.messages(chapter(), studio_script.headings(chapter())[1], [],
                                       course=chapter()["course"])[0]["content"]
        for phrase in ("ADP ko chhua", "baandh", "balloon", "½O₂", "lumen", "ledger", "dilchaspi", "CF₀"):
            self.assertNotIn(phrase.lower(), rules.lower().replace('"ledger"', ""))
        said = [line["says"] for p in passed["points"] for line in p["lines"]] + [passed["goal"], passed["misaal"]]
        for line in said:
            words = line.split()
            for n in range(len(words) - 5):                           # no run of six words of the example
                self.assertNotIn(" ".join(words[n:n + 6]), rules)
        self.assertIn('Never an accountant\'s or\n  an office\'s words ("ledger", "khaata", "contribution"', rules)

    def test_the_counts_show_both(self):
        ch = chapter()
        c = studio_script.counts(ch, parts())
        self.assertIn("bolchaal", c)
        self.assertIn("unopened", c)
        self.assertEqual(c["bolchaal"], 0)


class RawClient:
    """Answers with the given texts as they are (a lesson in plain text, or a JSON object)."""

    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def chat(self, *, model, messages, schema=None):
        self.calls.append((messages, schema))
        text = self.texts.pop(0)
        return {"content": text if isinstance(text, str) else json.dumps(text),
                "usage": {"input_tokens": 100, "output_tokens": 20}}

    def plan_usage(self):
        return None


def lesson_of(part):
    """A heading's part told as step 1's plain lesson."""
    rows = ["FACTS"] + [f"{f['id']} | {f['item']} | {f['kind']} | {f.get('term') or ''} | {f['fact']}"
                        for f in part.get("facts") or []]
    rows += [f"GOAL: {part.get('goal', '')}", f"MISAAL: {part.get('misaal', '')}", "LESSON"]
    for p in part["points"]:
        rows.append("[" + (", ".join(p.get("teaches") or []) or p["kind"]) + "]")
        rows += p["says"]
    rows.append(f"BRIDGE: {part.get('bridge', '')}")
    return "\n".join(rows)


class KahaniPehle(unittest.TestCase):
    """Pehle padhana, phir dhaancha (Navin, 26 November 2026, on BIE's 11.6.3 s9 beside the rewrite he passed: "Aas paas
    bhi nahi hai tumhare banaye namune ke abhi"; his card: "Haan, yahi plan"). BIE's own checks would have sent the passed
    rewrite back 12 times (points of at most 8 lines, one sentence in five a question, a kyun question): the rules that
    fought it are loosened, and each heading's first round is written as the teacher speaks it, then marked."""

    def test_the_passed_rewrite_meets_every_rule_of_form(self):
        _, passed, ch, heading = target()
        teaches = {"c2": ["p010-i14"], "c3": ["p010-i15", "p011-i1"]}
        points = [{"id": f"11.6.3-k{n}", "kind": "explain", "teaches": teaches[p["id"]], "screen": "figure", "recalls": [],
                   "terms": [], "prepares": [], "says": [line["says"] for line in p["lines"]],
                   "roles": [line["role"] for line in p["lines"]],
                   "uses": sorted({u for line in p["lines"] for u in line["uses"]})}
                  for n, p in enumerate(passed["points"], 1)]
        answer = {"section": "11.6.3", "goal": passed["goal"], "misaal": passed["misaal"], "facts": passed["facts"],
                  "points": points, "bridge": "Ab dekhenge ki yeh dhalaan banti kaise hai."}
        found = studio_script.problems(answer, heading, ch, [], [])
        # the gold standard (Navin, 26 Nov 2026: "sabhi niyam jo pdhane se script se jude hai uske hisab se taya hone
        # chahiye"): no check of the script sends it back; what is left is only what the heading's later steps teach (the
        # machine CF₀-CF₁ and its synthase, FNR, chemiosmosis, the checkpoint and the worked example of the whole heading)
        later_steps = ("'chemiosmosis'", "FNR (p011-i1), CF₀ (p011-i1), CF₁ (p011-i1)", "'synthase'",
                       "needs at least one checkpoint", "needs at least one worked example")
        self.assertEqual([x for x in found if not any(step in x for step in later_steps)], [])
        self.assertEqual(len(found), 6, found)

    def test_rule_b4_points_back_or_ahead_with_no_fixed_formula(self):
        rules = studio_script.messages(chapter(), studio_script.headings(chapter())[1], [],
                                       course=chapter()["course"])[0]["content"]
        self.assertIn('rule B4: no fixed formula, the context decides', rules)
        self.assertIn('"jaisa humne dekha tha ..."', rules)
        self.assertIn('"aage hum dekhenge ki ...; abhi ke liye bas itna jaan lo ki ..."', rules)
        _, passed, _, _ = target()                 # the gold standard does both: the path walked again, respiration ahead
        said = " ".join(line["says"] for p in passed["points"] for line in p["lines"])
        self.assertIn("jo hum pehle padh chuke hain", said)
        self.assertIn("aage respiration wale chapter mein", said)

    def test_the_lesson_is_read_and_its_lines_are_kept_word_for_word(self):
        part = parts()[2]
        lesson = studio_script.parse_lesson(lesson_of(part))
        self.assertEqual([b["head"] for b in lesson["blocks"]], [p.get("teaches") or [p["kind"]] for p in part["points"]])
        self.assertEqual(lesson["goal"], part["goal"])
        self.assertEqual(studio_script.lesson_drift(part, lesson), [])
        changed = copy.deepcopy(part)
        changed["points"][0]["says"][0] = "Kuch aur hi baat."
        self.assertIn("1 differ (first:", studio_script.lesson_drift(changed, lesson)[0])
        self.assertIsNone(studio_script.parse_lesson('{"section": "11.6.1", "points": []}'))

    def test_the_first_round_is_told_first_then_marked(self):
        written = parts()
        texts = []
        for part in written:
            texts += [lesson_of(part), part]                  # step 1: the lesson; step 2: its JSON
        client = RawClient(texts)
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"])
        self.assertEqual(record["problems"], {})
        self.assertEqual(len(client.calls), 2 * len(written))
        (first, schema1), (second, schema2) = client.calls[:2]
        self.assertIsNone(schema1)                            # step 1 is plain text
        self.assertIn("STEP 1 OF 2: THE LESSON, AS YOU SPEAK IT", first[-1]["content"])
        self.assertNotIn(studio_script.JSON_ONLY, first[0]["content"])        # s10: told "JSON only", it answered JSON
        self.assertIn(studio_script.TEXT_ONLY, first[0]["content"])
        self.assertIn(studio_script.JSON_ONLY, second[0]["content"])
        self.assertIs(schema2, studio_script.SCHEMA)
        self.assertEqual(second[-1]["content"], studio_script.STRUCTURE_PROMPT)
        self.assertEqual(second[-2]["content"], lesson_of(written[0]))
        self.assertIn("lesson", record["rounds"][0]["rounds"][0])
        self.assertEqual(record["usage"], {"input_tokens": 200 * len(written), "output_tokens": 40 * len(written)})

    def test_a_step_one_json_without_points_is_not_taken_for_the_heading(self):
        # job s10: step 1 came back as a JSON object of facts with no points ("no points" in round 1)
        written = parts()
        texts = [{"section": "", "facts": [], "goal": written[0]["goal"]}, written[0]]
        for part in written[1:]:
            texts += [part]
        client = RawClient(texts)
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"])
        self.assertEqual(record["problems"], {})
        self.assertEqual(client.calls[1][1], studio_script.SCHEMA)          # the JSON asked for directly
        self.assertIn("told_unread", record["rounds"][0]["rounds"][0])

    def test_a_maker_that_answers_with_json_at_once_is_taken_as_it_is(self):
        client = Client(parts())
        record = studio_script.write(client, "fake", chapter(), course=chapter()["course"])
        self.assertEqual(record["problems"], {})
        self.assertEqual(len(client.calls), len(parts()))


class SeekhS11(unittest.TestCase):
    """Job s11, the first run of the lesson step (26 November 2026): c2 one flow of 14 lines, 6 questions in the heading;
    but joined figure labels said aloud ("PQ; PQH₂; Plastoquinone wale carrier"), a hard word passed as opened when a
    meaning word stood elsewhere in its sentence, and today's question holding its answer."""

    def test_joined_labels_are_split_never_said_joined(self):
        _, passed, ch, heading = target()
        facts = [{"id": "f1", "item": "p011-i1", "kind": "label", "term": "Fd; FNR", "fact": "electron ka raasta"}]
        points = [{"id": "11.6.3-k1", "kind": "figure", "uses": ["f1"], "teaches": ["p011-i1"],
                   "says": ["PS I ke baad electron Fd, yaani ferredoxin, se FNR enzyme tak jaata hai."], "roles": ["fact"]}]
        found = " | ".join(studio_script.padhai_problems({"facts": facts}, heading, ch, points))
        self.assertNotIn("'Fd; FNR' is never said", found)                # each name said: no joined line asked
        self.assertNotIn("has no label", found)
        points[0]["says"] = ["PS I ke baad electron Fd tak jaata hai."]
        found = " | ".join(studio_script.padhai_problems({"facts": facts}, heading, ch, points))
        self.assertIn("fact f1: 'FNR' is never said in 11.6.3-k1", found)                 # names checked one by one
        self.assertEqual(studio_script._names("Stroma (low H⁺); Stroma"), ["Stroma (low H⁺)", "Stroma"])

    def test_a_hard_word_is_opened_only_where_its_meaning_stands_next_to_it(self):
        _, _, ch, heading = target()
        def unopened(*says):
            return [w for w, _ in studio_script.unopened_words(heading, ch, [{"id": "11.6.3-k1", "says": list(says)}])]
        self.assertIn("gradient", unopened("Protein ke raaste aise paar jaane ko facilitated diffusion kehte hain; yahaan "
                                           "unhe ulte gradient ke khilaaf nahi dhakela ja raha."))      # s11's false pass
        self.assertNotIn("gradient", unopened("Isi ko proton gradient kehte hain; gradient ka matlab hi dhalaan hai."))
        self.assertNotIn("gradient", unopened("Yeh ek dhalaan hai, yaani gradient."))

    def test_todays_question_does_not_name_the_headings_new_words(self):
        _, passed, ch, heading = target()
        part = {"goal": "Electron transport ki energy proton gradient ke zariye ATP banane tak kaise pahunchti hai?",
                "points": [{"id": "11.6.3-k1", "says": ["Electron transport ki energy proton gradient ke zariye ATP banane "
                                                         "tak kaise pahunchti hai?"]}], "bridge": "x"}
        found = " | ".join(studio_script.teacher_problems(part, heading, ch, part["points"]))
        self.assertIn("\"goal\" names 'proton gradient', which this heading opens", found)
        part["goal"] = passed["goal"]                                   # the gold standard's puzzle names no new word
        part["points"][0]["says"] = [passed["goal"]]
        self.assertNotIn("which this heading opens", " | ".join(studio_script.teacher_problems(part, heading, ch,
                                                                                                 part["points"])))


class TeacherVoice(unittest.TestCase):
    """Navin, 26 November 2026, on s11: "sentence ki lambai order sankya se hi clear ho rha hai kon teacher ki tarah
    samjha rha hai aur kaun ab bhi jyu ka tyo likh rha hai"; the gold standard: 68 sentences of 15.1 words, a quarter
    spoken to the learner, a third going on the way a teacher talks."""

    def test_a_packed_textbook_heading_is_sent_back_and_the_gold_standard_is_not(self):
        _, passed, ch, heading = target()
        packed = ["Concentration aur electrical haalat ke is fark ko proton gradient kehte hain jo membrane ke dono taraf "
                  "banta hai aur ATP formation se juda hai."] * 22
        part = {"goal": "Electron ne ADP ko chhua tak nahi; toh ATP bana kaise?", "bridge": "x",
                "points": [{"id": "11.6.3-k1", "kind": "explain", "says": ["Electron ne ADP ko chhua tak nahi; toh ATP "
                                                                           "bana kaise?"] + packed}]}
        found = " | ".join(studio_script.teacher_problems(part, heading, ch, part["points"]))
        self.assertIn("words on average (the passed rewrite: 15)", found)
        self.assertIn("of the sentences speak to the learner (the passed rewrite: a quarter)", found)
        self.assertIn("go on from the one before the way a teacher talks", found)
        points = [{"id": f"11.6.3-k{n}", "kind": "explain", "says": [line["says"] for line in p["lines"]],
                   "roles": [line["role"] for line in p["lines"]]} for n, p in enumerate(passed["points"], 1)]
        gold = {"goal": passed["goal"], "bridge": "x", "points": points}
        found = " | ".join(studio_script.teacher_problems(gold, heading, ch, points))
        for rule in ("words on average", "speak to the learner", "the way a teacher talks"):
            self.assertNotIn(rule, found)

    def test_the_lesson_comes_before_its_facts(self):
        self.assertLess(studio_script.LESSON_PROMPT.index("LESSON\n["), studio_script.LESSON_PROMPT.index("FACTS\nf1"))
        self.assertIn("write the lesson first and list its facts after it", studio_script.LESSON_PROMPT)
        text = ("GOAL: Toh ATP bana kaise?\nMISAAL: baandh\nLESSON\n[p010-i14]\nAb ek baat par gaur karo.\n"
                "Toh ATP bana kaise?\nFACTS\nf1 | p010-i14 | book | | ATP gradient se banta hai\nBRIDGE: Ab aage.")
        lesson = studio_script.parse_lesson(text)
        self.assertEqual(lesson["blocks"], [{"head": ["p010-i14"], "lines": ["Ab ek baat par gaur karo.",
                                                                              "Toh ATP bana kaise?"]}])
        self.assertEqual([f["id"] for f in lesson["facts"]], ["f1"])
        self.assertEqual((lesson["goal"], lesson["bridge"]), ("Toh ATP bana kaise?", "Ab aage."))


class LessonAsJson(unittest.TestCase):
    """Job s12, 11.6.3: Codex sent step 1 as a JSON object (GOAL, MISAAL, LESSON blocks of teaches and lines), and BIE
    threw the lesson away and asked the JSON directly."""

    def test_a_json_shaped_lesson_is_read(self):
        text = json.dumps({"GOAL": "Toh ATP bana kaise?", "MISAAL": "baandh", "LESSON": [
            {"teaches": ["p010-i14"], "lines": ["Ab ek baat par gaur karo.", "Toh ATP bana kaise?"]},
            {"teaches": "analogy", "lines": ["Ek baandh socho."]}],
            "FACTS": [{"id": "f1", "item": "p010-i14", "kind": "book", "term": "", "fact": "ATP gradient se banta hai"},
                      "f2 | p010-i14 | word | gradient | dhalaan"], "BRIDGE": "Ab aage."}, ensure_ascii=False)
        lesson = studio_script.parse_lesson(text)
        self.assertEqual([b["head"] for b in lesson["blocks"]], [["p010-i14"], ["analogy"]])
        self.assertEqual([f["id"] for f in lesson["facts"]], ["f1", "f2"])
        self.assertEqual((lesson["goal"], lesson["misaal"], lesson["bridge"]), ("Toh ATP bana kaise?", "baandh", "Ab aage."))
        self.assertIsNone(studio_script.parse_lesson('{"section": "11.6.1", "points": []}'))


class BridgeAndB3(unittest.TestCase):
    """Navin, 27 November 2026 (raasta A): the heading's last film speaks the bridge after the script's lines, so when the
    last line already leaves the next question open ("... aage hum dekhenge") the film does not say the end twice."""

    def test_an_open_last_line_is_recognised(self):
        for line, open_ in (("C₄ paudhe alag kis baat mein hain, yeh aage hum dekhenge.", True),
                            ("ATP bana kaise, yeh aage dekhenge.", True),
                            ("Yeh agle heading mein dekhenge.", True),
                            ("Toh ATP bana kaise?", False)):
            self.assertEqual(studio_script.ends_open({"points": [{"says": ["Ek line.", line]}]}), open_, line)
        self.assertFalse(studio_script.ends_open({"points": []}))

    def test_the_film_skips_the_bridge_after_an_open_last_line(self):
        ch = chapter()
        script = {"chapter_title": "Ch", "parts": copy.deepcopy(parts())}
        target = script["parts"][2]
        number = target["section"]
        def last_lines(s):
            films = studio_script.film_questions(s, ch)
            mine = [q for q in films["questions"] if q["pillar"] == number]
            return [x["roman"] for x in mine[-1]["teacher_lines"]]
        bridge = target["bridge"].strip()
        self.assertEqual(last_lines(script)[-1], bridge)                              # a closed end: the bridge leads on
        target["points"][-1]["says"].append("Electron ki kami kaun bharta hai, yeh aage hum dekhenge.")
        target["points"][-1]["roles"].append("link")
        lines = last_lines(script)
        self.assertEqual(lines[-1], "Electron ki kami kaun bharta hai, yeh aage hum dekhenge.")
        self.assertNotIn(bridge, lines)

