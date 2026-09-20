import unittest
from bie.visual_intelligence.access_contracts import *
from bie.visual_intelligence.alt_description_intent import *
def i(role="diagram"):return VisualAccessIntent("i",role,("e",),("r",))
class T(unittest.TestCase):
 def test_complex(self): self.assertEqual(build_alt_description_intent(i(),purpose="Explain field",key_elements=["charge","field"]).mode,"long_description")
 def test_decorative(self): self.assertEqual(build_alt_description_intent(i("decorative"),purpose="Decoration").mode,"empty_alt")
 def test_concise(self): self.assertEqual(build_alt_description_intent(i("image"),purpose="Show apparatus",key_elements=["apparatus"]).mode,"concise_alt")
 def test_complex_requires_elements(self):
  with self.assertRaises(AltIntentError): build_alt_description_intent(i("map"),purpose="Show route")
 def test_grounding(self):
  a=build_alt_description_intent(i(),purpose="Explain",key_elements=["x"]); self.assertEqual(a.evidence_refs,("e",))
 def test_avoid_invention(self):
  a=build_alt_description_intent(i(),purpose="Explain",key_elements=["x"]); self.assertIn("do_not_invent_unseen_facts",a.avoid)
 def test_decision(self):
  a=build_alt_description_intent(i(),purpose="Explain",key_elements=["x"]); self.assertEqual(as_decision(i(),a).action,"alt_description_intent")
 def test_not_accepted(self):
  a=build_alt_description_intent(i(),purpose="Explain",key_elements=["x"]); self.assertFalse(as_decision(i(),a).accepted)
