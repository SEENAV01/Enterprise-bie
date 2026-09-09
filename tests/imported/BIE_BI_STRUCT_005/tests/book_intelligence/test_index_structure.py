import unittest
from book_intelligence.index_structure import *
class T(unittest.TestCase):
    def test_ok(self): self.assertEqual(normalize([("Force",[3,2,3])],5)["Force"],(2,3))
    def test_empty_pages(self): self.assertEqual(normalize([("A",[])],2)["A"],())
    def test_page(self):
        with self.assertRaises(IndexError): normalize([("A",[3])],2)
    def test_term(self):
        with self.assertRaises(IndexError): normalize([("",[1])],2)
if __name__=="__main__": unittest.main()
