import unittest
from bie.pedagogy.bridge_content_scope import scope_bridge_content
class T(unittest.TestCase):
 def test_scope(self):
  r=scope_bridge_content(['b'],{'b':['a']},['a','b','c']); self.assertEqual(r.supporting_concepts,('a',)); self.assertEqual(r.excluded_concepts,('c',))
 def test_unknown_dep(self):
  with self.assertRaises(ValueError): scope_bridge_content(['b'],{'b':['x']},['b'])
