"""HARD012: causal/temporal/frame-aware checks on real native decision records.

Policy models are operator controlled. Causal model agreement is not empirical
causation; unknown mechanisms or overlapping time intervals require review.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from ...reasoning.decision_contracts import ReasoningDecision,ReasoningDecisionGraph
from .common import *

@dataclass(frozen=True)
class ReasonPolicy(PolicyDigest):
    required_ids: tuple[str,...]
    conditions: tuple[tuple[str,str,str],...]  # decision ID, source artifact, literal qualifier
    causal_edges: tuple[tuple[str,str,str],...] # cause,effect,intervention/mechanism/correlation
    chronology: tuple[tuple[str,str,str],...] # event, earliest, latest on same rational clock
    frames: tuple[tuple[str,str,str,str,str,str,str],...] # name,a,b,c,d,tx,ty to common frame
    limits: Limits=Limits()
    def __post_init__(self):
        ids(self.required_ids,'DECISION');require(type(self.limits)is Limits,'RE_LIMITS')
        for seq in (self.conditions,self.causal_edges,self.chronology,self.frames):require(type(seq)is tuple and len(seq)<=1024,'RE_POLICY_ROWS')
        require(len({r[0]for r in self.chronology})==len(self.chronology),'RE_EVENT_DUPLICATE')
        require(len({r[0]for r in self.frames})==len(self.frames),'RE_FRAME_DUPLICATE')
        require(len({r[:2]for r in self.causal_edges})==len(self.causal_edges),'RE_EDGE_DUPLICATE')
        for c,e,k in self.causal_edges:
            token(c,'cause');token(e,'effect');require(c!=e and k in ('intervention','mechanism','correlation'),'RE_CAUSAL_BASIS')
        for e,l,h in self.chronology:token(e,'event');require(rational(l)<=rational(h),'RE_CHRONOLOGY')
        for name,a,b,c,d,x,y in self.frames:
            token(name,'frame');require(rational(a)*rational(d)-rational(b)*rational(c)!=0,'RE_SINGULAR_FRAME');rational(x);rational(y)
        for d,s,t in self.conditions:require(d in self.required_ids,'RE_CONDITION_SUBJECT');token(s,'source');text(t,'condition')

def evaluate_reasoning(native,ref,source_refs,root,binding,policy):
    require(type(native)is tuple and 1<=len(native)<=policy.limits.max_records and all(type(d)is ReasoningDecision for d in native),'RE_NATIVE_RECORDS')
    ReasoningDecisionGraph(list(native)).validate()
    byid={d.decision_id:d for d in native};require(set(byid)==set(policy.required_ids),'RE_NATIVE_INVENTORY')
    data=read_input(root,ref,binding,policy,'BIE-QA-HARD-012',('native_digest','claims'))
    require(data['native_digest']==native_digest([asdict(d)for d in native]),'RE_NATIVE_DIGEST')
    src=verify_sources(root,source_refs);findings=[]
    for d in native:
        require(all(e.artifact_id in src for e in d.evidence_refs),'RE_UNBOUND_EVIDENCE')
        require(all(type(v)is str for v in d.constraints+d.premises),'RE_NATIVE_STATEMENTS')
        if d.requires_review or d.uncertainty:findings.append(Finding('NATIVE_REASONING_REQUIRES_REVIEW',d.decision_id))
    claims=items(data['claims'],'RE_CLAIMS',1,policy.limits.max_records);claims=unique(claims,'decision_id','RE_CLAIM_DUPLICATE')
    require(set(claims)==set(byid),'RE_CLAIM_INVENTORY')
    for did,sid,qualifier in policy.conditions:
        require(sid in src and qualifier in src[sid],'RE_CONDITION_SOURCE')
        d=byid[did]
        if qualifier not in d.rationale_summary and qualifier not in d.constraints:findings.append(Finding('RE_CONDITION_OMITTED',did,'BLOCKER'))
    times={k:(rational(a),rational(b))for k,a,b in policy.chronology};edges={(c,e):k for c,e,k in policy.causal_edges}
    frames={r[0]:list(map(rational,r[1:]))for r in policy.frames}
    def world(p):
        fields(p,('frame','x','y'));require(p['frame']in frames,'RE_UNKNOWN_COORDINATE_FRAME')
        a,b,c,d,tx,ty=frames[p['frame']];x,y=rational(p['x']),rational(p['y'])
        return bounded(a*x+b*y+tx),bounded(c*x+d*y+ty)
    for did,v in claims.items():
        kind=v.get('kind')
        if kind=='causal':
            fields(v,('decision_id','kind','cause','effect','assertion'))
            require(v['assertion']in ('causes','associated'),'RE_CAUSAL_ASSERTION')
            require(byid[did].decision_type=='causal_explanation','RE_DECISION_TYPE')
            basis=edges.get((v['cause'],v['effect']))
            if basis=='correlation'and v['assertion']=='causes':findings.append(Finding('CORRELATION_PROMOTED_TO_CAUSE',did,'BLOCKER'))
            elif basis is None:findings.append(Finding('CAUSAL_MODEL_UNSUPPORTED',did))
            else:findings.append(Finding('EMPIRICAL_CAUSAL_SUPPORT_REVIEW',did))
        elif kind=='temporal':
            fields(v,('decision_id','kind','before','after','clock'))
            require(v['clock']=='common_rational_time'and v['before']in times and v['after']in times and v['before']!=v['after'],'RE_TIME_REFERENCE')
            a,b=times[v['before']],times[v['after']]
            if a[0]>=b[1]:findings.append(Finding('CHRONOLOGY_COUNTEREXAMPLE',did,'BLOCKER'))
            elif a[1]>=b[0]:findings.append(Finding('CHRONOLOGY_INTERVAL_UNCERTAIN',did))
        elif kind=='spatial':
            fields(v,('decision_id','kind','left','right','relation'))
            a,b=world(v['left']),world(v['right']);rel=v['relation'];require(rel in ('left_of','above','same'),'RE_SPATIAL_RELATION')
            ok=(a[0]<b[0])if rel=='left_of'else(a[1]>b[1])if rel=='above'else a==b
            if not ok:findings.append(Finding('COORDINATE_FRAME_COUNTEREXAMPLE',did,'BLOCKER'))
        else:
            fields(v,('decision_id','kind'));token(kind,'unsupported_kind');findings.append(Finding('UNSUPPORTED_DOMAIN_REASONING',did))
    return finish('BIE-QA-HARD-012',binding,findings,(ref,*source_refs),dict(native_decisions=list(byid),native_graph_executed=True,claims=len(claims)))
