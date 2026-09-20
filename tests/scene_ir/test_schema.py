import unittest
from bie.scene_ir.scene_ir_json_schema import *
class TestSchema(unittest.TestCase):
 def test_shape(self):self.assertTrue(validate_json_schema_shape(SCENE_IR_JSON_SCHEMA))
 def test_draft(self):self.assertEqual(SCENE_IR_JSON_SCHEMA["$schema"],"https://json-schema.org/draft/2020-12/schema")
 def test_version(self):self.assertEqual(SCENE_IR_JSON_SCHEMA["properties"]["schema_version"]["const"],"1.0.0")
 def test_elements(self):self.assertIn("elements",SCENE_IR_JSON_SCHEMA["required"])
 def test_lineage(self):self.assertIn("source_refs",SCENE_IR_JSON_SCHEMA["required"])
 def test_closed(self):self.assertFalse(SCENE_IR_JSON_SCHEMA["additionalProperties"])
 def test_accept(self):self.assertFalse(SCENE_IR_JSON_SCHEMA["properties"]["accepted"]["const"])
 def test_fp(self):self.assertEqual(SCENE_IR_JSON_SCHEMA["properties"]["ir_fingerprint"]["pattern"],"^[0-9a-f]{64}$")
