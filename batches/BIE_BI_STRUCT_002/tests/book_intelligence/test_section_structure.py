import unittest
from book_intelligence.section_structure import *
class T(unittest.TestCase):
    def s(self): return Section("s","c","Title",1,"p1:r1")
    def test_ok(self): self.assertEqual(len(validate([self.s()])),1)
    def test_dup(self):
        with self.assertRaises(SectionError): validate([self.s(),self.s()])
    def test_order(self):
        with self.assertRaises(SectionError): validate([Section("a","c","A",1,"x"),Section("b","c","B",1,"y")])
    def test_anchor(self):
        with self.assertRaises(SectionError): validate([Section("a","c","A",1,"")])
if __name__=="__main__": unittest.main()
