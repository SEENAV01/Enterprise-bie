from __future__ import annotations
from .provenance_adapter import all_refs
import json
from ..canonical import fingerprint
from .contracts import *
def build_manifest(ctx:CompilerContext,artifacts):
    rows=[{'kind':a.kind.value,'path':a.path,'media_type':a.media_type,'sha256':a.sha256} for a in sorted(artifacts,key=lambda x:x.path)]
    edges=[['runtime/index.html','runtime/bootstrap.js'],['runtime/bootstrap.js','runtime/react-runtime.js'],['runtime/bootstrap.js','runtime/runtime-controller.js'],['runtime/bootstrap.js','runtime/state-machine.js'],['runtime/bootstrap.js','runtime/rules.js'],['runtime/bootstrap.js','runtime/interactions.js'],['runtime/bootstrap.js','runtime/scoring.js'],['runtime/bootstrap.js','runtime/feedback.js'],['runtime/bootstrap.js','runtime/adaptation.js'],['runtime/bootstrap.js','runtime/telemetry.js'],['runtime/react-runtime.js','runtime/game-ir.json'],['runtime/interactions.js','runtime/source-map.json']]
    data={'schema_version':'bie.game.runtime-manifest/2','document_fingerprint':ctx.document.fingerprint(),'compile_profile':ctx.compile_profile,'artifacts':rows,'expected_build_outputs':['runtime/bootstrap.js','runtime/react-runtime.js','runtime/state-machine.js','runtime/rules.js','runtime/interactions.js','runtime/scoring.js','runtime/feedback.js','runtime/adaptation.js','runtime/telemetry.js','runtime/runtime-controller.js'],'dependency_edges':edges,'security':{'remote_network':False,'inline_script':False,'eval':False,'dynamic_import':False,'telemetry_raw_text':False},'quality':{'studio_grade':True,'slide_deck_default':False,'semantic_visuals':True,'stateful_interaction':True,'pedagogical_motion':True,'accessibility':True},'product_accepted':False}
    refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.RUNTIME_MANIFEST,'runtime/manifest.json','application/json',json.dumps(data,sort_keys=True,separators=(',',':')),refs)
