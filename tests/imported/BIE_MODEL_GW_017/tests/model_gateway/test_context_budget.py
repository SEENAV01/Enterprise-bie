
import unittest
from bie.model_gateway.context_budget import *
class T(unittest.TestCase):
 def b(self):return ContextBudget(100,20,10)
 def test_available(self):self.assertEqual(available_input(self.b()),70)
 def test_fit(self):self.assertTrue(fits(70,self.b()))
 def test_over(self):self.assertFalse(fits(71,self.b()))
 def test_negative(self):self.assertFalse(fits(-1,self.b()))
 def test_bad(self):
  with self.assertRaises(ContextBudgetError):available_input(ContextBudget(10,10,1))
if __name__=="__main__":unittest.main()
