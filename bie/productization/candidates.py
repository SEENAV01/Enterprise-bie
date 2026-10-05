"""Explicit TECHNICAL source-derived gateway provider, never semantic acceptance.

Extractive lexical candidates and verbatim claims depend on native source text.
No pre-authored concepts, invented edges, live API, or second gateway exists here.
"""
import re
from bie.model_gateway.model_interface import ModelRequest, ModelResponse, validate_request
from bie.model_gateway.provider_registry import ProviderRegistry, ProviderDescriptor, RegistryError
from bie.knowledge_intelligence.knowledge_graph_build import build
from bie.knowledge_intelligence.knowledge_graph_validate import validate
from bie.knowledge_intelligence.ki_e2e_pipeline import run as validate_ki
from .contracts import (CANDIDATE_SCHEMA, KNOWLEDGE_SCHEMA, TECHNICAL_PROVIDER,
                        TECHNICAL_MODEL, ProducerError, canonical, strict_json,
                        digest, sha, require, validate_document)

COLLECTIONS = {"concepts", "claims", "relations", "definitions", "examples",
               "terms", "entities", "conditions"}


class TechnicalSourceDerivedProvider:
    def invoke(self, request):
        validate_request(request)
        document = validate_document(strict_json(request.messages[0]["content"].encode()))
        concepts = {}; claims = []
        for block in document["blocks"]:
            anchor = block["anchor_id"]
            for label in sorted(set(re.findall(r"[A-Za-z][A-Za-z-]{2,39}", block["text"])))[:5]:
                cid = "concept-" + digest(label.casefold())
                if cid not in concepts:
                    concepts[cid] = dict(concept_id=cid, label=label, anchor_ids=[])
                if anchor not in concepts[cid]["anchor_ids"]:
                    concepts[cid]["anchor_ids"].append(anchor)
            claims.append(dict(claim_id="claim-" + digest(anchor),
                               text=block["text"][:512], anchor_ids=[anchor]))
        require(0 < len(concepts) <= 200, "concept_budget")
        payload = dict(schema=CANDIDATE_SCHEMA, concepts=list(concepts.values()),
                       claims=claims, relations=[], definitions=[], examples=[],
                       terms=[], entities=[], conditions=[])
        return ModelResponse(TECHNICAL_PROVIDER, TECHNICAL_MODEL, canonical(payload).decode(),
            {}, "complete", {"evidence_kind":"TECHNICAL_SOURCE_DERIVED", "live":False})


def technical_registry():
    registry = ProviderRegistry()
    registry.register(ProviderDescriptor(TECHNICAL_PROVIDER, TECHNICAL_MODEL,
        frozenset({"structured_knowledge"})), TechnicalSourceDerivedProvider())
    return registry


def validate_candidates(payload, document):
    validate_document(document)
    require(type(payload) is dict and set(payload) == COLLECTIONS | {"schema"}
            and payload["schema"] == CANDIDATE_SCHEMA, "candidate_schema")
    for name in COLLECTIONS:
        require(type(payload[name]) is list and len(payload[name]) <= 200, "candidate_budget")
    require(payload["concepts"] and payload["claims"], "empty_knowledge")
    blocks = {b["anchor_id"]: b for b in document["blocks"]}
    for name, id_key, text_key in (("claims", "claim_id", "text"),
                                  ("concepts", "concept_id", "label")):
        seen = set()
        for item in payload[name]:
            require(type(item) is dict and set(item) == {id_key, text_key, "anchor_ids"},
                    "candidate_fields")
            value = item[text_key]; anchors = item["anchor_ids"]
            require(type(value) is str and 0 < len(value) <= (512 if name == "claims" else 80),
                    "candidate_text_budget")
            require(type(item[id_key]) is str and item[id_key] not in seen, "candidate_identity")
            seen.add(item[id_key])
            require(type(anchors) is list and anchors and len(anchors) == len(set(anchors))
                    and all(a in blocks for a in anchors), "missing_or_foreign_anchor")
            require(all((value in blocks[a]["text"] if name == "claims" else
                         value.casefold() in blocks[a]["text"].casefold()) for a in anchors),
                    "unsupported_candidate")
    # No ungrounded optional semantic structures accepted in this technical slice.
    require(all(not payload[n] for n in ("definitions","examples","terms","entities","conditions")),
            "unsupported_semantic_structure")
    for relation in payload["relations"]:
        require(type(relation) is dict and set(relation) == {"source","target","type","anchor_ids"},
                "relation_schema")
        require(relation["type"] == "co_occurs" and relation["anchor_ids"], "unsupported_relation")
        nodes = {c["concept_id"]:c for c in payload["concepts"]}
        require(relation["source"] in nodes and relation["target"] in nodes and
                all(a in nodes[relation["source"]]["anchor_ids"] and
                    a in nodes[relation["target"]]["anchor_ids"] for a in relation["anchor_ids"]),
                "invalid_relation")
    try:
        graph = build(payload["concepts"], payload["relations"])
        require(validate(graph)["passed"] and validate_ki(payload)["passed"], "ki_validation")
    except ProducerError:
        raise
    except Exception:
        raise ProducerError("ki_validation") from None
    return graph


def produce(document, config, registry=None):
    validate_document(document)
    registry = technical_registry() if registry is None else registry
    try:
        descriptor, provider = registry.get(config["provider"], config["model"])
    except RegistryError:
        raise ProducerError("provider_unavailable") from None
    require(descriptor.enabled and "structured_knowledge" in descriptor.capabilities,
            "provider_unavailable")
    # Task029 deliberately installs no live transport or credential provisioning.
    require((descriptor.provider_id, descriptor.model_id) == (TECHNICAL_PROVIDER, TECHNICAL_MODEL),
            "provider_unavailable")
    request = ModelRequest(digest(dict(document=digest(document), config=config)),
        ({"role":"user", "content":canonical(document).decode()},),
        frozenset({"structured_knowledge"}), {"schema":CANDIDATE_SCHEMA})
    try:
        response = provider.invoke(request)
    except TimeoutError:
        raise ProducerError("provider_timeout") from None
    except Exception:
        raise ProducerError("provider_execution_failed") from None
    require(type(response) is ModelResponse and response.provider == descriptor.provider_id and
            response.model == descriptor.model_id and response.finish_reason == "complete" and
            response.provenance == {"evidence_kind":"TECHNICAL_SOURCE_DERIVED", "live":False},
            "provider_response_identity")
    require(type(response.content) is str, "candidate_schema")
    payload = strict_json(response.content.encode())
    graph = validate_candidates(payload, document)
    output = dict(schema=KNOWLEDGE_SCHEMA, source_sha256=document["source_sha256"],
        nodes=graph["nodes"], edges=list(graph["edges"]), claims=payload["claims"],
        evidence_kind="TECHNICAL_SOURCE_DERIVED", privacy="PRIVATE", academic_acceptance=False)
    receipt = dict(schema="bie.knowledge.generation-receipt/1", request_id=request.request_id,
        input_sha256=digest(document), candidate_sha256=digest(payload), output_sha256=digest(output),
        provider=response.provider, model=response.model, prompt_version=config["prompt_version"],
        candidate_schema=CANDIDATE_SCHEMA, knowledge_schema=KNOWLEDGE_SCHEMA,
        evidence_kind="TECHNICAL_SOURCE_DERIVED", live_provider_executed=False,
        grounding="VERBATIM_SOURCE_BOUND", validation="PASS", academic_acceptance=False)
    return payload, output, receipt
