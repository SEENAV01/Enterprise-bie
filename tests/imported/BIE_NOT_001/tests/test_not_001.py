import unittest
from bie.notation_intelligence.notation import *
class T(unittest.TestCase):
 def test_greek(self): self.assertEqual(extract_notation("angle θ")[0].kind,"greek")
 def test_operator(self): self.assertTrue(any(x.raw=="∫" for x in extract_notation("∫ f dx")))
 def test_dedup(self): self.assertEqual(len(extract_notation("θ θ")),1)
 def test_empty(self): self.assertEqual(extract_notation("plain words"),[])
if __name__=="__main__": unittest.main()
