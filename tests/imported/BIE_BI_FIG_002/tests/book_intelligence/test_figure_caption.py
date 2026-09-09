
import unittest
from book_intelligence.figure_caption import *
class T(unittest.TestCase):
 def test_link(self):self.assertEqual(link([{"id":"f","page":1,"box":(0,0,.5,.5)}],[{"id":"c","page":1,"box":(0,.52,.5,.6)}])["f"],"c")
 def test_page(self):self.assertEqual(link([{"id":"f","page":1,"box":(0,0,.5,.5)}],[{"id":"c","page":2,"box":(0,.52,.5,.6)}]),{})
 def test_far(self):self.assertEqual(link([{"id":"f","page":1,"box":(0,0,.5,.5)}],[{"id":"c","page":1,"box":(0,.9,.5,1)}]),{})
 def test_empty(self):self.assertEqual(link([],[]),{})
if __name__=="__main__":unittest.main()
