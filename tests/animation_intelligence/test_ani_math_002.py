from hashlib import sha256
from bie.animation_intelligence.math_contracts import *
def ctx(**kw):
 d=dict(intent_id="math",evidence_refs=("src",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),notation_system="standard",source_revision=1)
 d.update(kw);return MathContext(**d)

import unittest
from bie.animation_intelligence.equation_morph import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="x+1=2",target_expression="x=1",token_map={"x":"x","2":"1"},source_ref="src",equivalence_status="equivalent").status,"PASS")
 def test_empty_map(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="a",target_expression="b",token_map={},source_ref="src",equivalence_status="equivalent").status,"BLOCKED")
 def test_duplicate_target(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="a+b",target_expression="x",token_map={"a":"x","b":"x"},source_ref="src",equivalence_status="equivalent").status,"BLOCKED")
 def test_not_equiv(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="a",target_expression="b",token_map={"a":"b"},source_ref="src",equivalence_status="not_equivalent").status,"BLOCKED")
 def test_implication_review(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="x=1",target_expression="x^2=1",token_map={"x":"x"},source_ref="src",equivalence_status="implication").status,"REVIEW")
 def test_unmapped_review(self):self.assertEqual(animate_equation_morph(ctx(),morph_id="m",source_expression="x+1",target_expression="x",token_map={"x":"x"},source_ref="src",equivalence_status="equivalent",preserve_unmapped_tokens=False).status,"REVIEW")
 def test_grounding(self):
  with self.assertRaises(MathGroundingError):animate_equation_morph(ctx(),morph_id="m",source_expression="a",target_expression="b",token_map={"a":"b"},source_ref="x",equivalence_status="equivalent")
 def test_not_accepted(self):self.assertFalse(animate_equation_morph(ctx(),morph_id="m",source_expression="a",target_expression="b",token_map={"a":"b"},source_ref="src",equivalence_status="equivalent").accepted)
