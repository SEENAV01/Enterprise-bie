import unittest
from bie.visual_intelligence.canonical_family_wiring import *
class T(unittest.TestCase):
 def family(self):return execute_original_family_path(domain='physics',representation='vector_diagram',tags=('vector',),grammar_inputs={'vectors':[{'id':'F','direction':[1,0],'source_ids':['e']}],'frame_id':'xy','scale':1.0},evidence_refs=('e',),reasoning_refs=('r',))
 def test_registry(self):self.assertEqual(len(build_original_grammar_registry().list()),11)
 def test_plan(self):self.assertEqual(self.family().status,'PASS')
 def test_grammar(self):self.assertEqual(self.family().grammar_plan.grammar_id,PHYSICS_VECTOR_GRAMMAR.grammar_id)
 def test_layout(self):self.assertTrue(self.family().layout_plan.fingerprint)
 def test_asset(self):self.assertTrue(self.family().asset_need.media_kinds)
 def test_text(self):self.assertTrue(self.family().text_decisions)
 def test_access(self):self.assertTrue(self.family().access_decisions)
 def test_qa(self):self.assertEqual(len(self.family().qa_results),3)
