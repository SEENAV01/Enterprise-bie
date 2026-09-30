"""BIO-001: oxygenic C3 photosynthesis budgets and misconception diagnostics.

Net bookkeeping is not the sequence of chemical steps. Calvin budgeting assumes
no photorespiration or C4/CAM overhead and supplied ATP/NADPH, not night-only work.
"""
from __future__ import annotations
from ..models import BenchmarkError
from .structured import amount, exact_map, observed_claims, record

PROFILE = {
    'oxygen_source': 'water',
    'fixed_carbon_source': 'carbon_dioxide',
    'calvin_location': 'chloroplast_stroma',
    'light_reaction_location': 'thylakoid_membrane',
    'calvin_direct_photon_requirement': False,
    'calvin_independent_of_atp_nadph_supply': False,
    'plants_also_respire': True,
}


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op = data.get('op')
    if op == 'net_budget':
        record(data, {'op', 'glucose_mol'})
        g = amount(data['glucose_mol'])
        return {'net_consumed_mol': exact_map({'CO2': 6*g, 'H2O': 6*g}),
                'net_produced_mol': exact_map({'C6H12O6': g, 'O2': 6*g}),
                'oxygen_source': 'water', 'profile': 'NET_OXYGENIC_BOOKKEEPING'}
    if op == 'calvin_budget':
        record(data, {'op', 'co2_mol'})
        c = amount(data['co2_mol'])
        return {'net_g3p_mol': str(c/3), 'atp_consumed_mol': str(3*c),
                'nadph_consumed_mol': str(2*c),
                'gross_g3p_reduced_mol': str(2*c),
                'g3p_recycled_mol': str(5*c/3),
                'rubp_regenerated_mol': str(c),
                'profile': 'IDEAL_C3_CALVIN_NO_PHOTORESPIRATION'}
    if op == 'resource_limited_calvin':
        record(data, {'op', 'co2_mol', 'atp_mol', 'nadph_mol'})
        c, a, n = (amount(data[k]) for k in ('co2_mol', 'atp_mol', 'nadph_mol'))
        capacities = {'CO2': c/3, 'ATP': a/9, 'NADPH': n/6}
        g = min(capacities.values())
        return {'net_g3p_mol': str(g),
                'limiting_resources': sorted(k for k,v in capacities.items() if v == g),
                'unused_mol': exact_map({'CO2': c-3*g, 'ATP': a-9*g, 'NADPH': n-6*g}),
                'profile': 'IDEAL_C3_SUPPLIED_POOLS_NOT_KINETIC_PREDICTION'}
    if op == 'audit_concepts':
        record(data, {'op', 'claims'})
        return observed_claims(data['claims'], PROFILE)
    raise BenchmarkError('UNSUPPORTED_OPERATION')
