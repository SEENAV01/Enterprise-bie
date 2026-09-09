import unittest
from bie.math_intelligence.tokenizer import *
class T(unittest.TestCase):
 def test_basic(self): self.assertEqual([x.value for x in tokenize("F=ma")],["F","=","ma"])
 def test_number(self): self.assertEqual(tokenize("3.14")[0].kind,"NUMBER")
 def test_command(self): self.assertEqual(tokenize(r"\\alpha")[0].kind,"COMMAND")
 def test_offsets(self): self.assertEqual(tokenize(" x ")[0].start,1)
if __name__=="__main__":unittest.main()
