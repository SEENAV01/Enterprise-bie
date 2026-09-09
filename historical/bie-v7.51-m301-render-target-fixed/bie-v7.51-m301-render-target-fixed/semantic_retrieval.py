import math
import re
from collections import defaultdict

STOP = {
    "the","a","an","and","or","of","to","in","is","are","was","were",
    "for","on","with","as","by","from","that","this","these","those",
    "it","its","be","has","have","had","into","at","which","can","may",
    "about","than","then","also"
}

def tokenize(text):
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text or "")
            if w.lower() not in STOP]

def tfidf_index(documents):
    """
    Small dependency-free lexical retrieval index.
    documents: {doc_id: text}
    """
    term_freq = {}
    doc_freq = defaultdict(int)
    for did, text in documents.items():
        counts = defaultdict(int)
        for token in tokenize(text):
            counts[token] += 1
        term_freq[did] = counts
        for token in counts:
            doc_freq[token] += 1

    n = max(1, len(documents))
    vectors = {}
    for did, counts in term_freq.items():
        vec = {}
        for token, tf in counts.items():
            idf = math.log((1+n)/(1+doc_freq[token])) + 1
            vec[token] = (1 + math.log(tf)) * idf
        norm = math.sqrt(sum(v*v for v in vec.values())) or 1.0
        vectors[did] = {k:v/norm for k,v in vec.items()}
    return {"documents":documents, "vectors":vectors, "doc_freq":dict(doc_freq)}

def search(index, query, top_k=5):
    q_counts = defaultdict(int)
    for token in tokenize(query):
        q_counts[token] += 1
    q = set(q_counts)
    scored = []
    for did, vec in index.get("vectors", {}).items():
        score = sum(vec.get(t,0.0) * q_counts[t] for t in q)
        if score > 0:
            scored.append((score,did))
    scored.sort(key=lambda x:(-x[0], x[1]))
    return [{"document_id":did, "score":round(score,6)}
            for score,did in scored[:max(1,top_k)]]

def build_section_documents(book_structure, evidence_index):
    docs = {}
    for section in book_structure.get("flat", []):
        sid = section["section_id"]
        ids = []
        # Recover content blocks by finding the tree node.
        ids.extend(_find_content_blocks(book_structure.get("tree", []), sid))
        text = " ".join(evidence_index.get(b,{}).get("text","") for b in ids)
        if section.get("title"):
            text = section["title"] + " " + text
        docs[sid] = text
    return docs

def _find_content_blocks(nodes, target):
    for node in nodes:
        if node.get("section_id") == target:
            return list(node.get("content_blocks", []))
        found = _find_content_blocks(node.get("children", []), target)
        if found:
            return found
    return []

def link_concepts(knowledge, book_structure):
    """
    Link identical/near-identical grounded terms across sections.
    No new factual claims are created; links point to existing entities/claims.
    """
    entity_to_sections = defaultdict(set)
    claim_map = {c["claim_id"]: c for c in knowledge.get("claims", [])}

    block_to_section = {}
    def walk(nodes):
        for n in nodes:
            for bid in n.get("content_blocks", []):
                block_to_section[bid] = n["section_id"]
            walk(n.get("children", []))
    walk(book_structure.get("tree", []))

    for entity in knowledge.get("entities", []):
        for cid in entity.get("source_claims", []):
            claim = claim_map.get(cid)
            if claim and claim.get("source_block_id") in block_to_section:
                entity_to_sections[entity["entity_id"]].add(
                    block_to_section[claim["source_block_id"]]
                )

    links = []
    for eid, sections in sorted(entity_to_sections.items()):
        sections = sorted(sections)
        if len(sections) > 1:
            links.append({
                "link_id": f"concept-link:{eid}",
                "entity_id": eid,
                "section_ids": sections,
                "evidence_claims": knowledge.get("entities", [])[0].get("source_claims", [])
                    if False else _claims_for_entity(knowledge, eid),
                "link_type": "same_grounded_entity_across_sections"
            })
    return links

def _claims_for_entity(knowledge, eid):
    for e in knowledge.get("entities", []):
        if e.get("entity_id") == eid:
            return list(e.get("source_claims", []))
    return []

def build_retrieval_ir(knowledge, book_structure):
    evidence = knowledge.get("evidence_index", {})
    docs = build_section_documents(book_structure, evidence)
    index = tfidf_index(docs)
    links = link_concepts(knowledge, book_structure)
    return {
        "retrieval_ir_version":"1.0",
        "index_type":"tfidf_lexical",
        "section_documents":docs,
        "index":index,
        "concept_links":links,
        "grounding_ref":"knowledge"
    }

def validate_retrieval(ir, knowledge):
    errors=[]
    known=set(knowledge.get("evidence_index",{}))
    for link in ir.get("concept_links",[]):
        if not link.get("evidence_claims"):
            errors.append(f"concept link without evidence: {link.get('link_id')}")
    for sid, text in ir.get("section_documents",{}).items():
        if not isinstance(text,str):
            errors.append(f"non-text section document: {sid}")
    return {"passed":not errors,"errors":errors}
