"""Task 046 Part B, the parts that need the toolbox extras: the frame checks on pixels (Pillow), the eSpeak NG placeholder
voice (a real waveform drives the timing) and the Blender sheets of the family members (route C). Runs in the toolbox
wrappers lane, which installs every extra and fails on any skip."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bie.brain.video import frame_checks, timing, voice  # noqa: E402

ACCENT = "#7cf59a"
OTHER = "#ff3b3b"


def frame(bg=(8, 20, 30), *, caption=False, accent=None, label=False, shift=0) -> bytes:
    """A synthetic 640×360 still: a caption band on top, a label box on the right, an accent patch that can move."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (640, 360), bg)
    draw = ImageDraw.Draw(im)
    draw.rectangle((40, 220, 600, 340), fill=(120, 60, 70))                       # the world: something lit, so the still is not blank
    draw.ellipse((200 + shift, 120, 320 + shift, 240), fill=(170, 110, 120))
    if caption:
        draw.rectangle((100, 14, 540, 40), fill=(255, 255, 255))
    if label:
        draw.rectangle((440, 120, 560, 150), fill=(250, 250, 250))
    if accent:
        r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
        draw.rectangle((300 + shift, 170, 360 + shift, 230), fill=(r, g, b))
    out = io.BytesIO()
    im.save(out, format="PNG")
    return out.getvalue()


