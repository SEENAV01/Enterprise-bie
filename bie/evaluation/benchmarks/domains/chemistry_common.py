"""Bounded chemical formula parser and atom/charge conservation helpers.

Formula grammar: element symbols, positive integer subscripts and up to four
nested ()/[] groups. No hydrates, isotope notation, phase suffixes, leading
coefficients or charge suffixes; charge is an explicit species field.
"""
from __future__ import annotations
from collections import defaultdict
import re
from ..models import BenchmarkError, ident
from .common import integer
from .structured import record, sequence

ELEMENTS = frozenset('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())


def parse_formula(formula: object) -> dict[str, int]:
    if type(formula) is not str or not 1 <= len(formula) <= 128:
        raise BenchmarkError('FORMULA_SIZE_OR_TYPE')
    tokens = re.findall(r'[A-Z][a-z]?|[0-9]+|[()\[\]]', formula)
    if ''.join(tokens) != formula:
        raise BenchmarkError('UNSUPPORTED_FORMULA_SYNTAX')
    index = 0
    def multiplier():
        nonlocal index
        if index < len(tokens) and tokens[index].isdigit():
            raw = tokens[index]; index += 1
            if raw.startswith('0') or len(raw) > 5 or not 1 <= int(raw) <= 10000:
                raise BenchmarkError('INVALID_SUBSCRIPT')
            return int(raw)
        return 1
    def group(depth=0, closing=None):
        nonlocal index
        if depth > 4:
            raise BenchmarkError('FORMULA_DEPTH_LIMIT')
        counts = defaultdict(int); units = 0
        while index < len(tokens):
            token = tokens[index]
            if token in (')', ']'):
                if token != closing or units == 0:
                    raise BenchmarkError('UNBALANCED_OR_EMPTY_GROUP')
                index += 1
                return dict(counts)
            index += 1
            if token in ('(', '['):
                sub = group(depth+1, ')' if token=='(' else ']')
            elif token in ELEMENTS:
                sub = {token:1}
            else:
                raise BenchmarkError('UNKNOWN_ELEMENT_OR_COEFFICIENT')
            factor = multiplier(); units += 1
            for element, n in sub.items():
                counts[element] += factor*n
                if counts[element] > 10000:
                    raise BenchmarkError('ATOM_COUNT_LIMIT')
        if closing is not None or units == 0:
            raise BenchmarkError('UNBALANCED_OR_EMPTY_GROUP')
        return dict(counts)
    counts = group()
    return dict(sorted(counts.items()))


def species_table(values: object, *, maximum=24) -> dict[str, dict]:
    result = {}
    for item in sequence(values, upper=maximum):
        record(item, {'id','formula','charge'})
        key = ident(item['id'])
        if key in result:
            raise BenchmarkError('DUPLICATE_SPECIES')
        result[key] = {'elements':parse_formula(item['formula']),
                       'charge':integer(item['charge'],-12,12)}
    return result


def coefficients(values: object, species: dict, *, nonempty=True) -> dict[str, int]:
    if type(values) is not dict or not (1 if nonempty else 0) <= len(values) <= 24:
        raise BenchmarkError('INVALID_COEFFICIENT_MAP')
    result = {}
    for key, value in values.items():
        ident(key)
        if key not in species:
            raise BenchmarkError('UNKNOWN_SPECIES')
        result[key] = integer(value,1,10000)
    return result


def inventory(side: dict[str,int], species: dict) -> dict[str,int]:
    totals = defaultdict(int)
    for key, coefficient in side.items():
        for element, count in species[key]['elements'].items():
            totals[element] += coefficient*count
        totals['charge'] += coefficient*species[key]['charge']
    return {k:v for k,v in sorted(totals.items()) if v}


def conserved(left: dict[str,int], right: dict[str,int], species: dict) -> bool:
    return inventory(left, species) == inventory(right, species)
