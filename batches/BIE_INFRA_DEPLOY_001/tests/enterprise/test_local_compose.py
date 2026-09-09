
import unittest
from enterprise.local_compose import *
class T(unittest.TestCase):
 def test_valid(self):self.assertTrue(validate(compose_spec()))
 def test_services(self):self.assertEqual(len(compose_spec()["services"]),4)
 def test_pg(self):self.assertTrue(compose_spec()["services"]["postgres"]["healthcheck"])
 def test_bad(self):
  with self.assertRaises(DeployError):validate({"services":{}})
if __name__=="__main__":unittest.main()
