
import unittest
from enterprise.deterministic_seed import *
H="a"*64
class T(unittest.TestCase):
 def test_same_seed(self): self.assertEqual(derive_seed("r","s",H),derive_seed("r","s",H))
 def test_stage_changes(self): self.assertNotEqual(derive_seed("r","s1",H),derive_seed("r","s2",H))
 def test_run_changes(self): self.assertNotEqual(derive_seed("r1","s",H),derive_seed("r2","s",H))
 def test_rng_repeat(self):
  a=seeded_rng("r","s",H).random(); b=seeded_rng("r","s",H).random(); self.assertEqual(a,b)
 def test_choice_repeat(self): self.assertEqual(deterministic_choice([1,2,3],"r","s",H),deterministic_choice([1,2,3],"r","s",H))
 def test_empty_items(self):
  with self.assertRaises(SeedError): deterministic_choice([],"r","s",H)
 def test_bad_hash(self):
  with self.assertRaises(SeedError): derive_seed("r","s","x")
if __name__=="__main__": unittest.main()
