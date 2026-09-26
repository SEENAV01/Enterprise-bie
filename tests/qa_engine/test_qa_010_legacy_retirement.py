import unittest,tempfile
from pathlib import Path
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_010 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(ROOT/'bie/game_engine')
 def test_pass_with_nonblocking_observation(self):assert_pass(self,self.good())
 def test_zero_blocking_findings(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='blocking_legacy_findings'),0)
 def test_quality_intent_present(self):self.assertFalse(any(f.code=='QUALITY_INTENT_MISSING' for f in self.good().findings))
 def test_legacy_generator_detected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'quality_intent.py').write_text('anti_slide_default=True\nmcq_only_core_experience_forbidden=True\nsemantic_visuals_required=True\n');(p/'bad.py').write_text('def keyword_game_generator(): pass\n');self.assertIs(evaluate(p).status,GateStatus.FAIL)
 def test_eval_detected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'quality_intent.py').write_text('anti_slide_default=True\nmcq_only_core_experience_forbidden=True\nsemantic_visuals_required=True\n');(p/'bad.py').write_text('def f(x): return eval(x)\n');self.assertIs(evaluate(p).status,GateStatus.FAIL)
 def test_keyword_routing_detected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);(p/'quality_intent.py').write_text('anti_slide_default=True\nmcq_only_core_experience_forbidden=True\nsemantic_visuals_required=True\n');(p/'bad.py').write_text('def f(topic, keyword):\n    if keyword in topic: return 1\n');self.assertIs(evaluate(p).status,GateStatus.FAIL)
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
