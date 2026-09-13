import unittest
from bie.pedagogy.cognitive_load_qa import cognitive_load_qa

class TestCognitiveLoadQA(unittest.TestCase):
    def test_overload_detected(self):
        self.assertFalse(cognitive_load_qa([("s1",2.0)]).passed)

    def test_abrupt_jump_detected(self):
        r=cognitive_load_qa([("s1",.2),("s2",1.2)])
        self.assertEqual(r.abrupt_jumps,("s1->s2",))
