import unittest
from bie.pedagogy.multi_constraint_sequencer import CurriculumNode,SequenceConstraint,sequence_curriculum

class TestMultiConstraintSequencer(unittest.TestCase):
    def test_hard_prerequisite_wins(self):
        r=sequence_curriculum([
            CurriculumNode("advanced",1,.4,.9),
            CurriculumNode("basic",2,.4,.2)
        ],[SequenceConstraint("basic","advanced","PREREQUISITE",True,1)])
        self.assertEqual(r.order,("basic","advanced"))

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            sequence_curriculum([CurriculumNode("a",0,.2,.5),CurriculumNode("b",1,.2,.5)],[
                SequenceConstraint("a","b","X"),SequenceConstraint("b","a","X")])

    def test_soft_violation_preserved(self):
        r=sequence_curriculum([
            CurriculumNode("a",0,.2,.9),CurriculumNode("b",1,.2,.1)
        ],[SequenceConstraint("b","a","SOURCE",False,.2)])
        self.assertEqual(r.violated_soft_constraints,(("b","a","SOURCE"),))
