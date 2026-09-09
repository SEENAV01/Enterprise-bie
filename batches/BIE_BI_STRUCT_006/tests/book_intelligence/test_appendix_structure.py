import unittest
from book_intelligence.appendix_structure import *
class T(unittest.TestCase):
    def test_ok(self): self.assertEqual(len(validate([{"id":"a","title":"Constants","start_page":10,"end_page":11}])),1)
    def test_range(self):
        with self.assertRaises(AppendixError): validate([{"id":"a","title":"x","start_page":2,"end_page":1}])
    def test_title(self):
        with self.assertRaises(AppendixError): validate([{"id":"a","title":"","start_page":1,"end_page":1}])
    def test_dup(self):
        with self.assertRaises(AppendixError): validate([{"id":"a","title":"x","start_page":1,"end_page":1},{"id":"a","title":"y","start_page":2,"end_page":2}])
if __name__=="__main__": unittest.main()
