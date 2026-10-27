"""Tests for the economy kit's plan compiler (layout, cue timing and the first-try checks)."""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
sys.path.insert(0, os.path.join(HERE, "..", "demos"))
import econ_canvas as ec  # noqa: E402
import make_demos  # noqa: E402

BASE = {
    "id": "t", "grid": [12, 8],
    "beats": [{"beat_id": "b1", "say": "दुकान पर दाम पचास रुपये है।"}, {"beat_id": "b2", "say": "फिर दाम पैंसठ हो जाता है, यही CPI।"}],
    "nodes": [
        {"id": "shop", "kind": "icon", "icon": "tw:1f3ea", "cell": [0, 2, 3, 3], "cue": ["b1", "दुकान"]},
        {"id": "p", "kind": "value", "cell": [4, 3, 3, 1], "steps": [{"text": "₹50", "cue": ["b1", "पचास"]},
                                                                  {"text": "₹65", "dir": "up", "cue": ["b2", "पैंसठ"]}]},
        {"id": "a", "kind": "arrow", "from": "shop", "to": "p", "cue": ["b1", "दाम"]},
    ],
}


class CompileTests(unittest.TestCase):
    def test_demos_compile_without_problems(self):
        for plan in (make_demos.D1, make_demos.D2, make_demos.D3):
            scene, report = ec.compile_plan(copy.deepcopy(plan))
            self.assertEqual(report["problems"], [], plan["id"])
            self.assertGreater(scene["duration"], 300)
            self.assertLessEqual(report["longest_still_s"], ec.TARGET_STILL_S)

    def test_cue_on_last_word_before_danda_is_found(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "t", "kind": "text", "text": "CPI", "cell": [8, 0, 3, 1], "cue": ["b2", "CPI"]})
        scene, _ = ec.compile_plan(plan)
        el = next(e for e in scene["layers"][0]["data"]["elements"] if e["id"] == "t")
        start, length = None, None
        # the cue must land near the end of beat b2, not at its start
        self.assertGreater(el["at"], next(e for e in scene["layers"][0]["data"]["elements"] if e["id"] == "p")["steps"][1]["at"])

    def test_unknown_cue_word_is_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"][0]["cue"] = ["b1", "बाज़ार"]
        with self.assertRaises(ec.PlanError):
            ec.compile_plan(plan)

    def test_shared_cells_on_screen_together_are_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "x", "kind": "icon", "icon": "tw:1f4b0", "cell": [1, 3, 2, 2], "cue": ["b2", "दाम"]})
        with self.assertRaises(ec.PlanError):
            ec.compile_plan(plan)

    def test_shared_cells_one_after_another_are_allowed(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"][0]["until_cue"] = ["b2", "", 0.0]
        plan["nodes"].append({"id": "x", "kind": "icon", "icon": "tw:1f4b0", "cell": [1, 3, 2, 2], "cue": ["b2", "दाम"]})
        plan["nodes"] = [n for n in plan["nodes"] if n["id"] != "a"]
        ec.compile_plan(plan)

    def test_text_that_cannot_fit_is_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "t", "kind": "text", "style": "box", "text": "बहुत लंबा वाक्य " * 30, "cell": [8, 0, 2, 1],
                              "cue": ["b2", "दाम"]})
        with self.assertRaises(ec.PlanError):
            ec.compile_plan(plan)

    def test_tag_wider_than_cell_is_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"].append({"id": "t", "kind": "text", "style": "tag", "text": "Demand-pull inflation explained", "cell": [8, 0, 2, 1],
                              "cue": ["b2", "दाम"]})
        with self.assertRaises(ec.PlanError):
            ec.compile_plan(plan)

    def test_missing_reference_is_refused(self):
        plan = copy.deepcopy(BASE)
        plan["nodes"][2]["to"] = "nowhere"
        with self.assertRaises(ec.PlanError):
            ec.compile_plan(plan)

    def test_long_still_picture_is_reported(self):
        plan = copy.deepcopy(BASE)
        plan["beats"].append({"beat_id": "b3", "say": "यह एक बहुत लंबा वाक्य है जिसमें कुछ नया नहीं दिखता " * 6})
        _, report = ec.compile_plan(plan)
        self.assertTrue(any("stays the same" in p for p in report["problems"]))

    def test_medium_still_picture_is_an_advisory_only(self):
        plan = copy.deepcopy(BASE)
        plan["beats"].append({"beat_id": "b3", "say": "यह एक लंबा वाक्य है जिसमें कुछ नया नहीं दिखता, बस बात चलती रहती है।"})
        _, report = ec.compile_plan(plan)
        self.assertEqual(report["problems"], [])
        self.assertTrue(any("stays the same" in a for a in report["advisories"]))

    def test_elements_stay_inside_safe_area(self):
        scene, _ = ec.compile_plan(copy.deepcopy(make_demos.D1))
        for e in scene["layers"][0]["data"]["elements"]:
            if "x" in e:
                self.assertGreaterEqual(e["x"], ec.SAFE["left"] - 1e-9, e["id"])
                self.assertLessEqual(e["x"] + e["w"], 1 - ec.SAFE["right"] + 1e-9, e["id"])
                self.assertLessEqual(e["y"] + e["h"], 1 - ec.SAFE["bottom"] + 1e-9, e["id"])

    def test_subtitles_follow_beats(self):
        scene, _ = ec.compile_plan(copy.deepcopy(BASE))
        subs = scene["layers"][0]["data"]["subtitles"]
        self.assertEqual(len(subs), 2)
        self.assertLess(subs[0]["until"], subs[1]["at"] + 1)


if __name__ == "__main__":
    unittest.main()


class WorldPlanTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(HERE, "..", "tools"))
        import world_plan  # noqa: E402
        self.wp = world_plan

    def test_world_demo_compiles(self):
        scene, report = self.wp.compile_world(copy.deepcopy(make_demos.D1C))
        self.assertEqual(report["problems"], [])
        data = scene["layers"][0]["data"]
        self.assertEqual(scene["layers"][0]["block"], "world_scene")
        self.assertTrue(all("at" in k for k in data["camera"]))
        crowd = next(e for e in data["elements"] if e["kind"] == "crowd")
        self.assertEqual([s["n"] for s in crowd["steps"]], [2, 12, 3])

    def test_unknown_kind_is_refused(self):
        plan = copy.deepcopy(make_demos.D1C)
        plan["elements"].append({"id": "x", "kind": "dragon", "cue": ["b1", "दुकान"]})
        with self.assertRaises(ec.PlanError):
            self.wp.compile_world(plan)

    def test_camera_out_of_order_is_refused(self):
        plan = copy.deepcopy(make_demos.D1C)
        plan["camera"][1], plan["camera"][2] = plan["camera"][2], plan["camera"][1]
        with self.assertRaises(ec.PlanError):
            self.wp.compile_world(plan)

    def test_touches_plan_gets_a_camera(self):
        scene, report = ec.compile_plan(copy.deepcopy(make_demos.D1B))
        data = scene["layers"][0]["data"]
        self.assertTrue(data["touches"])
        self.assertEqual(data["cam"][-1]["box"], {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0})
        flows = [e for e in data["elements"] if e.get("flow")]
        self.assertEqual(len(flows), 2)
