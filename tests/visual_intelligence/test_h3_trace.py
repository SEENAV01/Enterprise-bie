import unittest
from bie.visual_intelligence.qa_trace_matrix import *
class T(unittest.TestCase):
 def good(self): return TraceRow('v',True,('s',),('r',),'rep','g','l','t','a',('qa',),True)
 def test_pass(self): self.assertTrue(audit_trace([self.good()]).passed)
 def test_orphan(self): self.assertIn('v',audit_trace([TraceRow('v',True,(),('r',),'rep','g','l',None,None,('qa',),True)]).orphan_visual_ids)
 def test_unsupported(self): self.assertIn('v',audit_trace([TraceRow('v',True,('s',),('r',),'rep','g','l',None,None,('qa',),False)]).unsupported_visual_ids)
 def test_lost(self): self.assertIn('v',audit_trace([TraceRow('v',True,('s',),('r',),'rep',None,None,None,None,('qa',),True)]).lost_required_ids)
 def test_noqa(self): self.assertIn('v',audit_trace([TraceRow('v',True,('s',),('r',),'rep','g','l',None,None,(),True)]).missing_qa_ids)
 def test_duplicate(self):
  with self.assertRaises(TraceMatrixError): audit_trace([self.good(),self.good()])
