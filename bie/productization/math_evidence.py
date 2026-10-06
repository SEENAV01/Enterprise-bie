"""Source-bound, bounded native Math composition, never a semantic book solver.

Only complete display equalities, explicit dimensionless symbol declarations,
explicit numeric unit equalities and explicit rewrite steps are admitted.
All other mathematical obligations require review. Finite probes are NOT proof.
"""
from dataclasses import asdict
from pathlib import Path
import re
from bie.document_intelligence.equation_region import EquationRegion, validate as region_valid
from bie.document_intelligence.equation_source_link import EquationSourceLink, validate as link_valid
from bie.document_intelligence.equation_mode import classify
from bie.knowledge_intelligence.equation_claim_link import link as claim_link
from bie.knowledge_intelligence.equation_concept_link import link as concept_link
from bie.math_intelligence.math_pipeline import process_math
from bie.math_intelligence.equation_ast import parse_equation
from bie.math_intelligence.derivation_step import make_step
from bie.math_intelligence.derivation_chain import Step, validate_chain
from bie.math_intelligence.missing_steps import detect_missing_steps
from bie.math_intelligence.formula_qa import check_formula
from bie.math_intelligence.numerical_equivalence import compare
from bie.qa.math_v2.adapters import import_equation
from bie.qa.math_v2.expression import parse, render, rational, num
from bie.qa.math_v2.algebra import equal_expressions, domain_issues, interval, Interval
from bie.qa.math_v2.units import convert, unit
from bie.qa.math_v2.models import Scope, SymbolSpec, DerivationStep as QAStep
from bie.qa.math_v2.derivation import check_step
from bie.qa.release_v2.contracts import ContractError
from bie.reasoning.grounded_result import inference
from bie.reasoning.decision_contracts import EvidenceRef, ReasoningDecisionGraph
from .contracts import require, canonical, digest, sha, ProducerError, validate_document
from .pr_reasoning import (profile_config as old_config, verify_knowledge, math_required,
    binding as old_binding, reasoning_payload, RE_SCHEMA)

PROFILE = "source_grounded_di_knowledge_pr_math_reasoning_v1"
SCHEMA = "bie.math.evidence/1"
POLICY = "source-display-equalities-exact-native-v1"
ENGINE_MODULES = ("bie.math_intelligence.math_pipeline", "bie.math_intelligence.equation_ast",
    "bie.math_intelligence.derivation_step", "bie.math_intelligence.derivation_chain",
    "bie.math_intelligence.missing_steps", "bie.math_intelligence.formula_qa",
    "bie.math_intelligence.numerical_equivalence", "bie.qa.math_v2.expression",
    "bie.qa.math_v2.algebra", "bie.qa.math_v2.units", "bie.qa.math_v2.derivation",
    "bie.qa.math_v2.adapters", "bie.document_intelligence.equation_region",
    "bie.document_intelligence.equation_source_link", "bie.knowledge_intelligence.equation_claim_link",
    "bie.knowledge_intelligence.equation_concept_link")


def engine_identity():
    import importlib
    # Normalize Git text newlines, not mathematical inputs, for platform identity.
    return {name:sha(Path(importlib.import_module(name).__file__).read_bytes().replace(b"\r\n", b"\n"))
            for name in ENGINE_MODULES}


def profile_config(provider="technical_source_derived", model="lexical-extractive-v1"):
    return dict(old_config(provider,model), profile=PROFILE, math_schema=SCHEMA,
        math_policy=POLICY, graph_version="enterprise-math-v2", math_engines=engine_identity(),
        math_policy_version=1, math_extraction="whole-native-block-no-ocr-v1")


def binding(run_id,source_hash,knowledge_id,knowledge_hash,attempt):
    return dict(old_binding(run_id,source_hash,knowledge_id,knowledge_hash,attempt),
                profile=PROFILE, policy=POLICY)


def equation(text, symbols):
    """Exact source, no stripping prose/normalization/inferred units or domains."""
    require(type(text) is str and 0 < len(text) <= 512 and text.count("=")==1,
            "unsupported_equation_syntax")
    native=process_math(text,"source-bound-display")
    require(not native.qa and native.relation=="=", "unsupported_equation_syntax")
    native_eq=parse_equation(text)
    require(native_eq.relation=="=", "unsupported_equation_syntax")
    qa=import_equation(native_eq)
    require((qa.left.symbols|qa.right.symbols)<=set(symbols),"symbol_evidence_missing")
    # Only reviewed real dimensionless symbols; never guess physics units.
    for side in (qa.left,qa.right):
        require(not domain_issues(side,{}), "math_domain_unproved")
    if qa.left.symbols or qa.right.symbols:
        require(equal_expressions(qa.left,qa.right),"symbolic_identity_unproved")
        code="EXACT_RATIONAL_POLYNOMIAL_IDENTITY"
    else:
        left,right=interval(qa.left,{}),interval(qa.right,{})
        require(left.lo==left.hi==right.lo==right.hi,"numerical_mismatch")
        require(compare(float(left.lo),float(right.lo)).equivalent,"numerical_mismatch")
        code="EXACT_RATIONAL_NUMERICAL_EQUALITY"
    require(check_formula(text,balanced=True,known_symbols=set(symbols),
                used_symbols=set(qa.left.symbols|qa.right.symbols)).passed,"formula_validation")
    return qa, dict(original_expression=text,normalized_left=render(qa.left),
        normalized_right=render(qa.right),symbols=sorted(qa.left.symbols|qa.right.symbols),
        relation="=",proof=code,verified=True,physical_law_proven=False)


