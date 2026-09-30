"""GEO-001: directed boundary kinematics, spreading and tectonic concepts.

Velocities are local planar projections, not global Euler-pole reconstruction.
No earthquake occurrence/time prediction follows from an average plate speed.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError
from .structured import amount, choice, observed_claims, quantity, record, sequence

RATES={'cm/yr':1,'mm/yr':Fraction(1,10),'m/yr':100}
TIME={'Myr':1,'yr':Fraction(1,1000000)}
DISTANCE={'km':1,'m':Fraction(1,1000)}
CONCEPTS={'plate_material':'crust_and_rigid_uppermost_mantle',
          'mantle_entirely_liquid':False,
          'transform_creates_new_crust_in_ideal_model':False,
          'seafloor_age_increases_away_from_ridge_in_simple_model':True,
          'average_plate_speed_predicts_exact_earthquake_time':False}
FEATURES={
    'oceanic_divergent':{'oceanic_lithosphere_created':True,'oceanic_lithosphere_consumed':False,'landform':'mid_ocean_ridge'},
    'ocean_continent_convergent':{'oceanic_lithosphere_created':False,'oceanic_lithosphere_consumed':True,'landform':'trench_and_continental_arc'},
    'continent_collision':{'oceanic_lithosphere_created':False,'oceanic_lithosphere_consumed':False,'landform':'crustal_shortening_mountain_belt'},
    'transform':{'oceanic_lithosphere_created':False,'oceanic_lithosphere_consumed':False,'landform':'strike_slip_fault_zone'},
}


def velocity(value):
    record(value, {'values','unit'})
    units=choice(value['unit'],RATES)
    return tuple(amount(x,signed=True)*RATES[units] for x in sequence(value['values'],lower=2,upper=2))


def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='boundary_motion':
        record(data, {'op','velocity_a','velocity_b','normal_a_to_b'})
        va,vb=velocity(data['velocity_a']),velocity(data['velocity_b'])
        nx,ny=(amount(x,signed=True) for x in sequence(data['normal_a_to_b'],lower=2,upper=2))
        if nx*nx+ny*ny!=1:raise BenchmarkError('EXACT_UNIT_NORMAL_REQUIRED')
        dx,dy=vb[0]-va[0],vb[1]-va[1]
        normal=dx*nx+dy*ny;shear=-dx*ny+dy*nx
        motion='divergent' if normal>0 else 'convergent' if normal<0 else 'transform' if shear else 'no_relative_motion'
        if normal and shear:motion='oblique_'+motion
        return {'separation_cm_per_yr':str(normal),'tangential_cm_per_yr':str(shear),
                'motion':motion,'profile':'LOCAL_PLANAR_DIRECTED_UNIT_NORMAL'}
    if op=='spreading_distance':
        record(data, {'op','rate','rate_kind','duration'})
        rate=quantity(data['rate'],RATES)
        kind=choice(data['rate_kind'],{'half','full'})
        half=rate if kind=='half' else rate/2
        duration=quantity(data['duration'],TIME)
        distance=10*half*duration
        return {'one_flank_km':str(distance),'total_separation_km':str(2*distance),
                'profile':'CONSTANT_SYMMETRIC_SPREADING'}
    if op=='age_from_ridge':
        record(data, {'op','distance','half_rate'})
        distance=quantity(data['distance'],DISTANCE)
        rate=quantity(data['half_rate'],RATES,positive=True)
        return {'age_Myr':str(distance/(10*rate)),
                'profile':'CONSTANT_HALF_RATE_PER_FLANK'}
    if op=='boundary_features':
        record(data, {'op','boundary'})
        boundary=choice(data['boundary'],FEATURES)
        return {**FEATURES[boundary],'profile':'IDEALIZED_OCEANIC_LITHOSPHERE_BUDGET_NOT_TOTAL_CRUST_BUDGET'}
    if op=='audit_concepts':
        record(data, {'op','claims'})
        return observed_claims(data['claims'],CONCEPTS)
    raise BenchmarkError('UNSUPPORTED_OPERATION')
