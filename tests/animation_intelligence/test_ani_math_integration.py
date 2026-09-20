from hashlib import sha256
from bie.animation_intelligence.math_contracts import *
def ctx(**kw):
 d=dict(intent_id="math",evidence_refs=("src",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),notation_system="standard",source_revision=1)
 d.update(kw);return MathContext(**d)

import unittest
from bie.animation_intelligence.derivation_animation import animate_derivation
from bie.animation_intelligence.equation_morph import animate_equation_morph
from bie.animation_intelligence.graph_transformation import animate_graph_transformation
class T(unittest.TestCase):
 def test_derivation_to_morph(self):
  d=animate_derivation(ctx(),derivation_id="d",steps=(
    {"step_id":"s1","expression":"x+1=2","justification":"given"},
    {"step_id":"s2","expression":"x=1","justification":"subtract 1"}),source_ref="src")
  m=animate_equation_morph(ctx(),morph_id="m",source_expression="x+1=2",target_expression="x=1",
    token_map={"x":"x","2":"1"},source_ref="src",equivalence_status="equivalent")
  self.assertEqual((d.status,m.status),("PASS","PASS"))
 def test_graph_transform_guard(self):
  g=animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+2",
    transform_kind="translation",parameters={},source_ref="src")
  self.assertEqual(g.status,"BLOCKED")
 def test_equivalence_guard(self):
  m=animate_equation_morph(ctx(),morph_id="m",source_expression="a",target_expression="b",
    token_map={"a":"b"},source_ref="src",equivalence_status="unknown")
  self.assertEqual(m.status,"BLOCKED")
 def test_not_accepted(self):
  self.assertFalse(animate_graph_transformation(ctx(),graph_id="g",source_function="y=x",target_function="y=x+1",
    transform_kind="translation",parameters={"dy":1},source_ref="src").accepted)
