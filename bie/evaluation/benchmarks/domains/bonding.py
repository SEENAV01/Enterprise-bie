"""CHEM-001: explicit Lewis electron accounting and bounded VSEPR geometry.

Formal charge is bookkeeping, not partial charge. Resonance is not oscillation
between isolable molecules. Octet/duet diagnostics do not prove chemical stability.
"""
from __future__ import annotations
from ..models import BenchmarkError, ident
from .common import integer
from .structured import choice, observed_claims, record, sequence

VALENCE = {'H':1,'Be':2,'B':3,'C':4,'N':5,'O':6,'F':7}
GEOMETRIES = {
    (2,0):('linear','linear'),
    (3,0):('trigonal_planar','trigonal_planar'),
    (2,1):('trigonal_planar','bent'),
    (4,0):('tetrahedral','tetrahedral'),
    (3,1):('tetrahedral','trigonal_pyramidal'),
    (2,2):('tetrahedral','bent'),
}
CONCEPTS = {'formal_charge_is_partial_charge':False,
            'resonance_is_temporal_switching':False,
            'multiple_bond_vsepr_domains':'one',
            'polar_bonds_always_imply_polar_molecule':False}


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op = data.get('op')
    if op == 'lewis_audit':
        record(data, {'op','atoms','bonds','total_charge'})
        charge = integer(data['total_charge'],-12,12)
        atoms = {}
        for atom in sequence(data['atoms'], upper=32):
            record(atom, {'id','element','nonbonding_electrons'})
            key = ident(atom['id'])
            if key in atoms:
                raise BenchmarkError('DUPLICATE_ATOM')
            element = choice(atom['element'], VALENCE)
            nonbonding = integer(atom['nonbonding_electrons'],0,8)
            if nonbonding % 2:
                raise BenchmarkError('RADICAL_OUTSIDE_PROFILE')
            atoms[key] = (element, nonbonding)
        orders = {key:0 for key in atoms}; seen = set(); total_bond_order = 0
        for bond in sequence(data['bonds'], lower=0, upper=64):
            record(bond, {'a','b','order'})
            a,b = ident(bond['a']),ident(bond['b'])
            if a not in atoms or b not in atoms:
                raise BenchmarkError('DANGLING_BOND')
            if a==b:
                raise BenchmarkError('SELF_BOND')
            key = tuple(sorted((a,b)))
            if key in seen:
                raise BenchmarkError('DUPLICATE_BOND')
            seen.add(key)
            order = integer(bond['order'],1,3)
            orders[a] += order; orders[b] += order; total_bond_order += order
        formal = {k:VALENCE[e]-n-orders[k] for k,(e,n) in atoms.items()}
        electron_count = sum(n for _,n in atoms.values()) + 2*total_bond_order
        shells = {k:n+2*orders[k] for k,(_,n) in atoms.items()}
        defects = []
        if sum(formal.values()) != charge:
            defects.append('TOTAL_CHARGE_MISMATCH')
        for key,(element,_) in sorted(atoms.items()):
            target = 2 if element=='H' else 8
            if shells[key] > target:
                defects.append('OVERFILLED_SHELL:'+key)
            elif shells[key] < target:
                defects.append('INCOMPLETE_SHELL:'+key)
        return {'formal_charges':dict(sorted(formal.items())),
                'formal_charge_sum':sum(formal.values()),
                'drawn_valence_electrons':electron_count,
                'required_valence_electrons':sum(VALENCE[e] for e,_ in atoms.values())-charge,
                'shell_electrons':dict(sorted(shells.items())),
                'defects':defects, 'profile':'LEWIS_BOOKKEEPING_NOT_STABILITY_PROOF'}
    if op == 'vsepr':
        record(data, {'op','bonded_domains','lone_pairs'})
        b = integer(data['bonded_domains'],1,4); l = integer(data['lone_pairs'],0,3)
        if (b,l) not in GEOMETRIES:
            raise BenchmarkError('GEOMETRY_OUTSIDE_PROFILE')
        eg, mg = GEOMETRIES[(b,l)]
        return {'electron_geometry':eg, 'molecular_geometry':mg,
                'electron_domains':b+l, 'profile':'MAIN_GROUP_2_TO_4_DOMAINS'}
    if op == 'audit_concepts':
        record(data, {'op','claims'})
        return observed_claims(data['claims'], CONCEPTS)
    raise BenchmarkError('UNSUPPORTED_OPERATION')
