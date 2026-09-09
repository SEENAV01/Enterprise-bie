import unittest
from app.bie.misconception_intelligence.remediation import *
class T(unittest.TestCase):
 def test_confusion(self): self.assertEqual(remediation_for("m","confusion","medium").strategy,"contrast_cases")
 def test_causal(self): self.assertEqual(remediation_for("m","causal","medium").strategy,"mechanism_rebuild")
 def test_high_followup(self): self.assertIn("schedule delayed retrieval check",remediation_for("m","procedural","high").steps)
 def test_fallback(self): self.assertEqual(remediation_for("m","other","low").strategy,"diagnose_and_reteach")
if __name__=="__main__": unittest.main()
