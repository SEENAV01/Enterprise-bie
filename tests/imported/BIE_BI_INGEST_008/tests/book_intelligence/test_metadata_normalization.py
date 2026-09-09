
import unittest
from book_intelligence.metadata_normalization import *
class T(unittest.TestCase):
 def test_title(self):self.assertEqual(normalize({"title":" X "})["title"],"X")
 def test_author(self):self.assertEqual(normalize({"authors":" A "})["authors"],("A",))
 def test_authors(self):self.assertEqual(normalize({"authors":["A","B"]})["authors"],("A","B"))
 def test_empty(self):self.assertIsNone(normalize({})["title"])
 def test_year(self):
  with self.assertRaises(MetadataError):normalize({"published_year":99})
if __name__=="__main__":unittest.main()
