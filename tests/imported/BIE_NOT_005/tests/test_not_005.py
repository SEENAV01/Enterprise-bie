import unittest
from bie.notation_intelligence.math_tools import *
class T(unittest.TestCase):
 def test_calculus(self): self.assertEqual(infer_math_tools("differentiate the rate of change")[0].tool,"calculus")
 def test_vectors(self): self.assertTrue(any(x.tool=="vectors" for x in infer_math_tools("find vector magnitude and direction")))
 def test_none(self): self.assertEqual(infer_math_tools("historical narrative"),[])
 def test_rank(self): self.assertGreaterEqual(infer_math_tools("plot graph slope and solve equation")[0].confidence,infer_math_tools("plot graph slope and solve equation")[-1].confidence)
if __name__=="__main__": unittest.main()
