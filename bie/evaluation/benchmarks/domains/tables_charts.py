"""DATA-001: structured table arithmetic and data-to-chart fidelity.

No image/OCR reading is claimed. Exact supplied cells are source data; candidate
chart points are joined by row ID, never by their visual order alone.
"""
from __future__ import annotations
from fractions import Fraction
from ..models import BenchmarkError, ident
from .structured import amount, choice, record, sequence

def table(value, *, nullable=False):
    rows=sequence(value);out={}
    for row in rows:
        record(row, {'id','value'});key=ident(row['id'])
        if key in out:raise BenchmarkError('DUPLICATE_ROW_ID')
        out[key]=None if nullable and row['value'] is None else amount(row['value'],signed=True)
    return out

def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='summary':
        record(data, {'op','rows','missing_policy'})
        mode=choice(data['missing_policy'],{'reject','exclude_explicit'})
        vals=table(data['rows'],nullable=True);missing=sorted(k for k,v in vals.items() if v is None)
        if missing and mode=='reject':raise BenchmarkError('MISSING_CELL')
        nums=[v for v in vals.values() if v is not None]
        if not nums:raise BenchmarkError('NO_OBSERVED_VALUES')
        nums.sort();n=len(nums);median=nums[n//2] if n%2 else (nums[n//2-1]+nums[n//2])/2
        return {'sum':str(sum(nums)),'mean':str(sum(nums)/n),'median':str(median),
                'observed_count':n,'missing_count':len(missing),'excluded_ids':missing}
    if op=='percent_change':
        record(data, {'op','before','after'})
        before=amount(data['before'],positive=True);after=amount(data['after'])
        return {'absolute_change':str(after-before),'percent_change':str(100*(after-before)/before),
                'profile':'POSITIVE_BASE_RELATIVE_CHANGE'}
    if op=='weighted_mean':
        record(data, {'op','rows'});seen=set();num=Fraction(0);den=Fraction(0)
        for row in sequence(data['rows']):
            record(row, {'id','value','weight'});key=ident(row['id'])
            if key in seen:raise BenchmarkError('DUPLICATE_ROW_ID')
            seen.add(key);w=amount(row['weight']);v=amount(row['value'],signed=True)
            num+=v*w;den+=w
        if not den:raise BenchmarkError('ZERO_TOTAL_WEIGHT')
        return {'weighted_mean':str(num/den),'total_weight':str(den)}
    if op=='chart_fidelity':
        record(data, {'op','source_rows','chart_points','source_unit','chart_unit','chart_type','y_axis'})
        src=table(data['source_rows']);pts=table(data['chart_points'])
        su=ident(data['source_unit']);cu=ident(data['chart_unit'])
        kind=choice(data['chart_type'],{'bar','line','scatter'})
        record(data['y_axis'], {'minimum','maximum','scale'})
        lo=amount(data['y_axis']['minimum'],signed=True);hi=amount(data['y_axis']['maximum'],signed=True)
        scale=choice(data['y_axis']['scale'],{'linear','log'})
        if hi<=lo or (scale=='log' and lo<=0):raise BenchmarkError('INVALID_AXIS')
        defects=[]
        if su!=cu:defects.append({'id':'units','reason':'UNIT_MISMATCH_NO_IMPLICIT_CONVERSION'})
        for key in sorted(set(src)|set(pts)):
            if key not in pts:reason='MISSING_POINT'
            elif key not in src:reason='EXTRA_POINT'
            elif src[key]!=pts[key]:reason='CELL_VALUE_MISMATCH'
            elif not lo<=pts[key]<=hi:reason='POINT_OUTSIDE_AXIS'
            else:continue
            defects.append({'id':key,'reason':reason})
        warnings=[]
        if kind=='bar' and (lo>0 or hi<0):warnings.append('BAR_ZERO_BASELINE_NOT_VISIBLE')
        if scale=='log':warnings.append('LOG_SCALE_REQUIRES_CLEAR_LABEL')
        return {'data_faithful':not defects,'defects':defects,'presentation_warnings':warnings,
                'profile':'STRUCTURED_DATA_FIDELITY_NOT_RENDER_INSPECTION'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
