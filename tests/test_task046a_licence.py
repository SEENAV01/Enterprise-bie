"""Task 046a-L: the licence policy and the lesson licence gate.

Navin, 25 October 2026: "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi."

Unit tests for every licence class, the policy file's own checks, the registry and page reading the policy, software
versus content (no GPL-family program inside apps/), and end-to-end cases through the real gathering points: the asset
library, the toolbox sources (fake network), the Scene IR asset resolution, the compiler's asset bundle, the resolver
and the demo marks. Offline, standard library only; runs in the toolbox lane.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.assets import AssetError, AssetLibrary, Candidate  # noqa: E402
from bie.toolbox import demos, licence, page, registry, resolver, sources  # noqa: E402
from tests.test_task046a_toolbox import Opener  # noqa: E402

BOX = registry.load()
POLICY = json.loads(licence.POLICY.read_text(encoding="utf-8"))
CC_BY_URL = "https://creativecommons.org/licenses/by/4.0/"


def library(folder) -> AssetLibrary:
    return AssetLibrary(Path(folder) / "assets")


def z_anatomy_model(lib: AssetLibrary):
    """A Z-Anatomy heart as ``sources.z_anatomy`` records it (the Blender export itself is a wrapper test)."""
    return lib.add_bytes(b"glTF fake heart", mime="model/gltf-binary", source="z_anatomy", title="CardioVascular41: heart",
                         page_url="https://github.com/LluisV/Z-Anatomy", licence="CC BY-SA 4.0",
                         licence_url="https://creativecommons.org/licenses/by-sa/4.0/", author="Z-Anatomy project (github.com/LluisV)",
                         credit="Z-Anatomy, CC BY-SA 4.0", tags=["anatomy", "share-alike"])


def commons_page(licence_name: str, *, artist="Ramesh Lalwani", licence_url=""):
    meta = {"LicenseShortName": {"value": licence_name}}
    if artist:
        meta["Artist"] = {"value": f"<a href='x'>{artist}</a>"}
    if licence_url:
        meta["LicenseUrl"] = {"value": licence_url}
    return {"query": {"pages": {"1": {"title": "File:Gandhiji Leading Salt satyagrah.jpg", "imageinfo": [{
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Salt.jpg",
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Gandhiji_Leading_Salt_satyagrah.jpg",
        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Salt.jpg/960px-Salt.jpg",
        "width": 2000, "height": 1400, "mime": "image/jpeg", "extmetadata": meta}]}}}}


class LicenceClasses(unittest.TestCase):
    """One verdict per licence class, read from licence_policy.json."""

    def verdict(self, text):
        v = licence.classify(text)
        return v.licence_class, v.verdict

    def test_cc0_public_domain_and_the_public_domain_mark_are_allowed(self):
        for text in ("CC0", "CC0 1.0", "Public domain", "Public Domain Mark 1.0", "PDM", "PD-USGov-NASA",
                     "Public domain (NASA, US government work; NASA Images and Media Usage Guidelines)"):
            self.assertEqual(self.verdict(text), ("public-domain", "allowed"), text)
        self.assertFalse(licence.classify("CC0").credit_required)

    def test_cc_by_every_version_is_allowed_with_a_credit(self):
        for text in ("CC BY 2.0", "CC BY 2.5", "CC BY 3.0", "CC BY 4.0", "CC-BY-4.0", "Attribution 4.0 International",
                     "Creative Commons Attribution 3.0", "CC BY 3.0 IGO", "CC BY 4.0 (releases up to 3.0 were CC BY-SA 2.1 Japan)"):
            self.assertEqual(self.verdict(text), ("cc-by", "allowed"), text)
            self.assertTrue(licence.classify(text).credit_required)

    def test_share_alike_non_commercial_and_no_derivatives_are_refused(self):
        for text, cls in (("CC BY-SA 4.0", "share-alike"), ("CC BY-SA 2.0", "share-alike"), ("Creative Commons Attribution-ShareAlike 3.0", "share-alike"),
                          ("GFDL", "share-alike"), ("ODbL", "share-alike"), ("CC BY-NC 2.0", "non-commercial"),
                          ("CC BY-NC-SA 4.0", "non-commercial"), ("CC BY-NC-ND 3.0", "non-commercial"), ("CC BY-ND 4.0", "no-derivatives"),
                          ("GPL-3.0", "copyleft-program")):
            self.assertEqual(self.verdict(text), (cls, "refused"), text)

    def test_missing_or_unreadable_licences_are_refused(self):
        for text in ("", None, "licensed", "No restrictions", "CC Sampling+", "rights:fig-3"):
            self.assertEqual(self.verdict(text), ("unknown", "refused"), text)

    def test_custom_terms_wait_for_navin(self):
        for text in ("Free for scientific use with citation (CDS); commercial use under ESA's rules", "Free to use with citation (Tozer et al., 2019)",
                     sources.INDIA_CODE_TERMS, "MIT"):
            self.assertEqual(self.verdict(text), ("own-terms", "needs_navin"), text)

    def test_nasa_items_are_checked_one_by_one(self):
        ok = {"asset_id": "a1", "title": "Earthrise", "source": "nasa_images", "licence": "Public domain (NASA, US government work)",
              "author": "NASA JSC", "page_url": "https://images.nasa.gov/details/as08-14-2383"}
        self.assertTrue(licence.asset_verdict(ok).allowed)
        third = dict(ok, licence="third-party copyright (© Some Agency): check before use")
        self.assertEqual(licence.asset_verdict(third).verdict, "refused")
        self.assertEqual(licence.asset_verdict(dict(ok, third_party=True)).verdict, "refused")
        self.assertEqual(licence.tool_verdict(BOX.tool("nasa-images")).verdict, "per_item")

    def test_fonts_and_bies_own_work_are_allowed_without_a_credit(self):
        self.assertEqual(self.verdict("SIL Open Font License 1.1"), ("font", "allowed"))
        self.assertEqual(self.verdict("BIE's own model (made by BIE code)"), ("own-work", "allowed"))
        own = {"asset_id": "a2", "source": "bie", "licence": "", "title": "drawing"}
        self.assertTrue(licence.asset_verdict(own).allowed)
        self.assertEqual(licence.lesson_credits([own]), [])


class Policy(unittest.TestCase):
    def test_the_policy_file_is_valid_and_records_navins_words(self):
        self.assertEqual(licence.policy_problems(POLICY), [])
        self.assertEqual(POLICY["decided"]["words"], "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul nahi.")
        self.assertEqual(POLICY["decided"]["date"], "2026-10-25")
        names = {s["id"] for s in POLICY["sources"]["needs_navin"]}
        self.assertTrue({"india-code", "hipparcos", "bodyparts3d", "gmt-earth-relief"} <= names)
        # Navin's yes of 29 October 2026: three sources approved by name, Hipparcos still waiting (ESA's terms)
        self.assertEqual({a["id"] for a in POLICY["sources"]["approved_by_navin"]}, {"india-code", "gmt-earth-relief", "bodyparts3d"})
        self.assertIsNone(POLICY["india_boundary"]["approved_boundary"])

    def test_a_policy_that_lets_share_alike_in_is_named(self):
        bad = json.loads(json.dumps(POLICY))
        next(c for c in bad["classes"] if c["id"] == "share-alike")["verdict"] = "allowed"
        self.assertTrue(any("may be allowed" in p for p in licence.policy_problems(bad)))
        bad = json.loads(json.dumps(POLICY))
        bad["unreadable"]["verdict"] = "allowed"
        self.assertTrue(any("unreadable" in p for p in licence.policy_problems(bad)))
        bad = json.loads(json.dumps(POLICY))
        bad["sources"]["approved_by_navin"] = [{"id": "hipparcos"}]
        self.assertTrue(any("approved source" in p for p in licence.policy_problems(bad)))

    def test_every_licence_decision_reads_the_policy(self):
        from bie.brain import assets
        for text in ("CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 2.0", "Public domain", ""):
            self.assertEqual(assets.licence_allowed(text), licence.allowed(text), text)
            self.assertEqual(assets.normalise_licence(text), licence.normalise(text), text)
        self.assertEqual(registry._licence_needs("CC BY-SA 4.0"), {"share_alike"})
        self.assertEqual([c["id"] for c, _ in licence._classes()], [c["id"] for c in POLICY["classes"]])   # read from the file


    def test_a_source_navin_approves_by_name_opens_with_a_credit(self):
        waiting = json.loads(json.dumps(POLICY))
        waiting["sources"]["approved_by_navin"] = []                                    # the policy before 29 October 2026
        self.assertEqual(licence.policy_problems(waiting), [])
        act = {"asset_id": "a3", "title": "BNSS (India Code)", "source": "india_code", "licence": sources.INDIA_CODE_TERMS,
               "licence_url": "https://indiacode.gov.in", "author": "Legislative Department", "page_url": "https://indiacode.gov.in/handle/1"}
        with mock.patch.object(licence, "policy", return_value=waiting):
            self.assertEqual(licence.asset_verdict(act).verdict, "needs_navin")         # without his yes: waits for Navin
        self.assertTrue(licence.asset_verdict(act).allowed)                             # today: approved by name on 29 October 2026
        self.assertIn("approved by Navin on 2026-10-29", licence.asset_verdict(act).reason)
        self.assertIn("missing: author", licence.asset_verdict(dict(act, author="")).reason)
        self.assertEqual(licence.tool_verdict(BOX.tool("india-code")).verdict, "allowed")
        self.assertEqual(licence.tool_verdict(BOX.tool("hipparcos")).verdict, "needs_navin")
        self.assertEqual(licence.registry_problems(BOX.tools), [])


class RegistryAndPage(unittest.TestCase):
    def test_registry_and_policy_agree(self):
        self.assertEqual(licence.registry_problems(BOX.tools), [])
        reg = json.loads(registry.REGISTRY.read_text(encoding="utf-8"))
        tool = next(t for t in reg["tools"] if t["id"] == "world-bank")
        tool["licence_flags"] = ["custom"]
        found = licence.registry_problems(reg["tools"])
        self.assertTrue(any("world-bank" in p and "not named in licence_policy.json" in p for p in found))
        tool = next(t for t in reg["tools"] if t["id"] == "hipparcos")
        tool["licence_flags"] = []
        self.assertTrue(any("hipparcos" in p for p in licence.registry_problems(reg["tools"])))

    def test_lesson_use_verdicts_of_tools_and_sources(self):
        v = {t.id: licence.tool_verdict(t) for t in BOX.tools}
        self.assertEqual(v["z-anatomy"].verdict, "refused")
        self.assertEqual(v["hipparcos"].verdict, "needs_navin")
        for tid in ("bodyparts3d", "india-code", "gmt-earth-relief"):                     # approved by Navin on 29 October 2026
            self.assertEqual((v[tid].verdict, v[tid].credit_required), ("allowed", True), tid)
        for tid in ("nasa-images", "wikimedia-commons", "openverse", "nih-3d", "pubchem"):
            self.assertEqual(v[tid].verdict, "per_item", tid)
        for tid in ("servier-medical-art", "rcsb-pdb", "world-bank", "sc-judgments", "usgs-earthquakes", "jpl-de421", "noto-devanagari"):
            self.assertEqual(v[tid].verdict, "allowed", tid)
        self.assertIn("India's political boundary", v["natural-earth-vector"].note)
        for tid in ("blender", "psychopy", "pygplates", "lcapy", "remotion"):
            self.assertEqual((v[tid].basis, v[tid].verdict), ("software", "allowed"), tid)
        self.assertIn("never ship inside apps/", v["psychopy"].note)
        self.assertIn("3 people", v["remotion"].note)

    def test_the_page_shows_lesson_use_instead_of_recorded_not_blocked(self):
        text = page.render_markdown(BOX, None)
        self.assertNotIn("Recorded, not blocked", text)
        self.assertIn("| Lesson use |", text)
        self.assertIn("## Lesson licence gate", text)
        self.assertIn(POLICY["decided"]["words"], text)
        self.assertIn("| [Z-Anatomy](", text)
        row = next(l for l in text.splitlines() if l.startswith("| [Z-Anatomy]("))
        self.assertIn("**refused**", row)
        row = next(l for l in text.splitlines() if l.startswith("| [Hipparcos"))
        self.assertIn("**needs Navin**", row)


class SoftwareIsNotContent(unittest.TestCase):
    def test_no_gpl_family_program_is_inside_apps(self):
        self.assertEqual(licence.apps_copyleft_problems(ROOT / "apps", BOX.tools), [])

    def test_every_gpl_flagged_tool_is_checked(self):
        checked = {t.id for t in licence.copyleft_programs(BOX.tools)}
        self.assertTrue({t.id for t in BOX.tools if "gpl" in t.licence_flags} <= checked)
        self.assertTrue({"blender", "psychopy", "pygplates", "lcapy", "obspy"} <= checked)

    def test_a_gpl_tool_in_an_apps_manifest_or_import_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            apps = Path(folder) / "apps"
            (apps / "web").mkdir(parents=True)
            (apps / "web" / "package.json").write_text(json.dumps({"dependencies": {"react": "19.2.0"}}), encoding="utf-8")
            (apps / "android" / "app").mkdir(parents=True)
            (apps / "android" / "app" / "build.gradle.kts").write_text('dependencies { implementation("androidx.core:core-ktx:1.13.1") }\n',
                                                                       encoding="utf-8")
            (apps / "operator").mkdir()
            (apps / "operator" / "worker.py").write_text("import json\n# psychopy is not imported here\n", encoding="utf-8")
            self.assertEqual(licence.apps_copyleft_problems(apps, BOX.tools), [])
            (apps / "operator" / "requirements.txt").write_text("numpy==2.3.4\npsychopy==2026.2.4\n", encoding="utf-8")
            (apps / "operator" / "experiment.py").write_text("from pygplates import RotationModel\n", encoding="utf-8")
            (apps / "web" / "scene.ts").write_text("import { run } from 'obspy-wasm';\n", encoding="utf-8")
            found = licence.apps_copyleft_problems(apps, BOX.tools)
            self.assertTrue(any("requirements.txt" in p and "psychopy" in p for p in found), found)
            self.assertTrue(any("experiment.py" in p and "pygplates" in p for p in found), found)
            self.assertFalse(any("scene.ts" in p for p in found))                # obspy-wasm is another package
            (apps / "android" / "app" / "build.gradle.kts").write_text('dependencies { implementation("org.blender:bpy:4.2") }\n', encoding="utf-8")
            self.assertTrue(any("build.gradle.kts" in p and "bpy" in p for p in licence.apps_copyleft_problems(apps, BOX.tools)))


class Gate(unittest.TestCase):
    """End to end through the real gathering points."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict(os.environ, {"BIE_ASSET_CACHE": str(Path(self.tmp.name) / "cache")})
        self.env.start()
        self.lib = library(self.tmp.name)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def scene_with(self, record):
        from bie.scene_ir.asset_contract import AssetRegistry, resolve_assets
        from bie.scene_ir.unified_scene_ir_contract import UnifiedElement, UnifiedSceneIRDocument
        element = UnifiedElement("heart", "model3d", {"asset_ref": record.asset_id}, ("src",), ("r",), {"alt": "heart"})
        doc = UnifiedSceneIRDocument("s", "1.0.0", "Heart", 10, (element,), (), ("src",), ("r",))
        reg = AssetRegistry()
        reg.register(record)
        return resolve_assets(doc, reg)

    def record_of(self, asset):
        from bie.scene_ir.asset_contract import AssetRecord
        fields = {k: getattr(asset, k) for k in ("title", "source", "licence", "licence_url", "author", "page_url", "tags")}
        return AssetRecord(asset.asset_id, "asset://" + asset.path, asset.sha256, "library:" + asset.asset_id, "model/gltf-binary",
                           True, "src", fields)

    def test_a_lesson_scene_with_a_z_anatomy_model_is_stopped(self):
        heart = z_anatomy_model(self.lib)
        problems = self.lib.lesson_check([heart.asset_id])
        self.assertEqual(len(problems), 1)
        self.assertIn("refused: share-alike licence", problems[0])
        with self.assertRaises(licence.LicenceError) as stop:
            self.lib.require_lesson([heart.asset_id], where="video v1")
        self.assertIn("video v1", str(stop.exception))
        receipt = self.scene_with(self.record_of(heart))                     # Scene IR: the scene does not pass
        self.assertFalse(receipt.passed)
        self.assertTrue(any(b.startswith("asset_licence:") and "share-alike" in b for b in receipt.blockers))
        self.assertEqual(receipt.credits, ())
        from bie.compiler.asset_bundler import bundle_assets                # the compiler packages nothing
        from bie.compiler.compiler_asset_common import CompilerAssetRecord
        rec = self.record_of(heart)
        out = Path(self.tmp.name) / "bundle"
        bundle = bundle_assets([CompilerAssetRecord(heart.asset_id, str(self.lib.folder / heart.path), heart.sha256, "model/gltf-binary",
                                                    rec.rights_basis, True, dict(rec.licence))], out)
        self.assertFalse(bundle.passed)
        self.assertEqual(bundle.bundled, ())
        self.assertEqual(list((out / "public" / "assets").iterdir()), [])
        self.assertEqual(demos.lesson_use(demos.by_id("bio-heart-zanatomy").tools)["use"], licence.INTERNAL_PROOF)

    def test_a_cc_by_sa_commons_image_is_refused(self):
        opener = Opener({"https://commons.wikimedia.org/w/api.php": commons_page("CC BY-SA 4.0", licence_url="https://creativecommons.org/licenses/by-sa/4.0")})
        with self.assertRaisesRegex(sources.SourceError, "refused for lessons: share-alike"):
            sources.commons_image("File:Gandhiji Leading Salt satyagrah.jpg", self.lib, opener=opener, width=960)
        self.assertFalse(any("upload.wikimedia.org" in u for u in opener.urls))        # the file itself was never downloaded
        cand = Candidate("wikimedia_commons", "File:X.jpg", "https://commons.wikimedia.org/wiki/File:X.jpg", "https://upload.wikimedia.org/x.jpg",
                         "", 10, 10, "image/jpeg", "CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0", "A", "A")
        with self.assertRaises(AssetError):
            self.lib.add_candidate(cand, data=b"x")

    def test_a_cc_by_commons_image_passes_and_appears_in_the_credits(self):
        opener = Opener({"https://commons.wikimedia.org/w/api.php": commons_page("CC BY 2.0", licence_url="https://creativecommons.org/licenses/by/2.0"),
                         "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Salt.jpg/960px-Salt.jpg": b"\xff\xd8\xffjpeg"})
        picture = sources.commons_image("File:Gandhiji Leading Salt satyagrah.jpg", self.lib, opener=opener, width=960)
        servier = self.lib.add_bytes(b"\x89PNG lung", mime="image/png", source="servier_medical_art", title="Bronchial tree",
                                     page_url="https://smart.servier.com", licence="CC BY 4.0", licence_url=CC_BY_URL,
                                     author="Servier Medical Art", credit="Servier Medical Art (smart.servier.com), CC BY 4.0")
        own = self.lib.add_bytes(b"glTF flange", mime="model/gltf-binary", source="bie_toolbox", title="Pipe flange", page_url="",
                                 licence="BIE's own model (made by BIE code)", licence_url="", author="BIE", credit="made by BIE with CadQuery")
        credits = self.lib.require_lesson([picture.asset_id, servier.asset_id, own.asset_id])
        self.assertEqual(credits, [
            "File:Gandhiji Leading Salt satyagrah.jpg · Ramesh Lalwani · CC BY 2.0 (https://creativecommons.org/licenses/by/2.0) · "
            "https://commons.wikimedia.org/wiki/File:Gandhiji_Leading_Salt_satyagrah.jpg",
            "Bronchial tree · Servier Medical Art · CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) · https://smart.servier.com"])
        receipt = self.scene_with(self.record_of(picture))                   # the same picture passes the Scene IR gate
        self.assertTrue(receipt.passed)
        self.assertEqual(receipt.credits, (credits[0],))

    def test_a_cc_by_asset_without_author_fails(self):
        nameless = self.lib.add_bytes(b"\x89PNG anon", mime="image/png", source="wikimedia_commons", title="File:Anon.png",
                                      page_url="https://commons.wikimedia.org/wiki/File:Anon.png", licence="CC BY 4.0", licence_url=CC_BY_URL,
                                      author="", credit="")
        problems = self.lib.lesson_check([nameless.asset_id])
        self.assertEqual(problems, [f"{nameless.asset_id} (File:Anon.png): refused: CC BY needs a credit; missing: author"])
        no_url = self.lib.add_bytes(b"\x89PNG anon2", mime="image/png", source="wikimedia_commons", title="File:Anon2.png", page_url="",
                                    licence="CC BY 4.0", licence_url="", author="Someone", credit="")
        self.assertIn("missing: licence_url, page_url", self.lib.lesson_check([no_url.asset_id])[0])
        opener = Opener({"https://commons.wikimedia.org/w/api.php": commons_page("CC BY 4.0", artist="", licence_url=CC_BY_URL)})
        with self.assertRaisesRegex(sources.SourceError, "missing: author"):
            sources.commons_image("File:Gandhiji Leading Salt satyagrah.jpg", self.lib, opener=opener, width=960)

    def test_an_india_boundary_map_is_stopped(self):
        spec = {"scenes": [{"id": "s1", "layers": [{"type": "block", "block": "india_map", "data": {}}]}]}
        problems = licence.lesson_spec_check(spec)
        self.assertEqual(len(problems), 1)
        self.assertIn("needs Navin", problems[0])
        self.assertIn("Survey of India", problems[0])
        self.assertEqual(licence.lesson_spec_check({"scenes": [{"id": "s1", "layers": [{"type": "block", "block": "world_points"}]}]}), [])
        tagged = self.lib.add_bytes(b"{}", mime="application/json", source="natural_earth_vector", title="India states",
                                    page_url="https://www.naturalearthdata.com", licence="Public domain (Natural Earth)", licence_url="",
                                    author="Natural Earth", credit="", tags=["map", "india-boundary"])
        self.assertIn("needs Navin", self.lib.lesson_check([tagged.asset_id])[0])
        self.assertEqual(demos.lesson_use(demos.by_id("geo-india-state").tools, blocks=["india_map"])["use"], licence.INTERNAL_PROOF)
        self.assertEqual(demos.lesson_use(demos.by_id("geo-quake-map").tools, blocks=["world_points"])["use"], "lessons")

    def test_needs_navin_sources_stop_a_lesson_and_approved_ones_need_their_credit(self):
        stars = self.lib.add_bytes(b"hip", mime="text/plain", source="hipparcos", title="Hipparcos stars",
                                   page_url="https://cdsarc.cds.unistra.fr/viz-bin/cat/I/239", licence="scientific use with citation",
                                   licence_url="", author="ESA", credit="")
        law = self.lib.add_bytes(b'{"title": "BNSS"}', mime="application/json", source="india_code", title="BNSS (India Code)",
                                 page_url="https://indiacode.gov.in/handle/1", licence=sources.INDIA_CODE_TERMS, licence_url="https://indiacode.gov.in",
                                 author="Legislative Department", credit="India Code: BNSS")
        relief = self.lib.add_bytes(b"\x89PNG relief", mime="image/png", source="pygmt", title="Himalaya relief",       # an earlier receipt's name
                                    page_url="https://www.generic-mapping-tools.org/remote-datasets/", licence="free to use with citation",
                                    licence_url="", author="BIE with PyGMT", credit="")
        problems = self.lib.lesson_check([stars.asset_id, law.asset_id, relief.asset_id])
        self.assertEqual(len(problems), 2)
        self.assertIn("needs Navin", problems[0])                       # Hipparcos: ESA's terms unchecked
        self.assertIn("hipparcos", problems[0])
        self.assertIn("gmt-earth-relief", problems[1])                  # approved on 29 October 2026, but the citation (licence_url) is missing
        self.assertIn("missing: licence_url", problems[1])

    def test_an_asset_the_library_does_not_hold_cannot_pass(self):
        self.assertIn("not in the asset library", self.lib.lesson_check(["a-0000000000000000"])[0])

    def test_the_resolver_logs_a_gap_when_only_refused_sources_provide(self):
        waiting = json.loads(json.dumps(POLICY))
        waiting["sources"]["approved_by_navin"] = []                      # the policy before Navin's yes of 29 October 2026
        with tempfile.TemporaryDirectory() as folder:
            log = resolver.MissingLog(Path(folder) / "missing.jsonl")
            with mock.patch.object(licence, "policy", return_value=waiting):
                relief = resolver.resolve("terrain_or_layers", subject="earth_science", log=log)
                self.assertEqual(relief.assets, [])
                self.assertEqual([h["tool"] for h in relief.not_for_lessons], ["gmt-earth-relief"])
                self.assertIn("BIE draws it itself", relief.fallback)
                anatomy = resolver.resolve("anatomy_3d", subject="biology_medical", log=log)
                self.assertNotIn("z-anatomy", anatomy.assets)
                self.assertNotIn("bodyparts3d", anatomy.assets)
                self.assertIn("nih-3d", anatomy.assets)
                self.assertEqual(anatomy.licence_gap, "")
                rows = log.rows()
                self.assertEqual([r["capability"] for r in rows], ["terrain_or_layers"])
                self.assertIn("missing lesson-allowed source", rows[0]["reason"])
            # after his yes: the relief and BodyParts3D are lesson sources with their credit; Z-Anatomy stays out
            relief = resolver.resolve("terrain_or_layers", subject="earth_science", log=log)
            self.assertEqual(relief.assets, ["gmt-earth-relief"])
            anatomy = resolver.resolve("anatomy_3d", subject="biology_medical", log=log)
            self.assertIn("bodyparts3d", anatomy.assets)
            self.assertNotIn("z-anatomy", anatomy.assets)
            self.assertEqual(len(log.rows()), 1)

    def test_a_game_picture_without_a_library_record_stops_the_game(self):
        from bie.brain.game_build import game_pictures
        heart = z_anatomy_model(self.lib)
        game = {"missions": [{"mission_id": "m1", "stages": [{"background": {"src": "https://example.org/heart.png"}}]}]}
        ids, problems = game_pictures(game, self.lib)
        self.assertEqual(ids, [])
        self.assertIn("has no asset-library record", problems[0])
        game["missions"][0]["stages"][0]["background"] = {"src": "assets/" + heart.path, "asset_id": heart.asset_id}
        self.assertIn("share-alike", game_pictures(game, self.lib)[1][0])

    def test_proof_clips_with_refused_or_needs_navin_content_are_internal_proofs(self):
        marked = {d.id for d in demos.DEMOS if demos.lesson_use(d.tools)["use"] == licence.INTERNAL_PROOF}
        # 29 October 2026: BodyParts3D, the SRTM15+ relief and India Code are approved by Navin, the sky demo reads the Yale catalogue
        self.assertEqual(marked, {"bio-heart-zanatomy", "psy-brain-lobes"})   # the two India maps are caught by their block
        use = demos.lesson_use(demos.by_id("bio-organ-zoom").tools, [{"source": "servier_medical_art", "licence": "CC BY 4.0",
                                                                       "title": "lung", "id": "a"}])
        self.assertEqual(use, {"use": "lessons", "reasons": []})


if __name__ == "__main__":
    unittest.main()
