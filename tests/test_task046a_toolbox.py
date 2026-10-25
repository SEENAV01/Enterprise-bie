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
            (edited(tool="sympy", set={"proof": {"tests": ["tests/toolbox/test_wrappers.py::Nothing"]}}), "proof test"),
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
        self.assertEqual(set(marked), {"z-anatomy", "blender", "pygplates", "psychopy"})
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
        workflow = (ROOT / ".github/workflows/toolbox.yml").read_text(encoding="utf-8")
        for tid, version in base.NO_DEPS.items():                    # pinned in the lane's own --no-deps line
            dist = base.PYTHON_TOOLS[tid][1]
            self.assertEqual(BOX.tool(tid).version, version, tid)
            self.assertIn(f"--no-deps --ignore-requires-python {dist}=={version}", workflow)
        for tid, (_, dist, group) in base.PYTHON_TOOLS.items():
            if tid in base.NO_DEPS:
                continue
            self.assertIn(dist.lower(), pins, f"{dist} needs a pin in pyproject extras")    # PyPI names ignore case
            self.assertEqual(pins[dist.lower()], (group, BOX.tool(tid).version), tid)
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

        def fbx_part(fbx, match, out, exclude="", **kw):
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

    def test_usgs_quakes_rows_and_public_domain_credit(self):
        quake = {"type": "Feature", "properties": {"mag": 7.1, "place": "Southern Tibetan Plateau", "time": 1736211916734},
                 "geometry": {"type": "Point", "coordinates": [87.38, 28.60, 10.0]}}
        opener = Opener({"https://earthquake.usgs.gov/fdsnws/event/1/query": {"type": "FeatureCollection", "features": [quake]}})
        asset, rows = sources.usgs_quakes("2025-01-01", "2025-12-31", self.lib, magnitude=6.0, opener=opener)
        self.assertEqual(rows, [{"lon": 87.38, "lat": 28.6, "depth_km": 10.0, "magnitude": 7.1, "time_ms": 1736211916734,
                                 "place": "Southern Tibetan Plateau"}])
        self.assertEqual((asset.licence, asset.mime), ("Public domain (USGS)", "application/json"))
        self.assertIn("minmagnitude=6.0", opener.urls[0])
        with self.assertRaises(sources.SourceError):
            sources.usgs_quakes("2025-01-01&x=1", "2025-12-31", self.lib, opener=opener)

    def test_gplates_model_unpacks_only_its_two_files(self):
        def archive(member: str, body: bytes) -> bytes:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                z.writestr(member, body)
                z.writestr("../../outside.txt", b"never written")
            return buf.getvalue()
        spec = sources.GPLATES_MODELS["muller2019"]
        opener = Opener({spec["base"] + "Rotations.zip": archive(spec["rotations"][1], b"101 0.0 90 0 0 000 !x\n"),
                         spec["base"] + "Coastlines.zip": archive(spec["coastlines"][1], b"gpmlz")})
        with mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")}):
            model = sources.gplates_model("muller2019", opener=opener)
            again = sources.gplates_model("muller2019", opener=opener)
            self.assertEqual(model["rotations"].read_bytes(), b"101 0.0 90 0 0 000 !x\n")
            self.assertEqual((model["licence"], again["coastlines"]), ("CC BY 4.0", model["coastlines"]))
            self.assertEqual(len(opener.urls), 2)                          # fetched once, then read from the cache
            self.assertFalse((Path(self.tmp.name) / "outside.txt").exists())
        with self.assertRaises(sources.SourceError):
            sources.gplates_model("unknown")

    def test_nasa_image_takes_the_size_asked_for_and_marks_third_party_rights(self):
        meta = {"collection": {"items": [{"data": [{"title": "Earthrise", "center": "JSC", "description": "Apollo 8"}]}]}}
        files = {"collection": {"items": [{"href": "http://images-assets.nasa.gov/image/as08-14-2383/as08-14-2383~orig.jpg"},
                                          {"href": "http://images-assets.nasa.gov/image/as08-14-2383/as08-14-2383~medium.jpg"}]}}
        opener = Opener({"https://images-api.nasa.gov/search": meta, "https://images-api.nasa.gov/asset/": files,
                         "https://images-assets.nasa.gov/image/as08-14-2383/as08-14-2383~medium.jpg": b"\xff\xd8\xffjpeg"})
        asset = sources.nasa_image("as08-14-2383", self.lib, size="medium", opener=opener)
        self.assertEqual((asset.title, asset.credit), ("Earthrise", "NASA/JSC (as08-14-2383)"))
        self.assertIn("not copyrighted", asset.licence)
        meta["collection"]["items"][0]["data"][0]["secondary_creator"] = "© Some Agency"
        opener.routes["https://images-assets.nasa.gov/image/as08-14-2383/as08-14-2383~medium.jpg"] = b"\xff\xd8\xffother"
        other = sources.nasa_image("as08-14-2383", self.lib, size="medium", opener=opener)
        self.assertIn("third-party copyright", other.licence)
        with self.assertRaises(sources.SourceError):
            sources.nasa_image("../x", self.lib, opener=opener)

    def test_big_downloads_stay_in_the_cache_outside_git(self):
        with mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")}):
            opener = Opener({"https://example.org/big.zip": b"x" * 100})
            path = sources.cached("https://example.org/big.zip", "big.zip", opener=opener)
            sources.cached("https://example.org/big.zip", "big.zip", opener=opener)
            self.assertEqual(len(opener.urls), 1)
            self.assertFalse(str(path).startswith(str(ROOT)))
        with self.assertRaises(sources.SourceError):
            sources.fetch("http://insecure.example/x")


