import unittest
from bie.reasoning.reasoning_replay_manifest import build_replay_manifest,compare_replay

class TestReplayManifest(unittest.TestCase):
    def m(self,**kw):
        x=dict(input_hashes={"book":"h1"},policy_version="p1",config_hash="c1",
               decision_fingerprints={"d":"f1"},output_hashes={"o":"h2"},environment_fingerprint="env")
        x.update(kw); return build_replay_manifest(**x)
    def test_order_independent(self):
        a=build_replay_manifest(input_hashes={"b":"2","a":"1"},policy_version="p",config_hash="c",
          decision_fingerprints={"y":"2","x":"1"},output_hashes={"o":"3"},environment_fingerprint="e")
        b=build_replay_manifest(input_hashes={"a":"1","b":"2"},policy_version="p",config_hash="c",
          decision_fingerprints={"x":"1","y":"2"},output_hashes={"o":"3"},environment_fingerprint="e")
        self.assertEqual(a.fingerprint(),b.fingerprint())
    def test_difference_reported(self):
        self.assertEqual(compare_replay(self.m(),self.m(config_hash="c2")),("config_hash",))
    def test_blank_version_rejected(self):
        with self.assertRaises(ValueError): self.m(policy_version="")
