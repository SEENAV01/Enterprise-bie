import unittest
from bie.pedagogy.pedagogy_replay_manifest import build_pedagogy_replay_manifest,replay_diff

class TestPedagogyReplayManifest(unittest.TestCase):
    def make(self,**kw):
        x=dict(input_hashes={"book":"h1"},policy_version="p1",learner_state_version="l1",
               reasoning_fingerprints={"r":"f1"},output_hashes={"plan":"h2"},environment_fingerprint="env")
        x.update(kw); return build_pedagogy_replay_manifest(**x)

    def test_order_independent(self):
        a=build_pedagogy_replay_manifest(input_hashes={"b":"2","a":"1"},policy_version="p",
            learner_state_version="l",reasoning_fingerprints={"y":"2","x":"1"},output_hashes={"o":"3"},environment_fingerprint="e")
        b=build_pedagogy_replay_manifest(input_hashes={"a":"1","b":"2"},policy_version="p",
            learner_state_version="l",reasoning_fingerprints={"x":"1","y":"2"},output_hashes={"o":"3"},environment_fingerprint="e")
        self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_diff(self):
        self.assertEqual(replay_diff(self.make(),self.make(policy_version="p2")),("policy_version",))
