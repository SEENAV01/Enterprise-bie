import unittest, json
from bie.reasoning.temporal_result_contract import *

class T(unittest.TestCase):
    def test_canonical(self):
        a=TemporalResultContract("RESOLVED","x",("b","a","a"))
        b=TemporalResultContract("RESOLVED","x",("a","b"))
        self.assertEqual(canonical_temporal_json(a),canonical_temporal_json(b))
    def test_id(self):
        r=TemporalResultContract("RESOLVED","x",("e",))
        self.assertEqual(temporal_result_id(r),temporal_result_id(r))
    def test_bad_status(self):
        with self.assertRaises(ValueError):
            validate_temporal_result(TemporalResultContract("OK","x",()))
    def test_resolved_requires_conclusion(self):
        with self.assertRaises(ValueError):
            validate_temporal_result(TemporalResultContract("RESOLVED",None,()))
    def test_json_safe(self):
        self.assertEqual(json.loads(canonical_temporal_json(TemporalResultContract("AMBIGUOUS",None,("e",))))["status"],"AMBIGUOUS")
