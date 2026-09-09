
import unittest
from bie.infrastructure.production_containers import *
class T(unittest.TestCase):
 def c(self,**k):
  d=dict(name="api",image="bie-api:1.0.0",run_as_non_root=True,read_only_root=True,healthcheck="/health",cpu_limit=1,memory_mb=512);d.update(k);return ContainerSpec(**d)
 def test_ok(self):self.assertTrue(validate(self.c()))
 def test_latest(self):
  with self.assertRaises(ContainerError):validate(self.c(image="x:latest"))
 def test_root(self):
  with self.assertRaises(ContainerError):validate(self.c(run_as_non_root=False))
 def test_rw(self):
  with self.assertRaises(ContainerError):validate(self.c(read_only_root=False))
 def test_mem(self):
  with self.assertRaises(ContainerError):validate(self.c(memory_mb=64))
if __name__=="__main__":unittest.main()
