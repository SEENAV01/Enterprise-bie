import unittest
from app.bie.prerequisite_intelligence.assumed_knowledge import *
class T(unittest.TestCase):
 def test_recall(self): self.assertEqual(detect_assumed_knowledge("Recall that vectors have direction.",{"vectors"})[0].concept,"vectors")
 def test_none(self): self.assertEqual(detect_assumed_knowledge("Vectors are introduced now.",{"vectors"}),[])
 def test_case(self): self.assertEqual(len(detect_assumed_knowledge("AS YOU KNOW, ALGEBRA is useful.",{"algebra"})),1)
 def test_sorted(self): self.assertEqual([x.concept for x in detect_assumed_knowledge("Recall that a and b matter.",{"b","a"})],["a","b"])
if __name__=="__main__": unittest.main()
