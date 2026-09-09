import unittest
from enterprise.execution_graph import *

class EnterpriseIntegrationTests(unittest.TestCase):
    def test_default_graph_valid(self):
        default_enterprise_graph().validate()

    def test_reasoning_to_scene_ir(self):
        g=default_enterprise_graph()
        self.assertTrue(g._reachable("REASONING","SCENE_IR"))

    def test_reasoning_to_game_ir(self):
        g=default_enterprise_graph()
        self.assertTrue(g._reachable("REASONING","GAME_IR"))

    def test_scene_ir_required_before_video_code(self):
        g=default_enterprise_graph()
        self.assertTrue(g._reachable("SCENE_IR","VIDEO_CODE"))

    def test_game_ir_required_before_game_code(self):
        g=default_enterprise_graph()
        self.assertTrue(g._reachable("GAME_IR","GAME_CODE"))

    def test_raw_source_video_bypass_rejected(self):
        g=default_enterprise_graph()
        g.edges["SOURCE"].append("VIDEO_CODE")
        with self.assertRaises(EnterpriseGraphError):g.validate()

    def test_raw_source_game_bypass_rejected(self):
        g=default_enterprise_graph()
        g.edges["SOURCE"].append("GAME_CODE")
        with self.assertRaises(EnterpriseGraphError):g.validate()

    def test_all_qa_converges_to_release(self):
        g=default_enterprise_graph()
        for s in ["VIDEO_QA","GAME_QA","LINEAGE_QA","REGRESSION_QA","REPRODUCIBILITY_QA"]:
            self.assertTrue(g._reachable(s,"RELEASE_EVALUATION"))

    def test_release_manifest_derived_from_evaluation(self):
        g=default_enterprise_graph()
        self.assertTrue(g._reachable("RELEASE_EVALUATION","RELEASE_MANIFEST"))

    def test_graph_cycle_rejected(self):
        g=default_enterprise_graph()
        g.edges["RELEASE_MANIFEST"]=["SOURCE"]
        with self.assertRaises(EnterpriseGraphError):g.validate()

if __name__=="__main__":unittest.main()
