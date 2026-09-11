import unittest
from bie.reasoning.temporal_collision_guard import *

class T(unittest.TestCase):
    def test_identical_nonblocking(self):
        e=[FileRecord("x.py","a","old")]
        i=[FileRecord("x.py","a","new")]
        self.assertEqual(detect_collisions(e,i)[0].kind,"IDENTICAL")
        self.assertEqual(blocking_collisions(e,i),())
    def test_conflict_blocks(self):
        e=[FileRecord("x.py","a","old")]
        i=[FileRecord("x.py","b","new")]
        self.assertEqual(blocking_collisions(e,i)[0].kind,"CONTENT_CONFLICT")
    def test_new_path(self):
        self.assertEqual(detect_collisions([], [FileRecord("x.py","a","new")]),())
    def test_deterministic(self):
        e=[FileRecord("b.py","a","o"),FileRecord("a.py","a","o")]
        i=[FileRecord("b.py","b","n2"),FileRecord("a.py","b","n1")]
        self.assertEqual([c.path for c in detect_collisions(e,i)],["a.py","b.py"])
