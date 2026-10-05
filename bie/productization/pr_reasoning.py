"""Private Task030 contracts and bounded technical producer, not academic QA.

Only explicit lexical prerequisite statements are accepted. Graph-order reasoning
is native; temporal/causal/spatial interpretation is deliberately NOT executed.
No live transport, paid credentials, source-order dependency heuristic or new engine.
"""
from dataclasses import asdict
import re
from bie.prerequisite_intelligence.explicit_prerequisites import extract_explicit_prerequisites
from bie.prerequisite_intelligence.graph import Edge, build_graph, roots
from bie.prerequisite_intelligence.cycle_resolution import WeightedEdge, find_cycle
from bie.prerequisite_intelligence.teaching_order import teaching_order
from bie.prerequisite_intelligence.qa import validate_prerequisite_graph
from bie.reasoning.prerequisite_order import decide
from bie.reasoning.grounded_result import inference
from bie.reasoning.decision_contracts import EvidenceRef, ReasoningDecisionGraph
from bie.reasoning.structured_uncertainty import UncertaintyComponent, assess_uncertainty
from bie.reasoning.unsupported_reasoning_detection import ReasoningClaim, detect_unsupported_reasoning
from bie.model_gateway.model_interface import ModelRequest, ModelResponse, validate_request
from bie.model_gateway.provider_registry import ProviderRegistry, ProviderDescriptor, RegistryError
from .contracts import (PROFILE as OLD_PROFILE, profile_config as old_config, ProducerError,
    require, identifier, canonical, strict_json, digest, validate_document, KNOWLEDGE_SCHEMA)
from .candidates import validate_candidates, CANDIDATE_SCHEMA

PROFILE = "source_grounded_di_knowledge_pr_reasoning_v1"
PR_SCHEMA = "bie.prerequisite.graph/1"
RE_SCHEMA = "bie.reasoning.decision_set/1"
POLICY = "explicit-source-dependency-order-v1"
PROVIDER = "technical_source_derived"
MODEL = "explicit-dependency-graph-v1"


def profile_config(provider=PROVIDER, model="lexical-extractive-v1"):
    return dict(old_config(provider,model),profile=PROFILE,prerequisite_schema=PR_SCHEMA,
        reasoning_schema=RE_SCHEMA,continuation_policy=POLICY,
        continuation_provider=PROVIDER,continuation_model=MODEL,
        continuation_prompt="explicit-source-graph-v1",math_policy="missing-math-evidence-block-v1")


def verify_knowledge(knowledge, document):
    validate_document(document)
    require(type(knowledge) is dict and set(knowledge)=={"schema","source_sha256","nodes","edges",
        "claims","evidence_kind","privacy","academic_acceptance"},"knowledge_contract")
    require(knowledge["schema"]==KNOWLEDGE_SCHEMA and knowledge["source_sha256"]==document["source_sha256"]
        and knowledge["evidence_kind"]=="TECHNICAL_SOURCE_DERIVED" and knowledge["privacy"]=="PRIVATE"
        and knowledge["academic_acceptance"] is False,"knowledge_contract")
    require(type(knowledge["nodes"]) is dict,"knowledge_contract")
    candidate=dict(schema=CANDIDATE_SCHEMA,concepts=list(knowledge["nodes"].values()),
        relations=knowledge["edges"],claims=knowledge["claims"],definitions=[],examples=[],terms=[],entities=[],conditions=[])
    validate_candidates(candidate,document)
    require(all(k==v["concept_id"] for k,v in knowledge["nodes"].items()),"knowledge_node_identity")
    return knowledge


def math_required(document):
    """Conservative syntactic gate, not a mathematical/semantic domain classifier.

    Inspect FULL extracted text, not just bounded KI claim excerpts. Unknown
    mathematical obligations stay blocked: there is no admitted Math artifact.
    """
    validate_document(document)
    text="\n".join(b["text"] for b in document["blocks"])
    return bool(re.search(r"[=<>±×÷∑∫√^]|\d\s*[+*/-]\s*\d|\b(?:equation|formula|derivation|calculate|compute|solve|theorem|proof|integral|derivative|matrix|unit conversion|probability|percentage|percent|ratio|velocity|acceleration|force|joules?|newtons?)\b|\b\d+(?:\.\d+)?\s*(?:kg|cm|km|m/s|m2|m3|mol|Hz|Pa|%)",text,re.I))


