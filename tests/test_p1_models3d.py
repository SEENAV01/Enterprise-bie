"""Phase 1: the showing engine's 3D layer (Navin, 5 November 2026: 3D models, objects, worlds and processes that BIE's
scene plan can change and use).

Core lane (Node, no browser, no three.js): the manifest and the engine name the same models; a model's description is a
pure function of its parameters and of time; the scene-plan compiler accepts good 3D steps and names bad ones; a 3D
world is a backdrop and a 3D model is a thing to the box rule; plain specs never need three.js. The render smoke is in
the show lane (tests/toolbox/test_p1_show_render.py), where three.js is installed.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.gold.money_v2 import gold_spec  # noqa: E402
from bie.brain.video import models3d, narration, render, showplan  # noqa: E402

from tests.test_p1_show_director import LESSON  # noqa: E402

ENGINE = ROOT / "bie" / "brain" / "video" / "engine"
VIDEO = LESSON["videos"][0]


def timeline():
    return narration.Timeline(narration.script_of(VIDEO))


def el_of(model, p=None, **kw):
    return dict({"kind": "model3d", "id": "m", "model": model, "p": p or {}, "steps": [], "cam3d": [], "x": 960, "y": 540,
                 "w": 1920, "h": 1080, "s": 1, "t0": 0.0, "keys": [], "place": True}, **kw)


def scene(*steps, world3d=None, lines=("l1", "l2", "l3")):
    sc = {"id": "A", "lines": list(lines), "bg": "paper", "cam": [], "steps": list(steps)}
    if world3d is not None:
        sc["world3d"] = world3d
    return {"schema": "bie.scene-plan/1", "video": "v9", "scenes": [sc]}


def compiled(plan):
    # these plans test the 3D layer on the Money v2 lines without drawing the wheat and cloth those lines name, so the
    # dikhaya-bola check (tests/test_p1_shown_said.py) is left out here
    return showplan.compile_plan(json.loads(json.dumps(plan)), timeline(), width=1280, height=720, said_shown=False)


def refusal(plan):
    try:
        compiled(plan)
    except showplan.PlanProblems as exc:
        return exc.problems
    return []


RAMU = {"op": "person", "id": "ramu", "look": "ramu", "x": 260, "y": 1010, "h": 380}
HILL = {"op": "item", "id": "hill", "thing": {"model": "utilityHill", "p": {"rings": 5}}, "x": 1180, "y": 470}
FACTORY = {"model": "factory", "p": {"machines": 4, "running": 2}}


class Manifest(unittest.TestCase):
    def test_the_manifest_the_engine_and_the_vocabulary_name_the_same_models(self):
        kinds = models3d.js_kinds()
        self.assertEqual(sorted(kinds), models3d.names())
        self.assertEqual(sorted(showplan.vocab()["models3d"]), models3d.names())
        for name in models3d.names():
            entry = models3d.get(name)
            self.assertIn(entry["role"], ("place", "model"))
            self.assertEqual(len(entry["size"]), 2)
            self.assertTrue(entry["spots"], name)
            self.assertEqual(set(kinds[name]["camera"]), {"angle", "height", "dist", "tx", "ty", "tz", "fov"})

    def test_every_default_fits_its_own_manifest(self):
        for name in models3d.names():
            defaults = {k: v["default"] for k, v in models3d.get(name)["params"].items()}
            self.assertEqual(models3d.problems(name, defaults), [], name)
            self.assertEqual(models3d.check(name, defaults), [], name)

    def test_a_wrong_parameter_is_named(self):
        got = models3d.problems("factory", {"rate": 9, "light": "dusk", "belts": 2, "overtime": "yes"})
        self.assertIn("factory.rate: 9 is outside 0..3", got)
        self.assertTrue(any("'dusk' is not one of day, evening, night" in g for g in got))
        self.assertTrue(any("no parameter 'belts'" in g for g in got))
        self.assertTrue(any("factory.overtime: true or false" in g for g in got))
        self.assertIn("no 3D model 'factry'", models3d.problems("factry", {})[0])


class PureDescription(unittest.TestCase):
    """Same parameters and time -> the same scene description (read in Node, without WebGL)."""

    def test_every_model_is_the_same_twice_and_whole(self):
        for name in models3d.names():
            p = {"routes": "india-europe;china-usa", "highlight": "india"} if name == "globe" else {}
            a, b = models3d.describe(el_of(name, p), 2.4), models3d.describe(el_of(name, p), 2.4)
            self.assertNotIn("error", a, name)
            self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True), name)
            self.assertGreater(len(a["nodes"]), 8, name)
            self.assertNotRegex(json.dumps(a), r"null|NaN", name)
            for node in a["nodes"]:
                self.assertRegex(node["c"], r"^#[0-9a-f]{6}$", name)

    def test_a_process_moves_with_time_and_stands_still_without_it(self):
        moving = el_of("factory")
        self.assertNotEqual(models3d.describe(moving, 1.0)["nodes"], models3d.describe(moving, 1.4)["nodes"])
        still = el_of("factory", {"rate": 0, "smoke": 0, "running": 0, "workers": 0})
        self.assertEqual(models3d.describe(still, 1.0)["nodes"], models3d.describe(still, 1.4)["nodes"])

    def test_time_runs_from_the_moment_the_model_appears(self):
        a = models3d.describe(el_of("port", t0=0.0), 3.0)["nodes"]
        b = models3d.describe(el_of("port", t0=10.0), 13.0)["nodes"]
        self.assertEqual(a, b)

    def test_a_step_glides_a_number_and_switches_a_choice_on_its_word(self):
        el = el_of("containerCube", {"side": 1}, place=False, steps=[{"t": 2.0, "p": {"side": 2, "compare": True}, "d": 1.0}])

        def side(t):
            got = models3d.measure(el, t)["spots"]
            return got["side"]["x"] - got["cube"]["x"], "small" in got
        before, mid, after = side(1.9), side(2.5), side(3.2)
        self.assertFalse(before[1])
        self.assertTrue(mid[1])                                     # the choice changes on the word
        self.assertLess(before[0], mid[0])
        self.assertLess(mid[0], after[0])                           # the number glides
        self.assertEqual(side(3.2), side(9.0))

    def test_the_camera_moves_through_its_keys_and_turns_on_with_spin(self):
        el = el_of("globe", {"routes": "india-europe"}, place=False, cam3d=[{"t": 1.0, "d": 2.0, "angle": 90}, {"t": 4.0, "spin": 10}])
        cam = lambda t: models3d.describe(el, t)["cam"]["angle"]  # noqa: E731
        self.assertEqual(cam(0.5), 0)
        self.assertTrue(0 < cam(2.0) < 90)
        self.assertAlmostEqual(cam(3.5), 90, places=3)
        self.assertAlmostEqual(cam(6.0), 110, places=3)

    def test_the_hill_seen_from_the_top_reads_like_the_graph(self):
        """X runs to the right and Y up, and the rings (slices of the hill) lie in order from the origin: the map."""
        el = el_of("utilityHill", {"drop": 1, "flatten": 1}, place=False, w=1300, h=900,
                   cam3d=[{"t": 0.0, "d": 0.001, "angle": 0, "height": 18, "dist": 0, "ty": 0}])
        got = models3d.measure(el, 1.0)["spots"]
        self.assertGreater(got["xaxis"]["x"], got["origin"]["x"] + 300)
        self.assertAlmostEqual(got["xaxis"]["y"], got["origin"]["y"], delta=2)
        self.assertLess(got["yaxis"]["y"], got["origin"]["y"] - 300)
        self.assertAlmostEqual(got["yaxis"]["x"], got["origin"]["x"], delta=2)
        rings = [got[f"ring{k}"] for k in range(1, 6)]
        self.assertEqual(rings, sorted(rings, key=lambda r: r["x"]))
        self.assertEqual(rings, sorted(rings, key=lambda r: -r["y"]))

    def test_a_spot_behind_the_globe_says_so(self):
        got = models3d.measure(el_of("globe", {"routes": "india-europe", "highlight": "usa"}, place=False), 1.0)["spots"]
        self.assertTrue(got["india"]["front"])
        self.assertFalse(got["usa"]["front"])


class Compiler(unittest.TestCase):
    def good(self):
        return scene(
            RAMU,
            {"op": "text", "text": "मशीनें", "at": {"spot": "machine2", "dy": -70}, "size": 44},
            {"op": "mark", "kind": "circle", "at": {"of": "world3d", "spot": "output"}, "t0": {"line": "l2", "word": "कपड़ा"}},
            world3d=dict(FACTORY, steps=[{"t": {"line": "l2", "word": "कपड़ा"}, "p": {"running": 4, "output": 14}, "d": 1.2}],
                         cam3d=[{"t": {"line": "l3", "edge": "start"}, "d": 2, "angle": -15, "height": 10}]))

    def test_a_3d_place_with_steps_camera_and_spots_compiles(self):
        spec = compiled(self.good())
        els = spec["scenes"][0]["els"]
        world = els[0]
        self.assertEqual((world["kind"], world["id"], world["place"], world["z"], world["w"], world["h"]), ("model3d", "world3d", True, 0, 1920, 1080))
        self.assertIsInstance(world["steps"][0]["t"], float)          # the cue became seconds
        self.assertIsInstance(world["cam3d"][0]["t"], float)
        text = next(e for e in els if e.get("text") == "मशीनें")
        spot = models3d.measure(world, text["t0"])["spots"]["machine2"]
        self.assertEqual((text["x"], text["y"], text["on"]), (round(spot["x"], 1), round(spot["y"] - 70, 1), "world3d"))
        self.assertTrue(0 < text["x"] < 1920 and 0 < text["y"] < 1080)
        self.assertTrue(render.needs_3d(spec))

    def test_a_3d_model_is_a_thing_with_its_manifest_size(self):
        spec = compiled(scene(RAMU, HILL, {"op": "text", "text": "ढलान", "at": {"of": "hill", "spot": "peak", "dy": -40}, "size": 40, "style": "plain"}))
        hill = next(e for e in spec["scenes"][0]["els"] if e.get("kind") == "model3d")
        self.assertEqual((hill["id"], hill["place"], hill["w"], hill["h"], hill["enter"]), ("hill", False, 1300, 900, "fade"))

    def test_bad_3d_steps_are_named(self):
        cases = [
            (scene(RAMU, world3d={"model": "factry"}), "no 3D model 'factry'"),
            (scene(RAMU, world3d={"model": "factory", "p": {"rate": 7}}), "factory.rate: 7 is outside 0..3"),
            (scene(RAMU, world3d={"model": "factory", "p": {"speed": 1}}), "factory: no parameter 'speed'"),
            (scene(RAMU, world3d=dict(FACTORY, steps=[{"t": {"line": "l2", "edge": "start"}, "p": {"light": "noon"}}])), "'noon' is not one of day, evening, night"),
            (scene(RAMU, world3d=dict(FACTORY, steps=[{"t": 2.0, "p": {"rate": 2}, "ease": 1}])), "no field 'ease'"),
            (scene(RAMU, world3d=dict(FACTORY, cam3d=[{"t": 1.0, "zoom": 2}])), "cam3d key 1: no field 'zoom'"),
            (scene(RAMU, world3d=dict(FACTORY, cam3d=[{"t": 1.0, "fov": 170}])), "fov 170 is outside 10..100"),
            (scene(RAMU, world3d=dict(FACTORY, x=300)), "always fills the stage"),
            (scene(RAMU, world3d=dict(FACTORY, steps=[{"t": {"line": "l2", "word": "चाँद"}, "p": {"rate": 2}}])), "चाँद"),
            (scene(RAMU, {"op": "text", "text": "चिमनी", "at": {"spot": "chimny"}}, world3d=FACTORY), "has no spot 'chimny'"),
            (scene(RAMU, {"op": "text", "text": "चिमनी", "at": {"of": "port", "spot": "ship"}}, world3d=FACTORY), "at.of: no 3D model 'port'"),
            (scene(RAMU, {"op": "text", "text": "चिमनी", "at": {"spot": "chimney", "left": 5}}, world3d=FACTORY), "at has no field 'left'"),
            (scene(RAMU, {"op": "text", "text": "चिमनी", "at": {"spot": "chimney"}}), "at.of: no 3D model"),
            (scene(RAMU, {"op": "item", "thing": {"group": [{"model": "globe", "p": {}}]}, "x": 900, "y": 500}), "stands on its own"),
            (scene(RAMU, {"op": "item", "thing": {"model": "globe", "p": {"routes": "india-mars"}}, "x": 1200, "y": 480}), "no region 'mars'"),
            (scene(RAMU, {"op": "item", "id": "g", "thing": {"model": "globe", "p": {"routes": "india-europe", "highlight": "usa"}}, "x": 1200, "y": 480},
                   {"op": "text", "text": "अमेरिका", "at": {"of": "g", "spot": "usa"}}), "hidden from its camera"),
            (scene(RAMU, {"op": "item", "thing": {"model": "globe", "p": {}, "draw": "sack"}, "x": 1200, "y": 480}), "has only model and p"),
            (scene(RAMU, HILL, dict(HILL, x=400)), "two 3D models named 'hill'"),
        ]
        for plan, want in cases:
            got = refusal(plan)
            self.assertTrue(any(want in g for g in got), f"{want!r} not named in {got}")

    def test_a_3d_place_is_a_backdrop_and_a_3d_model_is_the_thing_shown(self):
        words = {"op": "text", "text": "उत्पादन", "x": 960, "y": 200, "size": 60, "style": "title"}
        bare = refusal(scene(words, world3d=FACTORY))
        self.assertTrue(any("only text on screen" in g for g in bare), bare)
        shown = refusal(scene(dict(words, x=420, y=140), HILL))
        self.assertFalse(any("only text on screen" in g for g in shown), shown)

    def test_the_recorder_writes_the_same_language(self):
        T = timeline()
        C, start, _ = showplan.cues(T)
        r = showplan.Recorder("A", ["l1", "l2", "l3"])
        r.world3d("port", p={"ships": 1, "arrive": 0}, steps=[{"t": C("l2", "कपड़ा"), "p": {"arrive": 1}, "d": 2.0}],
                  cam3d=[{"t": start("l3"), "angle": 40}])
        r.person("ramu", "ramu", 260, y=1010, h=380)
        r.text("जहाज़", at={"spot": "ship", "dy": -60, "when": start("l3")}, t0=start("l3"), size=44)
        r.model("cube", "containerCube", x=1500, y=330, w=600, h=540, p={"side": 1}, t0=start("l3"),
                steps=[{"t": start("l3", 0.5), "p": {"side": 2, "units": 8}}])
        plan = showplan.plan_of([r])
        self.assertEqual(plan["scenes"][0]["world3d"]["model"], "port")
        self.assertEqual(plan["scenes"][0]["world3d"]["steps"][0]["t"], {"line": "l2", "word": "कपड़ा"})
        spec = showplan.compile_plan(plan, T, width=1280, height=720, said_shown=False)
        kinds = [(e["id"], e["place"]) for e in spec["scenes"][0]["els"] if e.get("kind") == "model3d"]
        self.assertEqual(kinds, [("world3d", True), ("cube", False)])


class BoxRule(unittest.TestCase):
    def test_words_stay_off_a_3d_model_unless_they_label_its_spot(self):
        on_it = refusal(scene(RAMU, HILL, {"op": "text", "text": "उपयोगिता", "x": 1180, "y": 560, "size": 46}))
        self.assertTrue(any("sits on the 3D model 'hill' (utilityHill)" in g for g in on_it), on_it)
        label = refusal(scene(RAMU, HILL, {"op": "text", "text": "ढलान", "at": {"of": "hill", "spot": "hill"}, "size": 40, "style": "plain"}))
        self.assertFalse(any("box rule" in g for g in label), label)

    def test_a_3d_worlds_parts_are_reserved_zones_that_follow_its_camera(self):
        world = dict(el_of("factory", FACTORY["p"]), id="world3d", z=0)
        zone = next(z for z in models3d.measure(world, 1.0)["zones"] if z["name"] == "machines")
        cx, cy = (zone["box"][0] + zone["box"][2]) / 2, (zone["box"][1] + zone["box"][3]) / 2
        free = refusal(scene(RAMU, {"op": "text", "text": "मशीनें", "x": round(cx), "y": round(cy), "size": 44}, world3d=FACTORY))
        self.assertTrue(any("machines (3D world 'world3d')" in g and "reserved" in g for g in free), free)
        label = refusal(scene(RAMU, {"op": "text", "text": "मशीनें", "at": {"spot": "machine2", "dy": -70}, "size": 44}, world3d=FACTORY))
        self.assertFalse(any("box rule" in g for g in label), label)
        turned = dict(world, cam3d=[{"t": 0.0, "d": 0.001, "angle": 60}])
        self.assertNotEqual(next(z for z in models3d.measure(turned, 1.0)["zones"] if z["name"] == "machines")["box"], zone["box"])

    def test_a_person_may_stand_in_front_of_a_3d_place(self):
        self.assertEqual(refusal(scene(RAMU, {"op": "person", "id": "mohan", "look": "mohan", "x": 1500, "y": 1010, "h": 380},
                                       world3d=FACTORY)), [])


class PlainSpecsNeverNeedThree(unittest.TestCase):
    def imports_of(self, entry: Path, seen=None) -> set:
        """Every module the entry pulls in (static imports, followed through the engine's own files)."""
        seen = set() if seen is None else seen
        if entry in seen or not entry.exists():
            return set()
        seen.add(entry)
        out = set()
        for spec in re.findall(r"""(?:import|export)\s[^;]*?from\s+["']([^"']+)["']|import\s+["']([^"']+)["']""", entry.read_text(encoding="utf-8")):
            name = spec[0] or spec[1]
            out.add(name)
            if name.startswith("."):
                out |= self.imports_of((entry.parent / name).resolve(), seen)
        return out

    def test_the_plain_engine_bundle_has_no_three_and_no_3d_layer(self):
        plain = self.imports_of(ENGINE / "engine.mjs")
        self.assertFalse([m for m in plain if m == "three" or m.startswith("three/") or "layer3d" in m or "/three/" in m], plain)
        with3d = self.imports_of(ENGINE / "engine3d.mjs")
        self.assertIn("three", with3d)
        self.assertIn("./engine.mjs", with3d)
        # the measure the compiler runs in Node is pure too: no three.js, no browser
        self.assertNotIn("three", self.imports_of(ENGINE / "three" / "scene3d.mjs"))

    def test_only_a_spec_with_a_3d_model_asks_for_the_3d_page(self):
        gold = gold_spec(width=1280, height=720, assets={})
        self.assertFalse(render.needs_3d(gold))
        self.assertEqual(render._page(False, True, render.needs_3d(gold)), ["--page", "engine.html"])
        spec = compiled(scene(RAMU, world3d=FACTORY))
        self.assertTrue(render.needs_3d(spec))
        self.assertEqual(render._page(False, True, render.needs_3d(spec)), ["--page", "engine3d.html"])

    def test_the_plain_frame_is_the_same_string_as_before_the_layers(self):
        """engine.mjs draws a 2D frame as one layer, the very string renderFrame gives (checked in the file's own code)."""
        src = (ENGINE / "engine.mjs").read_text(encoding="utf-8")
        self.assertIn("el.innerHTML = L.svgs[0];", src)
        self.assertIn('if (kind === "model3d") { parts.push({ model: el, alpha, popS }); continue; }', src)
        self.assertIn("BIE_3D_MISSING", src)


if __name__ == "__main__":
    unittest.main()
