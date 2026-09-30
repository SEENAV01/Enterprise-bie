import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

from bie.evaluation.benchmarks.models import text
class UnicodeBoundary(unittest.TestCase):
    def test_high_surrogate_has_typed_error(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_UNICODE'): canonical_json({'x':'\ud800'})
    def test_low_surrogate_has_typed_error(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_UNICODE'): canonical_json(['\udfff'])
    def test_surrogate_key_has_typed_error(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_UNICODE'): canonical_json({'\ud800':1})
    def test_nested_surrogate_has_typed_error(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_UNICODE'): canonical_json({'a':[{'b':'\ud800'}]})
    def test_text_rejects_surrogate(self):
        with self.assertRaisesRegex(BenchmarkError,'INVALID_UNICODE'): text('a\ud800')
    def test_json_escape_surrogate_rejects(self):
        with self.assertRaises(BenchmarkError): strict_loads('"\\ud800"')
    def test_emoji_scalar_roundtrip(self):
        self.assertEqual({'x':'😀'},strict_loads(canonical_json({'x':'😀'})))
    def test_hindi_roundtrip(self):
        self.assertEqual({'x':'विद्युत आवेश'},strict_loads(canonical_json({'x':'विद्युत आवेश'})))
    def test_valid_escaped_surrogate_pair_roundtrip(self):
        self.assertEqual('😀',strict_loads('"\\ud83d\\ude00"'))
    def test_multibyte_budget_is_bytes_not_characters(self):
        with self.assertRaisesRegex(BenchmarkError,'JSON_SIZE_LIMIT'): canonical_json('अ'*666667)
    def test_duplicate_keys_still_rejected(self):
        with self.assertRaisesRegex(BenchmarkError,'DUPLICATE_JSON_KEY'): strict_loads('{"x":1,"x":2}')
    def test_nonfinite_still_rejected(self):
        with self.assertRaises(BenchmarkError): canonical_json({'x':float('nan')})
    def test_hash_order_independent(self): self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
    def test_normalization_not_silently_changed(self): self.assertNotEqual(digest('é'),digest('e\u0301'))
