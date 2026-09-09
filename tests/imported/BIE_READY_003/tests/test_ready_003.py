import unittest
from bie.readiness_intelligence.diagnostics import *
class T(unittest.TestCase):
 def test_question(self): self.assertIn("vectors",generate_diagnostic_questions({"vectors":{"objective":"explain vectors"}})[0].prompt)
 def test_priority(self):
  r=generate_diagnostic_questions({"a":{"strength":.2},"b":{"strength":.9}}); self.assertEqual(r[0].concept,"b")
 def test_limit(self): self.assertEqual(len(generate_diagnostic_questions({"a":{},"b":{}},1)),1)
 def test_invalid(self):
  with self.assertRaises(ValueError): generate_diagnostic_questions({"a":{}},0)
if __name__=="__main__": unittest.main()
