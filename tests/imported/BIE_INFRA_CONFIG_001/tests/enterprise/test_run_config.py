
import unittest
from bie.infrastructure.run_config import *
class T(unittest.TestCase):
    def test_valid(self): self.assertEqual(RunConfig(1,"r","src").validate().run_id,"r")
    def test_run_required(self):
        with self.assertRaises(ConfigError): RunConfig(1,"","src").validate()
    def test_source_required(self):
        with self.assertRaises(ConfigError): RunConfig(1,"r","").validate()
    def test_schema(self):
        with self.assertRaises(ConfigError): RunConfig(0,"r","s").validate()
    def test_outputs(self):
        with self.assertRaises(ConfigError): RunConfig(1,"r","s",("audio",)).validate()
    def test_policy(self):
        with self.assertRaises(ConfigError): RunConfig(1,"r","s",model_policy="cheap").validate()
    def test_canonical_outputs_sorted(self):
        d=RunConfig(1,"r","s",("game","video")).to_canonical_dict(); self.assertEqual(d["enabled_outputs"],["game","video"])
    def test_metadata_sorted_map(self):
        d=RunConfig(1,"r","s",metadata=(("b","2"),("a","1"))).to_canonical_dict(); self.assertEqual(list(d["metadata"]),["a","b"])
if __name__=="__main__": unittest.main()
