import unittest,hashlib
from bie.visual_intelligence.asset_lifecycle import *
H=hashlib.sha256(b'x').hexdigest()
class T(unittest.TestCase):
 def test_happy(self):
  a=AssetLifecycle('a');a=transition(a,'REUSE_CANDIDATE','source');a=transition(a,'ACQUIRED','reuse',uri='file://a',content_sha256=H,provenance_refs=('src',));a=transition(a,'GROUNDING_CHECKED','g',grounding_score=.9);a=transition(a,'RIGHTS_VERIFIED','r',rights_status='source-permitted');a=transition(a,'QUALITY_VERIFIED','q',quality_score=.8);a=transition(a,'READY','ready');self.assertTrue(production_ready(a))
 def test_bad_transition(self):
  with self.assertRaises(AssetTransitionError): transition(AssetLifecycle('a'),'READY','bad')
 def test_hash_required(self):
  a=transition(AssetLifecycle('a'),'REUSE_CANDIDATE','x')
  with self.assertRaises(AssetTransitionError): transition(a,'ACQUIRED','x',uri='file://a',provenance_refs=('s',))
 def test_rights(self):
  a=transition(transition(transition(AssetLifecycle('a'),'REUSE_CANDIDATE','x'),'ACQUIRED','x',uri='file://a',content_sha256=H,provenance_refs=('s',)),'GROUNDING_CHECKED','x',grounding_score=.9)
  with self.assertRaises(AssetTransitionError): transition(a,'RIGHTS_VERIFIED','x',rights_status='unknown')
 def test_fallback(self): self.assertEqual(transition(AssetLifecycle('a'),'FALLBACK','missing').state,'FALLBACK')
