"""Bounded source-linked native-PDF arithmetic observation for Section 16.

An operator chooses one existing canonical text block. This is neither
automatic formula detection nor a mathematical correctness/semantic judgment.
Unsupported notation fails closed, without text normalization or OCR.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re

from ...document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from ...math_intelligence.equation_ast import parse_equation
from ...math_intelligence.expression_ast import parse_expression
from ..release_v2.contracts import ContractError
from .adapters import import_equation, import_node

_ATOM = r'(?:[A-Za-z][A-Za-z0-9_]{0,47}|(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+))'
_CHAIN = re.compile(rf'\s*{_ATOM}(?:\s*[+\-*/^]\s*{_ATOM})*\s*\Z')
_TOKEN = re.compile(rf'{_ATOM}|[+\-*/^]')
_BLOCK_ID = re.compile(r'p[0-9]{4}-b[0-9]{4}\Z')


@dataclass(frozen=True)
class NativePdfMathObservation:
    source_hash: str
    byte_length: int
    page: int
    block_id: str
    region_id: str
    box: tuple[float, float, float, float]
    text_sha256: str
    char_count: int
    kind: str
    expression_digests: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            'box': list(self.box),
            'expression_digests': list(self.expression_digests),
            'native_parser_observed': True,
            'mathematical_truth_proven': False,
            'automatic_formula_detection': False,
            'product_accepted': False,
        }


def _parse_side(text: str):
    if not _CHAIN.fullmatch(text):
        raise ContractError('UNSUPPORTED_NATIVE_PDF_MATH_SYNTAX')
    tokens = _TOKEN.findall(text)
    if not 1 <= len(tokens) <= 127:
        raise ContractError('NATIVE_PDF_MATH_TOKEN_LIMIT')
    return import_node(parse_expression(tokens), text)


def _digest_expression(expression) -> str:
    payload = json.dumps(expression.to_dict(), sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def inspect_selected_native_pdf_math_line(data: bytes | bytearray, block_id: str) -> NativePdfMathObservation:
    """Parse only one selected canonical block, retaining exact source linkage."""
    if type(block_id) is not str or not _BLOCK_ID.fullmatch(block_id):
        raise ContractError('INVALID_NATIVE_PDF_MATH_BLOCK_ID')
    document = inspect_real_pdf_text(data)
    found = [item for page in document.pages for item in page.source_linked_blocks
             if item.block.block_id == block_id]
    if len(found) != 1:
        raise ContractError('NATIVE_PDF_MATH_BLOCK_NOT_UNIQUE')
    item = found[0]
    source_text = item.block.text
    if not 1 <= len(source_text) <= 2048:
        raise ContractError('INVALID_NATIVE_PDF_MATH_TEXT')
    if '=' in source_text:
        if source_text.count('=') != 1:
            raise ContractError('UNSUPPORTED_NATIVE_PDF_MATH_RELATION')
        native_equation = parse_equation(source_text)
        if native_equation.relation != '=':
            raise ContractError('UNSUPPORTED_NATIVE_PDF_MATH_RELATION')
        left = _parse_side(native_equation.left)
        right = _parse_side(native_equation.right)
        imported = import_equation(native_equation)
        if (imported.left, imported.right) != (left, right):
            raise ContractError('NATIVE_PDF_MATH_EQUATION_DIVERGENCE')
        expressions = (left, right)
        kind = 'equation'
    else:
        expressions = (_parse_side(source_text),)
        kind = 'expression'
    return NativePdfMathObservation(
        source_hash=document.source_hash,
        byte_length=document.byte_length,
        page=item.block.page,
        block_id=block_id,
        region_id=item.region.region_id,
        box=item.region.box,
        text_sha256=hashlib.sha256(source_text.encode('utf-8')).hexdigest(),
        char_count=len(source_text),
        kind=kind,
        expression_digests=tuple(_digest_expression(x) for x in expressions),
    )
