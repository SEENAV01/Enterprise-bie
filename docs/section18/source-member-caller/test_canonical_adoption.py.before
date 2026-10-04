"""Integration-specific contracts; the handoff example is explicitly synthetic."""
from pathlib import Path
from hashlib import sha256
from dataclasses import asdict
import importlib, json, tempfile, unittest
ROOT=Path(__file__).resolve().parents[2]

def handoffs():
    from bie.visual_intelligence.capability_handoff import PrimitiveRequirement, TimingBinding, build_downstream_handoff
    from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff
    from bie.animation_intelligence.animation_plan_contract import AnimationPlan, AnimationTrack
    from bie.animation_intelligence.ani_sceneir_handoff import build_sceneir_handoff, require_sceneir_ready
    from bie.scene_ir.ani_dsl_adopter import adopt_ani_handoff
    source=('synthetic:canonical-adoption',);reason=('test:teaching-intent',)
    v=build_downstream_handoff(handoff_id='vis:test',plan_fingerprint=sha256(b'synthetic-plan').hexdigest(),
        primitives=[PrimitiveRequirement('e','text',source_refs=source,reasoning_refs=reason)],assets=[],
        timing=[TimingBinding('e',0,1000,reveal=True)],accessibility_ready=True,target_capabilities=[],target_profile='technical-test')
    adopted=adopt_visual_handoff(asdict(v),1,expected_plan_fingerprint=v.plan_fingerprint)
    track=AnimationTrack('t','reveal',('e',),0,1000,source,reason,payload={})
    plan=AnimationPlan('ani:test','1.0.0',adopted.handoff_id,adopted.plan_fingerprint,1,1,'technical-test',(track,),0,1000,source,reason)
    a=build_sceneir_handoff(plan);require_sceneir_ready(a)
    d,receipt=adopt_ani_handoff(a,scene_id='integration-test',title='Synthetic integration',duration_ms=1000,
        element_catalog=[{'element_id':'e','element_type':'text','props':{'text':'Synthetic integration, not a book lesson','font_size':24},
        'source_refs':source,'reasoning_refs':reason,'accessibility':{},'normalized_box':{'x':.1,'y':.2,'width':.8,'height':.3}}])
    return v,plan,a,d,receipt

class PreservedInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=json.loads((ROOT/'manifests/post_dir_supplied_inputs.json').read_text())
        cls.adoption=json.loads((ROOT/'manifests/post_dir_integration_004.json').read_text())
    def test_all_supplied_names_retained(self): self.assertEqual(len(self.inputs['files']),386)
    def test_no_same_name_overwrite(self):
        names=[x['name'] for x in self.inputs['files']];self.assertEqual(len(names),len(set(names)))
    def test_every_supplied_file_exact(self):
        for item in self.inputs['files']:
            p=ROOT/item['repository_path'];self.assertTrue(p.is_file(),item['name']);self.assertEqual(sha256(p.read_bytes()).hexdigest(),item['sha256'],item['name']);self.assertEqual(p.stat().st_size,item['bytes'])
    def test_source_mapping_exact(self):
        for item in self.adoption['source_members']:
            self.assertEqual(sha256((ROOT/item['canonical_path']).read_bytes()).hexdigest(),item['canonical_sha256'],item['canonical_path'])
    def test_rebuild_and_history_not_conflated(self):
        self.assertTrue((ROOT/'bie/visual_intelligence/rep_original_codec.py').is_file());self.assertFalse(self.inputs['product_accepted'])
    def test_missing_historical_bytes_not_fabricated(self):
        absent=self.inputs['unavailable_declared_archives'];self.assertEqual(len(absent),10)
        self.assertTrue(all(x['name'].startswith('BIE_VIS_LAYOUT_') for x in absent))
    def test_canonical_alias_layer_preserved(self):
        self.assertIn('class _LegacyFinder',(ROOT/'app/bie/__init__.py').read_text());self.assertFalse((ROOT/'app/bie/compiler').exists())
    def test_old_scene_contract_retained(self): self.assertTrue((ROOT/'bie/scene_ir/contracts.py').is_file())
    def test_required_workers_live_in_canonical_tree(self):
        for name in ('isolated_math_worker.py','operational_math.py','real_paint.py','visual_assets.py'):
            self.assertTrue((ROOT/'bie/compiler'/name).is_file())
    def test_known_cross_section_amendments_recorded(self):
        paths={x['path'] for x in self.adoption['collisions'] if x['owner']=='COMP'}
        self.assertEqual(paths,{'bie/scene_ir/diagram_element.py','bie/scene_ir/image_element.py'})
    def test_existing_enterprise_families_still_discovered(self):
        code=(ROOT/'scripts/test_enterprise.py').read_text()
        for family in ('reasoning','pedagogy','director','assembly','visual_intelligence','animation_intelligence','scene_ir','compiler'):
            self.assertIn(family,code)

