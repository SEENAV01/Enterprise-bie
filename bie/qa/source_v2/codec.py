"""Closed-world JSON codec. Wire input carries data, never operator trust/policy."""
from __future__ import annotations
from dataclasses import fields
import json
from ..release_v2.contracts import ArtifactRef, ContractError, canonical_bytes
from .models import Request, Source, Block, Output, Claim, Citation, MAX_ITEMS
from .attestation import Assessment
MAX_REQUEST_JSON_BYTES = 16 * 1024 * 1024


def _shape(value, cls):
    if type(value) is not dict or set(value) != {f.name for f in fields(cls)}:
        raise ContractError('SOURCE_OBJECT_FIELDS_MISMATCH', cls.__name__)
    return dict(value)


def _array(value):
    if type(value) is not list or len(value) > MAX_ITEMS:
        raise ContractError('INVALID_SOURCE_JSON_ARRAY')
    return tuple(value)


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ContractError('DUPLICATE_JSON_KEY', key)
        result[key] = value
    return result


def _no_number(value):
    raise ContractError('NON_INTEGER_JSON_NUMBER')


def loads(data: bytes):
    if type(data) is not bytes or not 0 < len(data) <= MAX_REQUEST_JSON_BYTES:
        raise ContractError('SOURCE_JSON_SIZE_OR_TYPE')
    try:
        result = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                            parse_float=_no_number, parse_constant=_no_number)
        # Reuse Batch001 bounded JSON validation, including finite integer-only
        # values, Unicode encoding and depth. No JSON deserialization hooks run.
        canonical_bytes(result)
        return result
    except ContractError:
        raise
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ContractError('INVALID_SOURCE_JSON') from exc


def request_from_dict(value) -> Request:
    data = _shape(value, Request)
    converted = {}
    for name, cls in (('sources', Source), ('blocks', Block), ('outputs', Output),
                      ('citations', Citation), ('claims', Claim)):
        rows = []
        for raw in _array(data[name]):
            item = _shape(raw, cls)
            if 'artifact' in item: item['artifact'] = ArtifactRef(**_shape(item['artifact'], ArtifactRef))
            if 'box_ppm' in item: item['box_ppm'] = _array(item['box_ppm'])
            if 'citation_ids' in item: item['citation_ids'] = _array(item['citation_ids'])
            rows.append(cls(**item))
        converted[name] = tuple(rows)
    data.update(converted)
    return Request(**data)


def load_request(data: bytes) -> Request:
    return request_from_dict(loads(data))


def load_assessments(data: bytes) -> tuple[Assessment, ...]:
    return tuple(Assessment(**_shape(item, Assessment)) for item in _array(loads(data)))
