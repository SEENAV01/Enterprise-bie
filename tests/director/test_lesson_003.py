import unittest
from bie.director.narrative_arc import *
class T(unittest.TestCase):
    def test_conflict(self): self.assertIn("CONFLICT",[x.beat for x in build_narrative_arc(.5,.8,False)])
    def test_transfer(self): self.assertEqual(build_narrative_arc(.5,.1,True)[-1].beat,"TRANSFER")