class CanonicalIdentityAndHandoff(unittest.TestCase):
    def test_vis_alias_same_class(self):
        a=importlib.import_module('bie.visual_intelligence.visual_plan_contract');b=importlib.import_module('app.bie.visual_intelligence.visual_plan_contract');self.assertIs(a.VisualPlan,b.VisualPlan)
    def test_ani_alias_same_class(self):
        a=importlib.import_module('bie.animation_intelligence.animation_plan_contract');b=importlib.import_module('app.bie.animation_intelligence.animation_plan_contract');self.assertIs(a.AnimationPlan,b.AnimationPlan)
    def test_dsl_alias_same_class(self):
        a=importlib.import_module('bie.scene_ir.unified_scene_ir_contract');b=importlib.import_module('app.bie.scene_ir.unified_scene_ir_contract');self.assertIs(a.UnifiedSceneIRDocument,b.UnifiedSceneIRDocument)
    def test_comp_alias_same_function(self):
        a=importlib.import_module('bie.compiler.hardened_scene_compile');b=importlib.import_module('app.bie.compiler.hardened_scene_compile');self.assertIs(a.compile_h3_scene,b.compile_h3_scene)
    def test_actual_vis_producer_consumed_by_ani(self):
        v,plan,_,_,_=handoffs();self.assertEqual(plan.visual_plan_fingerprint,v.plan_fingerprint)
    def test_actual_ani_producer_consumed_by_dsl(self):
        _,plan,a,d,r=handoffs();self.assertEqual(a.animation_plan_fingerprint,plan.plan_fingerprint);self.assertEqual(r.adopted_track_count,1);self.assertEqual(d.tracks[0].action,'reveal')
    def test_source_and_reasoning_refs_survive(self):
        _,_,_,d,_=handoffs();self.assertEqual(d.source_refs,('synthetic:canonical-adoption',));self.assertEqual(d.reasoning_refs,('test:teaching-intent',))
    def test_handoff_cannot_claim_acceptance(self):
        for x in handoffs():self.assertFalse(x.accepted)
    def test_actual_dsl_output_compiles_to_source(self):
        from bie.compiler.hardened_scene_compile import compile_h3_scene
        _,_,_,d,_=handoffs();result=compile_h3_scene(d.to_dict());self.assertTrue(result.receipt.source_gate_passed);self.assertFalse(result.receipt.full_compile_verified);self.assertEqual(result.receipt.real_render_status,'NOT_RUN')
    def test_actual_cross_section_source_publication(self):
        from bie.compiler.hardened_scene_compile import publish_h3_scene,require_h3_workspace
        _,_,_,d,_=handoffs()
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'project';publish_h3_scene(d.to_dict(),out);self.assertTrue(require_h3_workspace(out).source_gate_passed);self.assertTrue((out/'src/Scene.tsx').is_file())
    def test_stale_vis_handoff_blocks_before_downstream(self):
        from bie.animation_intelligence.vis_ani_adoption import adopt_visual_handoff,StaleVisualHandoffError
        v,*_=handoffs();raw=asdict(v);raw['current']=False
        self.assertRaises(StaleVisualHandoffError,adopt_visual_handoff,raw,1)
