"""The PYQ lab (Navin, 19 November 2026): science models, lesson checks, the VM stage and the player data.

Offline: the maker is a fake; the lessons below are test data shaped like a maker's answer (not BIE output). The three
models are checked on the reference investigations (projectile height, alcohol + HBr with a hydride shift, the embryo
sac's n/2n/3n) and on fresh questions whose plans are not copied from the reference (range at 60°, a methyl shift, the
PEN's chromosome number for 2n = 20)."""
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

from bie.brain import pyq_bio, pyq_chem, pyq_math, pyq_models, studio_pyq  # noqa: E402
from bie.model_gateway.live.messages import strict_ready  # noqa: E402

PHYS_Q = {"id": "g1", "exam": "NEET 2023", "origin": "pyq", "answer": 3,
          "question": "A bullet is fired from a gun at 280 m/s, at 30° above the horizontal. What is the maximum height? "
                      "Take g = 9.8 m/s² and sin 30° = 0.5.", "options": ["3000 m", "2800 m", "2000 m", "1000 m"]}
PHYS_MODEL = {"kind": "projectile", "svg": "",
              "lines": ["u = 280 m/s", "theta = 30 deg", "g = 9.8 m/s2", "sin = 0.5", "asked = max_height",
                        'ref = 828 m "Burj Khalifa"']}
CHEM_LINES = ["reactant [CH3:1][CH:2]([OH:6])[C:3]([H:9])([CH3:4])[CH3:5]", "reactant [H:7][Br:8]", "label 2 C2",
              "label 3 C3", "step s1 protonation: lp 6 -> 7; bond 7-8 -> 8", "step s2 water leaves: bond 2-6 -> 6",
              "step s3 hydride shift: shift 9 3 -> 2", "step s4 bromide attacks: lp 8 -> 3",
              "trap t1 after s2 direct swap at C2: lp 8 -> 2", "option 1 CC(C)(C)CBr", "option 2 CCC(C)(C)Br",
              "option 3 CC=CC", "option 4 CC(Br)C(C)C"]
SAC = ['diploid 24', 'entity ant1 "Antipodal" cell sets=1 origin=maternal at=42,15',
       'entity ant2 "Antipodal" cell sets=1 origin=maternal at=50,12', 'entity ant3 "Antipodal" cell sets=1 origin=maternal at=58,15',
       'entity central "Central cell" cell sets=0 at=50,45',
       'entity polar1 "Polar nucleus" nucleus sets=1 origin=maternal in=central at=45,45',
       'entity polar2 "Polar nucleus" nucleus sets=1 origin=maternal in=central at=55,45',
       'entity egg "Egg" cell sets=1 origin=maternal at=50,78', 'entity syn1 "Synergid" cell sets=1 origin=maternal at=40,82',
       'entity syn2 "Synergid" cell sets=1 origin=maternal at=60,82',
       'entity m1 "Male gamete" gamete sets=1 origin=paternal at=30,96',
       'entity m2 "Male gamete" gamete sets=1 origin=paternal at=34,97',
       'fuse syngamy "Syngamy": m1 + egg -> zygote "Zygote" fate="embryo"',
       'fuse triple "Triple fusion": m2 + polar1 + polar2 -> pen "Primary endosperm nucleus" fate="endosperm"']
SAC_Q = SAC + ['asked sequence 1 2 3', 'option 1 = syn1, ant1, polar1', 'option 2 = syn1, pen, zygote',
               'option 3 = ant1, syn1, pen', 'option 4 = syn1, zygote, pen']


def beat(say, voice="यह वाक्य देवनागरी में है।", **kw):
    base = {"say": say, "voice": voice, "view": "main", "focus": [], "labels": [], "moment": "", "play": False,
            "board": "", "detail": "", "gate": ""}
    base.update(kw)
    return base


