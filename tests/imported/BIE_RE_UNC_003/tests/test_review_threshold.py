import unittest
from bie.reasoning.review_threshold import *
class T(unittest.TestCase):
 def test_review(self):self.assertTrue(review_required(.5,1,0)["review"])
 def test_pass(self):self.assertFalse(review_required(.9,1,0)["review"])
 def test_conflict(self):self.assertTrue(review_required(.9,1,1)["review"])
 def test_bad(self):
  with self.assertRaises(ValueError):review_required(2,1,0)
