import unittest
from app.bie.reasoning.teaching_order import *
class T(unittest.TestCase):
 def test_depth(self):self.assertEqual(decide([Candidate("b",1,0,1),Candidate("a",0,5,.1)]),("a","b"))
 def test_source(self):self.assertEqual(decide([Candidate("b",0,2,1),Candidate("a",0,1,.1)]),("a","b"))
 def test_empty(self):self.assertEqual(decide([]),())
 def test_bad(self):
  with self.assertRaises(ValueError):decide([Candidate("a",-1,0,1)])