def phys_lesson():
    return {
        "title": "Bullet sach mein kitni upar jaati hai?", "concept": "Projectile ki height sirf vertical motion se",
        "scene_title": "Hillside launch",
        "given": [{"name": "u", "value": "280 m/s"}, {"name": "θ", "value": "30°"}, {"name": "g", "value": "9.8 m/s²"}],
        "asked": "Maximum height H", "unknowns": ["uᵧ", "H"], "assumptions": ["Hawa ka rukawat nahi", "Same level par landing"],
        "objectives": ["Velocity ko components mein todna"], "prerequisites": [{"idea": "sin θ", "why": "opposite side"}],
        "evidence": [{"block_ids": ["p0001-b0001"], "idea": "Projectile ki motion do perpendicular motions hai",
                      "parts": ["vx", "vy"], "moment": "rise"}],
        "model": copy.deepcopy(PHYS_MODEL),
        "stages": [
            {"key": "see", "title": "Bullet ko pehle dekho", "text": "Ek tilted launch aur ek curved flight.",
             "beats": [beat("Gun ka barrel horizontal se tees degree upar hai, aur bullet ek curve mein jaati hai.",
                            focus=["launcher"], moment="launch"),
                       beat("Humein curve ki lambai nahi, ground se sabse ooncha point chahiye, yaani seedhi height.",
                            focus=["height", "peak"], moment="peak", play=True, gate="g_peak")]},
            {"key": "trap", "title": "Ek sin θ chhoot gaya?", "text": "Galat formula se 2000 m aata hai.",
             "beats": [beat("Aksar student formula mein sin theta ko square karna bhool jaata hai, tab 2000 m aata hai.",
                            focus=["ghost"]),
                       beat("Galti arithmetic mein nahi hai, galti yeh hai ki poori vertical velocity square nahi hui.",
                            focus=["vy"])]},
            {"key": "concept", "title": "Do motions, ek flight", "text": "uᵧ = u sin θ.",
             "beats": [beat("Launch velocity ko do arrows mein baantiye, ek aage le jaata hai aur ek upar le jaata hai.",
                            focus=["vx", "vy"], view="both", detail="d_tri", gate="g_uy"),
                       beat("Top par vertical arrow zero ho jaata hai, lekin horizontal arrow phir bhi bana rehta hai.",
                            focus=["vy", "vx", "peak"], moment="peak")]},
            {"key": "solve", "title": "Height nikalte hain", "text": "vᵧ² = uᵧ² − 2gH.",
             "beats": [beat("Pehla step yeh hai ki vertical launch speed 140 m/s hai, poori 280 nahi.", board="uy"),
                       beat("Ab 140 ka square lijiye, yaani 140 guna 140, jo 19,600 banta hai.", board="uy2",
                            detail="d_sq", gate="g_sq"),
                       beat("19,600 ko 19.6 se divide kijiye, height 1,000 m aati hai, option D.", board="H")]},
            {"key": "transfer", "title": "Speed aadhi karo", "text": "Ratio se socho.",
             "beats": [beat("Same angle par speed aadhi ho jaaye, toh vertical speed bhi aadhi ho jaati hai.", focus=["vy"]),
                       beat("Height vertical speed ke square par tiki hai, isliye height ek chauthai ho jaati hai.",
                            focus=["height"])]}],
        "details": [{"id": "d_tri", "title": "280 mein se upar kitna?", "text": "Opposite side uᵧ hai.",
                     "chain": ["Diagonal u = 280 m/s", "uᵧ = u sin 30°", "280 × 0.5 = 140 m/s"], "focus": ["vy"],
                     "moment": "launch"},
                    {"id": "d_sq", "title": "140 ka square", "text": "140 × 140.",
                     "chain": ["140 × (100 + 40)", "14,000 + 5,600", "19,600"], "focus": [], "moment": ""}],
        "gates": [
            {"id": "g_peak", "mechanic": "choose", "prompt": "Top par kya hota hai?",
             "choices": ["Sirf vᵧ zero, vₓ bachi rehti hai", "Poori bullet ruk jaati hai"], "answer": "0", "tolerance": 0,
             "wrong": [{"match": "1", "why": "Gravity sirf vertical speed ko zero tak laati hai, horizontal speed chalti rehti hai."}],
             "reveal": "peak", "why": "Top par sirf upar jaana rukta hai, aage jaana nahi rukta."},
            {"id": "g_uy", "mechanic": "number", "prompt": "Shuru ki upar wali speed kitni hai?", "choices": [], "answer": "uy",
             "tolerance": 0.01,
             "wrong": [{"match": "u", "why": "280 poori tirchhi speed hai, upar wala hissa uska sin θ guna hota hai."}],
             "reveal": "launch", "why": "280 × 0.5 = 140 m/s, yahi gold vertical arrow hai."},
            {"id": "g_sq", "mechanic": "number", "prompt": "140 × 140 kitna hai?", "choices": [], "answer": "uy2",
             "tolerance": 0.001,
             "wrong": [{"match": "other", "why": "Square poore number ka hota hai, sirf aakhri digit ka nahi."}],
             "reveal": "", "why": "14,000 + 5,600 = 19,600, yahi numerator hai."}],
        "board": [{"step": "uy", "note": "Sirf vertical hissa"}, {"step": "uy2", "note": "Poore hisse ka square"},
                  {"step": "H", "note": "Top par vᵧ = 0"}],
        "diagnoses": [{"option": 1, "title": "60° wala jawab", "why": "3000 m sirf 60° ke liye sahi hai.", "shows": ""},
                      {"option": 2, "title": "Speed ko height maan liya", "why": "280 m/s ek velocity hai.", "shows": ""},
                      {"option": 3, "title": "Sin θ square nahi kiya", "why": "Ek sin θ se 2000 m aata hai.",
                       "shows": "H_one_sin"},
                      {"option": 4, "title": "Sahi", "why": "uᵧ = 140, H = 1000 m.", "shows": ""}],
        "families": [{"id": "f_half", "title": "Speed aadhi", "question": "Speed 140 m/s ho toh height?",
                      "changes": ["u = 140 m/s"], "choices": ["500 m", "250 m"], "correct": 2,
                      "why": "uᵧ aadhi, square ek chauthai.", "transfer": True},
                     {"id": "f_range", "title": "Range", "question": "Isi launch ki range?", "changes": ["asked = range"],
                      "choices": ["6928 m", "3464 m"], "correct": 1, "why": "R = uₓ T.", "transfer": False},
                     {"id": "f_angle", "title": "Angle 60°", "question": "Same speed, 60° par height?",
                      "changes": ["theta = 60 deg", "sin = 0.866"], "choices": ["3000 m", "1000 m"], "correct": 1,
                      "why": "sin²θ teen guna.", "transfer": False}],
        "recap": "Height vertical motion ki hai: pehle uᵧ, phir poore uᵧ ka square.",
        "limitations": ["Burj Khalifa schematic hai"]}


