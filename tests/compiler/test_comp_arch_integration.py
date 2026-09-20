import unittest
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedTrack,UnifiedSceneIRDocument
from bie.compiler.compiler_architecture import CompilerTargetProfile,CompilerRequest,make_compiler_plan
from bie.compiler.scene_ir_loader import load_scene_ir_payload
from bie.compiler.compiler_capability_registry import CompilerCapabilityRegistry,CompilerAdapterCapability
from bie.compiler.component_registry import ComponentRegistry,ComponentSpec
from bie.compiler.compiler_diagnostics import build_diagnostic_report
from bie.compiler.deterministic_codegen import plan_deterministic_codegen

class T(unittest.TestCase):
 def doc(self):
  e=UnifiedElement("e","text",{"text":"Hello"},("src",),("r",))
  t=UnifiedTrack("t","e","reveal",0,100,{},("src",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","Title",100,(e,),(t,),("src",),("r",))

 def test_architecture_to_codegen_prebuild_chain(self):
  d=self.doc()
  loaded=load_scene_ir_payload(d)
  req=CompilerRequest("request:1",d.scene_id,d.fingerprint,CompilerTargetProfile("web",1920,1080,30),"1.0.0",42)
  plan=make_compiler_plan(req)
  self.assertEqual(plan.build_status,"NOT_RUN")
  self.assertEqual(plan.render_status,"NOT_RUN")

  caps=CompilerCapabilityRegistry()
  caps.register(CompilerAdapterCapability("cap:text","remotion:text","1",("text",),("reveal",),("web",),10,True))
  self.assertEqual(caps.require(element_type="text",action="reveal",profile="web").adapter_id,"remotion:text")

  components=ComponentRegistry()
  components.register(ComponentSpec("component:text","text","TextElement","@bie/primitives/text","cap:text",("web",),("text",),10))
  self.assertEqual(components.require("text","web").component_name,"TextElement")

  report=build_diagnostic_report([])
  self.assertTrue(report.passed)

  files=[
    ("src/Scene.tsx","export const Scene = () => <div>Hello</div>;\n"),
    ("src/compiler-input.json",'{"sceneId":"scene"}\n')
  ]
  cg=plan_deterministic_codegen(
    scene_fingerprint=loaded.scene_fingerprint,
    compiler_version="1.0.0",
    deterministic_seed=42,
    component_snapshot=components.snapshot(),
    files=files,
  )
  self.assertEqual(len(cg.files),2)
  self.assertFalse(cg.accepted)
