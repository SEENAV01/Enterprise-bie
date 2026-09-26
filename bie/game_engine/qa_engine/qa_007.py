from __future__ import annotations
import json,re
from .contracts import *
from .common import *
from .policy import GameQAPolicy
from ..interaction import ActionKind
SPATIAL={ActionKind.DRAG,ActionKind.DROP,ActionKind.ADJUST,ActionKind.PLACE,ActionKind.ORDER}
def evaluate(document,bundle,browser_evidence,policy=GameQAPolicy()):
    policy.validate();document.validate();findings=[];total=0;passed=0;refs=[]
    actions=[];entities=[]
    for exp in document.experiences:
      for level in exp.levels:
        actions.extend(level.interaction.actions);entities.extend(level.visual.entities)
    for a in actions:
        total+=1
        ok=bool(a.accessible_label.strip()) and (a.kind not in SPATIAL or bool(a.keyboard_equivalent));passed+=int(ok)
        if not ok:findings.append(finding('BIE-GAME-QA-007',len(findings)+1,'ACTION_ACCESSIBILITY_GAP',a.action_id))
    for e in entities:
        total+=1;ok=bool(e.accessible_description and e.accessible_description.strip());passed+=int(ok)
        if not ok:findings.append(finding('BIE-GAME-QA-007',len(findings)+1,'VISUAL_ACCESSIBILITY_GAP',e.entity_id))
    art=next((x for x in bundle.artifacts if x.path=='runtime/interactions.ts'),None)
    if art is None:findings.append(finding('BIE-GAME-QA-007',90,'INTERACTION_ARTIFACT_MISSING','runtime/interactions.ts missing'))
    else:
        refs=art.source_refs
        if 'keyboard_parity_required":true' not in art.content:findings.append(finding('BIE-GAME-QA-007',91,'COMPILED_KEYBOARD_PARITY_MISSING','compiled interaction policy missing',refs=refs))
    try:browser_evidence.validate()
    except Exception as e:findings.append(finding('BIE-GAME-QA-007',92,'BROWSER_ACCESSIBILITY_RUNTIME_INVALID',str(e),refs=refs))
    if browser_evidence.slide_deck or browser_evidence.entity_count<1:findings.append(finding('BIE-GAME-QA-007',93,'RUNTIME_SEMANTIC_ROOT_INVALID','runtime is slide-like or lacks semantic entities',refs=refs))
    cov=ratio(passed,total);score=cov if not findings else max(0,cov-.1*len(findings));metrics=(QualityMetric('accessibility_contract_coverage',cov,policy.accessibility_min,1),QualityMetric('semantic_entities',float(browser_evidence.entity_count),1,None,'count'))
    return result('BIE-GAME-QA-007',{'document':document.fingerprint(),'bundle':bundle.receipt.bundle_fingerprint,'browser':browser_evidence.bundle_sha256},score,metrics,findings,refs or ('accessibility',))
