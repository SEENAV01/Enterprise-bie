from collections import defaultdict

def _evidence_for_section(section, evidence_index):
    ids = section.get("content_blocks", [])
    return [
        evidence_index[bid] for bid in ids
        if bid in evidence_index and evidence_index[bid].get("text")
    ]

def _find_sections(nodes):
    out=[]
    def walk(items):
        for n in items:
            out.append(n)
            walk(n.get("children",[]))
    walk(nodes)
    return out

def rank_sections(query, retrieval_ir, book_structure, top_k=5):
    from semantic_retrieval import search
    hits = search(retrieval_ir["index"], query, top_k=top_k)
    by_id = {n["section_id"]: n for n in _find_sections(book_structure.get("tree",[]))}
    ranked=[]
    for hit in hits:
        section=by_id.get(hit["document_id"])
        if section:
            ranked.append({
                "section_id": section["section_id"],
                "title": section["title"],
                "score": hit["score"],
                "start_page": section.get("start_page")
            })
    return ranked

def build_teaching_units(book_structure, knowledge, retrieval_ir,
                         max_evidence_per_unit=6):
    evidence = knowledge.get("evidence_index", {})
    units=[]
    for section in _find_sections(book_structure.get("tree",[])):
        ev = _evidence_for_section(section, evidence)[:max_evidence_per_unit]
        if not ev:
            continue
        # Conservative teaching role: source-derived material first.
        kinds=[x.get("kind") for x in ev]
        if "HEADING" in kinds:
            role="concept"
        elif "TABLE" in kinds or "EQUATION_CANDIDATE" in kinds:
            role="worked_content"
        else:
            role="explanation"
        units.append({
            "unit_id": f"teach:{section['section_id']}",
            "section_id": section["section_id"],
            "title": section["title"],
            "role": role,
            "source_evidence":[x["block_id"] for x in ev],
            "pages":sorted({x.get("page") for x in ev if x.get("page") is not None}),
            "concept_links":[
                l["link_id"] for l in retrieval_ir.get("concept_links",[])
                if section["section_id"] in l.get("section_ids",[])
            ]
        })
    return units

def prerequisite_edges(units, book_structure):
    """Default prerequisite order follows the source hierarchy/order."""
    ordered=sorted(units, key=lambda u:(min(u["pages"]) if u["pages"] else 10**9,u["unit_id"]))
    edges=[]
    for a,b in zip(ordered,ordered[1:]):
        edges.append({
            "from":a["unit_id"],
            "to":b["unit_id"],
            "reason":"source_order",
            "confidence":0.55
        })
    return edges

def compile_lesson_plan(book_structure, knowledge, retrieval_ir):
    units=build_teaching_units(book_structure,knowledge,retrieval_ir)
    edges=prerequisite_edges(units,book_structure)
    return {
        "lesson_plan_ir_version":"1.0",
        "units":units,
        "prerequisites":edges,
        "planning_policy":"source-grounded sequencing; inferred prerequisites are confidence-scored",
        "grounding_ref":"knowledge",
        "retrieval_ref":"retrieval"
    }

def validate_lesson_plan(plan, knowledge):
    known=set(knowledge.get("evidence_index",{}))
    errors=[]
    ids={u["unit_id"] for u in plan.get("units",[])}
    for u in plan.get("units",[]):
        for bid in u.get("source_evidence",[]):
            if bid not in known:
                errors.append(f"unit has unknown evidence: {u['unit_id']}:{bid}")
    for e in plan.get("prerequisites",[]):
        if e.get("from") not in ids or e.get("to") not in ids:
            errors.append(f"invalid prerequisite edge: {e}")
    return {"passed":not errors,"errors":errors}