class Models(unittest.TestCase):
    def test_projectile_working_is_exact(self):
        r = pyq_math.projectile(PHYS_MODEL["lines"])
        self.assertEqual(r["problems"], [])
        self.assertEqual(pyq_math.fmt(r["values"]["uy"]), "140")
        self.assertEqual(pyq_math.fmt(r["values"]["uy2"]), "19,600")
        self.assertEqual(pyq_math.fmt(r["values"]["H"]), "1,000")
        self.assertEqual(r["clear_decimal"], {"times": "10", "num": "196,000", "den": "196", "value": "1,000"})
        self.assertEqual(r["square_split"]["pa"], "14,000")

    def test_units_are_checked(self):
        found = pyq_math.work(["given a = 3 m", "step b = a * 2 : s", "answer b"])["problems"]
        self.assertTrue(any("the working gives m, the line says s" in p for p in found))

    def test_projectile_answer_and_trap_options(self):
        r = pyq_models.build(PHYS_MODEL, PHYS_Q["options"])
        self.assertEqual(r["answer_option"], 3)
        self.assertEqual(r["trap_options"]["H_one_sin"], 2)

    def test_fresh_physics_range_at_60(self):
        r = pyq_models.build({"kind": "projectile", "lines": ["u = 20 m/s", "theta = 60 deg", "g = 10 m/s2", "asked = range"]},
                             ["17.32 m", "34.64 m", "40 m", "20 m"])
        self.assertEqual(r["answer_option"], 1)

    @unittest.skipUnless(pyq_chem.available(), "rdkit not installed")
    def test_reference_mechanism(self):
        r = pyq_chem.run(CHEM_LINES, ["A", "B", "C", "D"])
        self.assertEqual(r["problems"], [])
        self.assertEqual(r["answer_option"], 1)                     # 2-bromo-2-methylbutane
        self.assertEqual(r["trap_options"], {"t1": 3})              # the direct swap explains option D
        self.assertEqual([c["word"] for s in r["steps"] for c in s["cations"]], ["2°", "3°"])
        self.assertEqual(r["steps"][0]["changes"][0]["donor"], "a6")   # the O lone pair, not H⁺, gives the pair
        self.assertIn("O", r["product"]["byproducts"])

    @unittest.skipUnless(pyq_chem.available(), "rdkit not installed")
    def test_missing_or_forced_shift_is_named(self):
        missing = [l for l in CHEM_LINES if not l.startswith(("step s3", "step s4"))] + ["step s4 bromide: lp 8 -> 2"]
        self.assertIn("could become 3° by a 1,2-shift of H", " ".join(pyq_chem.run(missing, ["A"] * 4)["problems"]))
        no_lp = CHEM_LINES[:4] + ["step s1 wrong: lp 7 -> 6"]
        self.assertIn("no lone pair", " ".join(pyq_chem.run(no_lp, ["A"])["problems"]))

    @unittest.skipUnless(pyq_chem.available(), "rdkit not installed")
    def test_fresh_methyl_shift_and_no_shift(self):
        methyl = ["reactant [CH3:1][CH:2]([OH:6])[C:3]([CH3:4])([CH3:5])[CH3:10]", "reactant [H:7][Br:8]",
                  "step s1 p: lp 6 -> 7; bond 7-8 -> 8", "step s2 w: bond 2-6 -> 6", "step s3 methyl shift: shift 10 3 -> 2",
                  "step s4 b: lp 8 -> 3", "option 1 CC(C)C(C)(C)Br", "option 2 CC(Br)C(C)(C)C"]
        r = pyq_chem.run(methyl, ["2-bromo-2,3-dimethylbutane", "3-bromo-2,2-dimethylbutane"])
        self.assertEqual((r["problems"], r["answer_option"]), ([], 0))
        tertiary = ["reactant [CH3:1][C:2]([OH:6])([CH3:5])[CH2:3][CH3:4]", "reactant [H:7][Br:8]",
                    "step s1 p: lp 6 -> 7; bond 7-8 -> 8", "step s2 w: bond 2-6 -> 6", "step s3 b: lp 8 -> 2",
                    "option 1 CCC(C)(C)Br"]
        self.assertEqual(pyq_chem.run(tertiary, ["x"])["problems"], [])

    def test_embryo_sac(self):
        r = pyq_bio.run(SAC_Q, ["a", "b", "c", "d"])
        self.assertEqual(r["problems"], [])
        self.assertEqual(r["answer_option"], 3)
        self.assertEqual(r["counts"], {"cells": 7, "nuclei": 8})
        self.assertEqual([f["sum"] for f in r["fusions"]], ["n + n = 2n", "n + n + n = 3n"])
        pen = next(e for e in r["entities"] if e["id"] == "pen")
        self.assertEqual((pen["maternal"], pen["paternal"], pen["chromosomes"]), (2, 1, 36))

    def test_fresh_biology_counts(self):
        r = pyq_bio.run(SAC + ["diploid 20", "asked count pen"], ["10", "20", "30", "40"])
        self.assertEqual((r["problems"], r["answer_option"]), ([], 2))
        self.assertEqual(pyq_bio.run(SAC + ["asked ratio pen"], ["1:1", "2:1"])["answer_option"], 1)

    def test_exercise_question_without_options(self):
        r = pyq_models.build(PHYS_MODEL, [])
        self.assertEqual((r["problems"], r["answer_option"], r["answer_value"]), ([], None, "1,000"))

    def test_family_recomputes(self):
        f = pyq_models.family(PHYS_MODEL, ["u = 140 m/s"], ["500 m", "250 m"])
        self.assertEqual((f["correct"], f["value"]), (1, "250"))


