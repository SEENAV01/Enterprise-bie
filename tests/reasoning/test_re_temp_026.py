import unittest
from bie.reasoning.temporal_timezone_reasoning import *
class T(unittest.TestCase):
 def test_utc(self): self.assertEqual(utc_minutes(OffsetInstant(600,330)),270)
 def test_simultaneous(self): self.assertEqual(compare_instants(OffsetInstant(600,330),OffsetInstant(270,0)),"SIMULTANEOUS")
 def test_before(self): self.assertEqual(compare_instants(OffsetInstant(200,0),OffsetInstant(300,0)),"BEFORE")
 def test_bad_offset(self):
  with self.assertRaises(ValueError): utc_minutes(OffsetInstant(0,900))
