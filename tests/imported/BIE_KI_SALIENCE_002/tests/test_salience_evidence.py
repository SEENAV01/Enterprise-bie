import unittest
from salience_evidence import *
class T(unittest.TestCase):
 def test_contract(self):
  s=[{"kind":"HEADING","anchor_id":"p"}];self.assertTrue(bind("c",s)["grounded"])
  self.assertEqual(len(bind("c",s)["signals"]),1)
  with self.assertRaises(E):bind("",s)
  with self.assertRaises(E):bind("c",[{"kind":"BAD","anchor_id":"p"}])
