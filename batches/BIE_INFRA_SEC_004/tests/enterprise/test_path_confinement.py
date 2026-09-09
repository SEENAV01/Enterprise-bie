
import unittest,tempfile,os
from enterprise.path_confinement import *
class T(unittest.TestCase):
 def test_inside(self):
  with tempfile.TemporaryDirectory() as d:self.assertTrue(str(confined_path(d,"a/b")).startswith(d))
 def test_parent(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(PathSecurityError):confined_path(d,"../x")
 def test_absolute(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(PathSecurityError):confined_path(d,"/tmp/x")
 def test_normalized(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(confined_path(d,"a/../b").name,"b")
if __name__=="__main__":unittest.main()