class FrameRules(unittest.TestCase):
    def test_a_dark_captioned_moving_clip_passes_every_rule(self):
        pngs = [frame(caption=True, accent=ACCENT, label=True, shift=i * 30) for i in range(6)]
        found = frame_checks.demo_rules(pngs, ("B-11", "B-08", "B-10", "B-03", "VG-01"), accent=ACCENT)
        self.assertEqual(found["failed"], {})
        self.assertEqual(found["checked"], ["B-11", "B-08", "B-10", "B-03", "VG-01"])

    def test_each_rule_fails_on_its_own_fault(self):
        moving = [frame(caption=True, accent=ACCENT, label=True, shift=i * 30) for i in range(6)]
        bright = [frame((230, 230, 230), caption=True, accent=ACCENT, label=True, shift=i * 30) for i in range(6)]
        self.assertIn("B-11", frame_checks.demo_rules(bright, ("B-11",))["failed"])
        no_caption = [frame(accent=ACCENT, label=True, shift=i * 30) for i in range(6)]
        self.assertIn("B-08", frame_checks.demo_rules(no_caption, ("B-08",))["failed"])
        self.assertIn("B-10", frame_checks.demo_rules(moving, ("B-10",), accent=OTHER)["failed"])
        self.assertIn("B-10", frame_checks.demo_rules(moving, ("B-10",))["failed"])              # no accent given: the clip cannot claim it
        bare = [frame(shift=i * 30) for i in range(6)]
        self.assertIn("B-03", frame_checks.demo_rules(bare, ("B-03",))["failed"])
        frozen = [frame(caption=True, accent=ACCENT, label=True)] * 6
        self.assertIn("VG-01", frame_checks.demo_rules(frozen, ("VG-01",))["failed"])
        self.assertIn("ZZ-99", frame_checks.demo_rules(moving, ("ZZ-99",))["failed"])

    def test_check_frames_reports_per_shot_with_the_frame_number(self):
        rows = [{"shot_id": "b1.1", "from": 0, "to": 30, "capability": "cell_sheet_3d", "labels": ["nucleus"]},
                {"shot_id": "b1.2", "from": 30, "to": 60, "capability": "cell_sheet_3d", "labels": []},
                {"shot_id": "b1.3", "from": 60, "to": 90, "capability": "board_build", "labels": []}]
        # b1.1 clean; b1.2 dark but without its caption and with the wrong accent; b1.3 a bright frame (a board shot: no accent check)
        frames = [(5, frame(caption=True, accent=ACCENT, label=True)), (35, frame(accent=OTHER, shift=40)),
                  (65, frame((220, 220, 220), caption=True, accent=ACCENT, shift=80))]
        found = frame_checks.check_frames(frames, rows, accents={"b1.1": ACCENT, "b1.2": ACCENT, "b1.3": ACCENT})
        self.assertEqual((found["frames_checked"], found["shots_with_stills"]), (3, 3))
        f = found["findings"]
        self.assertEqual([(x["shot"], x["frame"]) for x in f["B-08"]], [("b1.2", 35)])
        self.assertEqual([(x["shot"], x["frame"]) for x in f["B-11"]], [("b1.3", 65)])
        self.assertEqual(f["VG-09"], f["B-11"])
        self.assertEqual([(x["shot"], x["frame"]) for x in f["B-10"]], [("b1.2", 35)])          # the board shot is not judged for its accent
        self.assertEqual(f["B-03"], [])
        self.assertEqual(f["VG-01"], [])
        table = frame_checks.rule_table_with_frames([{"rule": "B-08", "status": "pass", "note": ""}, {"rule": "B-04", "status": "pass", "note": ""}], found)
        self.assertEqual((table[0]["status"], table[0]["frame"]), ("fail", 35))
        self.assertEqual((table[1]["status"], table[1]["frame_status"]), ("pass", "not read"))

    def test_a_frozen_shot_is_caught(self):
        rows = [{"shot_id": "s", "from": 0, "to": 90, "capability": "cell_sheet_3d", "labels": []}]
        still = frame(caption=True, accent=ACCENT)
        found = frame_checks.check_frames([(0, still), (40, still)], rows)
        self.assertEqual([(x["shot"], x["frame"]) for x in found["findings"]["VG-01"]], [("s", 40)])

    def test_contact_sheet_is_written(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sheet.png"
            frame_checks.contact_sheet([(0, frame()), (30, frame(shift=20)), (60, frame(shift=40))], out, "three stills", cols=3)
            self.assertEqual(Image.open(out).size, (480 * 3, 270 + 50))


class PlaceholderVoice(unittest.TestCase):
    def test_espeak_narrates_every_beat_and_mixes_one_track(self):
        self.assertTrue(voice.available(), "eSpeak NG must be installed in the wrappers lane")
        beats = [{"beat_id": "b1", "say": "Squamous यानी चपटी cells, floor की tiles की तरह।"},
                 {"beat_id": "b2", "say": "Cuboidal cells dice जैसी होती हैं।"}]
        with tempfile.TemporaryDirectory() as tmp:
            spoken = voice.narrate(beats, tmp)
            self.assertEqual(sorted(spoken), ["b1", "b2"])
            for info in spoken.values():
                self.assertGreater(info["duration"], 0.8)
                self.assertTrue(Path(info["file"]).exists())
                self.assertEqual((info["provider"], info["words"]), (voice.PROVIDER, []))
            scenes = [{"scene_id": "s1", "beat_ids": ["b1", "b2"]}]
            tl = timing.build(beats, scenes, voice=spoken)
            self.assertEqual(tl["s1"]["beats"]["b1"][1], round(spoken["b1"]["duration"] * timing.FPS))
            mixed = voice.mix(spoken, scenes, tl, Path(tmp) / "narration.wav")
            self.assertEqual(mixed["beats"], 2)
            self.assertAlmostEqual(mixed["seconds"], tl["s1"]["duration"] / timing.FPS, delta=0.05)
            self.assertAlmostEqual(voice.seconds_of(Path(tmp) / "narration.wav"), mixed["seconds"], places=2)


class BlenderMembers(unittest.TestCase):
    def test_the_family_members_build_with_their_hairs_and_layers(self):
        from bie.toolbox.adapters import blender, meshes
        with tempfile.TemporaryDirectory() as tmp:
            cil = blender.cell_sheet(Path(tmp) / "c.glb", kind="ciliated", rows=2, cols=2)
            self.assertEqual((cil["cells"], cil["hairs"], cil["layers"]), (4, 28, 1))
            self.assertGreaterEqual(meshes.glb_info((Path(tmp) / "c.glb").read_bytes())["meshes"], 4 + 4 + 28 + 2)
            strat = blender.cell_sheet(Path(tmp) / "s.glb", kind="stratified_squamous", rows=1, cols=2)
            self.assertEqual((strat["cells"], strat["layers"]), (10, 5))
            gland = blender.cell_sheet(Path(tmp) / "g.glb", kind="glandular", rows=1, cols=2)
            self.assertGreaterEqual(meshes.glb_info((Path(tmp) / "g.glb").read_bytes())["meshes"], 2 + 2 + 3)


if __name__ == "__main__":
    unittest.main()
