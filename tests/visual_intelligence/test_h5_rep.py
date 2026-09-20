import unittest,tempfile
from bie.visual_intelligence.rep_original_codec import *
from bie.visual_intelligence.grammar_registry import VisualGrammarRegistry
from bie.visual_intelligence.physics_vector_grammar import PHYSICS_VECTOR_GRAMMAR
def raw():return {'decision_id':'rep','domain':'physics','representation':'vector_diagram','confidence':.9,'evidence_refs':['e'],'reasoning_refs':['r'],'tags':['vector']}
class T(unittest.TestCase):
 def test_count(self):self.assertEqual(len(EXPECTED_REP_ARCHIVE_SHA256),8)
 def test_strict(self):
  with self.assertRaises(OriginalRepSourceUnavailableError):decode_rep_decision(raw(),False,True)
 def test_fixture(self):self.assertFalse(decode_rep_decision(raw(),False,False).accepted)
 def test_hash(self):self.assertFalse(verify_rep_archive_bytes('BIE_VIS_REP_001.zip',b'bad'))
 def test_registry(self):
  r=VisualGrammarRegistry();r.register(PHYSICS_VECTOR_GRAMMAR);self.assertEqual(adapt_original_grammar_registry(r)[0].grammar_id,PHYSICS_VECTOR_GRAMMAR.grammar_id)
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(len(verify_rep_archive_directory(d).missing),8)
