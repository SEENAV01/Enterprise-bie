"""BIO-002: exact segregation, independent-locus crosses and H-W model.

No claims about personal genetic risk. Linked loci/epistasis are refused rather
than silently treated as independent Mendelian inheritance.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
import re
from ..models import BenchmarkError
from .structured import choice, exact_map, probability, record, sequence


def locus_cross(item: dict) -> dict[str, Fraction]:
    record(item, {'gene', 'parent_a', 'parent_b'})
    gene = item['gene']
    if type(gene) is not str or re.fullmatch('[A-Z]', gene) is None:
        raise BenchmarkError('INVALID_GENE_SYMBOL')
    genotypes = []
    for name in ('parent_a', 'parent_b'):
        g = item[name]
        if type(g) is not str or len(g) != 2 or any(x not in (gene, gene.lower()) for x in g):
            raise BenchmarkError('INVALID_DIPLOID_GENOTYPE')
        genotypes.append(g)
    result = defaultdict(Fraction)
    for a in genotypes[0]:
        for b in genotypes[1]:
            result[''.join(sorted(a+b))] += Fraction(1,4)
    return dict(result)


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op = data.get('op')
    if op == 'mendelian_cross':
        record(data, {'op', 'loci', 'assortment', 'dominance'})
        choice(data['assortment'], {'independent'})
        choice(data['dominance'], {'complete'})
        loci = sequence(data['loci'], upper=4)
        # Validate every locus before sorting or doing the Cartesian product.
        products = [(item, locus_cross(item)) for item in loci]
        genes = [item['gene'] for item, _ in products]
        if len(set(genes)) != len(genes):
            raise BenchmarkError('DUPLICATE_LOCUS')
        products.sort(key=lambda p: p[0]['gene'])
        distribution = {'': Fraction(1)}
        for _, local in products:
            distribution = {prefix + g: p*q for prefix,p in distribution.items()
                            for g,q in local.items()}
        phenotypes = defaultdict(Fraction)
        for genotype, p in distribution.items():
            label = '|'.join(genotype[i]+'_' if genotype[i].isupper() else genotype[i:i+2]
                             for i in range(0, len(genotype), 2))
            phenotypes[label] += p
        return {'genotype_probabilities': exact_map(distribution),
                'phenotype_probabilities': exact_map(phenotypes),
                'probability_sum': str(sum(distribution.values())),
                'profile': 'INDEPENDENT_DIPLOID_COMPLETE_DOMINANCE'}
    if op == 'hardy_weinberg':
        record(data, {'op', 'p', 'assumptions'})
        assumptions = sequence(data['assumptions'], lower=5, upper=5)
        required = {'random_mating','large_population','no_selection','no_mutation','no_migration'}
        if any(type(v) is not str for v in assumptions) or set(assumptions) != required:
            raise BenchmarkError('HARDY_WEINBERG_ASSUMPTIONS_REQUIRED')
        p = probability(data['p']); q = 1-p
        return {'p':str(p), 'q':str(q),
                'genotype_probabilities':exact_map({'AA':p*p, 'Aa':2*p*q, 'aa':q*q}),
                'profile':'IDEAL_TWO_ALLELE_HARDY_WEINBERG_NOT_OBSERVED_COUNTS'}
    if op == 'allele_frequency':
        from .common import integer
        record(data, {'op','AA','Aa','aa'})
        aa, ab, bb = [integer(data[k],0,10**9) for k in ('AA','Aa','aa')]
        total = aa+ab+bb
        if not total:
            raise BenchmarkError('EMPTY_POPULATION')
        return {'p':str(Fraction(2*aa+ab,2*total)),
                'q':str(Fraction(2*bb+ab,2*total)),
                'individuals':total, 'equilibrium_established':False}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
