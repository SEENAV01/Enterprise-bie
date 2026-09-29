"""HARD011: native prerequisite graph, learner evidence and explicit applicability.

Prior teaching is not mastery. A scoped no-math decision cannot remove a release
gate. All downstream release requirements remain in the returned inventory.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from .common import *
from ...prerequisite_intelligence.graph import PrerequisiteGraph
from ..reasoning_v2.adapters import import_prerequisite_graph
from ..source_v2.models import Request as SourceRequest, Policy as SourcePolicy
from ..source_v2.evaluator import evaluate as evaluate_source

@dataclass(frozen=True,slots=True)
class ReadinessPolicy:
    required_concepts: tuple[str,...]
    required_routes: tuple[str,...]
    required_gate_ids: tuple[str,...]
    criterion_floors: tuple[tuple[str,int],...]
    minimum_total_ppm: int
    diagnostic_max_age_seconds: int = 604800
    def __post_init__(self):
        for name in ('required_concepts','required_routes','required_gate_ids'):
            v=getattr(self,name);require(type(v) is tuple and 1<=len(v)<=1024 and len(set(v))==len(v),'READINESS_IDS')
            for x in v:token(x,name)
        require(type(self.criterion_floors) is tuple and bool(self.criterion_floors) and len({k for k,v in self.criterion_floors})==len(self.criterion_floors),'READINESS_CRITERIA')
        for k,v in self.criterion_floors:token(k,'criterion');integer(v,'floor',0,1000000)
        integer(self.minimum_total_ppm,'total_floor',0,1000000);integer(self.diagnostic_max_age_seconds,'age',1,604800)
    @property
    def content_digest(self):return digest(asdict(self))


def prerequisites(graph: PrerequisiteGraph) -> dict[str,set[str]]:
    nodes,edges=import_prerequisite_graph(graph)
    incoming={n:set() for n in nodes}
    for e in edges:incoming[e.dependent].add(e.prerequisite)
    result={};pending=set(nodes)
    while pending:
        ready=sorted(n for n in pending if incoming[n]<=set(result))
        require(bool(ready),'PREREQUISITE_CYCLE')
        for n in ready:
            result[n]=set(incoming[n])
            for p in incoming[n]:result[n]|=result[p]
            pending.remove(n)
    return result


def evaluate_readiness(graph: PrerequisiteGraph,lesson_ref: ArtifactRef,diagnostic_refs: tuple[ArtifactRef,...],root,
                       binding: Binding,policy: ReadinessPolicy,*,learner_id: str,now: int,
                       reviews: tuple[Review,...]=(),verifier: ReviewVerifier | None=None,
                       source_request: SourceRequest | None=None, source_policy: SourcePolicy | None=None) -> tuple[Report,dict]:
    require(binding.policy_digest==policy.content_digest,'READINESS_POLICY_BINDING');token(learner_id,'learner_id')
    inherited=prerequisites(graph)
    require(set(policy.required_concepts)<=set(inherited),'PREREQUISITE_INVENTORY_MISSING')
    findings=[];verifier=verifier or ReviewVerifier()
    require(type(reviews) is tuple and all(type(r) is Review for r in reviews) and len({(r.subject_id,r.purpose) for r in reviews})==len(reviews),'DUPLICATE_READINESS_REVIEW')
    review_map={(r.subject_id,r.purpose):r for r in reviews};mastered=set();inspected=[lesson_ref];rejected_concepts=set();seen_observations=set()
    source_ids_verified=set()
    if source_request is None or source_policy is None:
        findings.append(Finding('NATIVE_LESSON_SOURCE_EVIDENCE_REQUIRED','lesson'))
    else:
        require(type(source_request) is SourceRequest and type(source_policy) is SourcePolicy,'READINESS_SOURCE_INPUT')
        require((source_request.run_id,source_request.revision,source_request.candidate_digest)==(binding.run_id,binding.revision,binding.candidate_digest),'READINESS_SOURCE_BINDING')
        src=evaluate_source(source_request,root,source_policy,as_of=now)
        source_ids_verified={c.claim_id for c in source_request.claims}
        for r in (src.provenance,src.grounding):
            for f in r.findings:findings.append(Finding(f.code,'lesson-source','BLOCKER' if f.severity=='BLOCKER' else 'REVIEW'))
        inspected.extend(s.artifact for s in source_request.sources);inspected.extend(o.artifact for o in source_request.outputs)
    with SnapshotStore(root) as store:
        lesson=read_json(store,lesson_ref)
        fields(lesson,('schema_version','learner_id','binding','routes','source_claim_ids','applicability'))
        require(lesson['schema_version']=='bie.qa.native-lesson-scope/1','LESSON_SCOPE_SCHEMA')
        require(lesson['learner_id']==learner_id,'LEARNER_IDENTITY_MISMATCH');binding_matches(lesson['binding'],binding)
        source_ids=items(lesson['source_claim_ids'],'LESSON_SOURCE_CLAIMS',1,4096)
        require(len(set(source_ids))==len(source_ids),'LESSON_SOURCE_DUPLICATE')
        for value in source_ids:token(value,'source_claim')
        if source_request is not None:require(set(source_ids)<=source_ids_verified,'LESSON_SOURCE_UNKNOWN_CLAIM')
        seen=set()
        for ref in diagnostic_refs:
            require(ref.artifact_id not in seen,'DUPLICATE_DIAGNOSTIC');seen.add(ref.artifact_id);inspected.append(ref)
            d=read_json(store,ref)
            fields(d,('schema_version','observation_id','learner_id','concept_id','assessed_at','policy_digest','scores','reported_mastery','provenance_mode'))
            require(d['schema_version']=='bie.qa.learner-diagnostic/1','DIAGNOSTIC_SCHEMA')
            token(d['observation_id'],'observation_id')
            require(d['observation_id'] not in seen_observations,'DUPLICATE_OBSERVATION');seen_observations.add(d['observation_id'])
            integer(d['assessed_at'],'assessed_at');require(type(d['reported_mastery']) is bool,'DIAGNOSTIC_LABEL')
            require(d['provenance_mode'] in ('diagnostic','observed'),'DIAGNOSTIC_PROVENANCE')
            if d['learner_id']!=learner_id or d['concept_id'] not in inherited or d['policy_digest']!=policy.content_digest:
                findings.append(Finding('DIAGNOSTIC_SCOPE_MISMATCH',d['observation_id'],'BLOCKER'));continue
            if not 0<=now-d['assessed_at']<=policy.diagnostic_max_age_seconds:
                findings.append(Finding('DIAGNOSTIC_STALE',d['observation_id'],'BLOCKER'));continue
            require(type(d['scores']) is dict and set(d['scores'])==dict(policy.criterion_floors).keys(),'DIAGNOSTIC_CRITERION_COVERAGE')
            for value in d['scores'].values():integer(value,'diagnostic.score',0,1000000)
            passed=all(d['scores'][k]>=v for k,v in policy.criterion_floors) and sum(d['scores'].values())>=policy.minimum_total_ppm*len(d['scores'])
            if not passed:rejected_concepts.add(d['concept_id'])
            if d['reported_mastery']!=passed:findings.append(Finding('MASTERY_LABEL_CONTRADICTS_SCORES',d['observation_id'],'BLOCKER'))
            bound=digest(dict(binding=asdict(binding),lesson=asdict(lesson_ref),diagnostic=asdict(ref),learner_id=learner_id))
            trust=approved(review_map.get((d['observation_id'],'mastery')),verifier,subject=d['observation_id'],purpose='mastery',request_digest=bound,
                policy_digest=policy.content_digest,now=now,evidence_ids=(ref.artifact_id,),max_age=policy.diagnostic_max_age_seconds)
            if trust=='BLOCKED':findings.append(Finding('DIAGNOSTIC_AUTHENTICATION_FAILED',d['observation_id'],'BLOCKER'))
            elif trust!='VERIFIED' or d['provenance_mode']!='observed':findings.append(Finding('DIAGNOSTIC_NOT_OBSERVED_AND_VERIFIED',d['observation_id']))
            elif passed:mastered.add(d['concept_id'])
    mastered-=rejected_concepts  # A failing applicable observation cannot be outvoted.
    routes=items(lesson['routes'],'ROUTES',1,256);route_ids={r.get('route_id') for r in routes}
    require(len(route_ids)==len(routes) and route_ids==set(policy.required_routes),'LESSON_ROUTE_INVENTORY')
    routes_seen={}
    for route in routes:
        fields(route,('route_id','concept_order'));order=items(route['concept_order'],'ROUTE_CONCEPTS',1,1024)
        require(len(order)==len(set(order)) and set(order)<=set(inherited),'ROUTE_CONCEPT_SCOPE')
        seen=set(mastered)
        for concept in order:
            missing=inherited[concept]-seen
            if missing:findings.append(Finding('PREREQUISITE_NOT_READY',route['route_id']+':'+concept,'BLOCKER'))
            seen.add(concept)
        if not set(policy.required_concepts)<=set(order)|mastered:findings.append(Finding('REQUIRED_LESSON_CONCEPT_MISSING',route['route_id'],'BLOCKER'))
        routes_seen[route['route_id']]=dict(prior_diagnostic_concepts=sorted(mastered),planned_teaching=order,observed_mastery_not_inferred=True)
    entries=items(lesson['applicability'],'APPLICABILITY',0,128);seen_gates=set();applicability=[]
    for entry in entries:
        fields(entry,('gate_id','decision','source_claim_ids','rationale'))
        gate=entry['gate_id'];require(gate in policy.required_gate_ids and gate not in seen_gates,'APPLICABILITY_GATE');seen_gates.add(gate)
        require(entry['decision'] in ('APPLICABLE','NOT_APPLICABLE_REQUESTED'),'APPLICABILITY_DECISION')
        claims=items(entry['source_claim_ids'],'APPLICABILITY_SOURCE',1,4096)
        require(len(set(claims))==len(claims) and set(claims)<=set(source_ids),'APPLICABILITY_SOURCE_SCOPE')
        text(entry['rationale'],'applicability.rationale',4096)
        if entry['decision']=='NOT_APPLICABLE_REQUESTED':
            bound=digest(dict(binding=asdict(binding),lesson=asdict(lesson_ref),applicability=entry))
            trust=approved(review_map.get((gate,'mapping')),verifier,subject=gate,purpose='mapping',request_digest=bound,
                policy_digest=policy.content_digest,now=now,evidence_ids=tuple(claims))
            findings.append(Finding('APPLICABILITY_REQUIRES_GROUNDED_REVIEW',gate,'BLOCKER' if trust=='BLOCKED' else 'REVIEW'))
        applicability.append(entry)
    # This adapter never removes gate IDs, even with a positive applicability review.
    findings.append(Finding('LESSON_SOURCE_AND_RUNTIME_CORRESPONDENCE_REQUIRED','lesson'))
    details=dict(transitive_prerequisites={k:sorted(v) for k,v in inherited.items()},routes=routes_seen,applicability=applicability,
                 retained_required_gate_ids=list(policy.required_gate_ids),gates_waived=[],real_learner_mastery_certified=False)
    return report('BIE-QA-HARD-011',binding,findings,tuple(inspected),details),details
