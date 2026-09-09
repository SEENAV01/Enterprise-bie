import unittest
from book_intelligence.document_pipeline import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(run({s:(lambda st,s=s:{**st,s:True}) for s in ORDER})["qa"],True)
  with self.assertRaises(E):run({})
  bad={s:(lambda st:{}) for s in ORDER};bad["qa"]=1
  with self.assertRaises(E):run(bad)
  bad={s:(lambda st:{}) for s in ORDER};bad["layout"]=lambda st:None
  with self.assertRaises(E):run(bad)
if __name__=='__main__':unittest.main()
