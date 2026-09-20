import unittest
from bie.visual_intelligence.representation_grammar_arbitration import *
def r(**kw):
 d=dict(decision_id="r",revision=1,domain="physics",representation="vector",confidence=.9,evidence_refs=("e",),reasoning_refs=("q",),required_capabilities=("arrow",),tags=());d.update(kw);return RepDecision(**d)
def g(i,tags=(),caps=("arrow",)): return Grammar(i,"1.0.0",("physics",),("vector",),caps,tags)
class T(unittest.TestCase):
 def test_select(self): self.assertEqual(arbitrate(r(),[g("a")]).grammar_id,"a")
 def test_unsupported(self): self.assertEqual(arbitrate(r(required_capabilities=("arrow","label")),[g("a")]).status,"UNSUPPORTED")
 def test_ambiguous(self): self.assertEqual(arbitrate(r(),[g("a"),g("b")]).status,"REVIEW")
 def test_low_conf(self): self.assertEqual(arbitrate(r(confidence=.5),[g("a")]).status,"REVIEW")
 def test_tag(self): self.assertEqual(arbitrate(r(tags=("force",)),[g("a",("force",)),g("b")]).grammar_id,"a")
 def test_deterministic(self): self.assertEqual(arbitrate(r(),[g("a")]).fingerprint,arbitrate(r(),[g("a")]).fingerprint)
