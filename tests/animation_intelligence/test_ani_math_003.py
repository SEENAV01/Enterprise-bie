from hashlib import sha256
from bie.animation_intelligence.math_contracts import *
def ctx(**kw):
 d=dict(intent_id="math",evidence_refs=("src",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),notation_system="standard",source_revision=1)
 d.update(kw);return MathContext(**d)

import unittest
from bie.animation_intelligence.graph_transformation import *
class T(unittest.TestCase):
 def test_translation(self):self.assertEqual(animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+2",transform_kind="translation",parameters={"dy":2},source_ref="src").status,"PASS")
 def test_missing_params(self):self.assertEqual(animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+2",transform_kind="translation",parameters={},source_ref="src").status,"BLOCKED")
 def test_domain(self):self.assertEqual(animate_graph_transformation(ctx(),graph_id="g",source_function="y=x^2",target_function="y=x^2",transform_kind="domain_restriction",parameters={},source_ref="src",domain=(-1,1)).status,"PASS")
 def test_bad_domain(self):
  with self.assertRaises(MathDomainError):animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x",transform_kind="domain_restriction",parameters={},source_ref="src",domain=(1,1))
 def test_asymptote_review(self):self.assertEqual(animate_graph_transformation(ctx(),graph_id="g",source_function="y=1/x",target_function="y=1/(x-1)",transform_kind="translation",parameters={"dx":1},source_ref="src",preserve_asymptotes=True).status,"REVIEW")
 def test_asymptote_evidence(self):self.assertEqual(animate_graph_transformation(ctx(payload={"asymptote_evidence":True}),graph_id="g",source_function="y=1/x",target_function="y=1/(x-1)",transform_kind="translation",parameters={"dx":1},source_ref="src",preserve_asymptotes=True).status,"PASS")
 def test_grounding(self):
  with self.assertRaises(MathGroundingError):animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+1",transform_kind="translation",parameters={"dy":1},source_ref="x")
 def test_not_accepted(self):self.assertFalse(animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+1",transform_kind="translation",parameters={"dy":1},source_ref="src").accepted)
