"""Task 046 one-shot test (26 October 2026): the Route 2 prompt writer, the plate and parallax specs, the render workflow.
Standard library only (the core toolbox lane); the Blender recipe and the depth adapter are tested in tests/toolbox/."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.video import compose, still_prompt  # noqa: E402

SHOT = {"shot_id": "b37.2", "scene_id": "s4", "beat_id": "b37", "part_id": "c07.1", "purpose": "compare",
        "sentence": "खास तुलना: Simple squamous में पतली exchange boundary;", "member": "simple squamous", "start": 447.7,
        "seconds": 3.93, "frames": [8216, 118], "fps": 30, "capability": "split_compare", "camera": "zoom_in",
        "labels": ["simple squamous", "boundary"], "focus": "simple squamous",
        "caption": {"text": "खास तुलना: Simple squamous में पतली exchange boundary;", "terms": ["simple", "squamous", "exchange", "boundary"]}}


class StillPrompt(unittest.TestCase):
    def test_prompts_share_the_route1_layout_and_forbid_text(self):
        out = still_prompt.shot_prompts(SHOT)
        self.assertEqual((out["schema"], out["shot_id"], len(out["prompts"])), ("bie.image-prompts/1", "b37.2", 4))
        presets = json.loads((ROOT / "bie/toolbox/blender/epithelium_studio.json").read_text(encoding="utf-8"))
        self.assertEqual(out["layout"]["preset_version"], presets["version"])
        self.assertAlmostEqual(out["layout"]["elevation_deg"], 33.4, delta=0.2)       # the Blender camera's start angle
        ids = [p["id"] for p in out["prompts"]]
        self.assertEqual(len(set(ids)), 4)
        for p in out["prompts"]:
            self.assertTrue(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", p["id"]), p["id"])     # tools/vm_image.py's id rule
            self.assertTrue(40 <= len(p["prompt"]) <= 4000)
            self.assertIn(still_prompt.NO_TEXT, p["prompt"])
            self.assertIn("exactly one oval nucleus", p["prompt"])
            self.assertIn("no floating spheres", p["prompt"])                      # BIE's code draws the moving particles
            self.assertEqual(still_prompt.problems(p["prompt"], SHOT), [])
        self.assertEqual(out["labels_by_code"], ["simple squamous", "boundary"])

    def test_a_prompt_that_asks_for_text_is_refused(self):
        self.assertIn("the no-text clause is missing", still_prompt.problems("A sheet of flat cells " * 4))
        bad = still_prompt.NO_TEXT + " Add a caption that reads simple squamous over the centre."
        self.assertTrue(any("label" in p for p in still_prompt.problems(bad, SHOT)))
        self.assertTrue(any("quoted" in p for p in still_prompt.problems(still_prompt.NO_TEXT + ' Write "cell".', SHOT)))
        with self.assertRaises(ValueError):
            still_prompt.shot_prompts(dict(SHOT, member="transitional"))
        with self.assertRaises(ValueError):
            still_prompt.shot_prompts(SHOT, count=5)


class PlateSpecs(unittest.TestCase):
    def test_route1_plate_carries_anchors_labels_and_the_caption(self):
        anchors = {"simple squamous": [[0.47, 0.41, 8.3]] * 135, "boundary": [[0.68, 0.2, 10.1]] * 135}
        spec = compose.plate_spec(SHOT, pattern="assets/plate/f%04d.png", count=135, anchors=anchors)
        scene = spec["scenes"][0]
        self.assertEqual((spec["width"], spec["height"], spec["fps"], scene["duration"]), (1920, 1080, 30, 135))
        plate, caption = scene["layers"]
        self.assertEqual((plate["block"], plate["data"]["pattern"], plate["data"]["count"]), ("plate", "assets/plate/f%04d.png", 135))
        self.assertEqual([l["anchor"] for l in plate["data"]["labels"]], ["simple squamous", "boundary"])
        self.assertEqual((caption["block"], caption["at"], caption["until"]), ("kinetic_caption", 0, 135))
        self.assertEqual(caption["data"]["text"], SHOT["caption"]["text"])
        self.assertEqual(plate["data"]["accent"], caption["data"]["accent"])           # one accent per member (VG-09)
        missing = compose.plate_spec(SHOT, pattern="p", count=10, anchors={"boundary": [[0.5, 0.5, 1.0]]})
        self.assertEqual(missing["labels_missing"], ["simple squamous"])                # never guessed

    def test_route2_parallax_spec_flows_for_an_exchange_sentence(self):
        layout = {"anchors_uv": {"simple squamous": [0.5, 0.55], "boundary": [0.66, 0.19]}, "focus_uv": [0.5, 0.55]}
        spec = compose.parallax_spec(SHOT, still="assets/still.png", depth="assets/depth.png", layout=layout, count=135)
        plate = spec["scenes"][0]["layers"][0]
        self.assertEqual(plate["block"], "parallax_plate")
        self.assertEqual((plate["data"]["src"], plate["data"]["depth"], plate["data"]["focus_uv"]), ("assets/still.png", "assets/depth.png", [0.5, 0.55]))
        self.assertGreater(plate["data"]["particles"], 0)                              # "exchange" → particles cross (B-04)
        quiet = compose.parallax_spec(dict(SHOT, sentence="Simple squamous है: flat cells की boundaries irregular हैं।"),
                                      still="s", depth="d", layout=layout, count=10)
        self.assertEqual(quiet["scenes"][0]["layers"][0]["data"]["particles"], 0)

    def test_the_blocks_are_registered_and_bundled(self):
        tsx = (ROOT / "bie/brain/video/blocks/toolbox/plate.tsx").read_text(encoding="utf-8")
        for name in ("plate", "parallax_plate"):
            self.assertIn(f'registerBlock("{name}"', tsx)
        self.assertIn('import "./plate";', (ROOT / "bie/brain/video/blocks/toolbox/index.ts").read_text(encoding="utf-8"))


class OneShotTool(unittest.TestCase):
    def test_prompts_command_writes_the_vm_prompt_file(self):
        import importlib.util
        import tempfile
        spec = importlib.util.spec_from_file_location("oneshot", ROOT / "tools" / "oneshot.py")
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        with tempfile.TemporaryDirectory() as folder:
            shots = Path(folder) / "v3.json"
            shots.write_text(json.dumps({"shots": [SHOT]}, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(tool.main(["prompts", "--shots", str(shots), "--shot", "b37.2", "--out", str(Path(folder) / "p.json"), "--count", "2"]), 0)
            data = json.loads((Path(folder) / "p.json").read_text(encoding="utf-8"))
            self.assertEqual((data["schema"], len(data["prompts"])), ("bie.image-prompts/1", 2))
            with self.assertRaises(SystemExit):
                tool.shot_from(shots, "b99.9")
        self.assertEqual(tool.LOOK_FRAMES, (30, 75, 120))                                # after the fade-in, mid push, near the end


class RenderWorkflow(unittest.TestCase):
    def test_route1_render_is_gated_chunked_and_publishes_only_our_renders(self):
        flow = (ROOT / ".github/workflows/task046-oneshot.yml").read_text(encoding="utf-8")
        self.assertIn("grep -qF '[render-oneshot]'", flow)                              # not on every push
        self.assertIn("bie/toolbox/blender/epithelium_studio.py --params params.json", flow)
        self.assertIn('dest="runs/t046-oneshot/route1-plate"', flow)
        self.assertIn("contents: write  # only to push the plate", flow)
        self.assertNotIn("secrets.", flow)                                             # no key, no AI call
        self.assertNotIn("benchmark.mp4", flow)                                        # the benchmark never enters the repo or CI


if __name__ == "__main__":
    unittest.main()
