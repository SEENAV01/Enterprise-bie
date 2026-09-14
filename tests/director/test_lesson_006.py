import unittest
from bie.director.recap_strategy import *
class T(unittest.TestCase):
    def test_retrieval(self): self.assertEqual(len(plan_recap(["x"]).retrieval_prompts),1)
    def test_transfer_off(self): self.assertIsNone(plan_recap(["x"],transfer_required=False).transfer_prompt)
