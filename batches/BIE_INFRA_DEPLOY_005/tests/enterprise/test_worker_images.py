
import unittest
from enterprise.worker_images import *
class T(unittest.TestCase):
 def test_cpu(self):self.assertTrue(validate(WorkerImage("cpu_general","w:1",frozenset({"python"}))))
 def test_render(self):self.assertTrue(validate(WorkerImage("render_gpu","r:1",frozenset({"remotion","ffmpeg","gpu"}))))
 def test_unknown(self):
  with self.assertRaises(WorkerImageError):validate(WorkerImage("x","x:1",frozenset()))
 def test_missing(self):
  with self.assertRaises(WorkerImageError):validate(WorkerImage("render_gpu","r:1",frozenset({"gpu"})))
 def test_latest(self):
  with self.assertRaises(WorkerImageError):validate(WorkerImage("cpu_general","w:latest",frozenset({"python"})))
if __name__=="__main__":unittest.main()
