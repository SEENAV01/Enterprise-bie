import unittest
from bie.pedagogy.assessment_blueprint import AssessmentCell,build_assessment_blueprint

class TestAssessmentBlueprint(unittest.TestCase):
    def test_missing_transfer_cell_blocks(self):
        c=AssessmentCell("o","c","APPLY",None,False,("q1",),("e1",))
        r=build_assessment_blueprint([("o","c","APPLY",False),("o","c","APPLY",True)],[c])
        self.assertFalse(r.passed)
        self.assertEqual(r.uncovered_requirements,(("o","c","APPLY",True),))

    def test_provenance_required(self):
        with self.assertRaises(ValueError):
            build_assessment_blueprint([("o","c","APPLY",False)],
                [AssessmentCell("o","c","APPLY",None,False,("q",),())])
