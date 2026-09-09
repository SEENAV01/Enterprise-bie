import unittest
from bie.knowledge_intelligence.concept_definitions import *
class T(unittest.TestCase):
 def test_contract(self):
  r=attach("c",[{"text":"A push or pull","anchor_id":"a","confidence":.9}]);self.assertEqual(len(r["definitions"]),1)
  self.assertEqual(attach("c",[])["definitions"],())
  with self.assertRaises(E):attach("",[])
  with self.assertRaises(E):attach("c",[{"text":"","anchor_id":"a","confidence":1}])
if __name__=='__main__':unittest.main()
