import unittest
from book_intelligence.chapter_structure import *
class T(unittest.TestCase):
    def c(self): return Chapter("c","Intro",1,5,1)
    def test_ok(self): self.assertEqual(len(validate([self.c()])),1)
    def test_dup(self):
        with self.assertRaises(ChapterError): validate([self.c(),self.c()])
    def test_range(self):
        with self.assertRaises(ChapterError): validate([Chapter("c","x",5,4,1)])
    def test_overlap(self):
        with self.assertRaises(ChapterError): validate([Chapter("a","a",1,3,1),Chapter("b","b",3,5,2)])
    def test_title(self):
        with self.assertRaises(ChapterError): validate([Chapter("a"," ",1,2,1)])
if __name__=="__main__": unittest.main()
