import unittest
from bie.math_intelligence.symbol_scope import *
class T(unittest.TestCase):
 def test_local(self):
  t=ScopeTable();t.bind(Binding("x","position","chapter","p1"));self.assertEqual(t.resolve("x",["section","chapter"]).meaning,"position")
 def test_shadow(self):
  t=ScopeTable();t.bind(Binding("x","position","chapter","p1"));t.bind(Binding("x","unknown","section","p2"));self.assertEqual(t.resolve("x",["section","chapter"]).meaning,"unknown")
 def test_missing(self): self.assertIsNone(ScopeTable().resolve("x",["book"]))
 def test_conflict(self):
  t=ScopeTable();t.bind(Binding("x","a","s","1"));t.bind(Binding("x","b","s","2"));self.assertIn(("s","x"),t.conflicts())
if __name__=="__main__":unittest.main()
