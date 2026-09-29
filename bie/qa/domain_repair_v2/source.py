"""Deterministic UTF-8 extraction/anchor restoration; NOT source-fact rewriting."""
from dataclasses import replace
from ..release_v2.contracts import ContractError
from ..source_v2.models import Request,Policy
from .contracts import Limits
from .common import exact_inputs,finish

def repair(request,root,policy,limits=Limits()):
    if type(request) is not Request or type(policy) is not Policy:raise ContractError('DOMAIN_REPAIR_SOURCE_TYPE')
    data=exact_inputs(request,root,verify_blocks=False)
    if set(policy.expected_output_ids)!={o.output_id for o in request.outputs}:raise ContractError('DOMAIN_REPAIR_SOURCE_SCOPE')
    sources={s.source_id:s for s in request.sources};blocks=[];citations=[]
    # This profile restores a full-document UTF8 block only. Partial/page OCR needs
    # a separate extractor and reviewed page/region correspondence, never guesswork.
    for block in request.blocks:
        s=sources.get(block.source_id)
        if s is None or s.media_type!='utf8' or s.page_count!=1:raise ContractError('DOMAIN_REPAIR_EXTRACTOR_REQUIRED')
        if sum(b.source_id==s.source_id for b in request.blocks)!=1 or block.page!=1 or block.box_ppm!=(0,0,1000000,1000000):raise ContractError('DOMAIN_REPAIR_PARTIAL_BLOCK_UNSUPPORTED')
        try:text=data[s.artifact.artifact_id].decode('utf-8')
        except UnicodeError as exc:raise ContractError('DOMAIN_REPAIR_UTF8_REQUIRED') from exc
        if not text.strip():raise ContractError('DOMAIN_REPAIR_EMPTY_SOURCE')
        # No normalization, confidence increase, new source, invented quote or role change.
        blocks.append(replace(block,text=text,source_sha256=s.artifact.sha256))
    byid={b.block_id:b for b in blocks};anchors=[]
    for citation in request.citations:
        b=byid.get(citation.block_id)
        if b is None:raise ContractError('DOMAIN_REPAIR_UNKNOWN_BLOCK')
        # A correct existing position is disambiguating evidence and is preserved.
        if b.text[citation.start:citation.end]==citation.quote:
            start=citation.start
        else:
            start=b.text.find(citation.quote)
            if start<0:raise ContractError('DOMAIN_REPAIR_QUOTE_NOT_FOUND')
            if b.text.find(citation.quote,start+1)>=0:raise ContractError('DOMAIN_REPAIR_AMBIGUOUS_QUOTE')
        updated=replace(citation,start=start,end=start+len(citation.quote),block_digest=b.content_digest)
        citations.append(updated)
        if updated!=citation:anchors.append(citation.citation_id)
    after=replace(request,blocks=tuple(blocks),citations=tuple(citations))
    exact_inputs(after,root)
    return finish(request,after,dict(worker='utf8-extraction-and-anchor-restoration',reanchored_citation_ids=anchors,
        changed_block_ids=[a.block_id for a,b in zip(after.blocks,request.blocks) if a!=b],
        source_bytes_changed=False,claims_changed=False,confidence_increased=False,
        scope='exact original UTF8 block and existing quotation identities'),limits)
