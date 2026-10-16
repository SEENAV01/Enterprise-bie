"""M1 strict admission/legacy/selector controls; no rendered PASS inferred."""
from copy import deepcopy
from dataclasses import replace
import time
import unittest
from bie.compiler import governed_motion as gm
from bie.compiler.animation_behavior import motion_contract, motion_state, frame_window
from bie.compiler.animation_track_compiler import compile_animation_track
from bie.compiler.reduced_motion import resolve_reduced_motion
from bie.compiler.qa_scene_compile import native_qa_capabilities, compile_scene_for_qa
from tests.compiler.m1_support import prepared, admitted, TARGET
from tests.compiler.h2_test_support import track


class ProducerMotionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture, cls.cases = prepared()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    def context(self, family="cellular"):
        return admitted(self.fixture, self.cases[family])

    def setUp(self):
        # Fresh bounded test authorization per independent case. No production
        # expiry policy or child/process budget is changed by a long unit suite.
        self.fixture.p = replace(self.fixture.p, expires_at=time.time()+900)
        self.fixture.credentials.grant(self.fixture.token, self.fixture.p)

    def test_actual_three_families_and_reduced_request_are_admitted(self):
        for family in self.cases:
            with self.subTest(family=family), self.context(family) as (raw, bound, _):
                self.assertEqual(gm.validate_document(raw, TARGET), gm.PROFILE)
                self.assertEqual(len(bound["tracks"]), 1 if family == "quantitative" else 2)
                self.assertFalse(bound["upstream"]["plan"]["accepted"])
                if family.endswith("reduced"):
                    self.assertTrue(bound["upstream"]["plan"]["reduced_motion_requested"])

    def test_all_22_fields_have_verified_reconstructible_mapping(self):
        union = set()
        for family in self.cases:
            with self.context(family) as (raw, bound, _):
                original = {n["track_id"]: n for n in bound["upstream"]["handoff"]["nodes"]}
                for t in raw["tracks"]:
                    p = motion_contract(t).parameters
                    self.assertEqual(p["original"], original[t["track_id"]])
                    self.assertEqual(set(p["mapping"]), set(p["original"]["parameters"]))
                    union.update(p["mapping"])
        self.assertEqual(len(union), 22)

    def test_explicit_standard_and_reduced_same_semantics_not_receipt(self):
        for family in self.cases:
            with self.context(family) as (raw, _, _):
                original = deepcopy(raw)
                standard, sr = resolve_reduced_motion(raw, TARGET, "standard")
                reduced, rr = resolve_reduced_motion(raw, TARGET, "reduced")
                self.assertEqual(standard["tracks"], reduced["tracks"])
                self.assertEqual(raw, original)
                self.assertNotIn("producer_motion_v1", sr)
                self.assertEqual(len(rr["producer_motion_v1"]), len(raw["tracks"]))
                self.assertEqual(rr["learning_equivalence"], "NOT_EVALUATED")
                self.assertFalse(rr["accepted"])

    def test_full_frame_schedule_no_geometry_or_flash(self):
        for family in self.cases:
            with self.context(family) as (raw, _, _):
                frames = (raw["duration_ms"] * TARGET.fps + 999) // 1000
                for t in raw["tracks"]:
                    c = motion_contract(t)
                    states = [motion_state(c, f, TARGET.fps) for f in range(frames)]
                    key = ("series_opacity" if c.parameters["binding"]["element_type"] == "chart" else "opacity") if c.action == "reveal" else "focus_opacity"
                    self.assertTrue(all(set(s) == {key} for s in states))
                    values = [next(iter(s.values())) for s in states]
                    self.assertTrue(all(0 <= v <= 1 for v in values))
                    a, b = frame_window(c, TARGET.fps)
                    self.assertEqual(values[a], 0)
                    if c.action == "reveal":
                        self.assertEqual(values[b], 1)
                        self.assertEqual(values, sorted(values))
                    else:
                        self.assertGreater(max(values), .8)
                        self.assertEqual(values[b], 0)
                        self.assertTrue(all(v == 0 for v in values[:a] + values[b+1:]))

    def test_outside_authorized_context_rejected(self):
        with self.context() as (raw, _, _):
            t = deepcopy(raw["tracks"][0])
        with self.assertRaisesRegex(ValueError, "CURRENT_ADMISSION_REQUIRED"):
            motion_contract(t)

    def test_every_original_field_mutation_or_deletion_rejected(self):
        for family in ("quantitative", "cellular"):
            with self.context(family) as (raw, _, _):
                for field in raw["tracks"][0]["parameters"]["original"]["parameters"]:
                    for deletion in (False, True):
                        with self.subTest(field=field, deletion=deletion):
                            t = deepcopy(raw["tracks"][0]); p = t["parameters"]
                            if deletion: del p["original"]["parameters"][field]
                            else: p["original"]["parameters"][field] = "counterfeit"
                            p["original_sha256"] = gm.digest(p["original"])
                            p["mapping"] = gm.mapping_for(p["original"]["parameters"])
                            with self.assertRaises(ValueError): motion_contract(t)

    def test_unknown_version_profile_extra_field_and_safe_claim_rejected(self):
        with self.context() as (raw, _, _):
            for key, value in (("schema_version", "unknown"), ("profile", "web"),
                ("reduced_safe", True), ("scale_allowed", False), ("accepted", True),
                ("variant", "static_focus"), ("policy", "unknown")):
                with self.subTest(key=key):
                    t = deepcopy(raw["tracks"][0]); t["parameters"][key] = value
                    with self.assertRaises(ValueError): motion_contract(t)

    def test_target_time_refs_action_and_track_identity_rejected(self):
        with self.context() as (raw, _, _):
            for key, value in (("element_id", "foreign"), ("track_id", "foreign"),
                ("start_ms", True), ("end_ms", 99999), ("source_refs", ["foreign"]),
                ("reasoning_refs", ["foreign"]), ("action", "transform")):
                t = deepcopy(raw["tracks"][0]); t[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): motion_contract(t)

    def test_infinite_nan_and_nested_unknown_rejected(self):
        with self.context() as (raw, _, _):
            for value in (float("nan"), float("inf"), True, {"unknown": 1}):
                t = deepcopy(raw["tracks"][0]); t["parameters"]["original"]["parameters"]["uncertainty"] = value
                with self.assertRaises(ValueError): motion_contract(t)

    def test_variant_required_even_for_identical_safe_motion(self):
        with self.context() as (raw, _, _):
            raw["metadata"]["compiler_h3"]["reduced_motion_variants"] = {}
            with self.assertRaisesRegex(ValueError, "UNRESOLVED"): resolve_reduced_motion(raw, TARGET, "reduced")

    def test_missing_extra_or_foreign_replacements_block(self):
        with self.context() as (original, _, _):
            for mode in ("missing", "extra", "foreign"):
                raw = deepcopy(original)
                v = next(iter(raw["metadata"]["compiler_h3"]["reduced_motion_variants"].values()))
                if mode == "missing": v["track_replacements"] = {}
                elif mode == "extra": v["track_replacements"]["foreign"] = {"action": "emphasize", "parameters": {}}
                else: v["source_refs"] = ["foreign"]
                with self.subTest(mode=mode), self.assertRaises(ValueError): resolve_reduced_motion(raw, TARGET, "reduced")

    def test_reduced_variant_cannot_change_payload_easing_scale_or_timing(self):
        with self.context() as (original, _, _):
            for key, value in (("peak_scale", 1), ("easing", "linear"), ("scale_allowed", True), ("flash_hz", 4)):
                raw = deepcopy(original)
                v = next(iter(raw["metadata"]["compiler_h3"]["reduced_motion_variants"].values()))
                row = next(iter(v["track_replacements"].values()))
                row["parameters"]["original"]["parameters"][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): resolve_reduced_motion(raw, TARGET, "reduced")

    def test_reserved_derivation_cannot_impersonate_selector(self):
        with self.context() as (raw, _, _):
            raw["metadata"]["_bie_h3_derivation"] = {"accepted": True}
            with self.assertRaisesRegex(ValueError, "RESERVED"): resolve_reduced_motion(raw, TARGET, "reduced")

    def test_unknown_capability_and_missing_required_request_block(self):
        with self.context() as (original, _, _):
            for mode in ("missing", "wrong"):
                raw = deepcopy(original)
                if mode == "missing": raw["capability_requests"] = []
                else: raw["capability_requests"][0]["requested_action"] = "transform"
                with self.assertRaises(ValueError): gm.validate_document(raw, TARGET)

    def test_optional_or_wrong_type_capability_cannot_grant_admission(self):
        with self.context() as (original, _, _):
            for key,value in (("required",False),("element_type","chart"),("fallback","generic")):
                raw=deepcopy(original);raw["capability_requests"][0][key]=value
                with self.assertRaises(ValueError):gm.validate_document(raw,TARGET)

    def test_admission_does_not_survive_recomputed_foreign_binding(self):
        with self.context() as (raw, _, _):
            for field in ("narration_revision", "visual_revision", "row_sha256", "target_profile", "element_sha256"):
                t=deepcopy(raw["tracks"][0]);t["parameters"]["binding"][field]="foreign"
                t["parameters"]["admission_id"]=gm.digest(t["parameters"])
                with self.subTest(field=field),self.assertRaises(ValueError):motion_contract(t)

    def test_revoked_upstream_access_blocks_scope_exit(self):
        try:
            with self.assertRaisesRegex(ValueError,"unauthorized"):
                with self.context():self.fixture.credentials.revoke(self.fixture.token)
        finally:
            self.fixture.credentials.grant(self.fixture.token,self.fixture.p)

    def test_focus_gutter_cannot_be_replaced_by_unbounded_outline(self):
        from bie.compiler.producer_motion_admission import current_motion_admission
        with self.context() as (raw, _, service):
            elements=deepcopy(raw["elements"])
            elements[0]["props"]["nodes"][0]["x"]=2
            with current_motion_admission(service,self.cases["cellular"],self.fixture.p.tenant,elements) as other:
                raw["elements"]=elements;raw["tracks"]=list(other["tracks"].values())
                raw["metadata"][gm.METADATA]=other["metadata"]
                with self.assertRaisesRegex(ValueError,"GUTTER"):gm.validate_document(raw,TARGET)

    def test_fixture_scope_is_explicit_and_cannot_claim_current_scene_duration(self):
        from tests.compiler.m1_support import admitted, RENDER_TARGET
        with admitted(self.fixture,self.cases["cellular"],presentation=gm.FIXTURE_LAYOUT) as (raw,bound,_):
            self.assertEqual(raw["duration_ms"],2000)
            self.assertEqual(gm.validate_document(raw,RENDER_TARGET),gm.PROFILE)
            for t in raw["tracks"]:
                self.assertEqual(t["start_ms"],t["parameters"]["original"]["start_ms"])
                self.assertEqual(t["end_ms"],t["parameters"]["original"]["end_ms"])
                self.assertGreater(t["parameters"]["binding"]["original_scene_duration_ms"],2000)
                self.assertFalse(t["parameters"]["binding"]["production_catalog_claimed"])
            with self.assertRaisesRegex(ValueError,"FIXTURE_TARGET"):gm.validate_document(raw,TARGET)

    def test_versioned_capability_matrix_is_narrow(self):
        legacy = native_qa_capabilities()
        current = native_qa_capabilities(gm.PROFILE)
        for kind in ("chart", "diagram", "timeline", "map", "text"):
            for action in ("reveal", "emphasize", "transform"):
                self.assertFalse(legacy.supports("comp:m1:" + kind, kind, action, "web"))
                self.assertEqual(current.supports("comp:m1:" + kind, kind, action, gm.PROFILE), (kind, action) in gm.PAIRS)

    def test_missing_duplicated_or_mixed_same_target_tracks_block(self):
        with self.context() as (original, _, _):
            for mode in ("missing", "duplicate", "legacy"):
                raw = deepcopy(original)
                if mode == "missing": raw["tracks"].pop()
                elif mode == "duplicate": raw["tracks"].append(deepcopy(raw["tracks"][0]))
                else:
                    t = deepcopy(raw["tracks"][0]); t.update(track_id="legacy", action="enter", parameters={})
                    raw["tracks"].append(t)
                with self.subTest(mode=mode), self.assertRaises(ValueError): gm.validate_document(raw, TARGET)

    def test_element_geometry_text_color_or_type_mutation_block(self):
        with self.context() as (raw, _, _):
            t, e = raw["tracks"][0], raw["elements"][0]
            for mode in ("label", "fill", "geometry", "type"):
                other = deepcopy(e)
                if mode == "label": other["props"]["nodes"][0]["label"] = "invented"
                elif mode == "fill": other["props"]["nodes"][0]["fill"] = "red"
                elif mode == "geometry": other["normalized_box"]["width"] *= 2
                else: other["element_type"] = "timeline"
                with self.subTest(mode=mode), self.assertRaises(ValueError): compile_animation_track(t, element=other)

    def test_new_emitter_has_real_indicator_and_no_geometric_style(self):
        with self.context() as (raw, _, _):
            out = compile_animation_track(raw["tracks"][0], element=raw["elements"][0])
            self.assertIn('data-bie-focus-indicator="m1"', out.source_text)
            self.assertIn('opacity:state.focus_opacity', out.source_text)
            for forbidden in ("scale:", "translate:", "rotate:", "transform:", "clipPath:"):
                self.assertNotIn(forbidden, out.source_text)
            self.assertFalse(out.accepted)

    def test_legacy_scale_emphasis_and_unknown_key_rejection_unchanged(self):
        c = motion_contract(track("emphasize"))
        self.assertEqual(c.owned_properties, ("scale",))
        self.assertGreater(motion_state(c, 12, 24)["scale"], 1)
        with self.assertRaisesRegex(ValueError, "ANIMATION_PARAMETER_UNCONSUMED"):
            motion_contract(track("emphasize", {"scale_allowed": False}))

    def test_legacy_reduced_receipt_has_no_new_extension(self):
        from tests.compiler.h3_test_support import variant, move
        _, receipt = resolve_reduced_motion(variant(move()), TARGET, "reduced")
        self.assertNotIn("producer_motion_v1", receipt)
        self.assertEqual(receipt["schema_version"], "bie.motion-variant.v1")

    def test_scene_scope_and_duration_cannot_be_retimed(self):
        with self.context() as (original, _, _):
            for key, value in (("scene_id", "foreign"), ("duration_ms", 1500)):
                raw = deepcopy(original); raw[key] = value
                with self.assertRaises(ValueError): gm.validate_document(raw, TARGET)

    def test_current_canvas_and_frame_policy_cannot_be_changed(self):
        with self.context() as (raw, _, _):
            for target in (replace(TARGET,width=640),replace(TARGET,height=480),replace(TARGET,fps=30)):
                with self.assertRaisesRegex(ValueError,"CURRENT_TARGET"):gm.validate_document(raw,target)

    def test_current_replay_revalidates_and_reconstructs_same_envelope(self):
        with self.context() as (raw,bound,_):
            original=deepcopy(raw["tracks"]);identity=bound["identity"]
        with self.context() as (raw,bound,_):
            self.assertEqual(raw["tracks"],original)
            self.assertEqual(bound["identity"],identity)
        with self.context("chronology"):
            with self.assertRaisesRegex(ValueError,"ADMISSION_IDENTITY"):motion_contract(original[0])

    def test_mixed_legacy_element_uses_unchanged_opacity_replacement(self):
        from tests.compiler.h3_test_support import variant,move
        with self.context() as (raw,_,_):
            legacy=variant(move())
            raw["elements"]+=legacy["elements"];raw["tracks"]+=legacy["tracks"]
            raw["metadata"]["compiler_h3"]["reduced_motion_variants"].update(
                legacy["metadata"]["compiler_h3"]["reduced_motion_variants"])
            effective,receipt=resolve_reduced_motion(raw,TARGET,"reduced")
            self.assertEqual(len(receipt["producer_motion_v1"]),2)
            last=effective["tracks"][-1]
            self.assertEqual(last["action"],"enter")
            self.assertEqual(motion_contract(last).owned_properties,("opacity",))

    def test_catalog_rejects_content_changes_before_admission(self):
        from bie.compiler.producer_motion_admission import current_motion_admission
        with self.context() as (raw, _, service):
            elements = deepcopy(raw["elements"]); elements[0]["props"]["nodes"][0]["label"] = "invented"
            with self.assertRaisesRegex(ValueError, "CATALOG_CONTENT_CHANGED"):
                with current_motion_admission(service, self.cases["cellular"], self.fixture.p.tenant, elements): pass

    def test_complete_native_source_composition_both_preferences(self):
        for family in self.cases:
            with self.context(family) as (raw, _, _):
                for preference in ("standard", "reduced"):
                    effective, _ = resolve_reduced_motion(raw, TARGET, preference)
                    result = compile_scene_for_qa(effective, target=TARGET)
                    self.assertTrue(result.source_contract_passed, [f.code for f in result.findings])
                    self.assertTrue(result.capability_qa.passed)
                    self.assertFalse(result.accepted)


if __name__ == "__main__":
    unittest.main()
