import unittest
from bie.math_intelligence.symbol_disambiguation import *
class T(unittest.TestCase):
 def test_velocity(self):
  r=disambiguate("v","velocity speed motion",{"velocity":("speed","motion"),"volume":("space","capacity")});self.assertEqual(r[0].meaning,"velocity")
 def test_score(self): self.assertGreater(disambiguate("x","alpha beta",{"a":("alpha","beta")})[0].score,.5)
 def test_empty(self): self.assertEqual(disambiguate("x","",{}),[])
 def test_tie(self):
  r=disambiguate("x","",{"b":(),"a":()});self.assertEqual(r[0].meaning,"a")
if __name__=="__main__":unittest.main()
