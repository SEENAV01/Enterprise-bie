
import unittest
from bie.model_gateway.provider_registry import *
class T(unittest.TestCase):
 def d(self):return ProviderDescriptor("p","m",frozenset({"text","vision"}))
 def test_register(self):r=ProviderRegistry();r.register(self.d(),object());self.assertEqual(r.get("p","m")[0].model_id,"m")
 def test_duplicate(self):
  r=ProviderRegistry();r.register(self.d(),1)
  with self.assertRaises(RegistryError):r.register(self.d(),2)
 def test_candidate(self):r=ProviderRegistry();r.register(self.d(),1);self.assertEqual(len(r.candidates({"vision"})),1)
 def test_missing_cap(self):r=ProviderRegistry();r.register(self.d(),1);self.assertEqual(len(r.candidates({"embeddings"})),0)
 def test_missing(self):
  with self.assertRaises(RegistryError):ProviderRegistry().get("x","y")
if __name__=="__main__":unittest.main()