def explicit_edges(knowledge):
    nodes=knowledge["nodes"];by_label={}
    for cid,node in nodes.items():by_label.setdefault(node["label"].casefold(),[]).append(cid)
    edges=[];review=[];seen=set()
    for claim in knowledge["claims"]:
        for sentence in re.findall(r"[^.!?]+[.!?]?",claim["text"]):
            # Full explicit subject+dependency statement; no arbitrary co-occurrence/order.
            match=re.fullmatch(r"\s*([A-Za-z][A-Za-z-]{2,39})\s+(?:requires|depends on)\s+([^.!?]+)[.!?]?\s*",sentence,re.I)
            if not match:continue
            dependent=by_label.get(match[1].casefold(),[])
            for candidate in extract_explicit_prerequisites(match[1],sentence):
                pre=by_label.get(candidate.prerequisite.casefold(),[])
                if len(pre)!=1 or len(dependent)!=1:
                    review.append(dict(claim_id=claim["claim_id"],code="unsupported_prerequisite_candidate"));continue
                a,b=pre[0],dependent[0]
                anchors=sorted(set(claim["anchor_ids"]) & set(nodes[a]["anchor_ids"]) & set(nodes[b]["anchor_ids"]))
                require(a!=b,"prerequisite_self_edge")
                require(anchors,"missing_source_evidence")
                key=(a,b,claim["claim_id"])
                if key in seen:continue
                seen.add(key)
                edges.append(dict(prerequisite=a,dependent=b,claim_id=claim["claim_id"],anchor_ids=anchors,
                    confidence=0.5,evidence_kind="TECHNICAL_SOURCE_DERIVED"))
    require(len(edges)<=200,"prerequisite_budget")
    return sorted(edges,key=lambda e:(e["prerequisite"],e["dependent"],e["claim_id"])),review


def prerequisite_payload(knowledge):
    edges,review=explicit_edges(knowledge)
    nodes=set(knowledge["nodes"])
    pairs=sorted({(e["prerequisite"],e["dependent"]) for e in edges})
    graph=build_graph(nodes,[Edge(a,b,0.5) for a,b in pairs])
    require(not find_cycle(nodes,[WeightedEdge(a,b,0.5) for a,b in pairs]),"prerequisite_cycle")
    require(validate_prerequisite_graph(nodes,[(a,b,0.5) for a,b in pairs]).passed,"prerequisite_validation")
    return dict(edges=edges,review=review,order=teaching_order(nodes,pairs),roots=roots(graph))


def binding(run_id,source_hash,knowledge_id,knowledge_hash,attempt):
    identifier(run_id);identifier(knowledge_id)
    require(type(attempt) is int and attempt>0,"attempt_identity")
    return dict(run_id=run_id,source_sha256=source_hash,knowledge_artifact_id=knowledge_id,
        knowledge_sha256=knowledge_hash,attempt=attempt,profile=PROFILE,policy=POLICY,
        privacy="PRIVATE",evidence_kind="TECHNICAL_SOURCE_DERIVED",academic_acceptance=False)


def prerequisite_artifact(knowledge,context):
    return dict(context,schema=PR_SCHEMA,nodes=sorted(knowledge["nodes"]),**prerequisite_payload(knowledge))


def verify_prerequisite(value,knowledge,context):
    require(type(value) is dict and canonical(value)==canonical(prerequisite_artifact(knowledge,context)),"invalid_prerequisite_candidate")
    return value


def reasoning_payload(knowledge,prerequisite,pr_id):
    pairs=sorted({(e["prerequisite"],e["dependent"]) for e in prerequisite["edges"]})
    order,acyclic=decide(set(knowledge["nodes"]),pairs)
    require(acyclic and list(order)==prerequisite["order"],"reasoning_order_inconsistent")
    components=[UncertaintyComponent("technical-source","INFERENCE",
        "Lexical source assertion and graph order are not semantic or calibrated truth",(pr_id,),weight=0.5)]
    assessment=assess_uncertainty(components)
    refs=(EvidenceRef(prerequisite["knowledge_artifact_id"],"primary",assessment.conservative_confidence_ceiling),
          EvidenceRef(pr_id,"prerequisite",assessment.conservative_confidence_ceiling))
    result=inference("BIE-PROD-030","prerequisite_topological_order",
        dict(knowledge_sha256=digest(knowledge),prerequisite_sha256=digest(prerequisite)),
        dict(order=list(order),edge_count=len(pairs)),refs,
        assumptions=("explicit_source_dependency_only","id_tie_break_not_semantic_order"),
        uncertainty=("technical_not_academic","source_assertions_not_independently_verified"))
    decision=result.to_decision(decision_type="teaching_order",subject_id=prerequisite["run_id"],
        question="What dependency order is supported by the admitted explicit source graph?")
    claims=[ReasoningClaim(c["claim_id"],c["text"],(prerequisite["knowledge_artifact_id"],)) for c in knowledge["claims"]]
    require(detect_unsupported_reasoning(decision,claims).passed,"reasoning_missing_evidence")
    ReasoningDecisionGraph([decision]).validate()
    return dict(decisions=[asdict(decision)],source_claim_ids=sorted(c["claim_id"] for c in knowledge["claims"]),
        source_anchor_ids=sorted({a for c in knowledge["claims"] for a in c["anchor_ids"]}),
        uncertainty=asdict(assessment),executed_types=["teaching_order"],
        not_executed_types=["causal","temporal","spatial","mathematical_derivation"],requires_review=True)


