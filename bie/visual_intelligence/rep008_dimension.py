from dataclasses import dataclass
from .representation_core import *
@dataclass(frozen=True)
class Plan:
 plan_id:str;primary:str;secondary:tuple[str,...];dimension:str;status:str;complexity:float;fallbacks:tuple[str,...];evidence_refs:tuple[str,...];reasoning_refs:tuple[str,...];fingerprint:str;review_required:bool=True;accepted:bool=False
def dimension(intent,target,depth_semantics=False,occlusion_semantics=False,volumetric_structure=False,camera_motion_value=0.,three_d_required=False,estimated_complexity=.5):
 camera_motion_value=unit(camera_motion_value,'camera_motion_value');estimated_complexity=unit(estimated_complexity,'estimated_complexity');s=(.35 if depth_semantics else 0)+(.25 if occlusion_semantics else 0)+(.30 if volumetric_structure else 0)+.10*camera_motion_value
 if three_d_required:s=max(s,.9)
 if s>=.60:
  if not target.supports_3d:return decision(intent,'2d','BLOCKED' if three_d_required else 'REVIEW',.55,('3d_semantics_present_but_target_lacks_3d','2d_fallback'),{'3d_score':s},'dimension')
  if estimated_complexity>target.max_complexity:return decision(intent,'2d','REVIEW',.65,('3d_exceeds_target_complexity_budget','2d_fallback'),{'3d_score':s,'complexity':estimated_complexity},'dimension')
  return decision(intent,'3d','PASS',min(1,.70+s*.25),('depth_or_volume_semantics_justify_3d',),{'3d_score':s,'complexity':estimated_complexity},'dimension')
 return decision(intent,'2d','PASS',.9,('2d_preserves_required_semantics_at_lower_complexity',),{'3d_score':s,'complexity':estimated_complexity},'dimension')
def compose(intent,candidate_scores,dimension_decision,max_secondary=2,complexity=.5):
 complexity=unit(complexity,'complexity')
 if isinstance(max_secondary,bool) or not isinstance(max_secondary,int) or max_secondary<0:raise RepresentationError('max_secondary')
 ranked=sorted(candidate_scores,key=lambda x:(-x[1],x[0]))
 if not ranked:raise RepresentationError('candidate_scores required')
 primary=ranked[0][0];secondary=tuple(x[0] for x in ranked[1:1+max_secondary] if x[1]>=.6 and x[0]!=primary);fallbacks=();status='PASS'
 if dimension_decision.status in {'BLOCKED','UNSUPPORTED'}:status='BLOCKED';fallbacks=('2d',)
 elif dimension_decision.status=='REVIEW':status='REVIEW';fallbacks=('2d',)
 if complexity>.85 and len(secondary)>1:secondary=secondary[:1];status='REVIEW' if status=='PASS' else status
 payload={'intent':intent.intent_id,'primary':primary,'secondary':secondary,'dimension':dimension_decision.selected,'status':status,'complexity':complexity,'fallbacks':fallbacks}
 return Plan(intent.intent_id+':rep-plan',primary,secondary,dimension_decision.selected or 'unknown',status,complexity,fallbacks,intent.evidence_refs,intent.reasoning_refs,fp(payload),True,False)
