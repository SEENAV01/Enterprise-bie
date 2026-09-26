"""Seeded bounded properties; these are not full-section fuzz closure."""
from dataclasses import replace
import json
import random
import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.legacy_codec import load_legacy, dump_legacy
from bie.game_engine.legacy_migration import migrate_legacy
from tests.hardening_h6.legacy_support import fixture

class LegacyPropertyTests(unittest.TestCase):
    def test_unicode_nested_metadata_roundtrip_is_order_independent(self):
        rng = random.Random(1506001)
        wire, _ = fixture()
        words = ['physics', 'حرکت', 'गति', '移動', 'Δx', '🚀', '\\u0000', 'a"b\\c']
        for case in range(64):
            raw = json.loads(wire)
            rows = [(str(i), {'label': rng.choice(words), 'values': [rng.randint(-999,999), None, True]}) for i in range(rng.randrange(1,9))]
            raw['metadata'] = dict(rows)
            normalized = dump_legacy(load_legacy(json.dumps(raw)))
            rng.shuffle(rows); raw['metadata'] = dict(rows)
            with self.subTest(case=case):
                self.assertEqual(dump_legacy(load_legacy(json.dumps(raw))), normalized)
                self.assertEqual(dump_legacy(load_legacy(normalized)), normalized)

    def test_every_truncated_prefix_is_rejected(self):
        wire, _ = fixture()
        # Sample across the entire payload, including an almost-complete object.
        cuts = sorted(set(range(0, len(wire), max(1,len(wire)//64))) | {len(wire)-1})
        for cut in cuts:
            with self.subTest(cut=cut), self.assertRaises(GameContractError):
                load_legacy(wire[:cut])

    def test_source_and_candidate_mutations_cannot_reuse_review(self):
        wire, enrichment = fixture()
        for case in range(32):
            raw = json.loads(wire); raw['metadata']['mutation'] = case
            with self.subTest(source=case), self.assertRaisesRegex(GameContractError, 'STALE_SOURCE'):
                migrate_legacy(json.dumps(raw), enrichment)
            game = enrichment.candidate.experiences[0]
            candidate = replace(enrichment.candidate, experiences=(replace(game,title=game.title+str(case)),))
            with self.subTest(candidate=case), self.assertRaises(GameContractError):
                migrate_legacy(wire, replace(enrichment,candidate=candidate))

    def test_invalid_unicode_is_rejected_as_contract_error(self):
        wire, _ = fixture()
        for code in (0xD800,0xDBFF,0xDC00,0xDFFF):
            raw=json.loads(wire);raw['metadata']['invalid']=chr(code)
            for value in (chr(code), json.dumps(raw), b'\xff\xfe\x00'):
                with self.subTest(code=code,kind=type(value).__name__), self.assertRaises(GameContractError):
                    load_legacy(value)