def unit_equality(text):
    match=re.fullmatch(r"([0-9]+(?:\.[0-9]+)?) ([A-Za-z][A-Za-z0-9_/*^]*) = ([0-9]+(?:\.[0-9]+)?) ([A-Za-z][A-Za-z0-9_/*^]*)",text)
    require(match is not None,"unsupported_unit_syntax")
    a,u,b,v=match.groups();value=rational(a)
    result=convert(Interval(value,value),u,v)
    require(result.lo==result.hi==rational(b),"unit_value_mismatch")
    return dict(original_expression=text,from_unit=u,to_unit=v,
        dimensions=list(unit(u).dimensions),proof="EXACT_EXPLICIT_UNIT_CONVERSION",
        verified=True,physical_law_proven=False)


def source_binding(block, document, knowledge, expression):
    eid="equation-"+digest(dict(anchor=block["anchor_id"],expression=expression))
    region=EquationRegion(eid,block["physical_page"],tuple(block["geometry"]),1.0)
    region_valid(region)
    source=EquationSourceLink(eid,document["source_sha256"],block["physical_page"],
        block["region_id"],expression,1.0);link_valid(source)
    claims=[c for c in knowledge["claims"] if block["anchor_id"] in c["anchor_ids"]]
    require(claims,"equation_claim_missing")
    nodes=[c for c,n in knowledge["nodes"].items() if block["anchor_id"] in n["anchor_ids"]]
    out=dict(equation_id=eid,anchor_id=block["anchor_id"],block_id=block["block_id"],
        source_sha256=document["source_sha256"],physical_page=block["physical_page"],
        region=asdict(region),source_link=asdict(source),
        mode=classify(dict(isolated=True,line_fraction=1.0)),
        claim_links=[claim_link(eid,c["claim_id"],"EXPRESSES",block["anchor_id"]) for c in claims])
    # Numeric-only blocks need no invented semantic concept or symbol meaning.
    out["concept_link"]=concept_link(eid,nodes,[block["anchor_id"]],0.5) if nodes else None
    return out


