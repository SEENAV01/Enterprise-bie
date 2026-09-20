import unittest
from bie.compiler.props_generation import *
class T(unittest.TestCase):
 def fields(self):return ({"name":"topic","type":"string"},{"name":"level","type":"number","optional":True})
 def test_interface(self):self.assertIn("export interface BieSceneProps",emit_props(fields=self.fields()).content)
 def test_optional(self):self.assertIn("level?: number;",emit_props(fields=self.fields()).content)
 def test_default(self):self.assertIn('"topic": "Force"',emit_props(fields=self.fields(),defaults={"topic":"Force"}).content)
 def test_unknown_default(self):
  with self.assertRaises(ReactEmitterError):emit_props(fields=self.fields(),defaults={"x":1})
 def test_duplicate(self):
  with self.assertRaises(ReactEmitterError):emit_props(fields=({"name":"x","type":"string"},{"name":"x","type":"number"}))
 def test_bad_type(self):
  with self.assertRaises(ReactEmitterError):emit_props(fields=({"name":"x","type":"object"},))
