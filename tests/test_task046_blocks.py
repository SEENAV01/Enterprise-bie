"""Task 046 Part B: the benchmark blocks as code, the composer (shot list → VideoSpec), the placeholder voice's text side,
the render tool, the rule table with frames and the Blender sheet script. Offline, standard library only; the pixel
checks (Pillow), the real eSpeak NG voice and the real Blender sheets are in tests/toolbox/test_task046_frames.py (the
toolbox wrappers lane)."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import shots  # noqa: E402
from bie.brain.understanding import Course  # noqa: E402
from bie.brain.video import compose, frame_checks, render, voice  # noqa: E402
from bie.toolbox import demos, registry  # noqa: E402
import render_video  # noqa: E402

BLOCKS = ROOT / "bie/brain/video/blocks/toolbox"
FIXTURE = ROOT / "tests/fixtures/task046/v3_tissue.json"
BOX = registry.load()
V3 = json.loads(FIXTURE.read_text(encoding="utf-8"))
V3_COURSE = Course(**V3["course"])
V3_CHAPTER = {"course": V3["course"], "items": V3["items"], "level": V3["level"], "source_sha256": V3["source_sha256"]}
ACCENTS = json.loads((BLOCKS / "accents.json").read_text(encoding="utf-8"))
WORLD = ("cell_sheet", "particle_flow", "focus_glow", "organ_zoom", "leader_label", "camera_path", "cutaway", "exploded_view")
GRAMMAR = ("kinetic_caption", "board_build", "mnemonic_card", "concept_arrow", "split_compare", "scale_compare", "flow_arrows", "graph_plot", "timeline")
EIGHTEEN = WORLD + GRAMMAR + ("equation_steps",)


def registered_blocks() -> dict:
    out = {}
    for path in BLOCKS.glob("*.tsx"):
        for name in re.findall(r'registerBlock\("([a-z0-9_]+)"', path.read_text(encoding="utf-8")):
            out[name] = path.name
    return out


def bench_demos() -> list:
    return [d for d in demos.DEMOS if d.id.startswith("bench-")]


class TheEighteenBlocks(unittest.TestCase):
    def test_every_block_is_registered_in_the_toolbox_bundle(self):
        registered = registered_blocks()
        for name in EIGHTEEN:
            self.assertIn(name, registered)
        self.assertEqual({registered[n] for n in WORLD}, {"benchmark.tsx"})
        self.assertEqual({registered[n] for n in GRAMMAR}, {"grammar.tsx"})
        self.assertEqual(registered["equation_steps"], "maths.tsx")
        index = (BLOCKS / "index.ts").read_text(encoding="utf-8")
        self.assertIn('import "./benchmark"', index)
        self.assertIn('import "./grammar"', index)
        grammar = set(json.loads((ROOT / "bie/toolbox/capabilities.json").read_text(encoding="utf-8"))["grammar_blocks"]["blocks"])
        self.assertTrue(grammar <= set(registered), grammar - set(registered))

    def test_the_world_block_carries_every_flag_the_composer_writes(self):
        src = (BLOCKS / "benchmark.tsx").read_text(encoding="utf-8")
        for key in ("member?:", "focus?:", "flow?:", "camera?:", "cutaway?:", "exploded?:", "stretch?:", "dim?:", "labels?:", "organ?:"):
            self.assertIn(key, src, key)
        for member in ACCENTS:
            self.assertIn(f'"{member}"', src, member)
        self.assertIn("buildEarth", src)                                # the L4 demo world: shells and a bar magnet, code only
        self.assertIn('data.world === "earth"', src)
        self.assertIn("flagSince", src)                                 # a cut stays open across the sentences that keep it
        self.assertIn("loadGlb", src)                                   # route C: the same block draws a Blender-made glTF by src

    def test_every_block_has_a_demo_clip_checked_against_its_rules(self):
        bench = bench_demos()
        self.assertEqual(len(bench), 17)
        used = set()
        with tempfile.TemporaryDirectory() as tmp:
            for d in bench:
                work = demos.Work(folder=Path(tmp), library=None)
                spec = d.build(work)
                used |= set(demos.spec_blocks(spec))
                self.assertEqual((spec["width"], spec["height"]), (1280, 720), d.id)
                self.assertTrue(3.0 <= d.seconds <= 5.0, d.id)
                self.assertEqual(spec["scenes"][0]["duration"], int(round(d.seconds * 30)), d.id)
                self.assertIn("B-11", d.rules, d.id)
                self.assertIn("VG-01", d.rules, d.id)
                self.assertTrue(work.notes.get("accent", "").startswith("#"), d.id)
                self.assertEqual((d.batch, d.kind), (1, "web"), d.id)
                self.assertIn("bie-benchmark-blocks", d.tools, d.id)
        self.assertTrue(set(WORLD + GRAMMAR) <= used, set(WORLD + GRAMMAR) - used)
        self.assertIn('block("equation_steps"', Path(demos.__file__).read_text(encoding="utf-8"))   # proven by maths-equation

    def test_the_l4_demos_run_on_the_earth_wedge_and_magnet(self):
        with tempfile.TemporaryDirectory() as tmp:
            for did, name in (("bench-cutaway-earth", "cutaway"), ("bench-exploded-earth", "exploded_view"), ("bench-flow-arrows-earth", "cell_sheet")):
                work = demos.Work(folder=Path(tmp), library=None)
                spec = demos.by_id(did).build(work)
                world = next(l for l in spec["scenes"][0]["layers"] if l["block"] == name)
                self.assertEqual(world["data"]["world"], "earth", did)
                self.assertEqual(work.notes["accent"], demos.EARTH_ACCENT)
                flags = [k for s in world["data"]["shots"] for k in ("cutaway", "exploded") if s.get(k)]
                self.assertTrue(flags or name == "cell_sheet", did)
            arrows = [l for l in spec["scenes"][0]["layers"] if l["block"] == "flow_arrows"]
            self.assertEqual(len(arrows), 2)
            self.assertEqual(arrows[0]["data"]["label"], "field line N → S")

    def test_the_registry_entry_claims_only_what_the_demos_prove(self):
        tool = BOX.tool("bie-benchmark-blocks")
        self.assertEqual((tool.kind, tool.path, tool.status, tool.batch, tool.licence), ("js_lib", "web", "demo_proven", 1, "BIE's own code"))
        self.assertEqual(sorted(tool.proof["demos"]), sorted(d.id for d in bench_demos()))
        self.assertEqual(set(tool.capabilities), {c for d in bench_demos() for c in d.capabilities})
        for cap in tool.capabilities:
            self.assertIn(cap, BOX.capabilities)


class TheComposer(unittest.TestCase):
    """The v3 shot list (Part A) becomes a VideoSpec: one world per scene with every clause as a shot on its timeline, a kinetic
    caption per clause, panels for the L3 shots, credits last."""

    @classmethod
    def setUpClass(cls):
        cls.plan = shots.build_video(V3["video"], V3_CHAPTER, V3_COURSE, toolbox=BOX)
        cls.segment = compose.segment(cls.plan, parts=["c07.1"])
        cls.spec = compose.video_spec(cls.segment)

    def world(self, scene):
        return next(l for l in scene["layers"] if l["id"] == "world")

    def test_the_family_segment_is_one_world_with_a_caption_per_clause(self):
        self.assertEqual([s["part_id"] for s in self.segment["scenes"]], ["c07.1"])
        self.assertEqual(compose.check_spec(self.segment, self.spec), [])
        scene = self.spec["scenes"][0]
        world = self.world(scene)
        self.assertEqual((world["block"], world["at"], world["box"]), ("cell_sheet", 0, compose.FULL))
        self.assertEqual(len(world["data"]["shots"]), len(self.segment["shots"]))
        captions = [l for l in scene["layers"] if l.get("block") == "kinetic_caption"]
        self.assertEqual(len(captions), len(self.segment["shots"]))
        self.assertTrue(all(c["data"]["text"] and c["data"]["accent"].startswith("#") for c in captions))
        self.assertEqual(self.spec["scenes"][-1]["id"], "credits")
        self.assertEqual((self.spec["width"], self.spec["height"], self.spec["fps"], self.spec["schema"]), (1920, 1080, 30, compose.SCHEMA))
        total = sum(s["duration"] for s in self.spec["scenes"])
        self.assertTrue(150 <= total / 30 <= 360, total / 30)         # the family segment: a few minutes, the credits included

    def test_shot_frames_cover_every_shot_once_in_order(self):
        rows = compose.shot_frames(self.segment, self.spec)
        self.assertEqual([r["shot_id"] for r in rows], [s["shot_id"] for s in self.segment["shots"]])
        total = sum(s["duration"] for s in self.spec["scenes"])
        self.assertTrue(all(0 <= r["from"] < r["to"] <= total for r in rows))
        self.assertTrue(all(a["to"] <= b["from"] for a, b in zip(rows, rows[1:])))
        self.assertTrue(all(r["level"] in ("L2", "L3", "L4", "L5a") and r["capability"] for r in rows))

    def test_members_carry_across_clauses_and_panels_rest_the_world(self):
        world = self.world(self.spec["scenes"][0])
        members = [s["member"] for s in world["data"]["shots"]]
        self.assertTrue(set(members) <= set(ACCENTS), set(members) - set(ACCENTS))
        self.assertGreaterEqual(len(set(members)), 3)                   # the family: squamous, cuboidal, columnar and more
        for ws, ps in zip(world["data"]["shots"], self.segment["shots"]):
            if ps["capability"] in ("mnemonic_card", "split_compare", "tree_hierarchy"):
                self.assertTrue(ws.get("dim"), ps["shot_id"])
            if ps["capability"] == "particle_flow" or "particle_flow" in ps["blocks"]:
                self.assertIn(ws["flow"]["kind"], ("absorb", "secrete", "cross", "sweep", "shed"), ps["shot_id"])
            self.assertEqual(ws["camera"]["move"], ps["camera"] if "organ_zoom" not in (ps["capability"], *ps["blocks"]) else "zoom_in")

    def test_said_equals_shown_fails_on_an_unsaid_label(self):
        spec = copy.deepcopy(self.spec)
        self.world(spec["scenes"][0])["data"]["shots"][0]["labels"] = [{"text": "mitochondria", "part": "cell"}]
        problems = compose.check_spec(self.segment, spec)
        self.assertTrue(any("mitochondria" in p and "B-03" in p for p in problems), problems)
        spec = copy.deepcopy(self.spec)
        spec["scenes"][0]["layers"] = [l for l in spec["scenes"][0]["layers"] if l.get("block") != "kinetic_caption"]
        self.assertTrue(any("B-08" in p for p in compose.check_spec(self.segment, spec)))

    def test_voice_audio_and_credits_are_written_into_the_spec(self):
        spec = compose.video_spec(self.segment, voice={"provider": "espeak-ng-placeholder/1"}, audio="narration.wav",
                                  credits=[{"title": "Lung drawing", "author": "Someone", "licence": "CC BY 4.0"}])
        self.assertEqual(spec["audio"], "narration.wav")
        credits = json.dumps(spec["scenes"][-1], ensure_ascii=False)
        self.assertEqual(spec["scenes"][-1]["duration"], 120)
        for text in ("espeak-ng-placeholder/1", "Lung drawing", "CC BY 4.0", "BIE's own code"):
            self.assertIn(text, credits)
        silent = compose.video_spec(self.segment, with_credits=False)
        self.assertNotIn("audio", silent)
        self.assertNotEqual(silent["scenes"][-1]["id"], "credits")


class ThePlaceholderVoiceAndTheRenderTool(unittest.TestCase):
    def test_ssml_reads_hindi_and_english_runs_in_their_own_voices(self):
        text = voice.ssml("Squamous यानी चपटी, scale जैसी cells")
        self.assertTrue(text.startswith('<speak version="1.0" xml:lang="hi">'))
        self.assertEqual(re.findall(r'<voice name="(\w+)">([^<]*)</voice>', text),
                         [("en", "Squamous"), ("hi", " यानी चपटी, "), ("en", "scale"), ("hi", " जैसी "), ("en", "cells")])
        self.assertIn("&amp;", voice.ssml("A & B"))
        self.assertEqual(voice.PROVIDER, "espeak-ng-placeholder/1")

    def test_compose_command_writes_the_silent_segment_and_route_c_models(self):
        plan = shots.build_video(V3["video"], V3_CHAPTER, V3_COURSE, toolbox=BOX)
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "v3.json"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
            models = Path(tmp) / "models"
            models.mkdir()
            for member in ("simple_squamous", "simple_cuboidal"):
                (models / f"{member}.glb").write_bytes(b"glTF fake")
            out = Path(tmp) / "out"
            # the fixture v3 points at the book in five beats (W-01): the composer refuses it unless told this is a pipeline check
            self.assertFalse(plan["render_allowed"])
            self.assertEqual(render_video.main(["compose", "--plan", str(plan_path), "--beats", str(FIXTURE), "--parts", "c07.1", "--out", str(out),
                                                "--voice", "silent"]), 2)
            self.assertFalse((out / "video_spec.json").exists())
            code = render_video.main(["compose", "--plan", str(plan_path), "--beats", str(FIXTURE), "--parts", "c07.1", "--out", str(out),
                                      "--voice", "silent", "--route", "C", "--models", str(models), "--allow-blocked"])
            self.assertEqual(code, 0)
            summary = json.loads((out / "compose.json").read_text(encoding="utf-8"))
            self.assertEqual((summary["voice"], summary["route"], summary["check_spec"], summary["parts"], summary["blocked"]), ("silent", "C", [], ["c07.1"], True))
            spec = json.loads((out / "video_spec.json").read_text(encoding="utf-8"))
            rows = json.loads((out / "shots_frames.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["shots"], len(rows))
            self.assertEqual(summary["frames"], sum(s["duration"] for s in spec["scenes"]))
            self.assertNotIn("audio", spec)
            worlds = [l for s in spec["scenes"] for l in s["layers"] if l.get("block") == "cell_sheet"]
            models = {m: p for w in worlds for m, p in (w["data"].get("models") or {}).items()}
            self.assertEqual(models, {"simple_squamous": "assets/models/simple_squamous.glb", "simple_cuboidal": "assets/models/simple_cuboidal.glb"})
            self.assertEqual(summary["models"], ["simple_cuboidal", "simple_squamous"])
            self.assertTrue((out / "assets" / "models" / "simple_squamous.glb").exists())
            self.assertFalse((out / "assets" / "models" / "ciliated.glb").exists())       # no model made: the procedural sheet for that member
            members = {s["member"] for w in worlds for s in w["data"]["shots"]}
            self.assertTrue({"simple_squamous", "simple_cuboidal"} < members)               # the scene shows more members than it has models

    def test_chunks_cover_every_frame_once_and_measure_prices_at_the_list_price(self):
        ranges = [render_video.chunk_range(8938, i, 6) for i in range(6)]
        self.assertEqual(ranges[0][0], 0)
        self.assertEqual(ranges[-1][1], 8938)
        self.assertTrue(all(a[1] == b[0] for a, b in zip(ranges, ranges[1:])))
        self.assertEqual(render_video.chunk_range(10, 3, 3), (10, 10))                    # an empty last chunk, never past the end
        with tempfile.TemporaryDirectory() as tmp:
            for i, (video, took) in enumerate(((60.0, 300.0), (60.0, 420.0))):
                (Path(tmp) / f"part-{i:02d}.json").write_text(json.dumps({"chunk": i, "chunks": 2, "frames": [0, 1800], "video_seconds": video,
                                                                               "render_seconds": took, "machine": "x", "cpus": 2}), encoding="utf-8")
            self.assertEqual(render_video.main(["measure", "--out", tmp, "--route", "A"]), 0)
            cost = json.loads((Path(tmp) / "cost.json").read_text(encoding="utf-8"))
        self.assertEqual((cost["video_seconds"], cost["render_seconds"], cost["seconds_per_video_second"], cost["machine_minutes"]), (120.0, 720.0, 6.0, 12.0))
        self.assertEqual(cost["wall_clock_minutes_parallel"], 7.0)
        self.assertAlmostEqual(cost["usd_at_list_price"], 12.0 * render_video.LIST_PRICE_USD_PER_MINUTE, places=3)
        self.assertAlmostEqual(cost["inr_at_list_price"], round(12.0 * render_video.LIST_PRICE_USD_PER_MINUTE * render_video.USD_TO_INR, 2), places=2)

    def test_blocked_reasons_members_and_the_summary_over_routes(self):
        plan = shots.build_video(V3["video"], V3_CHAPTER, V3_COURSE, toolbox=BOX)
        reasons = render_video.blocked_reasons(plan)
        self.assertEqual(len([r for r in reasons if r.startswith("W-01")]), 5)
        self.assertTrue(any("b22" in r and "Book short cylindrical" in r for r in reasons), reasons)
        members = render_video.members_of(compose.segment(plan, parts=["c07.1"]))
        self.assertTrue({"simple_squamous", "simple_cuboidal", "simple_columnar", "ciliated", "stratified_squamous"} <= set(members), members)
        self.assertTrue(set(members) <= set(ACCENTS))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for route, spc, inr in (("A", 4.2, 310.5), ("C", 4.5, 330.0)):
                (out / route).mkdir()
                (out / route / "report.json").write_text(json.dumps({"shots": 76, "seconds": 302.0, "main_level": "L5a", "pace": {"seconds_per_change": spc},
                                                                     "tally": {"pass": 16, "partial": 3, "n/a": 5}, "cost": {"seconds_per_video_second": 6.1,
                                                                     "machine_minutes": 31.0, "inr_at_list_price": inr}}), encoding="utf-8")
            (out / "bridge").mkdir()
            (out / "bridge" / "bridge.json").write_text(json.dumps({"video_seconds": 10.0, "seconds_per_video_second": 9.5, "mean_differences": [1.1, 0.9, 1.4], "passed": True}), encoding="utf-8")
            self.assertEqual(render_video.main(["summary", "--out", tmp, "--run-id", "1", "--sha", "abcdef012345", "--run-url", "x"]), 0)
            text = (out / "REPORT.md").read_text(encoding="utf-8")
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        self.assertIn("| A | 76 | 302.0 | L5a | 4.2 s | 16 / 3 / 0 | 6.1 | 31.0 | 310.5 |", text)
        self.assertIn("| C | 76 |", text)
        self.assertIn("Bridge (real Remotion, first 10.0 s of route A): 9.5 render s per video s", text)
        self.assertIn("IMPLEMENTED", text)
        self.assertEqual(sorted(summary["routes"]), ["A", "C"])

    def test_the_renderer_takes_a_frame_range_for_chunks(self):
        stills = (ROOT / "bie/brain/video/preview/stills.mjs").read_text(encoding="utf-8")
        self.assertIn("args.from", stills)
        self.assertIn("args.to", stills)
        self.assertTrue(callable(render.mp4_range))
        self.assertIn("first", render.mp4_range.__code__.co_varnames)


class TheRuleTableWithFrames(unittest.TestCase):
    def test_frame_findings_override_the_plan_reading(self):
        plan_rows = [{"rule": "B-08", "status": "pass", "note": "caption per clause"}, {"rule": "B-11", "status": "partial", "note": "decided by the render"},
                     {"rule": "VG-09", "status": "partial", "note": "decided by the render"}, {"rule": "B-01", "status": "partial", "note": "18 clauses over 6 s"}]
        findings = {"findings": {"B-08": [{"shot": "b3.1", "frame": 412, "why": "no caption text in the top band"}], "B-11": [], "VG-09": []}}
        merged = {r["rule"]: r for r in frame_checks.rule_table_with_frames(plan_rows, findings)}
        self.assertEqual((merged["B-08"]["status"], merged["B-08"]["frame"], merged["B-08"]["frame_status"]), ("fail", 412, "fail"))
        self.assertIn("frame 412 (b3.1)", merged["B-08"]["note"])
        self.assertEqual((merged["B-11"]["status"], merged["B-11"]["frame_status"]), ("pass", "pass"))
        self.assertEqual(merged["VG-09"]["status"], "pass")
        self.assertEqual((merged["B-01"]["status"], merged["B-01"]["frame_status"], merged["B-01"]["frame"]), ("partial", "not read", None))


class TheSeekhFromVmJob1(unittest.TestCase):
    """VM job 1 stopped at its cap of Rs 5 before the review because the estimate priced the whole chapter (Rs 39.17) for a resume
    of one script; the estimate of a lesson resume now scales to the scripts asked (``--videos``)."""

    def test_the_estimate_of_a_lesson_resume_scales_to_the_selected_videos(self):
        from bie.brain import cost
        plan = {"videos": [{"video_id": "v0", "spoken_minutes": 7.0}, {"video_id": "v3", "spoken_minutes": 11.7},
                           {"video_id": "v5", "beats": [{"say": " ".join(["word"] * 1300)}]}]}            # 10 minutes at 130 wpm
        share = cost.lesson_share(plan, ["v3"])
        self.assertEqual((share["selected"], share["videos"]), (1, 3))
        self.assertAlmostEqual(share["share"], 11.7 / 28.7, places=3)
        self.assertEqual(cost.lesson_share(plan, ["v9"]), {"share": 1.0, "videos": 3, "selected": 0})      # nothing known selected: the whole chapter
        self.assertEqual(cost.lesson_share(plan, [])["share"], 1.0)
        self.assertEqual(cost.lesson_share({}, ["v3"])["share"], 1.0)
        whole = cost.estimate("lesson", 14, rate=94.59)["total_inr"]
        part = cost.estimate("lesson", round(14 * share["share"], 2), rate=94.59)["total_inr"]
        self.assertAlmostEqual(part / whole, 14 * share["share"] / 14 / 1, delta=0.01)
        self.assertLess(part, whole * 0.45)
        source = (ROOT / "tools/run_brain.py").read_text(encoding="utf-8")
        self.assertIn("cost_module.lesson_share(previous_lesson", source)
        self.assertIn("pages_to_run=round(chapter_pages(chapter) * share[\"share\"], 2)", source)


class TheBlenderSheetScript(unittest.TestCase):
    """The route C script (read without Blender: bpy is stubbed; the real run is in the wrappers lane)."""

    @classmethod
    def setUpClass(cls):
        sys.modules.setdefault("bpy", types.ModuleType("bpy"))
        spec = importlib.util.spec_from_file_location("cell_sheet_script", ROOT / "bie/toolbox/blender/cell_sheet.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_every_family_member_is_a_kind_with_its_layers(self):
        m = self.module
        for member in ACCENTS:
            self.assertIn(member, m.MEMBERS, member)
        for shape in ("squamous", "cuboidal", "columnar"):
            self.assertEqual(m.MEMBERS[shape], [shape])
        self.assertEqual(len(m.MEMBERS["stratified_squamous"]), 5)
        self.assertEqual(m.MEMBERS["stratified"], m.MEMBERS["stratified_squamous"])
        self.assertEqual(m.MEMBERS["keratinised"][-1], "keratin")
        self.assertEqual(m.MEMBERS["transitional"][-1], "dome")
        self.assertTrue(set(l for layers in m.MEMBERS.values() for l in layers) <= set(m.SHAPES))
        self.assertIsNone(m.SHAPES["keratin"][2])                        # dead flat cells: no nucleus

    def test_the_names_the_web_block_looks_for(self):
        src = (ROOT / "bie/toolbox/blender/cell_sheet.py").read_text(encoding="utf-8")
        for name in ('f"cell_{tag}"', 'f"nucleus_{tag}"', 'f"cilium_{r}_{c}_{k}"', 'f"microvillus_{r}_{c}_{k}"', '"basement_membrane"', '"underlying_tissue"', '"gland_duct"'):
            self.assertIn(name, src, name)
        self.assertIn('kind in ("ciliated", "pseudostratified")', src)
        self.assertIn('kind == "simple_cuboidal"', src)
        self.assertIn('kind == "glandular"', src)
        self.assertIn("export_format=\"GLB\"", src)


if __name__ == "__main__":
    unittest.main()
