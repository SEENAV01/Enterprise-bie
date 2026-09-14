import unittest
from bie.director.emphasis_plan import *
class T(unittest.TestCase):
    def test_risk(self): self.assertEqual(plan_emphasis([("a",.5,.1,.5),("b",.5,.9,.5)])[0].concept_id,"b")
