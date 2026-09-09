import unittest
from bie.notation_intelligence.symbols import *
class T(unittest.TestCase):
 def test_resolve(self): self.assertEqual(resolve_symbols([SymbolMeaning("v","velocity","s1")],"s1")[0].meaning if False else resolve_symbols([SymbolMeaning("v","velocity","s1")],"s1")[0].meanings,("velocity",))
 def test_ambiguous(self): self.assertTrue(resolve_symbols([SymbolMeaning("m","mass","global"),SymbolMeaning("m","slope","s1")],"s1")[0].ambiguous)
 def test_scope(self): self.assertEqual(resolve_symbols([SymbolMeaning("x","one","s1")],"s2"),[])
 def test_dedup(self): self.assertFalse(resolve_symbols([SymbolMeaning("x","position","global"),SymbolMeaning("x","position","global")],"s")[0].ambiguous)
if __name__=="__main__": unittest.main()
