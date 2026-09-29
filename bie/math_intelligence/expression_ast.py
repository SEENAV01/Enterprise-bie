"""Small, complete native binary-expression parser.

This preserves the original Node contract. Unsupported syntax fails closed;
callers requiring parentheses, unary operators or functions use the governed
Section 16 complete-parser adapter instead.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Node:
    kind: str
    value: str
    children: tuple["Node", ...] = ()


PREC = {"+": 10, "-": 10, "*": 20, "/": 20, "^": 30}
ATOM = re.compile(
    r"(?:[A-Za-z][A-Za-z0-9_]*|[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\Z"
)


def parse_expression(tokens: list[str]) -> Node:
    if type(tokens) is not list or not 1 <= len(tokens) <= 256:
        raise ValueError("invalid expression token inventory")
    if any(type(token) is not str or not 1 <= len(token) <= 160 for token in tokens):
        raise ValueError("invalid expression token")

    index = 0
    nodes = 0

    def parse(min_prec: int = 0, depth: int = 0) -> Node:
        nonlocal index, nodes
        if depth >= 24 or index >= len(tokens):
            raise ValueError("missing operand or expression too deep")
        atom = tokens[index]
        if ATOM.fullmatch(atom) is None:
            raise ValueError("unsupported native atom")
        index += 1
        nodes += 1
        left = Node("atom", atom)
        while index < len(tokens):
            op = tokens[index]
            precedence = PREC.get(op)
            if precedence is None or precedence < min_prec:
                break
            index += 1
            right = parse(precedence if op == "^" else precedence + 1, depth + 1)
            nodes += 1
            if nodes > 128:
                raise ValueError("expression node limit")
            left = Node("binary", op, (left, right))
        return left

    result = parse()
    if index != len(tokens):
        raise ValueError("unconsumed expression tokens")
    return result
