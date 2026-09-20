from dataclasses import dataclass
from .representation_core import *
@dataclass(frozen=True)
class Fitness:
 candidate_id:str;total:float;semantic_fidelity:float;explanatory_power:float;cognitive_fit:float;timing_fit:float;capability_fit:float;evidence_confidence:float;blockers:tuple[str,...];fingerprint:str
W={'semantic_fidelity':.30,'explanatory_power':.20,'cognitive_fit':.15,'timing_fit':.10,'capability_fit':.15,'evidence_confidence':.10}
def score(intent,candidate,target,semantic_fidelity,explanatory_power,cognitive_fit,timing_fit,evidence_confidence,weights=None):
 weights=dict(W if weights is None else weights)
 if set(weights)!=set(W) or abs(sum(weights.values())-1)>1e-9:raise RepresentationError('weights')
 vals={k:unit(v,k) for k,v in {'semantic_fidelity':semantic_fidelity,'explanatory_power':explanatory_power,'cognitive_fit':cognitive_fit,'timing_fit':timing_fit,'evidence_confidence':evidence_confidence}.items()};b=[];cap=1.
 for req in candidate.capabilities:
  if req=='3d' and not target.supports_3d:b.append('target_lacks_3d')
  elif req=='simulation' and not target.supports_simulation:b.append('target_lacks_simulation')
  elif req not in {'3d','simulation'} and req not in target.capabilities:b.append('missing_capability:'+req)
 if b:cap=0.
 vals['capability_fit']=cap;total=sum(vals[k]*weights[k] for k in weights)
 if b:total=min(total,.49)
 p={'id':candidate.candidate_id,'vals':vals,'b':b,'t':round(total,6)}
 return Fitness(candidate.candidate_id,round(total,6),vals['semantic_fidelity'],vals['explanatory_power'],vals['cognitive_fit'],vals['timing_fit'],cap,vals['evidence_confidence'],tuple(b),fp(p))
