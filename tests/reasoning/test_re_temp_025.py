import unittest
from bie.reasoning.temporal_calendar_normalization import *
class T(unittest.TestCase):
 def test_ce(self): self.assertEqual(normalize_year(CalendarDate(2020)),2020)
 def test_bce(self): self.assertEqual(normalize_year(CalendarDate(1,"BCE")),0)
 def test_compare(self): self.assertEqual(compare_dates(CalendarDate(2,"BCE"),CalendarDate(1,"BCE")),"BEFORE")
 def test_alias(self): self.assertEqual(normalize_year(CalendarDate(5,"BC")),-4)
 def test_unknown(self):
  with self.assertRaises(ValueError): normalize_year(CalendarDate(1,"UNKNOWN"))
