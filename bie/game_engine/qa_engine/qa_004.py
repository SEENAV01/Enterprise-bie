from __future__ import annotations
from collections import defaultdict,deque
from .contracts import *
from .common import *
from .policy import GameQAPolicy
from ..state_engine.reachability import analyze_reachability

def evaluate(system,start_id,goal_ids,policy=GameQAPolicy(),evidence_refs=('state-graph',)):
    policy.validate();analysis=analyze_reachability(system,start_id,set(goal_ids));known={n.node_id:n for n in system.nodes};visited=set(analysis['visited_order']);unreachable_all=sorted(set(known)-visited);dead=list(analysis['dead_ends']);findings=[]
    if len(dead)>policy.max_nonterminal_dead_ends:findings.append(finding('BIE-GAME-QA-004',1,'NONTERMINAL_DEAD_END',','.join(dead),refs=evidence_refs))
    if unreachable_all:findings.append(finding('BIE-GAME-QA-004',2,'UNREACHABLE_STATE',','.join(unreachable_all),refs=evidence_refs))
    bad_cycles=[c for c in analysis['cycles'] if not any(known[x].terminal for x in c if x in known)]
    if bad_cycles:findings.append(finding('BIE-GAME-QA-004',3,'NONTERMINAL_CYCLE',';'.join('>'.join(c) for c in bad_cycles),refs=evidence_refs))
    score=1.0 if not findings else max(0,1-.25*len(findings));metrics=(QualityMetric('nonterminal_dead_ends',float(len(dead)),0,float(policy.max_nonterminal_dead_ends),'count'),QualityMetric('unreachable_states',float(len(unreachable_all)),0,0,'count'),QualityMetric('nonterminal_cycles',float(len(bad_cycles)),0,0,'count'))
    return result('BIE-GAME-QA-004',{'system':system,'start':start_id,'goals':tuple(goal_ids)},score,metrics,findings,evidence_refs)
