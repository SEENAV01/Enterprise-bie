"""Private, bounded source-grounded artifact contracts for BIE-PROD-029."""
from dataclasses import asdict
import hashlib
import json
import re

from bie.document_intelligence.source_anchors import Anchor, validate as validate_anchor
from bie.document_intelligence.page_mapping import Anchor as PageAnchor, validate as validate_page_map
from bie.document_intelligence.real_pdf_text_runtime import READING_ORDER_POLICY

DOCUMENT_SCHEMA = "bie.document.structured/1"
KNOWLEDGE_SCHEMA = "bie.knowledge.graph/1"
CANDIDATE_SCHEMA = "bie.knowledge.candidates/1"
PROFILE = "source_grounded_di_knowledge_v1"
TECHNICAL_PROVIDER = "technical_source_derived"
TECHNICAL_MODEL = "lexical-extractive-v1"
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
MAX_BLOCKS = 200
MAX_TEXT_BYTES = 512 * 1024
HASH = re.compile(r"[a-f0-9]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


class ProducerError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(condition, code):
    if not condition:
        raise ProducerError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(canonical(value))


def identifier(value):
    require(type(value) is str and bool(ID.fullmatch(value)), "invalid_identifier")
    return value


def strict_json(raw):
    require(type(raw) is bytes and len(raw) <= MAX_ARTIFACT_BYTES, "artifact_budget")
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: require(False, "invalid_json"))
    except ProducerError:
        raise
    except Exception:
        raise ProducerError("invalid_json") from None


def profile_config(provider=TECHNICAL_PROVIDER, model=TECHNICAL_MODEL):
    identifier(provider); identifier(model)
    return dict(profile=PROFILE, document_schema=DOCUMENT_SCHEMA,
                knowledge_schema=KNOWLEDGE_SCHEMA, candidate_schema=CANDIDATE_SCHEMA,
                provider=provider, model=model, prompt_version="extractive-grounding-v1",
                max_blocks=MAX_BLOCKS, max_text_bytes=MAX_TEXT_BYTES,
                academic_acceptance=False)


def structured_document(inspection, source_id, runtime_identity):
    blocks = []
    for page in inspection.pages:
        for item in page.source_linked_blocks:
            anchor = asdict(item.source_anchor)
            blocks.append(dict(block_id=item.block.block_id, text=item.block.text,
                text_sha256=sha(item.block.text.encode()), physical_page=item.block.page,
                reading_order=item.order_index, region_id=item.region.region_id,
                geometry=list(item.region.box), anchor=anchor,
                anchor_id="anchor-" + digest(anchor), page_map=asdict(item.page_map_anchor)))
    document = dict(schema=DOCUMENT_SCHEMA, source_sha256=inspection.source_hash,
        source_artifact_id=source_id, byte_length=inspection.byte_length,
        runtime_identity=runtime_identity, reading_order_policy=READING_ORDER_POLICY,
        page_count=inspection.page_count, blocks=blocks, privacy="PRIVATE",
        academic_acceptance=False)
    validate_document(document)
    return document


def validate_document(document):
    require(type(document) is dict and document.get("schema") == DOCUMENT_SCHEMA,
            "document_schema")
    require(set(document) == {"schema","source_sha256","source_artifact_id","byte_length",
        "runtime_identity","reading_order_policy","page_count","blocks","privacy","academic_acceptance"},
        "document_fields")
    require(type(document.get("byte_length")) is int and 0 < document["byte_length"] <= 25*1024*1024,
            "source_budget")
    require(type(document.get("runtime_identity")) is str and bool(HASH.fullmatch(document["runtime_identity"]))
            and document.get("reading_order_policy") == READING_ORDER_POLICY,"runtime_identity")
    require(document.get("privacy") == "PRIVATE" and document.get("academic_acceptance") is False,
            "document_privacy")
    require(bool(HASH.fullmatch(document.get("source_sha256", ""))), "source_hash")
    identifier(document.get("source_artifact_id"))
    require(type(document.get("page_count")) is int and 0 < document["page_count"] <= 500,
            "page_budget")
    blocks = document.get("blocks")
    require(type(blocks) is list and 0 < len(blocks) <= MAX_BLOCKS, "block_budget")
    seen = set(); anchors = set(); orders = set(); total = 0
    for block in blocks:
        require(type(block) is dict, "block_schema")
        require(set(block) == {"block_id","text","text_sha256","physical_page","reading_order",
            "region_id","geometry","anchor","anchor_id","page_map"}, "block_fields")
        identifier(block.get("block_id"))
        text = block.get("text")
        require(type(text) is str and text.strip(), "empty_block")
        total += len(text.encode())
        require(total <= MAX_TEXT_BYTES, "text_budget")
        require(sha(text.encode()) == block.get("text_sha256"), "text_hash_mismatch")
        try:
            anchor = Anchor(**block["anchor"])
            validate_anchor(anchor)
            page_anchor=PageAnchor(**block["page_map"])
            validate_page_map((page_anchor,),document["page_count"])
        except Exception:
            raise ProducerError("invalid_anchor") from None
        require(anchor.source_hash == document["source_sha256"], "foreign_anchor")
        require(anchor.page == block.get("physical_page") and anchor.page <= document["page_count"],
                "anchor_page")
        require(type(anchor.page) is int and page_anchor.physical_page == anchor.page and
                page_anchor.region_id == anchor.region_id and list(page_anchor.box) == list(anchor.box),
                "page_map_binding")
        require(anchor.region_id == block.get("region_id") and
                list(anchor.box) == block.get("geometry"), "anchor_geometry")
        require(block.get("anchor_id") == "anchor-" + digest(block["anchor"]), "anchor_identity")
        order = (anchor.page, block.get("reading_order"))
        require(type(order[1]) is int and order[1] >= 0, "reading_order")
        require(block["block_id"] not in seen and block["anchor_id"] not in anchors and order not in orders,
                "duplicate_block")
        seen.add(block["block_id"]); anchors.add(block["anchor_id"]); orders.add(order)
    require(len(canonical(document)) <= MAX_ARTIFACT_BYTES, "artifact_budget")
    return document
