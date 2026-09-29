"""Strict existing-contract loading and byte-backed, read-only preconditions."""
from dataclasses import asdict
from ..release_v2.contracts import ContractError,canonical_bytes
from ..repair_v2.codec import decode
from ..source_v2.codec import loads
from ..source_v2.io import SnapshotStore
from ..source_v2.models import Request,Policy
from ..reasoning_v2.models import ReasoningRequest,ReasoningPolicy
from ..pedagogy_v2.models import PedagogyRequest,PedagogyPolicy
from ..director_v2.models import DirectorRequest,DirectorPolicy
TYPES={
 'BIE-QA-REPAIR-004':(Request,Policy),
 'BIE-QA-REPAIR-005':(ReasoningRequest,ReasoningPolicy),
 'BIE-QA-REPAIR-006':(PedagogyRequest,PedagogyPolicy),
 'BIE-QA-REPAIR-007':(DirectorRequest,DirectorPolicy),
}

def source_of(request):return request if type(request) is Request else request.source

def read_request(task_id,data):
    if task_id not in TYPES:raise ContractError('DOMAIN_REPAIR_UNKNOWN_TASK')
    return decode(loads(data),TYPES[task_id][0])

def read_policy(task_id,data):return decode(loads(data),TYPES[task_id][1])

def exact_inputs(request,root,*,verify_blocks=True):
    """All declared source/output bytes and every claim are actually checked.

    For source repair only, damaged block extraction/anchors are allowed as input;
    original source files and generated text claims are NEVER silently corrected.
    """
    source=source_of(request);refs=[s.artifact for s in source.sources]+[o.artifact for o in source.outputs]
    with SnapshotStore(root) as store:data={a.artifact_id:store.read(a) for a in refs}
    output={o.output_id:o for o in source.outputs}
    for c in source.claims:
        out=output.get(c.output_id)
        if out is None or out.artifact.sha256!=c.output_sha256:raise ContractError('DOMAIN_REPAIR_CLAIM_BINDING')
        try:text=data[out.artifact.artifact_id].decode('utf-8')
        except UnicodeError as exc:raise ContractError('DOMAIN_REPAIR_UTF8_REQUIRED') from exc
        if c.end>len(text) or text[c.start:c.end]!=c.text:raise ContractError('DOMAIN_REPAIR_CLAIM_TEXT_CHANGED')
    if verify_blocks:
        from ..source_v2.evaluator import evaluate
        p=Policy('domain-repair-byte-check',tuple(o.output_id for o in source.outputs))
        result=evaluate(source,root,p,as_of=0)
        if result.provenance.status=='BLOCKED':
            raise ContractError('DOMAIN_REPAIR_SOURCE_PROVENANCE_BLOCKED',','.join(sorted({f.code for f in result.provenance.findings if f.severity=='BLOCKER'})))
    return data

def stable_topology(items,edges):
    """Stable Kahn ordering; no deletion, insertion, cycle breaking or guessed nodes."""
    if len(items)!=len(set(items)):raise ContractError('DOMAIN_REPAIR_DUPLICATE_NODE')
    ids=set(items);deps={i:set() for i in items}
    for a,b in edges:
        if a not in ids or b not in ids:raise ContractError('DOMAIN_REPAIR_MISSING_NODE')
        if a==b:raise ContractError('DOMAIN_REPAIR_SELF_EDGE')
        deps[b].add(a)
    result=[];done=set()
    while len(done)<len(items):
        next_id=next((i for i in items if i not in done and deps[i]<=done),None)
        if next_id is None:raise ContractError('DOMAIN_REPAIR_CYCLE')
        result.append(next_id);done.add(next_id)
    return tuple(result)

def finish(before,after,witness,limits):
    b=canonical_bytes(asdict(after))
    if b==canonical_bytes(asdict(before)):raise ContractError('DOMAIN_REPAIR_NO_CHANGE')
    if len(b)>limits.max_generated_bytes:raise ContractError('DOMAIN_REPAIR_OUTPUT_LIMIT')
    return after,dict(witness,previous_reviews_invalidated=True,product_accepted=False)
