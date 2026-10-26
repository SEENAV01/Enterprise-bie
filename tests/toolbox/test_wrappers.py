"""Task 046a: one test per toolbox wrapper, with the real libraries (run in the toolbox lane, which installs every
toolbox extra; the lane fails on any skip, so a missing library is never hidden). Offline: network sources use fakes.

This file lives in tests/toolbox/, outside the canonical gate's discovery (tests/test*.py and its listed families): the
heavy libraries are optional extras that only the toolbox lane installs, so the canonical gates stay as light as before."""
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

ROOT = Path(__file__).resolve().parents[2]
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

    def test_epithelium_studio_renders_a_still_with_label_anchors(self):
        from bie.toolbox.adapters import blender
        with tempfile.TemporaryDirectory() as folder:
            info = blender.epithelium_studio(folder, {"resolution": [192, 108], "samples": 2, "width": 4.0, "depth": 3.0, "particles": 4,
                                                      "frames": 6, "camera": {"target": [0.0, 0.4, 0.1]}}, stills=[3])
            self.assertEqual((info["member"], info["frames_rendered"], info["samples"]), ("simple_squamous", 1, 2))
            self.assertGreater(info["cells"], 5)
            self.assertTrue(info["blender"].startswith("5.2"))
            self.assertTrue((Path(folder) / "frames" / "f0003.png").read_bytes().startswith(b"\x89PNG"))
            anchors = json.loads((Path(folder) / "anchors.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(anchors["points"]), ["boundary", "simple squamous"])
            self.assertEqual(len(anchors["points"]["simple squamous"]), 6)          # one [x, y, depth] per frame
            x, y, depth = anchors["points"]["simple squamous"][2]
            self.assertTrue(0 < x < 1 and 0 < y < 1 and depth > 0)
            again = Path(folder) / "again"                      # the same scene in every process (chunks on several runners)
            blender.epithelium_studio(again, {"resolution": [96, 54], "samples": 1, "width": 4.0, "depth": 3.0, "particles": 4,
                                              "frames": 6, "camera": {"target": [0.0, 0.4, 0.1]}}, stills=[1])
            self.assertEqual(json.loads((again / "anchors.json").read_text(encoding="utf-8"))["points"], anchors["points"])

    def test_manim_renders_a_clip(self):
        from bie.toolbox.adapters import manim_clips
        with tempfile.TemporaryDirectory() as folder:
            info = manim_clips.render("FunctionDraw", {"x": [0, 1, 2, 3], "y": [0, 1, 0, 1], "title": "test", "draw_seconds": 0.5},
                                      Path(folder) / "c.mp4", width=320, height=180)
            self.assertGreater(info["bytes"], 1000)


class Depth(unittest.TestCase):
    """Task 046 one-shot test, Route 2: the depth adapter around Depth Anything V2 Small (the model itself is not run here:
    a fake session stands in, so the lane needs no 99 MB download)."""

    def test_estimate_writes_a_16_bit_map_near_is_white(self):
        import numpy as np
        from PIL import Image
        from bie.toolbox.adapters import depth

        class Session:
            def get_inputs(self):
                return [type("I", (), {"name": "pixel_values"})()]

            def run(self, _outputs, feeds):
                x = feeds["pixel_values"]
                self.shape = x.shape
                rows = np.linspace(0.0, 10.0, depth.SIDE, dtype=np.float32)[:, None]   # bottom rows nearer
                return [np.repeat(rows, depth.SIDE, axis=1)[None]]

        with tempfile.TemporaryDirectory() as folder:
            Image.new("RGB", (320, 180), (200, 150, 150)).save(Path(folder) / "still.png")
            session = Session()
            info = depth.estimate(Path(folder) / "still.png", Path(folder) / "d.png", session=session)
            self.assertEqual(session.shape, (1, 3, depth.SIDE, depth.SIDE))
            out = Image.open(Path(folder) / "d.png")
            self.assertEqual((out.size, info["licence"]), ((320, 180), "Apache-2.0"))
            a = np.asarray(out)
            self.assertGreater(int(a[-1].mean()), int(a[0].mean()))
            self.assertGreater(int(a.max()), 255)                                         # 16-bit, not 8

    def test_anchors_find_the_far_edge_and_a_bump(self):
        import numpy as np
        from PIL import Image
        from bie.toolbox.adapters import depth
        h, w = 270, 480
        d = np.zeros((h, w), dtype=np.float32)
        d[int(0.2 * h):] = np.linspace(0.4, 1.0, h - int(0.2 * h))[:, None]            # the layer starts at 20 % from the top
        yy, xx = np.mgrid[0:h, 0:w]
        d += 0.15 * np.exp(-(((xx - 0.5 * w) / 9.0) ** 2 + ((yy - 0.6 * h) / 9.0) ** 2))  # one nucleus dome
        with tempfile.TemporaryDirectory() as folder:
            Image.fromarray((np.clip(d, 0, 1) * 65535).astype(np.uint16)).save(Path(folder) / "d.png")
            got = depth.layout_anchors(Path(folder) / "d.png", ["simple squamous", "boundary", "nucleus"], "simple squamous")
        self.assertAlmostEqual(got["edge_v"], 0.2, delta=0.03)
        self.assertAlmostEqual(got["anchors_uv"]["boundary"][1], 0.215, delta=0.03)
        self.assertAlmostEqual(got["anchors_uv"]["simple squamous"][0], 0.5, delta=0.02)
        self.assertAlmostEqual(got["anchors_uv"]["simple squamous"][1], 0.6, delta=0.03)
        self.assertNotIn("nucleus", got["anchors_uv"])                                    # not placed, never guessed

    def test_the_model_is_checked_by_sha256(self):
        from bie.toolbox.adapters import depth

        def opener(request, timeout=None):
            return FakeResponse(b"not the model")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "SHA-256"):
                depth.model_path(Path(folder), opener=opener)
            self.assertEqual(list((Path(folder) / "depth").iterdir()), [])


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


# ---------------------------------------------------------------- batch 2

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class Electrical(unittest.TestCase):
    def test_circuit_pieces_build_the_whole_drawing(self):
        from bie.toolbox.adapters import electrical
        parts = [("SourceV", "up", "5 V", {}), ("Resistor", "right", "1 kΩ", {}), ("Capacitor", "down", "100 µF", {}), ("Line", "tox:0", "", {})]
        c = electrical.circuit_parts(parts)
        self.assertEqual(len(c["pieces"]), 4)
        self.assertTrue(all(p.startswith("<") for p in c["pieces"]))
        self.assertIn("1 kΩ", "".join(c["pieces"]))
        self.assertEqual(len(c["view_box"].split()), 4)

    def test_ngspice_matches_lcapy_for_rc_charging(self):
        from bie.toolbox.adapters import electrical
        r = electrical.rc_charge(1000.0, 100e-6, 5.0, points=51)
        self.assertTrue(r["agree"], r["max_difference"])
        self.assertAlmostEqual(r["tau"], 0.1)
        i = min(range(51), key=lambda k: abs(r["t"][k] - 0.1))                 # one time constant: 63.2% of 5 V
        self.assertAlmostEqual(r["v_spice"][i] / 5.0, 0.632, delta=0.02)

    def test_step_responses_overshoot_falls_with_damping(self):
        from bie.toolbox.adapters import electrical
        data = electrical.step_responses((0.2, 0.7, 1.0))
        self.assertTrue(data["all_checked"])
        over = [r["overshoot_percent"] for r in data["responses"]]
        self.assertGreater(over[0], over[1])
        self.assertAlmostEqual(over[2], 0.0, delta=0.5)
        self.assertAlmostEqual(over[0], 52.7, delta=1.0)                        # exp(-πζ/√(1-ζ²)) for ζ = 0.2


class Mechanics(unittest.TestCase):
    def test_beam_matches_the_textbook(self):
        from bie.toolbox.adapters import mechanics
        b = mechanics.beam_point_load(6.0, 20e3, 3.0, E=200e9, I=8.36e-5)
        expected_mm = -20e3 * 6.0 ** 3 / (48 * 200e9 * 8.36e-5) * 1000           # central point load: PL³/48EI
        self.assertTrue(b["agree"])
        self.assertAlmostEqual(b["max_deflection_mm"], expected_mm, delta=abs(expected_mm) * 0.01)
        self.assertAlmostEqual(b["max_moment_kNm"], 20 * 6 / 4, delta=0.05)

    def test_flange_is_a_glb_with_a_sensible_mass(self):
        from bie.toolbox.adapters import mechanics
        data, facts = mechanics.flange_glb()
        self.assertEqual(data[:4], b"glTF")
        self.assertGreater(facts["mass_kg"], 0.5)
        self.assertLess(facts["mass_kg"], 5.0)

    def test_rankine_efficiency_is_physical(self):
        from bie.toolbox.adapters import mechanics
        r = mechanics.rankine(80.0, 0.1, 480.0)
        carnot = 1 - (r["states"][0]["T_C"] + 273.15) / (480 + 273.15)
        self.assertGreater(r["efficiency"], 0.3)
        self.assertLess(r["efficiency"], carnot)
        self.assertEqual(r["states"][0]["s"], r["states"][1]["s"])              # the ideal pump and turbine keep entropy

    def test_heat_plate_stays_between_its_edges(self):
        from bie.toolbox.adapters import mechanics
        h = mechanics.heated_plate(refine=3)
        self.assertAlmostEqual(min(h["temperature"]), 20.0, delta=0.01)
        self.assertAlmostEqual(max(h["temperature"]), 100.0, delta=0.01)
        self.assertTrue(all(fx >= -1e-6 for fx in h["arrows"]["fx"]))          # heat flows from the hot strip to the cold edge


class Earth(unittest.TestCase):
    def test_relief_draws_a_grid_and_profiles_it(self):
        import numpy as np
        import xarray as xr
        from bie.toolbox.adapters import earth
        lon, lat = np.linspace(70, 80, 101), np.linspace(20, 30, 101)
        z = np.outer(np.ones(101), np.linspace(0, 5000, 101))                   # rises from west to east
        grid = xr.DataArray(z, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"))
        with tempfile.TemporaryDirectory() as tmp:          # GMT's session folder stays in the asset cache, which outlives the test
            out = Path(tmp) / "relief.png"
            r = earth.relief((70, 80, 20, 30), out, profile=((71, 25), (79, 25)), grid=grid)
            self.assertEqual(out.read_bytes()[:4], b"\x89PNG")
        heights = r["profile"]["elevation_m"]
        self.assertLess(heights[0], heights[-1])
        self.assertAlmostEqual(heights[-1], 4500, delta=150)

    def test_p_arrives_before_s(self):
        from bie.toolbox.adapters import earth
        r = earth.ray_paths(60.0, 10.0, phases=("P", "S"))
        times = {ray["phase"]: ray["time_s"] for ray in r["rays"]}
        self.assertLess(times["P"], times["S"])
        self.assertAlmostEqual(times["P"], 607, delta=10)                        # IASP91, 60°: about 10 minutes

    def test_seismogram_has_three_normalised_traces(self):
        from bie.toolbox.adapters import earth
        s = earth.seismogram(points=200)
        self.assertEqual(len(s["traces"]), 3)
        self.assertTrue(all(max(abs(v) for v in t["values"]) <= 1.0 for t in s["traces"]))

    def test_a_plate_rotates_back_in_time(self):
        import pygplates
        from bie.toolbox.adapters import earth
        with tempfile.TemporaryDirectory() as tmp:
            rot = Path(tmp) / "toy.rot"
            rot.write_text("101 0.0 90.0 0.0 0.0 000 !toy\n101 100.0 0.0 0.0 30.0 000 !toy\n", encoding="utf-8")
            polygon = pygplates.PolygonOnSphere([(0, 0), (0, 10), (10, 10), (10, 0)])
            feature = pygplates.Feature.create_reconstructable_feature(pygplates.FeatureType.gpml_coastline, polygon, reconstruction_plate_id=101)
            coast = Path(tmp) / "toy.gpml"
            pygplates.FeatureCollection([feature]).write(str(coast))
            data = earth.reconstruct(rot, coast, ages=(100, 0), min_step_deg=0.1, min_points=3)
        now, then = data["frames"][1]["shapes"][0], data["frames"][0]["shapes"][0]
        self.assertEqual(len(now), len(then))
        self.assertNotEqual(now, then)
        self.assertIn([0.0, 0.0], [[round(x, 1), round(y, 1)] for x, y in now])


class Astro(unittest.TestCase):
    """Needs the JPL DE421 ephemeris (17 MB): fetched once into the asset cache; the stars come from a three-line fixture."""

    def setUp(self):
        from bie.toolbox import sources
        from bie.toolbox.adapters import astro
        (sources.cache_dir() / "skyfield").mkdir(parents=True, exist_ok=True)
        self.de421 = sources.cached(astro.EPHEMERIS["source"], "skyfield/de421.bsp")
        self.tmp = tempfile.TemporaryDirectory()
        folder = Path(self.tmp.name) / "skyfield"
        folder.mkdir()
        (folder / "de421.bsp").symlink_to(self.de421)
        (folder / "hip_main.dat").write_bytes((FIXTURES / "hip_main_3stars.dat").read_bytes())

    def tearDown(self):
        self.tmp.cleanup()

    def test_orbit_periods_follow_kepler(self):
        from bie.toolbox.adapters import astro
        o = astro.orbits("2026-01-01", 400, 5, cache=Path(self.tmp.name))
        periods = {p["name"]: p["kepler_period_days"] for p in o["planets"]}
        self.assertAlmostEqual(periods["earth"], 365.25, delta=2)
        self.assertAlmostEqual(periods["mars"], 687, delta=8)

    def test_sky_puts_orion_and_sirius_up_on_a_winter_evening(self):
        from bie.toolbox.adapters import astro
        s = astro.sky(28.61, 77.21, "2026-01-15T22:00:00", magnitude_limit=2.0, cache=Path(self.tmp.name))
        self.assertEqual(s["count"], 3)
        self.assertTrue(all(0 < a < 90 for a in s["stars"]["alt"]))


class Aero(unittest.TestCase):
    def test_aircraft_mesh_and_lift_curve(self):
        from bie.toolbox.adapters import aero
        data, facts = aero.trainer_aircraft(alphas=(0, 4, 8))
        self.assertEqual(data[:4], b"glTF")
        cl = [c["CL"] for c in facts["lift_curve"]]
        self.assertTrue(cl[0] < cl[1] < cl[2])
        self.assertAlmostEqual(facts["cl_per_degree"], 0.09, delta=0.03)       # a finite wing: below thin-airfoil 2π/rad

    def test_cessna_climbs_and_levels_off(self):
        from bie.toolbox.adapters import aero
        c = aero.climb(seconds=100.0)
        self.assertGreater(c["best_climb_fpm"], 500)
        self.assertAlmostEqual(c["altitude_ft"][-1], 2500, delta=120)


# ---------------------------------------------------------------- batch 3

def _geojson(features):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": p, "geometry": g} for p, g in features]}


def _box(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


class Maps(unittest.TestCase):
    """India's outline, two states that do not cover all of it, a neighbour that overlaps the outline, and three towns."""

    def setUp(self):
        from bie.toolbox.adapters import maps
        self.maps = maps
        self.tmp = tempfile.TemporaryDirectory()
        files = {
            "ne_10m_admin_0_countries_ind": _geojson([({"ADM0_A3": "IND", "NAME": "India"}, _box(70, 10, 90, 30)),
                                                      ({"ADM0_A3": "PAK", "NAME": "Pakistan"}, _box(62, 24, 72, 34))]),
            "ne_10m_admin_1_states_provinces": _geojson([
                ({"adm0_a3": "IND", "name": "North", "type_en": "State", "iso_3166_2": "IN-NO"}, _box(70, 20, 90, 28)),
                ({"adm0_a3": "IND", "name": "South", "type_en": "Union Territory", "iso_3166_2": "IN-SO"}, _box(70, 10, 90, 20))]),
            "ne_10m_populated_places_simple": _geojson([
                ({"name": "Allahabad", "nameascii": "Allahabad", "adm0_a3": "IND", "adm0name": "India", "latitude": 25.46, "longitude": 81.84, "pop_max": 1201000},
                 {"type": "Point", "coordinates": [81.84, 25.46]}),
                ({"name": "Delhi", "nameascii": "Delhi", "adm0_a3": "IND", "adm0name": "India", "latitude": 28.67, "longitude": 77.23, "pop_max": 15926000},
                 {"type": "Point", "coordinates": [77.23, 28.67]}),
                ({"name": "Delhi", "nameascii": "Delhi", "adm0_a3": "USA", "adm0name": "United States", "latitude": 42.0, "longitude": -75.0, "pop_max": 3000},
                 {"type": "Point", "coordinates": [-75.0, 42.0]})])}
        for name, body in files.items():
            (Path(self.tmp.name) / f"{name}.geojson").write_text(json.dumps(body), encoding="utf-8")
        maps._features.cache_clear()
        self.patch = mock.patch("bie.toolbox.sources.natural_earth", lambda name, opener=None: Path(self.tmp.name) / f"{name}.geojson")
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.maps._features.cache_clear()
        self.tmp.cleanup()

    def test_india_with_a_state_picked_out(self):
        d = self.maps.india(["North"])
        self.assertEqual([s["name"] for s in d["states"] if s["highlight"]], ["North"])
        north = next(s for s in d["states"] if s["name"] == "North")
        # on the sphere: R² · Δλ · (sin 28° − sin 20°) = 1.806 million km²
        import math
        self.assertAlmostEqual(north["area_km2"] / 1.0e6, 6371.0088 ** 2 * math.radians(20) * (math.sin(math.radians(28)) - math.sin(math.radians(20))) / 1.0e6,
                               delta=0.01)
        self.assertGreater(d["beyond_states_km2"], 0)                       # 28°–30° N is India's but no state's
        pak = d["neighbours"][0]
        self.assertEqual(pak["iso3"], "PAK")
        from shapely.geometry import shape
        self.assertLess(shape(pak["geometry"]).intersection(shape(d["outline"])).area, 1e-9)   # a neighbour never covers India
        with self.assertRaises(ValueError):
            self.maps.india(["Atlantis"])

    def test_places_take_the_renamed_city_and_the_country_asked_for(self):
        stops = self.maps.places(["Prayagraj", "Delhi"], countries=("IND",))
        self.assertEqual([s["country"] for s in stops], ["India", "India"])
        self.assertEqual(stops[0]["name"], "Prayagraj")                   # shown as asked, found under its older name
        route = self.maps.route(["Prayagraj", "Delhi"], countries=("IND",))
        self.assertAlmostEqual(route["total_km"], 580, delta=15)            # Allahabad to Delhi, great circle
        with self.assertRaises(ValueError):
            self.maps.places(["Nowhere"])


class Economics(unittest.TestCase):
    def test_cobb_douglas_constant_returns_and_the_cheapest_mix(self):
        from bie.toolbox.adapters import economics
        d = economics.cobb_douglas(alpha=0.4, beta=0.6, r=2.0, w=1.0, n=11)
        self.assertEqual(d["returns_to_scale"], "constant")
        self.assertAlmostEqual(d["k_over_l"], (0.4 / 0.6) * (1 / 2), places=3)
        k, l, q = d["expansion_path"][5]
        self.assertAlmostEqual(q, k ** 0.4 * l ** 0.6, places=2)
        self.assertAlmostEqual(d["Q"][10][10], 100.0, places=2)             # Q(100, 100) with A = 1

    def test_joined_frames_interpolate_inside_a_country_only(self):
        from bie.toolbox.adapters import economics
        rows = lambda vals: [{"iso3": "IND", "country": "India", "year": y, "value": v} for y, v in vals]
        d = economics.joined_frames({"x": rows([(2000, 10.0), (2002, 30.0)]), "y": rows([(2000, 1.0), (2001, 2.0), (2002, 3.0)])}, [2000, 2001, 2003])
        self.assertEqual(d["frames"][1]["points"][0]["x"], 20.0)
        self.assertTrue(d["frames"][1]["points"][0]["interpolated"])
        self.assertEqual(d["frames"][2]["points"], [])                      # 2003 is outside the data: never extrapolated


ACT = {"title": "The Test Sanhita, 2023", "act_number": "1", "year": "2023", "in_force": "01-07-2024", "act_id": "AC_CEN_1_2023",
       "sections": [{"number": "6", "title": "Classes of Courts.", "text": "There shall be the following classes, namely:— (i) Courts of Session; "
                     "(ii) Judicial Magistrates of the first class; and (iii) Executive Magistrates."},
                    {"number": "173", "title": "Information in cognizable cases.", "text": "(1) Every information ..."},
                    {"number": "250", "title": "Discharge.", "text": "If ..."}, {"number": "262", "title": "Discharge.", "text": "If ..."}]}


class Law(unittest.TestCase):
    def test_sections_are_found_by_official_title_only(self):
        from bie.toolbox.adapters import law
        self.assertEqual(law.find_section(ACT, "information in cognizable cases")["number"], "173")
        with self.assertRaises(law.LawDataError):
            law.find_section(ACT, "Discharge.")                               # two sections share it: a range must decide
        self.assertEqual(law.find_section(ACT, "Discharge.", between=(248, 260))["number"], "250")
        with self.assertRaises(law.LawDataError):
            law.find_section(ACT, "Arrest by a dragon.")

    def test_procedure_carries_section_numbers_and_rejects_unknown_steps(self):
        from bie.toolbox.adapters import law
        flow = law.procedure(ACT, [{"id": "fir", "title": "Information in cognizable cases.", "label": "FIR"},
                                   {"id": "q", "label": "Ground to proceed?", "kind": "decision"},
                                   {"id": "dis", "title": "Discharge.", "between": [248, 260], "kind": "end"}],
                             [["fir", "q"], ["q", "dis", "no"]])
        self.assertEqual([(n["id"], n.get("section")) for n in flow["nodes"]], [("fir", "173"), ("q", None), ("dis", "250")])
        self.assertEqual(flow["edges"][1], {"from": "q", "to": "dis", "label": "no"})
        with self.assertRaises(law.LawDataError):
            law.procedure(ACT, [{"id": "a", "label": "A"}], [["a", "b"]])

    def test_listed_items(self):
        from bie.toolbox.adapters import law
        self.assertEqual(law.listed_items(ACT["sections"][0]),
                         ["Courts of Session", "Judicial Magistrates of the first class", "Executive Magistrates"])

    def test_a_judgment_record_from_the_years_parquet(self):
        import pyarrow as pa
        import pyarrow.parquet as pq
        from bie.toolbox import sources
        from bie.toolbox.adapters import law
        raw = ("<div> | HIS HOLINESS KESAVANANDA BHARATI | versus | STATE OF KERALA | Coram : S.M. SIKRI | * | , J.M. SHELAT, K.S. HEGDE | | x "
               "| Bench : | | 13 Judges | | </div>")
        table = pa.table({k: [v] for k, v in {"title": "HIS HOLINESS KESAVANANDA BHARATI versus STATE OF KERALA", "petitioner": "HIS HOLINESS KESAVANANDA BHARATI",
                          "respondent": "STATE OF KERALA", "judge": "S.M. SIKRI", "author_judge": "<NA>", "citation": "[1973] SUPP. 1 S.C.R. 1",
                          "case_id": "1973 INSC 91", "cnr": "ESCR010003021973", "decision_date": "24-04-1973", "disposal_nature": "",
                          "court": "Supreme Court of India", "available_languages": "ENG,HIN", "path": "S_1973_1_1_1002", "year": "1973",
                          "raw_html": raw}.items()})
        buf = io.BytesIO()
        pq.write_table(table, buf)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": tmp}):
            opener = mock.Mock(side_effect=lambda req, timeout=None: FakeResponse(buf.getvalue()))
            lib = AssetLibrary(Path(tmp) / "lib")
            asset, record = sources.sc_judgment(1973, "KESAVANANDA", lib, opener=opener)
            card = law.case_card(record)
            self.assertEqual((record["bench_judges"], record["coram"]), (13, ["S.M. SIKRI", "J.M. SHELAT", "K.S. HEGDE"]))
            self.assertEqual((card["decided"], card["bench"]), ("24 April 1973", "13 judges"))
            self.assertIsNone(record["author_judge"])
            self.assertIn("S_1973_1_1_1002_EN.pdf", record["pdf"])
            self.assertEqual(asset.licence, "CC BY 4.0")
            with self.assertRaises(sources.SourceError):
                sources.sc_judgment(1973, "NOBODY", lib, opener=opener)


class Behaviour(unittest.TestCase):
    def test_psychopy_makes_the_same_stroop_list_for_a_seed(self):
        from bie.toolbox.adapters import behaviour
        a, b = behaviour.stroop(seed=7), behaviour.stroop(seed=7)
        self.assertEqual(a["trials"], b["trials"])
        self.assertEqual((len(a["trials"]), a["congruent"], a["incongruent"]), (9, 3, 6))
        self.assertEqual(sorted((t["word"], t["ink"]) for t in a["trials"]),
                         sorted((w.upper(), c) for w in ("red", "green", "blue") for c in ("red", "green", "blue")))
        self.assertIn("PsychoPy", a["designed_by"])

    def test_teaching_method_logit_matches_the_published_fit(self):
        from bie.toolbox.adapters import behaviour
        d = behaviour.teaching_method()
        self.assertEqual(d["n"], 32)
        self.assertAlmostEqual(d["odds_ratio_psi"], 10.79, delta=0.05)       # exp(2.3787), Spector and Mazzeo's PSI coefficient
        self.assertLess(d["p_value_psi"], 0.05)
        self.assertTrue(all(b >= a for a, b in zip(d["without_psi"], d["with_psi"])))


class Language(unittest.TestCase):
    def test_words_aksharas_and_iast(self):
        from bie.toolbox.adapters import language
        fixtures = ROOT / "tests" / "toolbox" / "fixtures" / "indic_nlp_resources"
        with mock.patch("bie.toolbox.sources.indic_nlp_resources", lambda opener=None: fixtures):
            d = language.sentence("सर्वे भवन्तु सुखिनः ।", glosses=["all", "may be", "happy"])
        self.assertEqual([w["roman"] for w in d["words"]], ["sarve", "bhavantu", "sukhinaḥ"])
        self.assertEqual(d["words"][2]["aksharas"], ["सु", "खि", "नः"])       # the visarga stays with its akshara
        self.assertEqual(d["words"][2]["punct"], "।")
        with self.assertRaises(ValueError):
            language.sentence("सर्वे भवन्तु", glosses=["only one"])
