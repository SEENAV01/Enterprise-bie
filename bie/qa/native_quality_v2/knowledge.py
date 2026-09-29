"""HARD008: native KI output to authoritative, source-bound QA inventory.

No natural-language statement is silently converted to a mathematical atom.
Independent facts are operator supplied and checked separately from citations.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from .common import *
from ..source_v2.models import Source, Block, Output, Citation, Request, Policy as SourcePolicy
from ..source_v2.adapters import claim_from_ki
from ..source_v2.evaluator import evaluate as evaluate_source
from ...knowledge_intelligence.claim_extraction import extract
from ...knowledge_intelligence.claim_evidence import bind
from ..semantic_v2.models import Normalization, ReferenceFact

@dataclass(frozen=True,slots=True)
class ConceptFacet:
    facet_id: str
    concept_id: str
    source_block_ids: tuple[str,...]
    required_conditions: tuple[str,...]
    critical: bool = True
    def __post_init__(self):
        token(self.facet_id,'facet');token(self.concept_id,'concept')
        require(type(self.source_block_ids) is tuple and 1<=len(self.source_block_ids)<=128 and len(set(self.source_block_ids))==len(self.source_block_ids),'FACET_SOURCE_IDS')
        require(type(self.required_conditions) is tuple and len(set(self.required_conditions))==len(self.required_conditions),'FACET_CONDITIONS')
        for value in self.required_conditions:text(value,'condition',4096)
        require(type(self.critical) is bool,'FACET_CRITICAL')

@dataclass(frozen=True,slots=True)
class KnowledgePolicy:
    expected_claim_ids: tuple[str,...]
    facets: tuple[ConceptFacet,...]
    independent_reference_ids: tuple[str,...]
    def __post_init__(self):
        for name in ('expected_claim_ids','independent_reference_ids'):
            values=getattr(self,name)
            require(type(values) is tuple and len(values)<=4096 and len(set(values))==len(values),'KNOWLEDGE_IDS')
            for value in values:token(value,name)
        require(bool(self.expected_claim_ids),'EMPTY_KNOWLEDGE_CLAIMS')
        require(type(self.facets) is tuple and all(type(f) is ConceptFacet for f in self.facets) and len({f.facet_id for f in self.facets})==len(self.facets),'KNOWLEDGE_FACETS')
    @property
    def content_digest(self):return digest(asdict(self))


def native_claims(block: Block, fragments: tuple[str,...]) -> tuple[dict,...]:
    """Actually call the preserved KI extractor on explicitly selected claims.

    Selection is upstream/operator data, not proof of autonomous claim discovery.
    """
    require(type(block) is Block and type(fragments) is tuple,'KI_SELECTION_INPUT')
    require(all(type(x) is str and x==x.strip() and x in block.text for x in fragments),'KI_SELECTED_TEXT_NOT_IN_SOURCE')
    return tuple(extract((dict(id=block.block_id,anchor_id=block.block_id,claims=fragments),)))


def source_request(source: Source,blocks: tuple[Block,...],output: Output,output_text: str,
                   native_records: tuple[dict,...], placements: dict[str,tuple[int,int]],binding: Binding) -> Request:
    by_id={b.block_id:b for b in blocks};citations=[];claims=[]
    require(len(by_id)==len(blocks),'KNOWLEDGE_DUPLICATE_BLOCK')
    require(type(native_records) is tuple and len({r['claim_id'] for r in native_records})==len(native_records),'KI_CLAIM_DUPLICATE')
    require(set(placements)=={r['claim_id'] for r in native_records},'KI_PLACEMENT_COVERAGE')
    for rec in native_records:
        fields(rec,('claim_id','text','anchor_id'),'KI_NATIVE_RECORD')
        require(rec['anchor_id'] in by_id,'KI_DANGLING_ANCHOR')
        b=by_id[rec['anchor_id']];value=rec['text'];text(value,'claim')
        require(b.text.count(value)==1,'KI_QUOTATION_AMBIGUOUS')
        start=b.text.index(value);cid='cite-'+rec['claim_id']
        citations.append(Citation(cid,b.block_id,b.content_digest,start,start+len(value),value))
        a,z=placements[rec['claim_id']]
        require(type(a) is int and type(z) is int and 0<=a<z<=len(output_text) and output_text[a:z]==value,'KI_OUTPUT_SPAN')
        native_binding=bind(rec['claim_id'],(b.block_id,),1.0)
        claims.append(claim_from_ki(rec,native_binding,output,start=a,end=z,citation_map={b.block_id:cid}))
    return Request('1.0.0',binding.run_id,binding.revision,binding.candidate_digest,(source,),blocks,(output,),tuple(citations),tuple(claims))


def inspect_inventory(request: Request,artifact_root,source_policy: SourcePolicy,policy: KnowledgePolicy,
                      facet_links: dict[str,tuple[str,...]],reference_artifacts: tuple[ArtifactRef,...],
                      *,binding: Binding,as_of: int,normalizations: tuple[Normalization,...]=(),
                      reference_facts: tuple[ReferenceFact,...]=()) -> tuple[Report,dict]:
    require(type(request) is Request and type(policy) is KnowledgePolicy,'KNOWLEDGE_INPUT')
    require((request.run_id,request.revision,request.candidate_digest)==(binding.run_id,binding.revision,binding.candidate_digest),'KI_REQUEST_BINDING')
    require(binding.policy_digest==policy.content_digest,'KI_POLICY_BINDING')
    pair=evaluate_source(request,artifact_root,source_policy,as_of=as_of)
    findings=[];claims={c.claim_id:c for c in request.claims};blocks={b.block_id:b for b in request.blocks}
    if set(claims)!=set(policy.expected_claim_ids):findings.append(Finding('CLAIM_INVENTORY_MISMATCH','claims','BLOCKER'))
    require(type(facet_links) is dict,'FACET_LINKS')
    if set(facet_links)!={f.facet_id for f in policy.facets}:findings.append(Finding('FACET_INVENTORY_MISMATCH','facets','BLOCKER'))
    for f in policy.facets:
        ids=facet_links.get(f.facet_id,())
        if type(ids) is not tuple or not ids or len(set(ids))!=len(ids) or not set(ids)<=set(claims):
            findings.append(Finding('MISSING_CRITICAL_FACET' if f.critical else 'MISSING_FACET',f.facet_id,'BLOCKER' if f.critical else 'REVIEW'));continue
        if not set(f.source_block_ids)<=set(blocks):findings.append(Finding('FACET_SOURCE_MISSING',f.facet_id,'BLOCKER'));continue
        claim_text='\n'.join(claims[i].text for i in ids)
        cited={cit.block_id for c in (claims[i] for i in ids) for cit in request.citations if cit.citation_id in c.citation_ids}
        if not set(f.source_block_ids)<=cited:findings.append(Finding('FACET_UNSUPPORTED',f.facet_id,'BLOCKER'))
        for condition in f.required_conditions:
            if not any(condition in blocks[i].text for i in f.source_block_ids):findings.append(Finding('CONDITION_NOT_IN_SOURCE',f.facet_id,'BLOCKER'))
            if condition not in claim_text:findings.append(Finding('LOST_SOURCE_CONDITION',f.facet_id,'BLOCKER'))
    require(type(reference_artifacts) is tuple and all(type(a) is ArtifactRef for a in reference_artifacts),'REFERENCE_ARTIFACTS')
    refs={a.artifact_id:a for a in reference_artifacts}
    require(len(refs)==len(reference_artifacts),'DUPLICATE_REFERENCE_ID')
    if set(refs)!=set(policy.independent_reference_ids):findings.append(Finding('REFERENCE_INVENTORY_MISMATCH','references','BLOCKER'))
    original_hashes={s.artifact.sha256 for s in request.sources};seen_hashes=set()
    with SnapshotStore(artifact_root) as store:
        for ref in reference_artifacts:
            store.read(ref)
            if ref.sha256 in original_hashes or ref.sha256 in seen_hashes:findings.append(Finding('REFERENCE_NOT_BYTE_INDEPENDENT',ref.artifact_id,'BLOCKER'))
            seen_hashes.add(ref.sha256)
    require(type(normalizations) is tuple and all(type(n) is Normalization for n in normalizations),'NATIVE_NORMALIZATIONS')
    require(len({n.claim_id for n in normalizations})==len(normalizations) and all(n.claim_id in claims for n in normalizations),'NORMALIZATION_CLAIMS')
    require(type(reference_facts) is tuple and all(type(f) is ReferenceFact for f in reference_facts),'NATIVE_REFERENCE_FACTS')
    require(len({f.reference_id for f in reference_facts})==len(reference_facts),'DUPLICATE_REFERENCE_FACT')
    # ReferenceFact uses source-QA citation identities, not arbitrary artifact labels.
    citation_ids={c.citation_id for c in request.citations}
    for f in reference_facts:
        require(set(f.citation_ids)<=citation_ids,'REFERENCE_CITATION_MISSING')
    for n in normalizations:
        findings.append(Finding('PROPOSITION_MAPPING_ASSESSMENT_REQUIRED',n.claim_id))
    if set(claims)-{n.claim_id for n in normalizations}:findings.append(Finding('OPEN_WORLD_CLAIMS_NOT_FABRICATED_AS_ATOMS','claims'))
    for r in (pair.provenance,pair.grounding):
        for f in r.findings:findings.append(Finding(f.code,f.subject_id if hasattr(f,'subject_id') else str(getattr(f,'subject','source')),'BLOCKER' if f.severity=='BLOCKER' else 'REVIEW'))
    findings.extend((Finding('REFERENCE_TRUTH_AND_INDEPENDENCE_REQUIRE_REVIEW','references'),Finding('FACET_TEACHING_ALIGNMENT_REQUIRES_REVIEW','facets')))
    details=dict(native_claim_count=len(claims),source_request_digest=request.content_digest,source_qa=pair.to_dict(),
                 facet_links=facet_links,normalizations=[asdict(n) for n in normalizations],reference_facts=[asdict(r) for r in reference_facts],
                 source_entailment_is_truth=False,automatic_semantic_extraction=False)
    return report('BIE-QA-HARD-008',binding,findings,tuple(s.artifact for s in request.sources)+tuple(o.artifact for o in request.outputs)+reference_artifacts,details),details
