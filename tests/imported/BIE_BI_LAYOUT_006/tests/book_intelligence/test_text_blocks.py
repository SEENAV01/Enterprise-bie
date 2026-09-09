
import unittest
from bie.document_intelligence.text_blocks import *
class T(unittest.TestCase):
 def test_ok(self):self.assertEqual(build("b"," x ",("r1",),1,.9).text,"x")
 def test_empty(self):
  with self.assertRaises(TextBlockError):build("b","",("r",),1,.9)
 def test_regions(self):
  with self.assertRaises(TextBlockError):build("b","x",(),1,.9)
 def test_dup(self):
  with self.assertRaises(TextBlockError):build("b","x",("r","r"),1,.9)
 def test_conf(self):
  with self.assertRaises(TextBlockError):build("b","x",("r",),1,2)
if __name__=="__main__":unittest.main()
