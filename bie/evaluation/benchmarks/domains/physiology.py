"""BIO-003: explicitly educational steady-flow physiology diagnostics.

Not patient interpretation, diagnosis, treatment or a normal-range classifier.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError
from .structured import choice, exact_map, observed_claims, quantity, record

VOLUME = {'mL':1, 'L':1000}
RATE = {'per_min':1, 'per_s':60}
OSMOLAR = {'mOsm/L':1, 'Osm/L':1000}
CIRCULATION = {
    'systemic': ['left_ventricle','systemic_arteries','systemic_capillaries',
                 'systemic_veins','right_atrium'],
    'pulmonary': ['right_ventricle','pulmonary_arteries','pulmonary_capillaries',
                  'pulmonary_veins','left_atrium']}
CONCEPTS = {'artery_defined_by': 'flow_away_from_heart',
            'vein_defined_by': 'flow_towards_heart',
            'pulmonary_artery_relative_oxygen': 'lower',
            'pulmonary_vein_relative_oxygen': 'higher',
            'negative_feedback_response': 'opposes_deviation'}


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError('INVALID_FIELDS')
    op = data.get('op')
    if op == 'cardiac_output':
        record(data, {'op','stroke_volume','heart_rate'})
        v = quantity(data['stroke_volume'], VOLUME)
        r = quantity(data['heart_rate'], RATE)
        return {'cardiac_output_L_per_min':str(v*r/1000),
                'profile':'STEADY_PER_VENTRICLE_EDUCATIONAL_FLOW'}
    if op == 'ventilation':
        record(data, {'op','tidal_volume','dead_space','breathing_rate'})
        t = quantity(data['tidal_volume'], VOLUME)
        d = quantity(data['dead_space'], VOLUME)
        r = quantity(data['breathing_rate'], RATE)
        if d > t:
            raise BenchmarkError('DEAD_SPACE_EXCEEDS_TIDAL_VOLUME')
        return {'minute_ventilation_L_per_min':str(t*r/1000),
                'alveolar_ventilation_L_per_min':str((t-d)*r/1000),
                'profile':'FIXED_DEAD_SPACE_EDUCATIONAL_MODEL'}
    if op == 'circulation_route':
        record(data, {'op','circuit'})
        circuit = choice(data['circuit'], CIRCULATION)
        return {'route':list(CIRCULATION[circuit]),
                'profile':'ADULT_POSTNATAL_NORMAL_CIRCULATION'}
    if op == 'osmosis':
        record(data, {'op','inside','outside','solute_profile'})
        choice(data['solute_profile'], {'nonpenetrating_ideal'})
        inside = quantity(data['inside'], OSMOLAR)
        outside = quantity(data['outside'], OSMOLAR)
        relation = 'isotonic' if outside==inside else 'hypertonic' if outside>inside else 'hypotonic'
        direction = 'no_net_flow' if outside==inside else 'out_of_cell' if outside>inside else 'into_cell'
        return {'outside_relative_tonicity':relation, 'water_direction':direction,
                'profile':'INITIAL_IDEAL_NONPENETRATING_SOLUTE_EQUAL_PRESSURE'}
    if op == 'audit_concepts':
        record(data, {'op','claims'})
        return observed_claims(data['claims'], CONCEPTS)
    raise BenchmarkError('UNSUPPORTED_OPERATION')
