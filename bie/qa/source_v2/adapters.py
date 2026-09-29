"""Explicit adapters for the inspected canonical BI and KI contracts.

Legacy grounded=True/confidence fields never constitute semantic support. Native
PDF runtime and Director caller migration are intentionally not claimed here.
"""
from __future__ import annotations
import math
from decimal import Decimal
from bie.document_intelligence.source_anchors import Anchor, validate as validate_anchor
from bie.document_intelligence.text_blocks import TextBlock
from ..release_v2.contracts import ContractError, token, tuple_tokens
from .models import Source, Block, Output, Claim


def _ppm(value, name: str) -> int:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ContractError('INVALID_BI_NORMALIZED_NUMBER', name)
    scaled = Decimal(str(value)) * 1_000_000
    if scaled != scaled.to_integral_value():
        raise ContractError('BI_PRECISION_UNREPRESENTABLE', name)
    return int(scaled)


def block_from_bi(block: TextBlock, anchor: Anchor, source: Source, *,
                  extractor_id: str, extractor_version: str) -> Block:
    """Preserve canonical identity; reject geometry requiring silent rounding."""
    if type(block) is not TextBlock or type(anchor) is not Anchor or type(source) is not Source:
        raise ContractError('INVALID_BI_ADAPTER_INPUT')
    if type(anchor.box) is not tuple or len(anchor.box) != 4:
        raise ContractError('INVALID_BI_GEOMETRY_SHAPE')
    try:
        validate_anchor(anchor)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ContractError('INVALID_CANONICAL_BI_ANCHOR') from exc
    if (anchor.source_hash != source.artifact.sha256 or anchor.page != block.page or
        type(block.region_ids) is not tuple or block.region_ids != (anchor.region_id,)):
        raise ContractError('BI_BLOCK_ANCHOR_MISMATCH')
    return Block(block.block_id, source.source_id, anchor.source_hash, block.page,
                 anchor.region_id, tuple(_ppm(v, 'box') for v in anchor.box), block.text,
                 extractor_id, extractor_version, _ppm(block.confidence, 'confidence'))


def claim_from_ki(record: dict, binding: dict, output: Output, *, start: int, end: int,
                  citation_map: dict[str, str], kind: str = 'FACT') -> Claim:
    """Map exact canonical claim/anchor IDs without crediting legacy booleans."""
    if type(record) is not dict or set(record) != {'claim_id', 'text', 'anchor_id'}:
        raise ContractError('INVALID_KI_CLAIM_SHAPE')
    if type(binding) is not dict or set(binding) != {'claim_id', 'anchor_ids', 'confidence', 'grounded'}:
        raise ContractError('INVALID_KI_BINDING_SHAPE')
    if type(output) is not Output or type(citation_map) is not dict:
        raise ContractError('INVALID_KI_ADAPTER_INPUT')
    if binding['claim_id'] != record['claim_id']:
        raise ContractError('KI_CLAIM_ID_MISMATCH')
    for anchor_id, citation_id in citation_map.items():
        token(anchor_id, 'canonical_anchor_id'); token(citation_id, 'citation_id')
    anchors = binding['anchor_ids']
    tuple_tokens(anchors, 'canonical_anchor_ids', 1, 128)
    if (type(anchors) is not tuple or not anchors or len(set(anchors)) != len(anchors) or
            record['anchor_id'] not in anchors or any(a not in citation_map for a in anchors)):
        raise ContractError('KI_ANCHOR_MAPPING_MISMATCH')
    _ppm(binding['confidence'], 'confidence')
    if type(binding['grounded']) is not bool:
        raise ContractError('INVALID_KI_GROUNDED_LABEL')
    return Claim(record['claim_id'], output.output_id, output.artifact.sha256,
                 start, end, record['text'], kind, tuple(citation_map[a] for a in anchors))
