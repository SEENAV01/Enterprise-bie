"""BIE-AUDIO-VO-003: bounded LaTeX parser -> immutable math tree -> speech.

No eval, CAS simplification, theorem proof or provider is used. Operators,
fractions, signs, grouping, indices and limits are explicitly voiced. Unknown
commands or ambiguous constructs require an upstream supplied realization.
English speech templates v1; other locales are reserved for VO-006 adoption.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .contracts import AudioError, fingerprint, text

GREEK = dict(zip(
    ('alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega').split(),
    ('alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega').split()))
UNICODE_GREEK = dict(zip('αβγδεζηθικλμνξοπρστυφχψω', GREEK))
OPERATORS = {r'\cdot': '*', r'\times': '*', r'\div': '/', r'\pm': '±', r'\le': '≤', r'\leq': '≤',
    r'\ge': '≥', r'\geq': '≥', r'\ne': '≠', r'\neq': '≠', r'\approx': '≈', r'\to': '→',
    '×': '*', '·': '*', '÷': '/', '−': '-', '<=': '≤', '>=': '≥', '!=': '≠'}
FUNCTIONS = {'sin': 'sine', 'cos': 'cosine', 'tan': 'tangent', 'log': 'log', 'ln': 'natural log', 'exp': 'exponential'}
RELATIONS = {'=': 'equals', '<': 'is less than', '>': 'is greater than', '≤': 'is less than or equal to',
    '≥': 'is greater than or equal to', '≠': 'is not equal to', '≈': 'is approximately equal to', '→': 'tends to'}
DIGITS = ('zero one two three four five six seven eight nine').split()
TEENS = ('ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen').split()
TENS = ('zero ten twenty thirty forty fifty sixty seventy eighty ninety').split()


def _integer_words(number: int) -> str:
    if number < 10:
        return DIGITS[number]
    if number < 20:
        return TEENS[number - 10]
    if number < 100:
        return TENS[number // 10] + (' ' + DIGITS[number % 10] if number % 10 else '')
    if number < 1000:
        return DIGITS[number // 100] + ' hundred' + (' ' + _integer_words(number % 100) if number % 100 else '')
    for factor, label in ((1_000_000_000, 'billion'), (1_000_000, 'million'), (1000, 'thousand')):
        if number >= factor:
            return _integer_words(number // factor) + ' ' + label + (' ' + _integer_words(number % factor) if number % factor else '')
    raise AudioError('NUMBER_RANGE')


def number_words(raw: str) -> str:
    if type(raw) is not str or len(raw) > 64 or not re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)', raw):
        raise AudioError('MATH_NUMBER', detail=str(raw)[:100])
    whole, dot, fractional = raw.partition('.')
    whole = whole or '0'
    if (len(whole) > 1 and whole.startswith('0')) or len(whole) > 12:
        spoken = ' '.join(DIGITS[int(d)] for d in whole)
    else:
        spoken = _integer_words(int(whole))
    return spoken + (' point ' + ' '.join(DIGITS[int(d)] for d in fractional) if dot else '')


@dataclass(frozen=True, slots=True)
class MathNode:
    kind: str
    value: str = ''
    children: tuple['MathNode', ...] = ()


@dataclass(frozen=True, slots=True)
class MathPronunciation:
    original_expression: str
    tree: MathNode
    spoken_text: str
    language: str
    policy_version: str = 'bie-audio-math/en/1'
    mathematical_truth_verified: bool = False
    audio_generated: bool = False

    @property
    def identity(self):
        return fingerprint(self)


def tokenize(expression: str) -> tuple[str, ...]:
    text(expression, 'math_expression', maximum=4096)
    result, i = [], 0
    while i < len(expression):
        if expression[i].isspace():
            i += 1
            continue
        token = re.match(r'\\[A-Za-z]+|\\[,;! ]|<=|>=|!=|(?:sin|cos|tan|log|ln|exp)(?=\s*\()|(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)[eE][+-]?[0-9]+|(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)|.', expression[i:]).group()
        i += len(token)
        if token in (r'\,', r'\;', r'\!', '\\ ', r'\left', r'\right'):
            continue
        result.append(OPERATORS.get(token, token))
        if len(result) > 512:
            raise AudioError('MATH_TOKEN_LIMIT')
    if not result:
        raise AudioError('EMPTY_MATH')
    return tuple(result)


class _Parser:
    def __init__(self, expression: str):
        self.tokens = tokenize(expression)
        self.pos = 0
        self.depth = 0
        self.nodes = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ''

    def take(self, expected=None):
        token = self.peek()
        if not token or (expected is not None and token != expected):
            raise AudioError('MATH_SYNTAX', str(self.pos), f'expected {expected}, got {token}')
        self.pos += 1
        return token

    def node(self, kind, *children, value=''):
        self.nodes += 1
        if self.nodes > 512:
            raise AudioError('MATH_NODE_LIMIT')
        return MathNode(kind, value, tuple(children))

    def group(self, opening='{', closing='}'):
        self.take(opening)
        self.depth += 1
        if self.depth > 24:
            raise AudioError('MATH_DEPTH_LIMIT')
        value = self.relation()
        self.take(closing)
        self.depth -= 1
        return value

    def relation(self):
        value = self.add()
        while self.peek() in RELATIONS:
            op = self.take()
            value = self.node('relation', value, self.add(), value=op)
        return value

    def add(self):
        value = self.product()
        while self.peek() in ('+', '-', '±'):
            op = self.take()
            value = self.node('binary', value, self.product(), value=op)
        return value

    def _atom_start(self):
        token = self.peek()
        return bool(token) and (token[0].isalnum() or token.startswith('\\') or token in ('(', '{', '√', '∞', 'π'))

    def product(self):
        value = self.unary()
        while True:
            if self.peek() in ('*', '/'):
                op = self.take()
                value = self.node('fraction' if op == '/' else 'binary', value, self.unary(), value='' if op == '/' else '*')
            elif self._atom_start():
                # Juxtaposed single-letter symbols are a documented syntax rule.
                value = self.node('binary', value, self.unary(), value='*')
            else:
                return value

    def unary(self):
        if self.peek() in ('+', '-', '±'):
            op = self.take()
            self.depth += 1
            if self.depth > 24:
                raise AudioError('MATH_DEPTH_LIMIT')
            child = self.unary()
            self.depth -= 1
            return self.node('unary', child, value=op)
        return self.power()

    def script_atom(self):
        if self.peek() == '{':
            return self.group()
        token = self.peek()
        if len(token) > 1 and not token.startswith('\\'):
            raise AudioError('MATH_SCRIPT_BRACES_REQUIRED', str(self.pos), token)
        return self.primary()

    def power(self):
        base = self.primary()
        seen = set()
        while self.peek() in ('_', '^'):
            op = self.take()
            if op in seen:
                raise AudioError('AMBIGUOUS_MATH_SCRIPT', str(self.pos), 'Use explicit braces')
            seen.add(op)
            base = self.node('power' if op == '^' else 'subscript', base, self.script_atom())
        return base

    def primary(self):
        token = self.peek()
        if token == '(':
            return self.node('group', self.group('(', ')'))
        if token == '{':
            return self.node('group', self.group())
        if re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)[eE][+-]?[0-9]+', token):
            self.take()
            mantissa, exponent = re.split('[eE]', token)
            exp_sign = exponent[0] if exponent[0] in '+-' else ''
            exp_digits = exponent[1:] if exp_sign else exponent
            n = self.node('number', value=exp_digits)
            if exp_sign:
                n = self.node('unary', n, value=exp_sign)
            return self.node('scientific', self.node('number', value=mantissa), n)
        if re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)', token):
            self.take()
            number_words(token)
            return self.node('number', value=token)
        if token in (r'\frac', r'\dfrac', r'\tfrac'):
            self.take()
            return self.node('fraction', self.group(), self.group())
        if token in (r'\sqrt', '√'):
            self.take()
            degree = self.group('[', ']') if self.peek() == '[' else None
            if self.peek() != '{' and len(self.peek()) > 1 and not self.peek().startswith('\\'):
                raise AudioError('MATH_ROOT_BRACES_REQUIRED', str(self.pos))
            radicand = self.group() if self.peek() == '{' else self.primary()
            return self.node('root', radicand, *(() if degree is None else (degree,)))
        if token in (r'\vec', r'\hat', r'\bar'):
            self.take()
            return self.node('accent', self.group(), value=token[1:])
        if token in (r'\sum', r'\prod'):
            self.take()
            self.take('_'); lower = self.script_atom()
            self.take('^'); upper = self.script_atom()
            body = self.group()
            return self.node('bounded', lower, upper, body, value=token[1:])
        if (token.startswith('\\') and token[1:] in FUNCTIONS) or token in FUNCTIONS:
            self.take()
            if self.peek() not in ('{', '('):
                raise AudioError('MATH_FUNCTION_GROUP_REQUIRED', str(self.pos))
            argument = self.group() if self.peek() == '{' else self.group('(', ')')
            return self.node('function', argument, value=token.lstrip('\\'))
        if token == r'\infty' or token == '∞':
            self.take()
            return self.node('symbol', value='infinity')
        if token.startswith('\\') and token[1:] in GREEK:
            self.take()
            return self.node('symbol', value=token[1:])
        if token in UNICODE_GREEK:
            self.take()
            return self.node('symbol', value=UNICODE_GREEK[token])
        if len(token) == 1 and token.isascii() and token.isalpha():
            self.take()
            # f(x) can mean function evaluation or multiplication; explicit
            # notation is required instead of choosing a semantics silently.
            if token in ('f', 'g', 'h') and self.peek() == '(':
                raise AudioError('MATH_FUNCTION_AMBIGUITY', str(self.pos), token)
            return self.node('identifier', value=token)
        raise AudioError('MATH_UNSUPPORTED', str(self.pos), token)


def _speak(node: MathNode, depth=0) -> str:
    if depth > 64:
        raise AudioError('MATH_DEPTH_LIMIT')
    speak = lambda n: _speak(n, depth + 1)
    children = node.children
    if node.kind == 'scientific':
        return speak(children[0]) + ' times ten to the power of ' + speak(children[1]) + ' end power'
    if node.kind == 'number':
        return number_words(node.value)
    if node.kind == 'identifier':
        return ('capital ' + node.value.lower()) if node.value.isupper() else node.value
    if node.kind == 'symbol':
        return node.value
    if node.kind == 'group':
        return 'open quantity ' + speak(children[0]) + ' close quantity'
    if node.kind == 'fraction':
        return 'start fraction numerator ' + speak(children[0]) + ' denominator ' + speak(children[1]) + ' end fraction'
    if node.kind == 'binary':
        return speak(children[0]) + {'+': ' plus ', '-': ' minus ', '*': ' times ', '±': ' plus or minus '}[node.value] + speak(children[1])
    if node.kind == 'unary':
        return {'+': 'positive ', '-': 'negative ', '±': 'plus or minus '}[node.value] + speak(children[0])
    if node.kind == 'relation':
        return speak(children[0]) + ' ' + RELATIONS[node.value] + ' ' + speak(children[1])
    if node.kind == 'power':
        exponent = children[1]
        return speak(children[0]) + ((' squared' if exponent.value == '2' else ' cubed') if
            exponent.kind == 'number' and exponent.value in ('2', '3') else
            ' to the power of ' + speak(exponent) + ' end power')
    if node.kind == 'subscript':
        return speak(children[0]) + ' subscript ' + speak(children[1]) + ' end subscript'
    if node.kind == 'root':
        return ('square root of ' if len(children) == 1 else 'root with index ' + speak(children[1]) + ' of ') + speak(children[0]) + ' end root'
    if node.kind == 'function':
        return FUNCTIONS[node.value] + ' of ' + speak(children[0]) + ' end function'
    if node.kind == 'accent':
        return {'vec': 'vector ', 'hat': 'hat ', 'bar': 'bar over '}[node.value] + speak(children[0]) + ' end accent'
    if node.kind == 'bounded':
        label = 'sum' if node.value == 'sum' else 'product'
        return label + ' from ' + speak(children[0]) + ' to ' + speak(children[1]) + ' of ' + speak(children[2]) + ' end ' + label
    raise AudioError('MATH_NODE_KIND', node.kind)


def pronounce_math(expression: str, *, language='en') -> MathPronunciation:
    if language not in ('en', 'en-US', 'en-GB', 'en-IN'):
        raise AudioError('MATH_LANGUAGE_UNSUPPORTED', language, 'VO-006 language policy not yet adopted')
    parser = _Parser(expression)
    tree = parser.relation()
    if parser.peek():
        raise AudioError('MATH_TRAILING_INPUT', str(parser.pos), parser.peek())
    spoken = _speak(tree)
    if len(spoken) > 32_000:
        raise AudioError('MATH_SPEECH_LIMIT')
    return MathPronunciation(expression, tree, spoken, language)
