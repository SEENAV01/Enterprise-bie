import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.map_strategy import assess
from tests.strategy_test_support import bundle,missing_runtime
class MapStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.MAP)).eligible)
    def test_two_entities_required(self):
        b=bundle(StrategyKind.MAP);self.assertFalse(assess(replace(b,geo_entities=b.geo_entities[:1])).eligible)
    def test_coordinate_validation(self):
        b=bundle(StrategyKind.MAP);bad=replace(b.geo_entities[0],latitude=100)
        with self.assertRaises(GameContractError):assess(replace(b,geo_entities=(bad,b.geo_entities[1])))
    def test_map_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.MAP),'map_runtime')).eligible)
    def test_not_background_image(self):self.assertIn('map_is_semantic_workspace_not_background_image',assess(bundle(StrategyKind.MAP)).studio_design_requirements)
    def test_camera_purpose(self):self.assertIn('camera_zoom_has_learning_purpose',assess(bundle(StrategyKind.MAP)).studio_design_requirements)
    def test_score(self):self.assertGreaterEqual(assess(bundle(StrategyKind.MAP)).score,80)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.MAP)),assess(bundle(StrategyKind.MAP)))
if __name__=='__main__':unittest.main()
