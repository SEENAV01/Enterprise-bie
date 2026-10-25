"""Task 046a: the toolbox registry, capability vocabulary, resolver, asset sources (fake network), demo list and page.

Offline, standard library only (no toolbox extras needed); runs in the toolbox lane and in the Task 045 lane.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain.video import render  # noqa: E402
from bie.toolbox import demos, page, registry, resolver, sources  # noqa: E402
from bie.toolbox.adapters import base  # noqa: E402

REG = json.loads(registry.REGISTRY.read_text(encoding="utf-8"))
CAPS = json.loads(registry.CAPABILITIES.read_text(encoding="utf-8"))
BOX = registry.load()
NAVIN_CAPABILITIES = """cell_sheet_3d, particle_flow, organ_zoom, focus_glow, kinetic_caption, concept_arrow, board_build, mnemonic_card,
anatomy_3d, molecule_3d, reaction_steps, circuit_diagram, signal_plot, function_graph, equation_transform, vector_field, physics_sim_2d,
physics_sim_3d, wave_motion, orbit_motion, sky_map, aircraft_shape, flight_motion, map_region, map_route, terrain_or_layers, earthquake_waves,
plate_motion, timeline, flowchart, process_cycle, tree_hierarchy, network_graph, chart_bar_line_pie, table_build, case_card, machine_part_3d,
structure_load, ecg_trace, protein_3d, text_kinetic"""


def edited(**changes):
    reg = json.loads(json.dumps(REG))
    for tool in reg["tools"]:
        if tool["id"] == changes.get("tool"):
            tool.update(changes.get("set", {}))
            for key in changes.get("drop", ()):
                tool.pop(key, None)
    return reg


class Registry(unittest.TestCase):
    def test_both_files_are_valid_and_every_adapter_exists(self):
        self.assertEqual(registry.problems(REG, CAPS, repo_root=ROOT), [])
        self.assertGreaterEqual(len(BOX.tools), 30)

    def test_the_vocabulary_is_navins_list_plus_the_benchmark_split_compare(self):
        wanted = {c.strip() for c in NAVIN_CAPABILITIES.split(",")}
        self.assertEqual(set(BOX.capabilities) - {"split_compare"}, wanted)
        benchmark = json.loads((ROOT / "bie/brain/rulebook/benchmarks/epithelium_animation.json").read_text(encoding="utf-8"))
        blocks = {s["block"] for s in benchmark["shots"]}
        served = {c.benchmark_block for c in BOX.capabilities.values() if c.benchmark_block}
        self.assertEqual(blocks - served, set(), "every block of the Task 046 benchmark has a capability")

    def test_content_types_are_the_rulebooks(self):
        types = {t["id"] for t in json.loads((ROOT / "bie/brain/rulebook/content_types.json").read_text(encoding="utf-8"))["types"]}
        self.assertEqual(set(BOX.content_types), types)

    def test_schema_file_matches_the_code(self):
        schema = json.loads(registry.SCHEMA.read_text(encoding="utf-8"))
        item = schema["properties"]["tools"]["items"]
        self.assertEqual(set(item["required"]), set(registry.REQUIRED))
        self.assertEqual(set(item["properties"]), set(registry.REQUIRED) | set(registry.OPTIONAL))
        self.assertEqual(item["properties"]["status"]["enum"], list(registry.STATUSES))
        self.assertEqual(item["properties"]["kind"]["enum"], list(registry.KINDS))
        self.assertEqual(item["properties"]["licence_flags"]["items"]["enum"], list(registry.FLAGS))

    def test_bad_entries_are_named(self):
        cases = [
            (edited(tool="three", set={"capabilities": ["teleport"]}), "unknown capability 'teleport'"),
            (edited(tool="three", set={"status": "blocked_with_reason"}), "blocked_with_reason needs blocked_reason"),
            (edited(tool="three", set={"proof": {}}), "needs proof"),
            (edited(tool="sympy", set={"proof": {"tests": ["tests/test_task046a_wrappers.py::Nothing"]}}), "proof test"),
            (edited(tool="sympy", set={"proof": {"tests": ["tests/no_such_file.py::Maths"]}}), "does not exist"),
            (edited(tool="z-anatomy", set={"licence_flags": []}), "needs the flag share_alike"),
            (edited(tool="blender", set={"licence_flags": []}), "needs the flag gpl"),
            (edited(tool="three", set={"source": "http://x"}), "source must be an https URL"),
            (edited(tool="molstar", set={"levels": ["phd"]}), "unknown level profile 'phd'"),
            (edited(tool="three", set={"surprise": 1}), "unknown fields surprise"),
            (edited(tool="three", drop=("version",)), "missing version"),
            (edited(tool="sympy", set={"adapter": "bie.toolbox.adapters.nothing"}), "does not exist"),
        ]
        for reg, expected in cases:
            found = registry.problems(reg, CAPS, repo_root=ROOT)
            self.assertTrue(any(expected in p for p in found), (expected, found))
        with self.assertRaises(registry.RegistryError):
            registry.from_data(cases[0][0], CAPS)

    def test_licence_flags_follow_the_licence_name_not_its_notes(self):
        self.assertEqual(registry._licence_needs("CC BY-SA 4.0"), {"share_alike"})
        self.assertEqual(registry._licence_needs("CC BY 4.0 (releases up to 3.0 were CC BY-SA 2.1 Japan)"), set())
        self.assertEqual(registry._licence_needs("GPL-3.0-or-later (the program)"), {"gpl"})
        self.assertEqual(registry._licence_needs("LGPL-2.1"), set())
        self.assertEqual(registry._licence_needs("CC BY-NC 4.0"), {"non_commercial"})

    def test_share_alike_and_gpl_items_are_marked_not_blocked(self):
        marked = {t.id: t for t in BOX.tools if set(t.licence_flags) & {"share_alike", "gpl"}}
        self.assertEqual(set(marked), {"z-anatomy", "blender"})
        self.assertTrue(all(t.usable for t in marked.values()))

    def test_pins_match_the_install_files(self):
        web = json.loads((ROOT / "bie/toolbox/web_packages.json").read_text(encoding="utf-8"))
        pinned = {k: v for g in web["groups"].values() for k, v in g.items()}
        for tid, package in web["tool_packages"].items():
            self.assertEqual(BOX.tool(tid).version, pinned[package], tid)
        import tomllib
        extras = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["optional-dependencies"]
        pins = {}
        for group, items in extras.items():
            if group.startswith("toolbox-"):
                for item in items:
                    name, _, version = item.partition("==")
                    self.assertTrue(version, f"{group}: {item} must be pinned with ==")
                    pins[name.lower()] = (group, version)
        for tid, (_, dist, group) in base.PYTHON_TOOLS.items():
            self.assertIn(dist, pins, f"{dist} needs a pin in pyproject extras")
            self.assertEqual(pins[dist], (group, BOX.tool(tid).version), tid)
            self.assertEqual(BOX.tool(tid).install_group, group, tid)
        self.assertEqual(web["npm_before_file"], "tools/npm_before.txt")
        self.assertTrue(BOX.npm_before.startswith((ROOT / "tools/npm_before.txt").read_text().strip()[:10]))


class Resolver(unittest.TestCase):
    def test_every_capability_resolves_or_is_reported_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            log = resolver.MissingLog(Path(folder) / "missing.jsonl")
            for cap in BOX.capabilities:
                r = resolver.resolve(cap, path="web", log=log)
                self.assertEqual(r.missing, not r.draw, cap)
            rows = log.rows()
            self.assertEqual({r["capability"] for r in rows}, {c for c in BOX.capabilities if resolver.resolve(c, log=None).missing})
            self.assertTrue(all(r["registry_version"] == BOX.version for r in rows))

    def test_batch_1_capabilities_draw_on_the_web_path(self):
        for cap, subject, first in (("cell_sheet_3d", "biology_medical", "three"), ("protein_3d", "biology_medical", "3dmol"),
                                    ("equation_transform", "maths_statistics", "katex"), ("ecg_trace", "biology_medical", "d3"),
                                    ("physics_sim_2d", "physics", "matter-js"), ("network_graph", "computer_science", "d3"),
                                    ("organ_zoom", "biology_medical", "bie-blocks")):
            r = resolver.resolve(cap, subject=subject, log=None)
            self.assertFalse(r.missing, cap)
            self.assertEqual(r.draw[0], first, (cap, r.draw))

    def test_compute_assets_and_makers_are_listed(self):
        r = resolver.resolve("cell_sheet_3d", subject="biology_medical", log=None)
        self.assertIn("blender", r.makers)
        r = resolver.resolve("protein_3d", subject="biology_medical", log=None)
        self.assertEqual(r.compute, ["biopython"])
        self.assertEqual(set(r.assets), {"rcsb-pdb", "nih-3d"})
        r = resolver.resolve("reaction_steps", subject="chemistry", log=None)
        self.assertEqual(set(r.compute), {"rdkit", "cantera"})

    def test_level_filters_and_status_orders(self):
        school = resolver.resolve("protein_3d", level="school", log=None)
        self.assertNotIn("molstar", school.draw)
        upsc = resolver.resolve("protein_3d", level="upsc_pcs", log=None)
        self.assertEqual(upsc.draw[:2], ["3dmol", "molstar"])
        reg = edited(tool="molstar", set={"status": "used_on_real_book", "proof": {"tests": ["x"]}})
        box = registry.from_data(reg, CAPS)
        self.assertEqual(resolver.resolve("protein_3d", level="upsc_pcs", toolbox=box, log=None).draw[0], "molstar")

    def test_offline_path_and_fallback(self):
        r = resolver.resolve("function_graph", path="offline", log=None)
        self.assertEqual((r.path, r.draw[0], r.fallback), ("offline", "manim", ""))
        r = resolver.resolve("molecule_3d", path="offline", log=None)
        self.assertEqual(r.path, "web")
        self.assertIn("no offline tool draws molecule_3d", r.fallback)

    def test_blocked_tools_are_skipped_and_named(self):
        reg = edited(tool="katex", set={"status": "blocked_with_reason", "blocked_reason": "test"})
        box = registry.from_data(reg, CAPS)
        r = resolver.resolve("equation_transform", toolbox=box, log=None)
        self.assertNotIn("katex", r.draw)
        self.assertIn("manim", r.draw + [r.path == "offline" and "manim"])

    def test_unknown_capability_is_logged(self):
        with tempfile.TemporaryDirectory() as folder:
            log = resolver.MissingLog(Path(folder) / "m.jsonl")
            r = resolver.resolve("hologram", subject="physics", log=log, context="v3 b12")
            self.assertTrue(r.missing)
            self.assertEqual(log.summary()[0]["capability"], "hologram")
            with mock.patch.dict(os.environ, {"BIE_TOOLBOX_MISSING_LOG": str(Path(folder) / "env.jsonl")}):
                resolver.resolve("hologram")
            self.assertEqual(len(resolver.MissingLog(Path(folder) / "env.jsonl").rows()), 1)

    def test_visual_verbs_point_to_capabilities(self):
        self.assertEqual(resolver.match("oxygen dots cross the thin sheet")[0], "particle_flow")
        self.assertIn("organ_zoom", resolver.match("organ_zoom: lung → alveolus → the flat sheet"))
        self.assertEqual(resolver.match("an ECG with the QRS complex")[0], "ecg_trace")
        self.assertEqual(resolver.match("nothing visual here"), [])


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Opener:
    def __init__(self, routes: dict):
        self.routes, self.urls = routes, []

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.urls.append(url)
        for prefix, body in self.routes.items():
            if url.startswith(prefix):
                return FakeResponse(body if isinstance(body, bytes) else json.dumps(body).encode())
        raise AssertionError("unexpected URL " + url)


NIH_META = {"entryId": 22787, "threedpxId": "3DPX-022787", "submissions": [
    {"submissionId": 1, "version": 1, "submissionStatus": "Archived", "metadata": {"title": "old", "license": "Public Domain"},
     "inputFiles": [{"fileId": 10, "fileFormat": "GLB"}]},
    {"submissionId": 37664, "version": 2, "submissionStatus": "Published", "metadata": {"title": "Human Heart 3d Model", "license": "Public Domain"},
     "inputFiles": [{"fileId": 1448470, "fileFormat": "GLB"}], "workflowRuns": [{"outputFiles": [{"fileId": 5, "fileFormat": "STL"}]}]}]}


class Sources(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lib = AssetLibrary(Path(self.tmp.name) / "lib")

    def tearDown(self):
        self.tmp.cleanup()

    def test_pdb_and_pubchem_with_licences(self):
        opener = Opener({"https://files.rcsb.org/download/1CRN.pdb": b"HEADER CRAMBIN\nATOM ...\nEND\n",
                         "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/caffeine/SDF": b"caffeine\n  RDKit\n\nM  END\n$$$$\n"})
        pdb = sources.rcsb_pdb("1crn", self.lib, opener=opener)
        sdf = sources.pubchem_sdf("caffeine", self.lib, opener=opener)
        self.assertEqual((pdb.mime, pdb.licence, pdb.path.endswith(".pdb")), ("chemical/x-pdb", "CC0 1.0", True))
        self.assertEqual((sdf.mime, sdf.path.endswith(".sdf")), ("chemical/x-mdl-sdfile", True))
        self.assertIn("RCSB PDB 1CRN", self.lib.credits([pdb.asset_id])[0] + pdb.credit)
        with self.assertRaises(sources.SourceError):
            sources.rcsb_pdb("../etc", self.lib, opener=opener)
        with self.assertRaises(sources.SourceError):
            sources.pubchem_sdf("caffeine", self.lib, opener=Opener({"https://pubchem": b"no record"}))

    def test_nih3d_takes_the_newest_published_glb_and_its_licence(self):
        opener = Opener({"https://3d.nih.gov/api/entries/": NIH_META,
                         "https://3d.nih.gov/api/download?submissionId=37664&fileIds=1448470": b"glTF\x02\x00\x00\x00rest"})
        asset = sources.nih3d("3DPX-022787", self.lib, opener=opener)
        self.assertEqual((asset.mime, asset.licence), ("model/gltf-binary", "Public Domain"))
        self.assertIn("3DPX-022787", asset.page_url)
        meta = json.loads(json.dumps(NIH_META))
        meta["submissions"][1]["metadata"]["license"] = "CC BY-NC 4.0"
        with self.assertRaises(sources.SourceError):
            sources.nih3d("3DPX-022787", self.lib, opener=Opener({"https://3d.nih.gov/api/entries/": meta}))
        meta["submissions"][1]["metadata"]["license"] = "CC BY-SA 4.0"
        opener = Opener({"https://3d.nih.gov/api/entries/": meta, "https://3d.nih.gov/api/download": b"glTF\x02\x00\x00\x00other"})
        self.assertIn("share-alike", sources.nih3d("3DPX-022787", self.lib, opener=opener).tags)

    def test_servier_path_and_credit(self):
        opener = Opener({"https://smart.servier.com/wp-content/uploads/2016/10/poumon_10.png": b"\x89PNG\r\n\x1a\nfake"})
        asset = sources.servier("2016/10/poumon_10.png", self.lib, opener=opener)
        self.assertEqual((asset.licence, asset.credit), ("CC BY 4.0", "Servier Medical Art (smart.servier.com), CC BY 4.0"))
        with self.assertRaises(sources.SourceError):
            sources.servier("https://evil.example/x.png", self.lib, opener=opener)

    def test_z_anatomy_parts_are_exported_by_blender_and_marked_share_alike(self):
        made = []

        def fbx_part(fbx, match, out, exclude=""):
            made.append((Path(fbx).read_bytes(), match, exclude))
            Path(out).write_bytes(b"glTF\x02\x00\x00\x00" + match.encode())
            return {"objects": 2, "names": ["Left ventricle", "Right ventricle"]}

        with mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")}), \
                mock.patch("bie.toolbox.adapters.blender.fbx_part", fbx_part):
            opener = Opener({sources.ZANATOMY_FBX.format(name="CardioVascular41"): b"Kaydara FBX Binary"})
            asset, info = sources.z_anatomy("CardioVascular41", "ventricle", self.lib, opener=opener, title="Heart")
            again, _ = sources.z_anatomy("CardioVascular41", "ventricle", self.lib, opener=opener, title="Heart")
            self.assertEqual(len(opener.urls), 1)                     # the FBX is fetched once into the cache
            self.assertEqual(asset.asset_id, again.asset_id)
            self.assertEqual((asset.licence, asset.mime, info["objects"]), ("CC BY-SA 4.0", "model/gltf-binary", 2))
            self.assertIn("share-alike", asset.tags)
            self.assertIn("Z-Anatomy", asset.credit)
            self.assertEqual(made[0], (b"Kaydara FBX Binary", "ventricle", ""))
            with self.assertRaises(sources.SourceError):
                sources.z_anatomy("../../etc/passwd", "x", self.lib, opener=opener)

    def test_big_downloads_stay_in_the_cache_outside_git(self):
        with mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")}):
            opener = Opener({"https://example.org/big.zip": b"x" * 100})
            path = sources.cached("https://example.org/big.zip", "big.zip", opener=opener)
            sources.cached("https://example.org/big.zip", "big.zip", opener=opener)
            self.assertEqual(len(opener.urls), 1)
            self.assertFalse(str(path).startswith(str(ROOT)))
        with self.assertRaises(sources.SourceError):
            sources.fetch("http://insecure.example/x")


class DemosAndPage(unittest.TestCase):
    def test_every_demo_names_known_tools_and_capabilities(self):
        ids = [d.id for d in demos.DEMOS]
        self.assertEqual(len(ids), len(set(ids)))
        for d in demos.DEMOS:
            for t in d.tools:
                BOX.tool(t)
            for c in d.capabilities:
                self.assertIn(c, BOX.capabilities)
            self.assertTrue(3.0 <= d.seconds <= 5.0, d.id)

    def test_every_batch_1_tool_has_a_demo_or_a_test(self):
        covered = {t for d in demos.DEMOS if d.batch == 1 for t in d.tools}
        for tool in BOX.batch(1):
            proof = tool.proof
            self.assertTrue(tool.id in covered or proof.get("tests"), f"{tool.id} has no demo and no test")
            for demo_id in proof.get("demos", []):
                self.assertIn(tool.id, demos.by_id(demo_id).tools, (tool.id, demo_id))

    def test_a_status_claim_fails_when_its_demo_did_not_pass(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("toolbox_demos", ROOT / "tools" / "toolbox_demos.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        results = [{"demo": d.id, "passed": True} for d in demos.DEMOS if d.batch == 1]
        self.assertEqual(runner.claims(BOX, 1, results), [])
        results[[r["demo"] for r in results].index("bio-ecg")]["passed"] = False
        wrong = runner.claims(BOX, 1, results)
        self.assertTrue(any(w.startswith("neurokit2 is demo_proven") and "bio-ecg" in w for w in wrong), wrong)
        bridges = [t for tool in BOX.batch(1) for t in tool.proof.get("tests", []) if "--bridge" in t]
        for line in bridges:                                   # the bridge proof names a demo that exists
            demos.by_id(line.split("--bridge", 1)[1].strip())
        self.assertTrue(bridges)

    def test_demo_blocks_are_registered_in_the_web_bundle(self):
        registered = set()
        for path in (ROOT / "bie/brain/video/blocks/toolbox").glob("*.tsx"):
            registered |= set(re.findall(r'registerBlock\("([a-z0-9_]+)"', path.read_text(encoding="utf-8")))
        imported = set(re.findall(r'import "\./([a-z0-9]+)"', (ROOT / "bie/brain/video/blocks/toolbox/index.ts").read_text()))
        self.assertEqual(imported, {p.stem for p in (ROOT / "bie/brain/video/blocks/toolbox").glob("*.tsx")} - {"common"})
        used = set()
        work = demos.Work(folder=Path("."), library=None)
        for d in demos.DEMOS:
            source = Path(demos.__file__).read_text(encoding="utf-8")
            used |= set(re.findall(r'block\("([a-z0-9_]+)"', source))
        self.assertTrue(used <= registered, used - registered)

    def test_toolbox_specs_pick_the_toolbox_bundle(self):
        spec = demos.scene([demos.block("wave", {})], 4.0)
        self.assertTrue(render.needs_toolbox(spec))
        self.assertFalse(render.needs_toolbox({"scenes": [{"layers": [{"type": "title"}]}]}))
        self.assertEqual(spec["scenes"][0]["duration"], 120)

    def test_the_page_lists_families_blocked_and_missing(self):
        reg = edited(tool="katex", set={"status": "blocked_with_reason", "blocked_reason": "needs fonts"})
        text = page.render_markdown(registry.from_data(reg, CAPS), {"batch": 1, "demos": 1, "results": [
            {"demo": "maths-equation", "title": "t", "tools": ["sympy", "katex"], "seconds": 4.5, "passed": True}]})
        for words in ("## By subject family", "### Biology and medical", "**KaTeX**: needs fonts", "## Missing capabilities",
                      "orbit_motion", "maths-equation", "Z-Anatomy: CC BY-SA 4.0"):
            self.assertIn(words, text)

    def test_adapters_import_without_their_libraries(self):
        with mock.patch.dict(sys.modules, {"rdkit": None}):
            with self.assertRaises(base.Unavailable) as caught:
                base.need("rdkit")
        self.assertIn("toolbox-chem", str(caught.exception))
        self.assertEqual(base.clean([1.234567, float("nan"), {"a": float("inf")}]), [1.2346, None, {"a": None}])

    def test_blender_runs_in_its_own_process(self):
        from bie.toolbox.adapters import blender
        with mock.patch.dict(os.environ, {"BIE_BLENDER": "/opt/blender/blender"}):
            cmd = blender.command("cell_sheet.py", ["--out", "x.glb"])
        self.assertEqual(cmd[:4], ["/opt/blender/blender", "-b", "--factory-startup", "--python"])
        self.assertEqual(cmd[-3:], ["--", "--out", "x.glb"])


if __name__ == "__main__":
    unittest.main()
