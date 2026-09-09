
import unittest
from bie.document_intelligence.header_footer import *
class T(unittest.TestCase):
 def test_header(self):self.assertIn(("Book","top"),recurring_candidates([[("Book","top")],[("Book","top")]]))
 def test_footer(self):self.assertIn(("1","bottom"),recurring_candidates([[("1","bottom")],[("1","bottom")]]))
 def test_body(self):self.assertEqual(recurring_candidates([[("X","body")],[("X","body")]]),())
 def test_fraction(self):self.assertEqual(recurring_candidates([[("A","top")],[]],.6),())
 def test_empty(self):
  with self.assertRaises(HeaderFooterError):recurring_candidates([])
if __name__=="__main__":unittest.main()