class Lesson(unittest.TestCase):
    def setUp(self):
        self.model = pyq_models.build(PHYS_MODEL, PHYS_Q["options"])

    def test_schema_strict_and_good_lesson_passes(self):
        self.assertTrue(strict_ready(studio_pyq.SCHEMA))
        self.assertEqual(studio_pyq.problems(phys_lesson(), PHYS_Q, self.model, {"p0001-b0001"}), [])

    def test_problems_are_named(self):
        bad = phys_lesson()
        bad["stages"] = bad["stages"][:4]
        bad["stages"][2]["beats"][0]["focus"] = ["rocket"]
        bad["stages"][3]["beats"][0]["say"] = "Speed 150 m/s hai, illustrative tareeke se."
        bad["gates"][1]["wrong"] = []
        bad["diagnoses"][2]["shows"] = ""
        bad["families"][0]["correct"] = 1
        bad["evidence"][0]["block_ids"] = ["p9999-b0001"]
        found = " | ".join(studio_pyq.problems(bad, PHYS_Q, self.model, {"p0001-b0001"}))
        for text in ("exactly see, trap, concept, solve, transfer", "rocket", "150", "caution line", "wrong branches",
                     "set shows to 'H_one_sin'", "choice 2 is right", "not in the chapter"):
            self.assertIn(text, found)

    def test_key_disagreeing_with_the_model_is_flagged(self):
        q = dict(PHYS_Q, answer=0)
        self.assertIn("the model proves option 4", " ".join(studio_pyq.problems(phys_lesson(), q, self.model, {"p0001-b0001"})))

    def test_player_data_computes_answers(self):
        rec = {"question": PHYS_Q, "lesson": phys_lesson(), "model": self.model, "problems": [], "rounds": []}
        data = studio_pyq.player_data([rec], title="Projectile", tint="#4b4fa8")
        item = data["items"][0]
        self.assertEqual(item["proved"], 3)
        gate = next(g for g in item["gates"] if g["id"] == "g_uy")
        self.assertEqual((gate["value"], gate["wrong_values"]), (140.0, {"u": 280.0}))
        self.assertEqual(item["families"][0]["right"], 1)
        self.assertEqual(item["board"][0]["with_values"], "280 × 0.5")
        self.assertNotIn("block_ids", json.dumps(item["evidence"]))
        page = studio_pyq.html(data, (ROOT / "bie" / "brain" / "studio_pyq_player.html").read_text(encoding="utf-8"))
        self.assertNotIn("/*__PYQ__*/null", page)

    def test_player_lets_every_part_be_tapped_and_names_it(self):
        """The first VM runs (19 Nov 2026): the physics gate "tap the vertical component" could not be answered (the vᵧ
        arrow was not a tap target), a tap that landed on a label or beside a thin line did nothing, the chemistry scene
        labelled atoms "a2", "a3", and the second question's first transfer try counted as a later try."""
        import re
        src = (ROOT / "bie" / "brain" / "studio_pyq_player.html").read_text(encoding="utf-8")
        kit = src[src.index("KITS.projectile="):src.index("KITS.mechanism=")]
        for part in pyq_models.PROJECTILE_PARTS:            # every part a cue or a tap gate may name is a tap target
            self.assertRegex(kit, r"hit\(el\([^;]*?\),'%s'\)" % part, part)
        self.assertIn("S.tapAll=!!(S.gate&&S.waiting&&(S.gate.mechanic==='tap_part'||S.gate.mechanic==='pair'))", src)
        self.assertIn("'stroke-width':30", src)                    # a finger-sized target on every vector
        self.assertIn("const p=nearestPart(e);", src)
        self.assertIn("return bd<=28?best:null;", src)
        self.assertIn("const name=partName(id);", src)
        self.assertIn("label(svg,bb.x+bb.width/2,bb.y,name,", src)
        self.assertIn("atoms[x].tag||atoms[x].label", src)
        self.assertIn("if(a.tag&&a.tag.length<=4)el('text'", src)      # long maker tags only as labels, never piled on atoms
        self.assertIn("unclash(svg);$('scrub')", src)                    # labels never sit on each other
        self.assertIn("unclash(svg);$('dscrub')", src)
        self.assertIn("t.textContent.startsWith(name+' ')", src)       # no second label for a part the scene already names
        self.assertIn("'H = '+(m.values.H||", src)                        # the peak label is the height, never u_y
        self.assertIn("if(bx+w+16>W-4)bx=Math.max(4,x-w-19);", src)       # labels stay inside the picture
        self.assertIn("function human(t)", src)
        self.assertIn("S.tries=0;S.tTries=0;", src)
        self.assertNotRegex(src, r"let t?[tT]ries=0;")
        self.assertIn("const vyNow=t<=.02?m.values.uy:", src)