def math_artifact(document,knowledge,prerequisite,context,did,pid):
    validate_document(document);verify_knowledge(knowledge,document)
    require(context["source_sha256"]==document["source_sha256"] and
            context["knowledge_sha256"]==digest(knowledge),"math_source_mismatch")
    blocks=document["blocks"];symbols={};declarations=[];items=[];steps=[];findings=[]
    for block in blocks:
        match=re.fullmatch(r"Symbols: ([A-Za-z][A-Za-z0-9_]*(?:, [A-Za-z][A-Za-z0-9_]*)*) dimensionless\.",block["text"])
        if match:
            for name in match[1].split(", "):
                require(name not in symbols,"symbol_ambiguous")
                symbols[name]=block["anchor_id"]
            declarations.append(dict(anchor_id=block["anchor_id"],symbols=match[1].split(", "),unit="1"))
    require(len(symbols)<=8,"math_symbol_budget")
    def observe(block,text):
        if re.fullmatch(r"[0-9.]+ [A-Za-z][A-Za-z0-9_/*^]* = [0-9.]+ [A-Za-z][A-Za-z0-9_/*^]*",text):
            result=unit_equality(text);typed=None
        else:
            typed,result=equation(text,symbols)
        return typed,dict(result,**source_binding(block,document,knowledge,text),
            symbol_declaration_anchors=[symbols[s] for s in result.get("symbols",[])])
    for block in blocks:
        text=block["text"]
        if any(block["anchor_id"]==d["anchor_id"] for d in declarations):continue
        try:
            if text.startswith("Step: "):
                require(text.count(" => ")==1,"unsupported_derivation_syntax")
                before,after=text[6:].split(" => ")
                a,ai=observe(block,before);b,bi=observe(block,after)
                require(a is not None and b is not None,"unsupported_derivation_syntax")
                native=make_step(before,after,"rewrite","explicit source rewrite",block["anchor_id"])
                scope=Scope("source-scope",tuple(SymbolSpec(s,"1") for s in sorted(symbols)))
                proof=check_step(QAStep("step-"+digest(text),(ai["claim_links"][0]["claim_id"],),a,b,"rewrite",num(0)),scope)
                require(proof.status=="PROVED","invalid_derivation_step")
                items.extend((ai,bi));steps.append(dict(native=asdict(native),anchor_id=block["anchor_id"],proof=proof.code))
            elif "=" in text:
                _,item=observe(block,text);items.append(item)
            else:
                probe=dict(document,blocks=[block])
                if math_required(probe) or re.search(r"[\\{}\[\]∂∇+*/%]|[A-Za-z0-9)]\s*-\s*[A-Za-z0-9(]|\b(?:vectors?|matrices|calculus|trigonometry|arithmetic|addition|subtraction|multiplication|division|geometry|statistics|numbers?)\b|\b\d+(?:\.\d+)?\s+(?:m|s|kg|A|K|mol|cd)\b",text,re.I):
                    findings.append(dict(anchor_id=block["anchor_id"],code="unsupported_mathematical_obligation"))
        except (ProducerError,ContractError,ValueError,OverflowError):
            findings.append(dict(anchor_id=block["anchor_id"],code="math_item_requires_review"))
    require(len(items)<=64 and len(steps)<=32,"math_item_budget")
    chain=None;gaps=[]
    if steps:
        native_steps=[Step(s["native"]["before"],s["native"]["after"]) for s in steps]
        chain=asdict(validate_chain(native_steps))
        if not chain["valid"]:findings.append(dict(code="invalid_derivation_chain",indices=list(chain["breaks"])))
        # No inferred intermediate step. Discontinuities remain explicit findings.
        for index in range(1,len(steps)):
            observed=detect_missing_steps([steps[index-1]["native"]["after"],steps[index]["native"]["before"]],
                lambda a,b:0 if a.strip()==b.strip() else 2)
            if observed:gaps.append(dict(index=index,code="missing_derivation_step",severity=observed[0].severity))
    if symbols and not items:findings.append(dict(code="unused_math_scope_requires_review"))
    required=bool(items or findings or declarations)
    applicability="REVIEW_REQUIRED" if findings else ("REQUIRED" if required else "NOT_REQUIRED")
    return dict(context,schema=SCHEMA,document_artifact_id=did,document_sha256=digest(document),
        prerequisite_artifact_id=pid,prerequisite_sha256=digest(prerequisite),
        applicability=applicability,policy_version=1,evaluator="bounded-native-math-v1",
        engine_identity=engine_identity(),source_inventory=[dict(anchor_id=b["anchor_id"],
            text_sha256=b["text_sha256"],page=b["physical_page"]) for b in blocks],
        symbols=declarations,equations=items,derivation_steps=steps,chain=chain,missing_steps=gaps,
        findings=findings,no_math_justification="complete_native_block_inventory_no_syntactic_obligation" if not required else None,
        requires_semantic_review=True,academic_acceptance=False,product_accepted=False)


def verify_math(value,document,knowledge,prerequisite,context,did,pid):
    require(type(value) is dict and canonical(value)==canonical(math_artifact(
        document,knowledge,prerequisite,context,did,pid)),"invalid_math_artifact")
    return value


def reasoning_artifact(knowledge,prerequisite,math,context,pid,mid):
    require(math["applicability"] in ("REQUIRED","NOT_REQUIRED") and not math["findings"],"math_review_required")
    require(math["run_id"]==context["run_id"] and math["source_sha256"]==context["source_sha256"]
        and math["knowledge_artifact_id"]==context["knowledge_artifact_id"] and
        math["prerequisite_artifact_id"]==pid and math["prerequisite_sha256"]==digest(prerequisite),"foreign_math_artifact")
    payload=reasoning_payload(knowledge,prerequisite,pid)
    result=inference("BIE-PROD-031","math_evidence_admission",
        dict(math_sha256=digest(math)),dict(applicability=math["applicability"],
        verified_equations=len(math["equations"])),(EvidenceRef(mid,"constraint",0.5),),
        assumptions=("bounded_source_display_fragment_only",),uncertainty=("technical_not_academic",))
    decision=result.to_decision(decision_type="evidence_arbitration",subject_id=context["run_id"],
        question="Which verified bounded Math evidence can constrain graph-order reasoning?")
    # Both the teaching-order and evidence-admission decisions bind the exact Math blob.
    for row in payload["decisions"]:row["evidence_refs"].append(asdict(EvidenceRef(mid,"constraint",0.5)))
    payload["decisions"].append(asdict(decision))
    payload["executed_types"].append("evidence_arbitration")
    ReasoningDecisionGraph([decision]).validate()
    return dict(context,schema=RE_SCHEMA,prerequisite_artifact_id=pid,
        prerequisite_sha256=digest(prerequisite),math_artifact_id=mid,math_sha256=digest(math),**payload)


def verify_reasoning(value,knowledge,prerequisite,math,context,pid,mid):
    require(canonical(value)==canonical(reasoning_artifact(knowledge,prerequisite,math,context,pid,mid)),
            "invalid_reasoning_candidate")
    return value
