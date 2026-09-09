import unittest
from app.bie.prerequisite_intelligence.teaching_order import *
class T(unittest.TestCase):
 def test_chain(self): self.assertEqual(teaching_order({"a","b","c"},[("a","b"),("b","c")]),["a","b","c"])
 def test_priority(self): self.assertEqual(teaching_order({"a","b"},[],{"b":2}),["b","a"])
 def test_cycle(self):
  with self.assertRaises(ValueError): teaching_order({"a","b"},[("a","b"),("b","a")])
 def test_unknown(self):
  with self.assertRaises(ValueError): teaching_order({"a"},[("a","b")])
if __name__=="__main__": unittest.main()