class Stage(unittest.TestCase):
    def test_pyq_stage_writes_the_lab(self):
        import vm_studio
        page = SimpleNamespace(number=1, blocks=[SimpleNamespace(id="p0001-b0001", text="Projectile motion is two "
                               "independent perpendicular motions: horizontal at constant speed and vertical under g." * 2)])

        class Fake:
            def __init__(self):
                self.calls = 0

            def chat(self, *, model, messages, schema=None):
                self.calls += 1
                return {"content": json.dumps(phys_lesson(), ensure_ascii=False), "usage": {"input_tokens": 3, "output_tokens": 2}}

        with tempfile.TemporaryDirectory() as folder:
            pyqs = Path(folder) / "pyqs.json"
            pyqs.write_text(json.dumps([PHYS_Q]), encoding="utf-8")
            args = SimpleNamespace(stage="pyq", source="x.pdf", from_run="", pyqs=str(pyqs), videos="", out=str(Path(folder) / "out"),
                                   pages="", course="NEET Physics", language="Hinglish", model="", max_rounds=2)
            summary = vm_studio.run(args, client=Fake(), load=lambda *a, **k: ("h", 1, [page]),
                                    voice_maker=lambda: (None, "test"), read=lambda s: b"%PDF-")
            out = Path(folder) / "out"
            self.assertEqual(summary["status"], "ok", summary)
            self.assertIn("1,000", (out / "PYQ.html").read_text(encoding="utf-8"))
            for name in ("PYQS.md", "pyq/g1.json", "SUMMARY.json"):
                self.assertTrue((out / name).exists(), name)
            self.assertEqual(summary["pyq"][0]["proved"], 4)

    def test_pyq_job(self):
        import codex_vm
        job = {"job": "bie.vm-job/1", "id": "pyq-test", "section": "studio", "stage": "pyq",
               "source": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/chapters/x.pdf",
               "pyqs": "https://raw.githubusercontent.com/SEENAV01/Enterprise-bie/blindtest-inputs/pyqs/x.json"}
        cmd = codex_vm.argv(codex_vm.validate(dict(job)), Path("/tmp/out"), "python")
        self.assertEqual(cmd[cmd.index("--stage") + 1], "pyq")
        self.assertEqual(cmd[cmd.index("--pyqs") + 1], job["pyqs"])
        with self.assertRaises(codex_vm.JobError):
            codex_vm.validate({k: v for k, v in job.items() if k != "pyqs"})


if __name__ == "__main__":
    unittest.main()
