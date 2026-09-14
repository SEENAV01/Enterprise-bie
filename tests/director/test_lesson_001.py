import unittest
from bie.director.lesson_architecture_contract import *
class T(unittest.TestCase):
    def test_deterministic(self):
        a=LessonSceneIntent("a","hook",("o",),("e",)); b=LessonSceneIntent("b","explain",("o",),("e",),("a",))
        self.assertEqual(build_lesson_architecture("l","T",[b,a],["o"],["s"],"v").fingerprint(),build_lesson_architecture("l","T",[a,b],["o"],["s"],"v").fingerprint())
    def test_parent(self):
        with self.assertRaises(ValueError): build_lesson_architecture("l","T",[LessonSceneIntent("a","x",("o",),("e",),("z",))],["o"],["s"],"v")
