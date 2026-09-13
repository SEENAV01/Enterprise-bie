import unittest
from bie.pedagogy.pedagogy_realbook_fixture import SourceAnchor,PedagogyArtifactRef,evaluate_pedagogy_fixture,REQUIRED_STAGES

class TestPedagogyRealBookFixture(unittest.TestCase):
    def complete(self):
        arts=[]
        prev=None
        for i,s in enumerate(REQUIRED_STAGES):
            arts.append(PedagogyArtifactRef(f"a{i}",s,("e1",),(() if prev is None else (prev,))))
            prev=f"a{i}"
        return arts

    def test_complete_fixture_passes(self):
        self.assertTrue(evaluate_pedagogy_fixture("fx",[SourceAnchor("e1",1,"text")],self.complete()).passed)

    def test_missing_anchor_blocks(self):
        arts=self.complete()
        arts[-1]=PedagogyArtifactRef(arts[-1].artifact_id,arts[-1].stage,("missing",),arts[-1].parent_ids)
        r=evaluate_pedagogy_fixture("fx",[SourceAnchor("e1",1,"text")],arts)
        self.assertFalse(r.passed)
        self.assertEqual(r.missing_anchor_ids,("missing",))
