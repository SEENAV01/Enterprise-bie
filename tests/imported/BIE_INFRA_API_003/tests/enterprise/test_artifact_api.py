
import unittest
from bie.infrastructure.artifact_api import *
class C:
 def get(self,k):return {"artifact_id":"a","content_hash":"h"} if k=="a" else None
 def parents(self,k):return ["p"]
class B:
 def get(self,h):return b"x"
class T(unittest.TestCase):
 def test_meta(self):self.assertEqual(ArtifactAPI(C(),B()).metadata("a")["artifact_id"],"a")
 def test_content(self):self.assertEqual(ArtifactAPI(C(),B()).content("a"),b"x")
 def test_lineage(self):self.assertEqual(ArtifactAPI(C(),B()).lineage("a"),("p",))
 def test_missing(self):
  with self.assertRaises(ArtifactAPIError):ArtifactAPI(C(),B()).metadata("z")
if __name__=="__main__":unittest.main()
