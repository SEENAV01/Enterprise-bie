import re
from collections import defaultdict

STOP = {
    "the","a","an","and","or","of","to","in","is","are","was","were",
    "for","on","with","as","by","from","that","this","these","those",
    "it","its","be","has","have","had","into","at","which","can","may"
}

def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()

def candidate_terms(text):
    """Conservative noun/technical-term candidates; never invent source text."""
    t = normalize(text)
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", t)
    counts = defaultdict(int)
    for w in words:
        lw = w.lower()
        if lw not in STOP:
            counts[lw] += 1
    return sorted(counts, key=lambda x: (-counts[x], x))[:12]

def collect_blocks(ir):
    blocks = []
    for page in ir.get("pages", []):
        for block in page.get("blocks", []):
            text = normalize(block.get("text", ""))
            if text or block.get("kind") in {"FIGURE","TABLE"}:
                item = dict(block)
                item["page"] = page.get("page")
                blocks.append(item)
    return blocks

def build_evidence_index(ir):
    index = {}
    for block in collect_blocks(ir):
        bid = block.get("block_id")
        if not bid:
            continue
        index[bid] = {
            "block_id": bid,
            "page": block.get("page"),
            "kind": block.get("kind"),
            "text": normalize(block.get("text", "")),
            "bbox": block.get("bbox")
        }
    return index

def compile_claims(ir):
    """
    Turn source blocks into grounded claims.
    A claim is intentionally a source sentence/block, not an LLM-generated fact.
    """
    claims = []
    for block in collect_blocks(ir):
        text = normalize(block.get("text", ""))
        if not text or block.get("kind") in {"FIGURE","TABLE"}:
            continue
        # Split only on strong sentence boundaries; retain source wording.
        sentences = [normalize(x) for x in re.split(r"(?<=[.!?])\s+", text) if normalize(x)]
        if not sentences:
            sentences = [text]
        for i, sentence in enumerate(sentences):
            cid = f"claim:{block.get('block_id')}:{i}"
            claims.append({
                "claim_id": cid,
                "text": sentence,
                "source_block_id": block.get("block_id"),
                "page": block.get("page"),
                "terms": candidate_terms(sentence)
            })
    return claims

def compile_entities(claims):
    entity_map = {}
    for claim in claims:
        for term in claim["terms"]:
            eid = f"entity:{term}"
            entity_map.setdefault(eid, {
                "entity_id": eid,
                "label": term,
                "source_claims": []
            })
            if claim["claim_id"] not in entity_map[eid]["source_claims"]:
                entity_map[eid]["source_claims"].append(claim["claim_id"])
    return list(entity_map.values())

def compile_relations(claims, entities):
    entity_ids = {e["label"]: e["entity_id"] for e in entities}
    relations = []
    for claim in claims:
        terms = [t for t in claim["terms"] if t in entity_ids]
        # Co-occurrence is explicitly typed as "co_occurs_in_claim";
        # it is not asserted as a semantic causal relation.
        for i, a in enumerate(terms):
            for b in terms[i+1:]:
                relations.append({
                    "relation_id": f"rel:{claim['claim_id']}:{a}:{b}",
                    "subject": entity_ids[a],
                    "predicate": "co_occurs_in_claim",
                    "object": entity_ids[b],
                    "evidence": [claim["claim_id"]]
                })
    return relations

def compile_knowledge(ir, book_structure=None):
    evidence = build_evidence_index(ir)
    claims = compile_claims(ir)
    entities = compile_entities(claims)
    relations = compile_relations(claims, entities)
    return {
        "knowledge_ir_version": "1.0",
        "source_uri": ir.get("source_uri"),
        "evidence_index": evidence,
        "claims": claims,
        "entities": entities,
        "relations": relations,
        "structure_ref": "book_structure" if book_structure else None,
        "grounding_policy": "every claim references a source block; inferred semantics are not represented as facts"
    }

def validate_grounding(knowledge):
    errors = []
    evidence_ids = set(knowledge.get("evidence_index", {}))
    claim_ids = set()
    for claim in knowledge.get("claims", []):
        cid = claim.get("claim_id")
        claim_ids.add(cid)
        if claim.get("source_block_id") not in evidence_ids:
            errors.append(f"un-grounded claim: {cid}")
    for rel in knowledge.get("relations", []):
        for ev in rel.get("evidence", []):
            if ev not in claim_ids:
                errors.append(f"relation has unknown evidence: {rel.get('relation_id')}")
    return {"passed": not errors, "errors": errors}
