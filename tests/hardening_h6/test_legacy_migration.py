from dataclasses import replace
from pathlib import Path
import hashlib
import json
import unittest
from bie.game_engine import GameDocument as V2Document
from bie.game_engine.contracts import GameDocument as V1Document
from bie.game_engine.canonical import canonical_json
from bie.game_engine.errors import GameContractError
from bie.game_engine.legacy_codec import load_legacy, dump_legacy, LEGACY_CONTRACT_SHA256
from bie.game_engine.legacy_migration import migrate_legacy
from bie.game_engine.validation import validate_game_document
from tests.hardening_h6.legacy_support import fixture, seal

class LegacyCodecTests(unittest.TestCase):
    def test_original_contract_bytes_and_class_identity(self):
        import bie.game_engine.contracts as original
        self.assertEqual(hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest(), LEGACY_CONTRACT_SHA256)
        self.assertIsNot(V1Document, V2Document)

    def test_lossless_normalized_roundtrip(self):
        wire, _ = fixture()
        self.assertEqual(dump_legacy(load_legacy(wire)), wire)
        self.assertEqual(load_legacy(wire).metadata, {'historical_note': 'preserved'})

    def test_legacy_never_implicitly_enters_v2_validation(self):
        wire, _ = fixture()
        with self.assertRaisesRegex(GameContractError, 'GAME_DOCUMENT_TYPE'):
            validate_game_document(load_legacy(wire))

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(GameContractError, 'DUPLICATE_JSON_KEY'):
            load_legacy('{"document_id":"a","document_id":"b"}')

    def test_unknown_field_is_not_silently_discarded(self):
        wire, _ = fixture()
        raw = json.loads(wire); raw['unrecognized'] = True
        with self.assertRaisesRegex(GameContractError, 'UNKNOWN_FIELD'):
            load_legacy(json.dumps(raw))

    def test_boolean_cannot_masquerade_as_difficulty(self):
        wire, _ = fixture(); raw = json.loads(wire)
        raw['experiences'][0]['levels'][0]['challenges'][0]['difficulty'] = True
        with self.assertRaisesRegex(GameContractError, 'FIELD_TYPE'):
            load_legacy(json.dumps(raw))

    def test_nonfinite_nested_metadata_rejected(self):
        wire, _ = fixture(); raw = json.loads(wire); raw['metadata']['invalid'] = float('nan')
        with self.assertRaisesRegex(GameContractError, 'NONFINITE'):
            load_legacy(json.dumps(raw))

    def test_oversized_wire_rejected(self):
        with self.assertRaisesRegex(GameContractError, 'WIRE_LIMIT'):
            load_legacy(' ' * 2_000_001)

    def test_deep_wire_rejected(self):
        with self.assertRaises(GameContractError):
            load_legacy('[' * 100 + '0' + ']' * 100)

    def test_unknown_version_rejected(self):
        wire, _ = fixture(); raw = json.loads(wire); raw['game_ir_version'] = '3.0.0'
        with self.assertRaisesRegex(GameContractError, 'VERSION'):
            load_legacy(json.dumps(raw))

