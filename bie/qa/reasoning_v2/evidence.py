"""Premise-by-premise evidence sufficiency; citations do not add independent votes."""
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class EvidenceWitness:
    argument_id: str
    premise_id: str
    independent_groups: tuple[str,...]
    required_groups: int
    sufficient: bool
    conditional_assumption: bool


def lineage_groups(request,policy):
    # Union by governed ancestry AND identical source bytes. Relabeling a byte
    # duplicate under a different source ID/group cannot manufacture independence.
    sources={s.source_id:s for s in request.source.sources}
    parent={x.source_id:x.source_id for x in policy.lineages}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    seen_group={};seen_hash={}
    for row in sorted(policy.lineages,key=lambda x:x.source_id):
        sid=row.source_id
        aliases=[]
        if row.lineage_group in seen_group:aliases.append(seen_group[row.lineage_group])
        seen_group[row.lineage_group]=sid
        if sid in sources:
            h=sources[sid].artifact.sha256
            if h in seen_hash:aliases.append(seen_hash[h])
            seen_hash[h]=sid
        for other in aliases:
            a,b=sorted((root(sid),root(other)));parent[b]=a
    return {x:root(x) for x in parent}


def check_evidence(c):
    r,p=c.request,c.policy;witnesses=[];sufficient_args=set();conflicted=set()
    sources={s.source_id:s for s in r.source.sources}
    if {l.source_id for l in p.lineages}!=set(sources):
        c.add('evidence','SOURCE_LINEAGE_INVENTORY_MISMATCH','reasoning-scope','Every submitted source needs independently provisioned provenance/independence lineage.')
    groups=lineage_groups(r,p);support={};bad_premises=set()
    for e in sorted(r.evidence,key=lambda x:x.evidence_id):
        a=c.arguments.get(e.argument_id);s=c.statements.get(e.premise_id)
        if a is None or e.premise_id not in a.premise_ids or s is None or s.claim_id not in c.claims:
            c.add('evidence','EVIDENCE_PREMISE_REFERENCE_INVALID',e.evidence_id,'Support must attach to a real root premise, not a derived conclusion or unknown argument.');continue
        if e.premise_id in a.assumption_ids:
            c.add('evidence','ASSUMPTION_MASQUERADING_AS_EVIDENCE',e.evidence_id,'Explicit assumptions are not empirically verified premises.');continue
        sidset=set();ok=True
        for cid in e.citation_ids:
            citation=c.citations.get(cid);block=c.blocks.get(citation.block_id) if citation else None
            if block is None or block.source_id not in groups:
                c.add('evidence','EVIDENCE_CITATION_UNRESOLVED',e.evidence_id,'Citation is unresolved or from a source without governed lineage.');ok=False
            else:sidset.add(groups[block.source_id])
        if e.relation=='support' and not set(e.citation_ids)<=set(c.claims[s.claim_id].citation_ids):
            c.add('evidence','PREMISE_CITATION_LINK_MISMATCH',e.evidence_id,'Supporting citations must actually be attached to the output premise.');ok=False
        if ('support',e.evidence_id) not in c.ready:
            c.add('evidence','PREMISE_SUPPORT_UNVERIFIED',e.evidence_id,'A citation ID and a self-supplied strength do not establish evidential support.','REVIEW');ok=False
        if e.relation=='contradiction' and ('support',e.evidence_id) in c.ready:
            c.add('evidence','UNRESOLVED_COUNTEREVIDENCE',e.argument_id,'Reviewed contradictory evidence is not outvoted by additional supporting citations.')
            conflicted.add(e.argument_id);bad_premises.add((e.argument_id,e.premise_id));ok=False
        if ok and c.source.grounding.status=='CHECKS_PASSED':
            support.setdefault((e.argument_id,e.premise_id),set()).update(sidset)
    for a in sorted(r.arguments,key=lambda x:x.argument_id):
        good=True
        for pid in a.premise_ids:
            assumed=pid in a.assumption_ids
            origins=tuple(sorted(support.get((a.argument_id,pid),())))
            sufficient=assumed or (len(origins)>=p.minimum_independent_sources and (a.argument_id,pid) not in bad_premises)
            if not sufficient:
                good=False;c.add('evidence','PREMISE_EVIDENCE_INSUFFICIENT',a.argument_id,
                    f'{pid}: independent reviewed source groups {len(origins)} below {p.minimum_independent_sources}, or unresolved counterevidence.')
            witnesses.append(EvidenceWitness(a.argument_id,pid,origins,0 if assumed else p.minimum_independent_sources,sufficient,assumed))
        if ('mapping',a.argument_id) not in c.ready:
            c.add('evidence','PREMISE_MAPPING_UNVERIFIED',a.argument_id,'Logical root selection and its text alignment require complete authorized mapping.','REVIEW');good=False
        if good and a.argument_id not in conflicted:sufficient_args.add(a.argument_id)
    c.metrics['evidence'].update(evidence_links=len(r.evidence),premise_obligations=len(witnesses),
        sufficient_premises=sum(x.sufficient and not x.conditional_assumption for x in witnesses),
        conditional_assumptions=sum(x.conditional_assumption for x in witnesses),independent_source_groups=len(set(groups.values())))
    return tuple(witnesses),sufficient_args,conflicted
