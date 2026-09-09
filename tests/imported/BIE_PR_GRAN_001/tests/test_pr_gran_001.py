import unittest
from app.bie.prerequisite_intelligence.granularity import *
class T(unittest.TestCase):
 def setUp(self): self.h={"alg":Skill("alg",("eq","frac")),"eq":Skill("eq"),"frac":Skill("frac")}
 def test_partial(self): self.assertEqual(minimum_required_scope("alg",self.h,{"eq"}).selected,("eq",))
 def test_whole(self): self.assertEqual(minimum_required_scope("alg",self.h,{"eq","frac"}).selected,("alg",))
 def test_none(self): self.assertEqual(minimum_required_scope("alg",self.h,set()).selected,())
 def test_unknown(self):
  with self.assertRaises(ValueError): minimum_required_scope("x",self.h,set())
if __name__=="__main__": unittest.main()
