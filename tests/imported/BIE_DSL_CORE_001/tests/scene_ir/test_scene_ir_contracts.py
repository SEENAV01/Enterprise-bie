import unittest
from bie.scene_ir.contracts import *

def elem(**kw):
    d=dict(element_id="e1",kind="diagram",semantic_role="concept_representation",
           lifetime=TimeRange(0,5),spatial=SpatialIntent(x=.1,y=.1,width=.5,height=.5),
           content={},animations=[],interactions=[],concept_refs=["c1"],
           accessibility=Accessibility(label="concept diagram"))
    d.update(kw); return SceneElement(**d)
def scene(elements=None, duration=5):
    return Scene("s1","Scene",duration,"Teach concept",elements or [elem()])

class SceneIRTests(unittest.TestCase):
    def test_valid_scene(self): scene().validate()
    def test_not_fixed_layout(self):
        s=scene([elem(spatial=SpatialIntent(anchor="center",constraints=["keep_safe_area"]))])
        s.validate()
    def test_bad_normalized_geometry_fails(self):
        with self.assertRaises(SceneIRContractError):
            scene([elem(spatial=SpatialIntent(x=1.2,y=.1))]).validate()
    def test_animation_outside_lifetime_fails(self):
        a=AnimationTrack("a","reveal",TimeRange(4,6))
        with self.assertRaises(SceneIRContractError):
            scene([elem(animations=[a])]).validate()
    def test_meaningful_element_needs_semantic_link(self):
        with self.assertRaises(SceneIRContractError):
            scene([elem(concept_refs=[],learning_objective_refs=[],reasoning_decision_refs=[],source_artifact_refs=[])]).validate()
    def test_accessibility_required(self):
        with self.assertRaises(SceneIRContractError):
            scene([elem(accessibility=Accessibility())]).validate()
    def test_relative_target_must_exist(self):
        with self.assertRaises(SceneIRContractError):
            scene([elem(spatial=SpatialIntent(relative_to="missing"))]).validate()
    def test_duplicate_element_fails(self):
        with self.assertRaises(SceneIRContractError):
            scene([elem(),elem()]).validate()
    def test_multiple_visual_grammars_supported(self):
        es=[
          elem(element_id="map",kind="map"),
          elem(element_id="timeline",kind="timeline",spatial=SpatialIntent(anchor="bottom")),
          elem(element_id="eq",kind="equation",spatial=SpatialIntent(anchor="top")),
          elem(element_id="model",kind="model_3d",spatial=SpatialIntent(anchor="center"))
        ]
        scene(es).validate()

if __name__=="__main__":unittest.main()
