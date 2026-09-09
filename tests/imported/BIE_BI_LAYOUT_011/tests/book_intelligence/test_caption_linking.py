
import unittest
from book_intelligence.caption_linking import *
class T(unittest.TestCase):
 def c(self):return {"kind":"caption","center":(.5,.5)}
 def test_link(self):self.assertEqual(link_caption(self.c(),[{"id":"f","center":(.5,.55)}]),"f")
 def test_nearest(self):self.assertEqual(link_caption(self.c(),[{"id":"a","center":(.5,.57)},{"id":"b","center":(.5,.51)}]),"b")
 def test_kind(self):
  with self.assertRaises(CaptionError):link_caption({"kind":"text","center":(0,0)},[])
 def test_far(self):
  with self.assertRaises(CaptionError):link_caption(self.c(),[{"id":"f","center":(0,0)}])
 def test_ambig(self):
  with self.assertRaises(CaptionError):link_caption(self.c(),[{"id":"a","center":(.45,.5)},{"id":"b","center":(.55,.5)}])
if __name__=="__main__":unittest.main()
