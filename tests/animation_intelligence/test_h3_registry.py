import unittest
from bie.animation_intelligence.domain_animation_registry import *
class T(unittest.TestCase):
 def test_register_resolve(self):
  r=DomainAnimationRegistry();r.register(DomainAdapter("chem","chemistry","1",("reaction",),10));self.assertEqual(r.resolve("chemistry","reaction").adapter_id,"chem")
 def test_priority(self):
  r=DomainAnimationRegistry();r.register(DomainAdapter("a","x","1",("c",),1));r.register(DomainAdapter("b","x","1",("c",),2));self.assertEqual(r.resolve("x","c").adapter_id,"b")
 def test_duplicate(self):
  r=DomainAnimationRegistry();a=DomainAdapter("a","x","1",("c",),1);r.register(a)
  with self.assertRaises(DomainRegistryError):r.register(a)
 def test_missing(self):
  with self.assertRaises(DomainRegistryError):DomainAnimationRegistry().resolve("x","c")
 def test_meta(self):
  with self.assertRaises(DomainRegistryError):DomainAnimationRegistry().register(DomainAdapter("","x","1",("c",),1))
 def test_snapshot(self):
  r=DomainAnimationRegistry();r.register(DomainAdapter("a","x","1",("c",),1));self.assertEqual(len(r.snapshot()),1)
 def test_provider_neutral(self):self.assertTrue(DomainAdapter("a","x","1",("c",),1).provider_neutral)
