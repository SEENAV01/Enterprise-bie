from hashlib import sha256
from bie.animation_intelligence.math_contracts import *
def ctx(**kw):
 d=dict(intent_id="math",evidence_refs=("src",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),notation_system="standard",source_revision=1)
 d.update(kw);return MathContext(**d)

import unittest
from bie.animation_intelligence.derivation_animation import *
S=({"step_id":"s1","expression":"x+1=2","justification":"given"},
   {"step_id":"s2","expression":"x=1","justification":"subtract 1","side_conditions":[]})
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="src").status,"PASS")
 def test_dependency(self):
  r=animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="src",dependency_edges=[{"before":"s1","after":"s2"}])
  self.assertEqual(r.operations[1]["step_order"],["s1","s2"])
 def test_cycle_block(self):
  r=animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="src",dependency_edges=[{"before":"s1","after":"s2"},{"before":"s2","after":"s1"}])
  self.assertEqual(r.status,"BLOCKED")
 def test_side_condition_block(self):
  steps=({"step_id":"s1","expression":"x/y=1","justification":"given","side_conditions":["y != 0"]},
         {"step_id":"s2","expression":"x=y","justification":"multiply by y","side_conditions":["y != 0"]})
  self.assertEqual(animate_derivation(ctx(),derivation_id="d",steps=steps,source_ref="src",preserve_side_conditions=False).status,"BLOCKED")
 def test_bad_edge(self):
  with self.assertRaises(MathAnimationError):animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="src",dependency_edges=[{"before":"s1","after":"x"}])
 def test_grounding(self):
  with self.assertRaises(MathGroundingError):animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="x")
 def test_uncertainty(self):self.assertEqual(animate_derivation(ctx(uncertainty=.5),derivation_id="d",steps=S,source_ref="src").status,"REVIEW")
 def test_not_accepted(self):self.assertFalse(animate_derivation(ctx(),derivation_id="d",steps=S,source_ref="src").accepted)
