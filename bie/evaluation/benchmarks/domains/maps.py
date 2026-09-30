"""GEO-002: bounded map scale, DMS and spherical/planar geometry references.

A caller-specified sphere is not an ellipsoidal geodesic or a routing service.
All scale lengths refer to the printed map at its declared scale.
"""
from __future__ import annotations
from fractions import Fraction
import math
from ..models import BenchmarkError, number
from .structured import amount, choice, quantity, record, sequence
LENGTH={'mm':Fraction(1,1000),'cm':Fraction(1,100),'m':1,'km':1000}
AREA={'mm2':Fraction(1,1000000),'cm2':Fraction(1,10000),'m2':1}

def coordinate(value):
    record(value, {'latitude_deg','longitude_deg'})
    lat=number(value['latitude_deg'],maximum=90)
    lon=number(value['longitude_deg'],maximum=180)
    return math.radians(lat),math.radians(lon)

def solve(data: dict) -> dict:
    if type(data) is not dict: raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='scale_distance':
        record(data, {'op','map_length','scale_denominator'})
        d=quantity(data['map_length'],LENGTH)
        scale=amount(data['scale_denominator'],positive=True)
        return {'ground_m':str(d*scale),'profile':'PRINTED_REPRESENTATIVE_FRACTION'}
    if op=='scale_area':
        record(data, {'op','map_area','scale_denominator'})
        a=quantity(data['map_area'],AREA)
        scale=amount(data['scale_denominator'],positive=True)
        return {'ground_m2':str(a*scale*scale),'profile':'UNIFORM_PLANAR_SCALE_AREA'}
    if op=='dms':
        record(data, {'op','axis','degrees','minutes','seconds','hemisphere'})
        axis=choice(data['axis'],{'latitude','longitude'})
        limit=90 if axis=='latitude' else 180
        deg=data['degrees'];minute=data['minutes'];sec=amount(data['seconds'])
        if type(deg) is not int or type(minute) is not int or not 0<=deg<=limit or not 0<=minute<60 or not 0<=sec<60:
            raise BenchmarkError('INVALID_DMS')
        h=choice(data['hemisphere'],{'N','S'} if axis=='latitude' else {'E','W'})
        angle=Fraction(deg)+Fraction(minute,60)+sec/3600
        if angle>limit:raise BenchmarkError('INVALID_DMS')
        if h in {'S','W'}:angle=-angle
        return {'decimal_degrees':str(angle),'axis':axis}
    if op=='spherical_distance':
        record(data, {'op','a','b','sphere_radius_m'})
        a,b=coordinate(data['a']),coordinate(data['b'])
        radius=float(amount(data['sphere_radius_m'],positive=True))
        # Haversine is continuous across the antimeridian. Clamp roundoff only.
        h=math.sin((b[0]-a[0])/2)**2+math.cos(a[0])*math.cos(b[0])*math.sin((b[1]-a[1])/2)**2
        angle=2*math.asin(math.sqrt(max(0.0,min(1.0,h))))
        return {'distance_m':radius*angle,'central_angle_rad':angle,'profile':'DECLARED_SPHERE_NOT_ELLIPSOID'}
    if op=='planar_bearing':
        record(data, {'op','delta_east_m','delta_north_m'})
        e=float(amount(data['delta_east_m'],signed=True));n=float(amount(data['delta_north_m'],signed=True))
        if e==n==0:raise BenchmarkError('BEARING_UNDEFINED_AT_ZERO_DISTANCE')
        return {'bearing_deg':math.degrees(math.atan2(e,n))%360,
                'distance_m':math.hypot(e,n),'profile':'CLOCKWISE_FROM_GRID_NORTH'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