class MigrationTests(unittest.TestCase):
    def test_explicit_conversion_is_deterministic_and_retains_legacy(self):
        wire, enrichment = fixture()
        first = migrate_legacy(wire, enrichment)
        self.assertEqual(first, migrate_legacy(wire, enrichment))
        self.assertEqual(first.legacy_wire, wire)
        self.assertEqual(first.document(), enrichment.candidate)
        self.assertIsNot(first.document(), first.document())
        receipt = json.loads(first.receipt_wire)
        self.assertFalse(receipt['product_accepted'])
        self.assertFalse(receipt['runtime_verified'])
        self.assertFalse(receipt['independent_semantic_equivalence_proven'])

    def test_missing_enrichment_rejected(self):
        wire, _ = fixture()
        with self.assertRaisesRegex(GameContractError, 'EXPLICIT_ENRICHMENT'):
            migrate_legacy(wire, None)

    def test_stale_source_rejected(self):
        wire, e = fixture()
        with self.assertRaisesRegex(GameContractError, 'STALE_SOURCE'):
            migrate_legacy(wire, replace(e, legacy_sha256='0' * 64))

    def test_changed_review_binding_rejected(self):
        wire, e = fixture()
        e = replace(e, text_catalog={**e.text_catalog, 'new:unreviewed': 'text'})
        with self.assertRaisesRegex(GameContractError, 'REVIEW_BINDING'):
            migrate_legacy(wire, e)

    def test_missing_source_provenance_rejected(self):
        wire, e = fixture(); refs = e.candidate.provenance.refs
        changed = replace(refs[0], artifact_id='source:other')
        doc = replace(e.candidate, provenance=replace(e.candidate.provenance, refs=(changed, *refs[1:])))
        with self.assertRaisesRegex(GameContractError, 'PROVENANCE_LOSS'):
            migrate_legacy(wire, seal(replace(e, candidate=doc)))

    def test_text_loss_rejected(self):
        wire, e = fixture()
        with self.assertRaisesRegex(GameContractError, 'TEXT_LOSS'):
            migrate_legacy(wire, seal(replace(e, text_catalog={})))

    def test_missing_expression_binding_rejected(self):
        wire, e = fixture()
        with self.assertRaisesRegex(GameContractError, 'EXPRESSION_UNRESOLVED'):
            migrate_legacy(wire, seal(replace(e, expressions=e.expressions[:-1])))

    def test_expression_evidence_tamper_rejected(self):
        wire, e = fixture(); item = e.expressions[0]
        item = replace(item, reasoning_evidence=replace(item.reasoning_evidence, content_sha256='0' * 64))
        with self.assertRaisesRegex(GameContractError, 'EXPRESSION_EVIDENCE'):
            migrate_legacy(wire, seal(replace(e, expressions=(item, *e.expressions[1:]))))

    def test_missing_policy_rejected(self):
        wire, e = fixture()
        with self.assertRaisesRegex(GameContractError, 'POLICY_EVIDENCE_REQUIRED'):
            migrate_legacy(wire, seal(replace(e, policy_evidence=())))

    def test_mechanic_cannot_be_guessed(self):
        wire, e = fixture()
        with self.assertRaisesRegex(GameContractError, 'MECHANIC_UNRESOLVED'):
            migrate_legacy(wire, seal(replace(e, mechanic_modes={})))

    def test_entity_kind_cannot_silently_change(self):
        wire, e = fixture(); raw = json.loads(wire)
        raw['experiences'][0]['levels'][0]['manipulables'][0]['object_type'] = 'vector'
        wire = dump_legacy(load_legacy(json.dumps(raw)))
        e = seal(replace(e, legacy_sha256=hashlib.sha256(wire).hexdigest()))
        with self.assertRaisesRegex(GameContractError, 'ENTITY_KIND'):
            migrate_legacy(wire, e)

    def test_unsupported_features_fail_closed(self):
        for feature in ('hints', 'append', 'vector2', 'telemetry'):
            wire, e = fixture(); raw = json.loads(wire); game = raw['experiences'][0]; level = game['levels'][0]
            if feature == 'hints':
                level['challenges'][0]['hints'] = [{'hint_id': 'hint:1', 'text': 'Hint', 'level': 1}]
            elif feature == 'append':
                level['rules'][0]['effects'][0]['operation'] = 'append'
            elif feature == 'vector2':
                level['state_variables'][0]['value_type'] = 'vector2'
            else:
                game['telemetry_events'] = ['click']
            wire = dump_legacy(load_legacy(json.dumps(raw)))
            e = seal(replace(e, legacy_sha256=hashlib.sha256(wire).hexdigest()))
            with self.subTest(feature=feature), self.assertRaises(GameContractError):
                migrate_legacy(wire, e)

    def test_caller_inputs_unchanged(self):
        wire, e = fixture(); before = canonical_json(e)
        migrate_legacy(wire, e)
        self.assertEqual(canonical_json(e), before)
