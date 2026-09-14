import unittest
from bie.director.pacing_plan import *
class T(unittest.TestCase):
    def test_load(self):
        r=build_pacing_plan([("a",.1,.5),("b",.9,.5)]); self.assertGreater(r[1].target_seconds,r[0].target_seconds)
