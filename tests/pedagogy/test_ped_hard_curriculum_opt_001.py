import unittest
from bie.pedagogy.book_scale_curriculum_optimizer import *
class T(unittest.TestCase):
 def u(self,i,o,p=.5,l=.4,r=.4,m=.4,t=10): return CurriculumUnit(i,o,p,l,r,m,t)
 def test_hard_dep(self):
  r=optimize_book_curriculum([self.u("adv",0,.9),self.u("basic",1,.2)],[CurriculumDependency("basic","adv","PREREQ")])
  self.assertLess(r.order.index("basic"),r.order.index("adv"))
 def test_split(self):
  r=optimize_book_curriculum([self.u("a",0,t=30),self.u("b",1,t=30)],[])
  self.assertEqual(r.lesson_groups,(("a",),("b",)))
 def test_cycle(self):
  with self.assertRaises(ValueError): optimize_book_curriculum([self.u("a",0),self.u("b",1)],[CurriculumDependency("a","b","x"),CurriculumDependency("b","a","x")])