class BatchThreeSources(unittest.TestCase):
    """Task 046a batch 3: maps, World Bank, India Code, Commons, Openverse, the script font and the Indic NLP tables."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.lib = AssetLibrary(Path(self.tmp.name) / "lib")
        self.env = mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_pinned_files_must_match_their_hash(self):
        import hashlib
        body = b'{"type": "FeatureCollection", "features": []}'
        name = "ne_10m_populated_places_simple"
        with mock.patch.dict(sources.NATURAL_EARTH_FILES, {name: hashlib.sha256(body).hexdigest()}):
            opener = Opener({sources.NATURAL_EARTH.format(name=name): body})
            path = sources.natural_earth(name, opener=opener)
            self.assertEqual(path.read_bytes(), body)
            sources.natural_earth(name, opener=opener)
            self.assertEqual(len(opener.urls), 1)
        name = "ne_10m_admin_1_states_provinces"
        with self.assertRaises(sources.SourceError):
            sources.natural_earth(name, opener=Opener({sources.NATURAL_EARTH.format(name=name): b"changed upstream"}))
        self.assertFalse((sources.cache_dir() / f"natural-earth-5.1.2-{name}.geojson").exists())     # a wrong file is not kept
        with self.assertRaises(sources.SourceError):
            sources.natural_earth("../../secrets")

    def test_world_bank_rows_and_credit(self):
        body = [{"page": 1}, [{"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth (annual %)"}, "country": {"id": "IN", "value": "India"},
                                "countryiso3code": "IND", "date": "2021", "value": 9.69},
                               {"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth (annual %)"}, "country": {"id": "IN", "value": "India"},
                                "countryiso3code": "IND", "date": "2020", "value": -5.78},
                               {"indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth (annual %)"}, "country": {"id": "IN", "value": "India"},
                                "countryiso3code": "IND", "date": "2025", "value": None}]]
        opener = Opener({"https://api.worldbank.org/v2/country/IND/indicator/NY.GDP.MKTP.KD.ZG": body})
        asset, rows, meta = sources.world_bank("NY.GDP.MKTP.KD.ZG", ["ind"], 2020, 2025, self.lib, opener=opener)
        self.assertEqual([(r["year"], r["value"]) for r in rows], [(2020, -5.78), (2021, 9.69)])     # sorted, empty years left out
        self.assertEqual((asset.licence, meta["name"]), ("CC BY 4.0", "GDP growth (annual %)"))
        self.assertIn("date=2020:2025", opener.urls[0])
        for bad in (("NY.GDP;rm", ["IND"]), ("NY.GDP.MKTP.KD.ZG", ["IND&x=1"])):
            with self.assertRaises(sources.SourceError):
                sources.world_bank(bad[0], bad[1], 2000, 2001, self.lib, opener=opener)

    def test_india_code_act_reads_every_section_once_and_keeps_it(self):
        def item(name, **md):
            return {"_embedded": {"indexableObject": {"name": name, "handle": "123456789/496550",
                                                       "metadata": {k: [{"value": v}] for k, v in md.items()}}}}

        def page(objects, number, total):
            return {"_embedded": {"searchResult": {"_embedded": {"objects": objects}, "page": {"number": number, "totalPages": total}}}}
        act = page([item("The Test Sanhita, 2023", **{"dc.identifier.act_number": "46", "dc.date.act_year": "2023"})], 0, 1)
        sec = lambda n, t: item(t, **{"dc.identifier.section_number": n, "dc.identifier.section_page_note": "<span>(1) Text of " + n + "</span>"})
        calls = []

        def opener(request, timeout=None):
            url = request.full_url
            calls.append(url)
            if "collection%3AACT" in url:
                return FakeResponse(json.dumps(act).encode())
            body = page([sec("173", "Information in cognizable cases."), sec("2", "Definitions.")], 0, 2) if "page=0" in url else \
                page([sec("10", "Courts.")], 1, 2)
            return FakeResponse(json.dumps(body).encode())
        asset, data = sources.india_code_act("AC_CEN_5_23_00049_202346_1719552320687", self.lib, opener=opener)
        self.assertEqual([s["number"] for s in data["sections"]], ["2", "10", "173"])          # numeric order
        self.assertEqual(data["sections"][2]["text"], "(1) Text of 173")
        self.assertTrue(all("sort=dc.title%2CASC" in u for u in calls[1:]))                     # India Code pages stably only when sorted
        n = len(calls)
        sources.india_code_act("AC_CEN_5_23_00049_202346_1719552320687", self.lib, opener=opener)
        self.assertEqual(len(calls), n)                                                         # kept in the cache
        self.assertIn("52(1)(q)", asset.licence)
        with self.assertRaises(sources.SourceError):
            sources.india_code_act("x OR 1=1", self.lib, opener=opener)

    def test_commons_and_openverse_keep_share_alike_marked_and_refuse_non_commercial(self):
        commons = {"query": {"pages": {"1": {"title": "File:Marche sel.jpg", "imageinfo": [{
            "url": "https://upload.wikimedia.org/wikipedia/commons/4/4b/Marche_sel.jpg", "descriptionurl": "https://commons.wikimedia.org/wiki/File:Marche_sel.jpg",
            "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Marche_sel.jpg/1280px-Marche_sel.jpg?utm_source=commons.wikimedia.org&utm_content=thumbnail",
            "width": 2000, "height": 1500,
            "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "Public domain"}, "Artist": {"value": "<a>Unknown</a>"}}}]}}}}
        opener = Opener({"https://commons.wikimedia.org/w/api.php": commons,
                         "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Marche_sel.jpg/1280px-Marche_sel.jpg": b"\xff\xd8\xffjpeg"})
        old = sources.commons_image("File:Marche sel.jpg", self.lib, opener=opener, width=1280)
        self.assertEqual((old.licence, old.mime, old.source, old.author), ("Public domain", "image/jpeg", "wikimedia_commons", "Unknown"))
        self.assertIn("iiurlwidth=1280", opener.urls[0])               # a standard Wikimedia thumbnail width, below the original's 2000
        row = {"id": "bafa11dc-b447-4e43-804c-c3f8f3eca309", "title": "Dandi salt march", "creator": "Nagarjun", "license": "by-sa",
               "license_version": "2.0", "foreign_landing_url": "https://www.flickr.com/photos/x/1", "attribution": '"Dandi salt march" by Nagarjun'}
        opener = Opener({"https://api.openverse.org/v1/images/bafa11dc-b447-4e43-804c-c3f8f3eca309/thumb/": b"\xff\xd8\xffdiorama",
                         "https://api.openverse.org/v1/images/bafa11dc-b447-4e43-804c-c3f8f3eca309/": row})
        new = sources.openverse_image("bafa11dc-b447-4e43-804c-c3f8f3eca309", self.lib, opener=opener)
        self.assertEqual((new.licence, new.page_url), ("CC BY-SA 2.0", "https://www.flickr.com/photos/x/1"))
        self.assertIn("share-alike", new.tags)
        n = len(opener.urls)
        sources.openverse_image("bafa11dc-b447-4e43-804c-c3f8f3eca309", self.lib, opener=opener)
        self.assertEqual(len(opener.urls), n)                                     # the record and the file are kept in the cache
        import shutil
        shutil.rmtree(sources.cache_dir() / "open-images")
        row["license"] = "by-nc"
        with self.assertRaises(sources.SourceError):
            sources.openverse_image("bafa11dc-b447-4e43-804c-c3f8f3eca309", self.lib, opener=opener)
        with self.assertRaises(Exception):
            sources.openverse_image("../../x", self.lib, opener=opener)

    def test_commons_asks_for_a_standard_width_smaller_than_the_original(self):
        from bie.brain import assets
        def reply(width):
            thumb = f"https://upload.wikimedia.org/x/{width}px-A.jpg" if width < 1200 else "https://upload.wikimedia.org/x/A.jpg?utm_content=thumbnail_unscaled"
            return {"query": {"pages": {"1": {"title": "File:A.jpg", "imageinfo": [{"url": "https://upload.wikimedia.org/x/A.jpg", "thumburl": thumb,
                    "width": 1200, "height": 800, "mime": "image/jpeg", "extmetadata": {"LicenseShortName": {"value": "CC BY 2.0"}}}]}}}}
        urls = []

        def opener(request, timeout=None):
            urls.append(request.full_url)
            width = int(re.search(r"iiurlwidth=(\d+)", request.full_url).group(1))
            return FakeResponse(json.dumps(reply(width)).encode())
        candidate = assets.commons_file("File:A.jpg", thumb_width=1500, opener=opener)
        self.assertEqual([re.search(r"iiurlwidth=(\d+)", u).group(1) for u in urls], ["1280", "960"])   # 1280 >= the original 1200
        self.assertEqual(candidate.file_url, "https://upload.wikimedia.org/x/960px-A.jpg")

    def test_a_refusing_api_is_named_not_read_as_a_missing_file(self):
        from bie.brain import assets
        opener = Opener({"https://commons.wikimedia.org/w/api.php": {"error": {"code": "ratelimited", "info": "slow down"}}})
        with self.assertRaises(assets.AssetError) as err:
            assets.commons_file("File:Marche sel.jpg", opener=opener)
        self.assertIn("ratelimited", str(err.exception))

    def test_a_busy_server_is_asked_again_after_its_wait(self):
        import urllib.error
        from bie.brain import assets
        answers = [urllib.error.HTTPError("https://commons.wikimedia.org/w/api.php", 429, "Too Many Requests", {"retry-after": "2"}, None),
                   FakeResponse(b"ok")]

        def opener(request, timeout=None):
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer
        with mock.patch("time.sleep") as slept:
            self.assertEqual(assets._open("https://commons.wikimedia.org/w/api.php?x=1", opener=opener), b"ok")
        slept.assert_called_once_with(2.0)

    def test_font_and_indic_tables_are_pinned(self):
        import hashlib
        body = b"\x00\x01\x00\x00font"
        with mock.patch.dict(sources.NOTO_DEVANAGARI, {"sha256": hashlib.sha256(body).hexdigest()}):
            font = sources.noto_devanagari(self.lib, opener=Opener({sources.NOTO_DEVANAGARI["url"]: body}))
        self.assertEqual((font.mime, font.licence, font.path.endswith(".ttf")), ("font/ttf", "SIL Open Font License 1.1", True))
        tables = {rel: f"table {rel}".encode() for rel in sources.INDIC_NLP_RESOURCES["files"]}
        pins = {rel: hashlib.sha256(b).hexdigest() for rel, b in tables.items()}
        with mock.patch.dict(sources.INDIC_NLP_RESOURCES, {"files": pins}):
            root = sources.indic_nlp_resources(opener=Opener({sources.INDIC_NLP_RESOURCES["base"] + rel: b for rel, b in tables.items()}))
        self.assertEqual((root / "script" / "all_script_phonetic_data.csv").read_bytes(), tables["script/all_script_phonetic_data.csv"])


class ExamMap(unittest.TestCase):
    def test_every_ugc_net_subject_and_gate_paper_is_mapped(self):
        from bie.toolbox import exams
        data = exams.load()
        codes = [e["code"] for e in data["ugc_net"]]
        self.assertEqual((len(codes) - 1, len(data["gate"])), (86, 30))                # the official lists of 25 October 2026, plus Paper I
        self.assertEqual(codes[0], "00")
        self.assertIn("XH", [e["code"] for e in data["gate"]])
        cov = exams.coverage()
        self.assertEqual(cov["totals"]["without_a_tool"], [])                        # every subject has at least one usable tool
        law = next(r for r in cov["ugc_net"] if r["code"] == "58")
        self.assertIn("case_card", law["capabilities"])

    def test_bad_entries_are_named(self):
        from bie.toolbox import exams
        bad = json.loads(exams.EXAM_MAP.read_text(encoding="utf-8"))
        bad["gate"].append(dict(bad["gate"][0]))
        bad["ugc_net"][1]["families"] = ["astrology"]
        bad["ugc_net"][2]["fit"] = "partial"
        bad["ugc_net"][2]["gap"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "exam_map.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            with mock.patch.object(exams, "EXAM_MAP", path), self.assertRaises(exams.ExamMapError) as err:
                exams.load()
        text = str(err.exception)
        for want in ("listed 2 times", "unknown family 'astrology'", "needs the gap named"):
            self.assertIn(want, text)


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

    def test_every_tool_has_a_demo_or_a_test_in_its_own_batch(self):
        # the demos lane checks each batch's claims against that batch's clips, so a proof demo must be in the tool's batch
        for batch in (1, 2, 3):
            covered = {t for d in demos.DEMOS if d.batch == batch for t in d.tools}
            for tool in BOX.batch(batch):
                if tool.status == "blocked_with_reason":
                    continue
                proof = tool.proof
                self.assertTrue(tool.id in covered or proof.get("tests"), f"{tool.id} has no demo and no test")
                for demo_id in proof.get("demos", []):
                    self.assertIn(tool.id, demos.by_id(demo_id).tools, (tool.id, demo_id))
                    self.assertEqual(demos.by_id(demo_id).batch, batch, (tool.id, demo_id))

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

    def test_the_relief_download_is_asked_again_when_gmts_server_is_unreachable(self):
        from bie.toolbox.adapters import earth
        calls, waits = [], []

        class Datasets:
            def __init__(self, failures):
                self.failures = list(failures)

            def load_earth_relief(self, **kwargs):
                calls.append(kwargs)
                if self.failures:
                    raise RuntimeError(self.failures.pop(0))
                return "grid"

        fake = type("PyGMT", (), {})()
        fake.datasets = Datasets(["gmtread [ERROR]: Remote download is currently deactivated\nmore"])
        self.assertEqual(earth.load_relief(fake, resolution="02m", region=(70, 100, 20, 40), sleep=waits.append), "grid")
        self.assertEqual((len(calls), waits), (2, [20.0]))
        self.assertEqual(calls[0]["region"], [70, 100, 20, 40])
        fake.datasets = Datasets(["Unable to obtain remote file @earth_relief_02m_g"] * 3)
        with self.assertRaisesRegex(RuntimeError, "could not be reached in 3 attempts"):
            earth.load_relief(fake, resolution="02m", region=(70, 100, 20, 40), sleep=waits.append)
        self.assertEqual(waits, [20.0, 20.0, 40.0])
        fake.datasets = Datasets(["grid region out of range"])            # any other error is not asked again
        with self.assertRaisesRegex(RuntimeError, "out of range"):
            earth.load_relief(fake, resolution="02m", region=(70, 100, 20, 40), sleep=waits.append)
        self.assertEqual(len(waits), 3)

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
