"""Task 046a: one test per toolbox wrapper, with the real libraries (run in the toolbox lane, which installs every
toolbox extra; the lane fails on any skip, so a missing library is never hidden). Offline: network sources use fakes."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.toolbox import registry  # noqa: E402
from bie.toolbox.adapters import base  # noqa: E402

PDB = """HEADER    PLANT PROTEIN                           30-APR-81   1CRN
HELIX    1  H1 ILE A    7  PRO A   19  1                                  13
SHEET    1  S1 2 THR A   1  CYS A   4  0
ATOM      1  N   THR A   1      17.047  14.099   3.625  1.00 13.79           N
ATOM      2  CA  THR A   1      16.967  12.784   4.338  1.00 10.80           C
ATOM      3  C   THR A   1      15.685  12.755   5.133  1.00  9.19           C
ATOM      4  N   THR A   2      15.115  11.555   5.265  1.00  7.81           N
ATOM      5  CA  THR A   2      13.856  11.469   6.066  1.00  8.31           C
ATOM      6  C   THR A   2      14.164  10.785   7.379  1.00  5.80           C
ATOM      7  N   CYS A   3      13.488  11.241   8.417  1.00  6.07           N
ATOM      8  CA  CYS A   3      13.660  10.707   9.787  1.00  5.24           C
END
"""
CUBE = b"""v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nv 0 0 1\nv 1 0 1\nv 1 1 1\nv 0 1 1
f 1 2 3\nf 1 3 4\nf 5 6 7\nf 5 7 8\nf 1 2 6\nf 1 6 5\nf 2 3 7\nf 2 7 6\nf 3 4 8\nf 3 8 7\nf 4 1 5\nf 4 5 8\n"""


class Versions(unittest.TestCase):
    def test_every_python_tool_is_installed_at_the_registry_version(self):
        box = registry.load()
        for tid in base.PYTHON_TOOLS:
            self.assertEqual(base.installed_version(tid), box.tool(tid).version, tid)


class Physics(unittest.TestCase):
    def test_falling_body_drag_lands_later_and_no_drag_matches_the_formula(self):
        from bie.toolbox.adapters import physics
        d = physics.falling_body(height=20.0, drag=0.12, seconds=3.6)
        self.assertAlmostEqual(d["t_ground_free"], (2 * 20 / 9.81) ** 0.5, places=3)
        self.assertGreater(d["t_ground_drag"], d["t_ground_free"])
        self.assertEqual(len(d["t"]), 109)
        self.assertEqual(d["y_drag"][-1], 0.0)

    def test_standing_wave_nodes_stay_still(self):
        from bie.toolbox.adapters import physics
        d = physics.wave(seconds=1.0)
        node = min(range(len(d["x"])), key=lambda i: abs(d["x"][i] - d["nodes"][1]))
        self.assertTrue(all(abs(frame[node]) < 0.05 for frame in d["sum"]))


class Maths(unittest.TestCase):
    def test_equation_steps_are_checked_and_a_wrong_step_is_caught(self):
        from bie.toolbox.adapters import maths
        good = maths.equation_steps(["2x + 3 = 11", "2x = 8", "x = 4"])
        self.assertTrue(good["all_checked"])
        self.assertEqual(good["steps"][-1]["latex"], "x = 4")
        written = maths.equation_steps(["3(x - 2) + 4 = 2x + 7", "3x - 6 + 4 = 2x + 7", "3x - 2 = 2x + 7"])
        self.assertEqual([s["latex"] for s in written["steps"]],                  # each step as written, not simplified
                         [r"3 \left(x - 2\right) + 4 = 2 x + 7", "3 x - 6 + 4 = 2 x + 7", "3 x - 2 = 2 x + 7"])
        bad = maths.equation_steps(["2x + 3 = 11", "2x = 14"])
        self.assertFalse(bad["all_checked"])
        with self.assertRaises(maths.StepError):
            maths.equation_steps(["2x + 3"])

    def test_function_samples_and_regression(self):
        from bie.toolbox.adapters import maths
        f = maths.function_samples("x^2/4 - 2", x_min=-6, x_max=6, points=121)
        self.assertEqual((f["y_min"], f["y_max"]), (-2.0, 7.0))
        self.assertIn("frac{x}{2}", f["derivative_latex"])
        r = maths.regression([1, 2, 3, 4], [2, 4, 6, 8.1])
        self.assertAlmostEqual(r["slope"], 2.03, places=2)
        self.assertGreater(r["r_squared"], 0.99)


class Graphs(unittest.TestCase):
    def test_layout_is_repeatable_and_bfs_goes_level_by_level(self):
        from bie.toolbox.adapters import graphs
        edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "E")]
        a, b = graphs.layout_and_bfs(edges, "A"), graphs.layout_and_bfs(edges, "A")
        self.assertEqual(a["nodes"], b["nodes"])
        self.assertEqual(a["order"][0], "A")
        self.assertEqual(set(a["order"][1:3]), {"B", "C"})
        self.assertTrue(all(0 <= n["x"] <= 1 and 0 <= n["y"] <= 1 for n in a["nodes"]))


class Biology(unittest.TestCase):
    def test_ecg_has_beats_at_the_heart_rate(self):
        from bie.toolbox.adapters import biology
        d = biology.ecg(duration=4.0, heart_rate=72, sampling_rate=250)
        self.assertEqual(len(d["mv"]), 1000)
        gaps = [b - a for a, b in zip(d["r_peaks"], d["r_peaks"][1:])]
        self.assertTrue(all(180 < g < 240 for g in gaps), gaps)            # 72 per minute = 208 samples at 250 Hz

    def test_pdb_structure(self):
        from bie.toolbox.adapters import biology
        d = biology.pdb_structure(PDB, pdb_id="1CRN")
        self.assertEqual(d["chains"][0]["id"], "A")
        self.assertEqual(d["chains"][0]["residues"], 3)
        self.assertEqual(len(d["chains"][0]["ca"]), 3)
        self.assertEqual((len(d["helices"]), len(d["sheets"])), (1, 1))


class Chemistry(unittest.TestCase):
    def test_molecule_in_3d(self):
        from bie.toolbox.adapters import chemistry
        m = chemistry.molecule("CC(=O)OC1=CC=CC=C1C(=O)O", name="aspirin")
        self.assertEqual((m["formula"], len(m["atoms"])), ("C9H8O4", 21))
        self.assertIn("M  END", m["molblock"])
        with self.assertRaises(ValueError):
            chemistry.molecule("not a smiles")

    def test_reaction_balanced_with_drawings(self):
        from bie.toolbox.adapters import chemistry
        rx = chemistry.reaction("[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5].[OH2:3]", ["CC(=O)O", "OCC"],
                                names={"CCOC(C)=O": "ethyl acetate", "O": "water"})
        self.assertTrue(rx["balanced"])
        self.assertEqual([p["name"] for p in rx["products"]], ["ethyl acetate", "water"])
        self.assertTrue(all(c["svg"].lstrip().startswith(("<?xml", "<svg")) for c in rx["reactants"] + rx["products"]))

    def test_kinetics_makes_water(self):
        from bie.toolbox.adapters import chemistry
        k = chemistry.kinetics(temperature=1100.0, t_end=0.0006, points=30, species=("H2", "O2", "H2O"))
        self.assertLess(k["species"]["H2"][-1], k["species"]["H2"][0])
        self.assertGreater(k["species"]["H2O"][-1], 0.3)
        self.assertGreater(k["T"][-1], 2500)


class Meshes(unittest.TestCase):
    def test_obj_to_glb(self):
        from bie.toolbox.adapters import meshes
        glb, info = meshes.to_glb(CUBE, "obj")
        self.assertEqual(glb[:4], b"glTF")
        self.assertEqual(info["faces"], 12)
        self.assertEqual(meshes.glb_info(glb)["faces"], 12)


class OfflineRenderers(unittest.TestCase):
    def test_blender_builds_a_cell_sheet(self):
        from bie.toolbox.adapters import blender
        with tempfile.TemporaryDirectory() as folder:
            info = blender.cell_sheet(Path(folder) / "s.glb", kind="squamous", rows=2, cols=3)
            self.assertEqual((info["cells"], info["kind"]), (6, "squamous"))
            self.assertTrue(info["blender"].startswith("5.2"))
            from bie.toolbox.adapters import meshes
            self.assertGreaterEqual(meshes.glb_info((Path(folder) / "s.glb").read_bytes())["meshes"], 13)

    def test_manim_renders_a_clip(self):
        from bie.toolbox.adapters import manim_clips
        with tempfile.TemporaryDirectory() as folder:
            info = manim_clips.render("FunctionDraw", {"x": [0, 1, 2, 3], "y": [0, 1, 0, 1], "title": "test", "draw_seconds": 0.5},
                                      Path(folder) / "c.mp4", width=320, height=180)
            self.assertGreater(info["bytes"], 1000)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class BodyParts3D(unittest.TestCase):
    def test_a_concept_becomes_one_glb_with_its_credit(self):
        from bie.toolbox import sources
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("partof_BP3D_4.0_obj_99/FJ1.obj", CUBE)
            z.writestr("partof_BP3D_4.0_obj_99/FJ2.obj", CUBE)
        table = b"concept id\tname\telement file id\nFMA7088\theart\tFJ1\nFMA7088\theart\tFJ2\nFMA1\tother\tFJ9\n"

        def opener(request, timeout=None):
            return FakeResponse(table if request.full_url.endswith(".txt") else buf.getvalue())
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": folder}):
            lib = AssetLibrary(Path(folder) / "lib")
            asset = sources.bodyparts3d("FMA7088", lib, opener=opener)
            self.assertEqual((asset.mime, asset.licence, asset.credit), ("model/gltf-binary", "CC BY 4.0", sources.BP3D_CREDIT))
            from bie.toolbox.adapters import meshes
            self.assertEqual(meshes.glb_info((lib.folder / asset.path).read_bytes())["meshes"], 2)


if __name__ == "__main__":
    unittest.main()
