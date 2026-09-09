import unittest
from bie.document_intelligence.subsection_structure import *
class T(unittest.TestCase):
    def test_ok(self): self.assertEqual(len(validate([{"id":"x","section_id":"s","title":"T","order":1}],{"s"})),1)
    def test_parent(self):
        with self.assertRaises(SubsectionError): validate([{"id":"x","section_id":"z","title":"T","order":1}],{"s"})
    def test_title(self):
        with self.assertRaises(SubsectionError): validate([{"id":"x","section_id":"s","title":"","order":1}],{"s"})
    def test_dup(self):
        with self.assertRaises(SubsectionError): validate([{"id":"x","section_id":"s","title":"A","order":1},{"id":"x","section_id":"s","title":"B","order":2}],{"s"})
if __name__=="__main__": unittest.main()
