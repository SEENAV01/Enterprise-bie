"""CHEM-003: exact rational nullspace balancing, charge and limiting reagents.

A balanced formula equation proves bookkeeping only, not reaction feasibility.
Solution is unique only when the matrix has nullity one and positive coefficients.
"""
from __future__ import annotations
from fractions import Fraction
from functools import reduce
from math import gcd, lcm
from ..models import BenchmarkError
from .structured import amount, exact_map, record, sequence
from .chemistry_common import coefficients, conserved, species_table


def setup(data):
    left = sequence(data['reactants'], upper=6)
    right = sequence(data['products'], upper=6)
    species = species_table(left+right, maximum=12)
    return species, [v['id'] for v in left], [v['id'] for v in right]


def balance(species: dict, reactants: list[str], products: list[str]) -> dict:
    keys = reactants+products
    elements = sorted({e for item in species.values() for e in item['elements']})+['charge']
    matrix=[]
    for element in elements:
        row=[]
        for key in keys:
            item=species[key]
            count=item['charge'] if element=='charge' else item['elements'].get(element,0)
            row.append(Fraction(count * (1 if key in reactants else -1)))
        matrix.append(row)
    pivots=[]; row_index=0
    for col in range(len(keys)):
        pivot=next((i for i in range(row_index,len(matrix)) if matrix[i][col]),None)
        if pivot is None:
            continue
        matrix[row_index],matrix[pivot]=matrix[pivot],matrix[row_index]
        divisor=matrix[row_index][col]
        matrix[row_index]=[v/divisor for v in matrix[row_index]]
        for i in range(len(matrix)):
            if i!=row_index and matrix[i][col]:
                factor=matrix[i][col]
                matrix[i]=[v-factor*p for v,p in zip(matrix[i],matrix[row_index])]
        pivots.append(col);row_index+=1
        if row_index==len(matrix):break
    free=[i for i in range(len(keys)) if i not in pivots]
    if len(free)!=1:
        raise BenchmarkError('BALANCE_NOT_UNIQUE' if free else 'NO_NONZERO_BALANCE')
    solution=[Fraction(0)]*len(keys);solution[free[0]]=Fraction(1)
    for row,pivot in enumerate(pivots):
        solution[pivot]=-matrix[row][free[0]]
    scale=lcm(*(v.denominator for v in solution))
    integers=[int(v*scale) for v in solution]
    if any(v<=0 for v in integers):
        raise BenchmarkError('NO_STRICTLY_POSITIVE_BALANCE')
    divisor=reduce(gcd,integers)
    result={key:n//divisor for key,n in zip(keys,integers)}
    if max(result.values())>10000:
        raise BenchmarkError('BALANCE_COEFFICIENT_LIMIT')
    return result


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='balance':
        record(data, {'op','reactants','products'})
        species,left,right=setup(data)
        result=balance(species,left,right)
        return {'reactants':{k:result[k] for k in sorted(left)},
                'products':{k:result[k] for k in sorted(right)},
                'profile':'PRIMITIVE_INTEGER_ATOM_AND_CHARGE_BALANCE'}
    if op=='reaction_extent':
        record(data, {'op','reactants','products','coefficients','feed_mol'})
        species,left,right=setup(data)
        coeff=coefficients(data['coefficients'],species)
        if set(coeff)!=set(species):
            raise BenchmarkError('COMPLETE_COEFFICIENTS_REQUIRED')
        if not conserved({k:coeff[k] for k in left},{k:coeff[k] for k in right},species):
            raise BenchmarkError('UNBALANCED_REACTION')
        feeds=data['feed_mol']
        if type(feeds) is not dict or set(feeds)!=set(left):
            raise BenchmarkError('COMPLETE_REACTANT_FEED_REQUIRED')
        feeds={k:amount(v) for k,v in feeds.items()}
        capacities={k:feeds[k]/coeff[k] for k in left}
        extent=min(capacities.values())
        return {'extent_mol':str(extent),
                'limiting_reactants':sorted(k for k,v in capacities.items() if v==extent),
                'consumed_mol':exact_map({k:extent*coeff[k] for k in left}),
                'remaining_mol':exact_map({k:feeds[k]-extent*coeff[k] for k in left}),
                'produced_mol':exact_map({k:extent*coeff[k] for k in right}),
                'profile':'IDEAL_COMPLETE_CONVERSION_NO_SIDE_REACTIONS'}
    if op=='percent_yield':
        record(data, {'op','actual_mol','theoretical_mol'})
        actual=amount(data['actual_mol']);theoretical=amount(data['theoretical_mol'],positive=True)
        if actual>theoretical:
            raise BenchmarkError('PURE_PRODUCT_YIELD_EXCEEDS_THEORY')
        return {'percent_yield':str(100*actual/theoretical),
                'profile':'PURE_PRODUCT_SAME_SPECIES_MOLAR_YIELD'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