def reasoning_artifact(knowledge,prerequisite,context,pr_id,document):
    require(not math_required(document),"math_evidence_required")
    return dict(context,schema=RE_SCHEMA,prerequisite_artifact_id=pr_id,
        prerequisite_sha256=digest(prerequisite),**reasoning_payload(knowledge,prerequisite,pr_id))


def verify_reasoning(value,knowledge,prerequisite,context,pr_id,document):
    require(type(value) is dict and canonical(value)==canonical(reasoning_artifact(knowledge,prerequisite,context,pr_id,document)),
        "invalid_reasoning_candidate")
    return value


class TechnicalGraphProvider:
    def invoke(self,request):
        validate_request(request)
        payload=strict_json(request.messages[0]["content"].encode())
        knowledge=verify_knowledge(payload["knowledge"],payload["document"])
        if payload["stage"]=="PREREQUISITE":value=prerequisite_payload(knowledge)
        else:
            require(not math_required(payload["document"]),"math_evidence_required")
            value=reasoning_payload(knowledge,payload["prerequisite"],payload["prerequisite_id"])
        return ModelResponse(PROVIDER,MODEL,canonical(value).decode(),{},"complete",
            {"evidence_kind":"TECHNICAL_SOURCE_DERIVED","live":False})


def registry_for():
    registry=ProviderRegistry()
    registry.register(ProviderDescriptor(PROVIDER,MODEL,frozenset({"grounded_pr_reasoning"})),TechnicalGraphProvider())
    return registry


def gateway_candidate(stage,knowledge,document,config,*,prerequisite=None,prerequisite_id=None,registry=None):
    if stage=="REASONING":require(not math_required(document),"math_evidence_required")
    registry=registry_for() if registry is None else registry
    try:descriptor,provider=registry.get(config["continuation_provider"],config["continuation_model"])
    except RegistryError:raise ProducerError("provider_unavailable") from None
    require(descriptor.enabled and "grounded_pr_reasoning" in descriptor.capabilities and
        (descriptor.provider_id,descriptor.model_id)==(PROVIDER,MODEL),"provider_unavailable")
    inputs=dict(stage=stage,knowledge=knowledge,document=document,prerequisite=prerequisite,
        prerequisite_id=prerequisite_id,policy=config["continuation_policy"])
    raw=canonical(inputs);require(len(raw)<=4*1024*1024,"candidate_request_budget")
    request=ModelRequest(digest(inputs),({"role":"user","content":raw.decode()},),
        frozenset({"grounded_pr_reasoning"}),{"schema":PR_SCHEMA if stage=="PREREQUISITE" else RE_SCHEMA})
    try:response=provider.invoke(request)
    except ProducerError as exc:
        require(exc.code in {"math_evidence_required","prerequisite_self_edge","prerequisite_cycle",
            "missing_source_evidence","prerequisite_budget","prerequisite_validation"},"provider_execution_failed")
        raise
    except TimeoutError:raise ProducerError("provider_timeout") from None
    except Exception:raise ProducerError("provider_execution_failed") from None
    require(type(response) is ModelResponse and response.provider==PROVIDER and response.model==MODEL
        and response.finish_reason=="complete" and response.provenance=={"evidence_kind":"TECHNICAL_SOURCE_DERIVED","live":False}
        and type(response.content) is str,"provider_response_identity")
    value=strict_json(response.content.encode())
    expected=prerequisite_payload(knowledge) if stage=="PREREQUISITE" else reasoning_payload(knowledge,prerequisite,prerequisite_id)
    require(canonical(value)==canonical(expected),"invalid_prerequisite_candidate" if stage=="PREREQUISITE" else "invalid_reasoning_candidate")
    return value,dict(request_id=request.request_id,prompt_version=config["continuation_prompt"],
        provider=PROVIDER,model=MODEL,candidate_sha256=digest(value),policy=POLICY,
        grounding="EXPLICIT_SOURCE_BOUND",validation="PASS",live_provider_executed=False)
