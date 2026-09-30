"""CHEM-002: atom/charge-conserving step sums and rate-law scope guards.

Conservation is necessary, NOT proof that a mechanism actually occurs. No
conditions, synthesis instructions or mechanistic inference from net equations.
"""
from __future__ import annotations
from collections import defaultdict
from ..models import BenchmarkError, ident
from .common import integer
from .structured import amount, exact_map, record, sequence
from .chemistry_common import coefficients, conserved, species_table


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op = data.get('op')
    if op == 'audit_steps':
        record(data, {'op','species','steps'})
        species = species_table(data['species'])
        net = defaultdict(int); first = {}; used=set()
        for step in sequence(data['steps'], upper=16):
            record(step, {'reactants','products'})
            left = coefficients(step['reactants'], species)
            right = coefficients(step['products'], species)
            if not conserved(left,right,species):
                raise BenchmarkError('UNBALANCED_ELEMENTARY_STEP')
            for key in sorted(set(left)|set(right)):
                used.add(key)
                delta = right.get(key,0)-left.get(key,0)
                net[key] += delta
                if delta and key not in first:
                    first[key] = delta
        if used != set(species):
            raise BenchmarkError('UNUSED_SPECIES')
        if not any(net.values()):
            raise BenchmarkError('NO_NET_REACTION')
        cancelled = [k for k in net if net[k]==0]
        return {'net_reactants':{k:-v for k,v in sorted(net.items()) if v<0},
                'net_products':{k:v for k,v in sorted(net.items()) if v>0},
                'intermediates':sorted(k for k in cancelled if first.get(k,0)>0),
                'catalysts':sorted(k for k in cancelled if first.get(k,0)<0),
                'spectators':sorted(k for k in cancelled if first.get(k,0)==0),
                'mechanism_experimentally_established':False,
                'profile':'DECLARED_STEP_SEQUENCE_CONSERVATION_ONLY'}
    if op == 'elementary_rate_law':
        record(data, {'op','reactants','is_elementary'})
        if data['is_elementary'] is not True:
            raise BenchmarkError('ELEMENTARY_STEP_REQUIRED')
        reactants = data['reactants']
        if type(reactants) is not dict or not 1 <= len(reactants) <= 3:
            raise BenchmarkError('INVALID_REACTANT_MAP')
        exponents = {ident(k):integer(v,1,3) for k,v in reactants.items()}
        molecularity = sum(exponents.values())
        if molecularity>3:
            raise BenchmarkError('MOLECULARITY_OUTSIDE_PROFILE')
        return {'concentration_exponents':dict(sorted(exponents.items())),
                'overall_order':molecularity,
                'profile':'DECLARED_ELEMENTARY_MASS_ACTION'}
    if op == 'energy_profile':
        record(data, {'op','energies_kJ_per_mol'})
        energies = [amount(x,signed=True) for x in sequence(data['energies_kJ_per_mol'],lower=3,upper=17)]
        if len(energies)%2==0:
            raise BenchmarkError('ALTERNATING_MINIMA_MAXIMA_REQUIRED')
        forward=[]; reverse=[]
        for i in range(1,len(energies),2):
            if energies[i] <= max(energies[i-1],energies[i+1]):
                raise BenchmarkError('TRANSITION_STATE_NOT_MAXIMUM')
            forward.append(str(energies[i]-energies[i-1]))
            reverse.append(str(energies[i]-energies[i+1]))
        return {'forward_barriers_kJ_per_mol':forward,
                'reverse_barriers_kJ_per_mol':reverse,
                'net_energy_change_kJ_per_mol':str(energies[-1]-energies[0]),
                'rate_determining_step_inferred':False,
                'profile':'ENERGY_DIFFERENCES_NOT_FULL_KINETICS'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
