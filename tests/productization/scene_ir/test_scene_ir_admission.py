"""Strict-boundary adversarial controls, not product or render evidence."""
from copy import deepcopy
import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement, UnifiedTrack, UnifiedSceneIRDocument
from bie.productization.scene_ir_contract import strict_document
from bie.productization.contracts import canonical, ProducerError


def document():
    box = dict(x=0.1, y=0.1, width=0.8, height=0.8)
    element = UnifiedElement("target", "chart", dict(chart_kind="bar", categories=["synthetic"], values=[2]),
        ("source",), ("reasoning",), dict(alt="synthetic", color_independent_encoding=True), box)
    track = UnifiedTrack("track", "target", "reveal", 0, 100, dict(easing="ease_out"), ("source",), ("reasoning",))
    return UnifiedSceneIRDocument("scene", "1.0.0", "Synthetic strict boundary", 1000, (element,), (track,),
        ("source",), ("reasoning",), compiler_capabilities=("comp:chart",)).to_dict()


class StrictDocumentControls(unittest.TestCase):
    def reject(self, mutate):
        value = document()
        mutate(value)
        with self.assertRaises((ProducerError, ValueError)):
            strict_document(canonical(value))

    def test_exact_native_fields_roundtrip(self):
        value = document()
        self.assertEqual(strict_document(canonical(value)).to_dict(), value)

    def test_duplicate_root_key(self):
        raw = canonical(document())
        with self.assertRaises(ProducerError):
            strict_document(b'{"scene_id":"foreign",' + raw[1:])

    def test_unknown_root_field(self):
        self.reject(lambda v: v.update(unknown=True))

    def test_unknown_element_field(self):
        self.reject(lambda v: v["elements"][0].update(unknown=True))

    def test_unknown_track_field(self):
        self.reject(lambda v: v["tracks"][0].update(unknown=True))

    def test_handoff_not_relabelled_document(self):
        with self.assertRaises(ProducerError):
            strict_document(canonical(dict(schema_version="0.1.0", nodes=[])))

    def test_boolean_duration(self):
        self.reject(lambda v: v.update(duration_ms=True))

    def test_boolean_revision(self):
        self.reject(lambda v: v.update(upstream_revision=True))

    def test_boolean_start(self):
        self.reject(lambda v: v["tracks"][0].update(start_ms=False))

    def test_fractional_end(self):
        self.reject(lambda v: v["tracks"][0].update(end_ms=99.5))

    def test_negative_start(self):
        self.reject(lambda v: v["tracks"][0].update(start_ms=-1))

    def test_outside_scene(self):
        self.reject(lambda v: v["tracks"][0].update(end_ms=1001))

    def test_zero_window(self):
        self.reject(lambda v: v["tracks"][0].update(end_ms=0))

    def test_duplicate_target(self):
        self.reject(lambda v: v["elements"].append(deepcopy(v["elements"][0])))

    def test_duplicate_track(self):
        self.reject(lambda v: v["tracks"].append(deepcopy(v["tracks"][0])))

    def test_foreign_target(self):
        self.reject(lambda v: v["tracks"][0].update(element_id="foreign"))

    def test_string_as_ref_list(self):
        self.reject(lambda v: v["elements"][0].update(source_refs="source"))

    def test_boolean_box(self):
        self.reject(lambda v: v["elements"][0]["normalized_box"].update(x=False))

    def test_box_unknown_field(self):
        self.reject(lambda v: v["elements"][0]["normalized_box"].update(units="meters"))

    def test_nan(self):
        with self.assertRaises(ProducerError):
            strict_document(canonical(document()).replace(b'"start_ms":0', b'"start_ms":NaN'))

    def test_infinite(self):
        with self.assertRaises(ProducerError):
            strict_document(canonical(document()).replace(b'"end_ms":100', b'"end_ms":Infinity'))

    def test_fingerprint_tamper(self):
        self.reject(lambda v: v.update(fingerprint="0" * 64))

    def test_accepted_not_promoted(self):
        self.reject(lambda v: v.update(accepted=True))

    def test_review_required_not_removed(self):
        self.reject(lambda v: v.update(review_required=False))

    def test_empty_inventory(self):
        self.reject(lambda v: v.update(elements=[]))

    def test_revision_string_not_coerced(self):
        self.reject(lambda v: v.update(upstream_revision="1"))

    def test_unicode_exact(self):
        value = document()
        del value["fingerprint"]
        from bie.scene_ir.unified_scene_ir_codec import decode_scene_ir
        value["title"] = "Synthetic Δ — 中文"
        value = decode_scene_ir(value).to_dict()
        self.assertEqual(strict_document(canonical(value)).title, value["title"])


if __name__ == "__main__":
    unittest.main()
