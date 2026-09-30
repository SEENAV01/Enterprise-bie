"""GEO-003: declared energy/water budgets and complete-series diagnostics.

The 30-year arithmetic profile is not NOAA's station homogenization pipeline.
Effective radiating temperature is NOT observed surface temperature or forecast.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, ident
from .structured import amount, choice, probability, quantity, record, sequence
DEPTH={'mm':1,'cm':10,'m':1000}
SIGMA=Fraction(5670374419,10**17)

def celsius(value):
    record(value, {'value','unit'})
    q=amount(value['value'],signed=True,maximum=1000)
    unit=choice(value['unit'],{'degC','K'})
    q=q-Fraction(27315,100) if unit=='K' else q
    if q < -Fraction(27315,100):raise BenchmarkError('BELOW_ABSOLUTE_ZERO')
    return q

def year(value):
    if type(value) is not int or not 1<=value<=9999:raise BenchmarkError('INVALID_YEAR')
    return value

def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='planetary_budget':
        record(data, {'op','solar_constant_W_m2','albedo','emissivity'})
        s=amount(data['solar_constant_W_m2'],positive=True);a=probability(data['albedo']);e=probability(data['emissivity'])
        if e==0:raise BenchmarkError('ZERO_EMISSIVITY')
        absorbed=s*(1-a)/4
        return {'absorbed_W_m2':str(absorbed),'reflected_W_m2':str(s*a/4),
                'effective_radiating_temperature_K':float(absorbed/(e*SIGMA))**0.25,
                'profile':'GLOBAL_MEAN_STEADY_STATE_EFFECTIVE_NOT_SURFACE'}
    if op=='water_budget':
        record(data, {'op','precipitation','evapotranspiration','runoff'})
        p,e,q=(quantity(data[k],DEPTH) for k in ('precipitation','evapotranspiration','runoff'))
        return {'storage_change_mm':str(p-e-q),'profile':'CLOSED_CATCHMENT_INTERVAL_NO_LATERAL_IMPORT'}
    if op=='temperature_anomaly':
        record(data, {'op','baseline_start','baseline_end','annual_means','observation'})
        start,end=year(data['baseline_start']),year(data['baseline_end'])
        if end-start!=29:raise BenchmarkError('EXACT_30_YEAR_BASELINE_REQUIRED')
        rows=sequence(data['annual_means'],lower=30,upper=30);seen={}
        for row in rows:
            record(row, {'year','temperature'});y=year(row['year'])
            if y in seen:raise BenchmarkError('DUPLICATE_YEAR')
            seen[y]=celsius(row['temperature'])
        if set(seen)!=set(range(start,end+1)):raise BenchmarkError('BASELINE_YEAR_GAP')
        mean=sum(seen.values())/30
        return {'baseline_mean_degC':str(mean),'anomaly_degC':str(celsius(data['observation'])-mean),
                'profile':'COMPLETE_EQUAL_YEAR_MEANS_NO_HOMOGENIZATION'}
    if op=='area_weighted_temperature':
        record(data, {'op','regions'})
        regions=sequence(data['regions']);ids=set();total=Fraction(0);den=Fraction(0)
        for row in regions:
            record(row, {'id','area_km2','temperature'});rid=ident(row['id'])
            if rid in ids:raise BenchmarkError('DUPLICATE_ID')
            ids.add(rid);a=amount(row['area_km2'],positive=True)
            total+=a*celsius(row['temperature']);den+=a
        return {'mean_degC':str(total/den),'total_area_km2':str(den),'profile':'DECLARED_NONOVERLAPPING_AREA_WEIGHTS'}
    if op=='feedback_loop':
        record(data, {'op','links'})
        links=sequence(data['links'],lower=2,upper=32);out={};targets=set();sign=1
        for row in links:
            record(row, {'from','to','sign'});a,b=ident(row['from']),ident(row['to'])
            if a==b or a in out or b in targets:raise BenchmarkError('SIMPLE_CLOSED_LOOP_REQUIRED')
            out[a]=b;targets.add(b)
            sign*=1 if choice(row['sign'],{'+','-'})=='+' else -1
        if set(out)!=targets:raise BenchmarkError('SIMPLE_CLOSED_LOOP_REQUIRED')
        at=next(iter(out));seen=set()
        while at not in seen:seen.add(at);at=out[at]
        if len(seen)!=len(out):raise BenchmarkError('SIMPLE_CLOSED_LOOP_REQUIRED')
        return {'loop_sign':sign,'feedback':'reinforcing' if sign>0 else 'balancing',
                'profile':'DECLARED_LINK_POLARITY_NOT_EMPIRICAL_ATTRIBUTION'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
