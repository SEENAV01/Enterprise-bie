from __future__ import annotations
from .contracts import *
from .common import *
from ..state_engine.reachability import analyze_reachability

def evaluate(system,start_id,challenge_targets,evidence_refs=('state-graph',)):
    if not isinstance(challenge_targets,dict) or not challenge_targets:raise ValueError('challenge targets required')
    targets=set(challenge_targets.values());analysis=analyze_reachability(system,start_id,targets);findings=[]
    missing=sorted(analysis['unreachable'])
    if missing:findings.append(finding('BIE-GAME-QA-003',1,'CHALLENGE_TARGET_UNREACHABLE',','.join(missing),refs=evidence_refs))
    empty=[cid for cid,target in challenge_targets.items() if target in analysis['reached'] and not analysis['paths'].get(target)]
    if empty:findings.append(finding('BIE-GAME-QA-003',2,'REACHABILITY_PATH_MISSING',','.join(empty),refs=evidence_refs))
    cov=ratio(len(analysis['reached']),len(targets));metrics=(QualityMetric('challenge_reachability',cov,1,1),QualityMetric('visited_states',float(len(analysis['visited_order'])),1,None,'count'))
    return result('BIE-GAME-QA-003',{'system':system,'start':start_id,'targets':challenge_targets},cov,metrics,findings,evidence_refs)
