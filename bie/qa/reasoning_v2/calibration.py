"""Recompute finite held-out calibration diagnostics from verified artifact bytes.

These are descriptive sample metrics, not statistical guarantees or independent
proof of dataset correctness, nonleakage or future model performance.
"""
from __future__ import annotations
from dataclasses import dataclass
from ..release_v2.contracts import ContractError,integer,token,sha256
from ..source_v2.codec import loads
from ...reasoning.calibration_diagnostics import CalibrationSample,calibration_report
from .models import CalibrationArtifact

@dataclass(frozen=True, slots=True)
class CalibrationMetrics:
    samples: int
    ece_ppm: int
    brier_ppm: int
    bins: tuple[tuple[int,int,int,int],...]
    dataset_id: str
    canonical_ece_ppm: int
    canonical_brier_ppm: int


def inspect_calibration(payload:bytes,artifact:CalibrationArtifact,excluded_hashes:tuple[str,...]):
    if type(artifact) is not CalibrationArtifact:raise ContractError('INVALID_CALIBRATION_ARTIFACT')
    data=loads(payload)
    expected={'schema_version','calibration_id','model_id','model_version','domain','language','issued_at','dataset_id','split','source_hashes','samples'}
    if type(data) is not dict or set(data)!=expected:raise ContractError('CALIBRATION_FIELDS_MISMATCH')
    if data['schema_version']!='1.0.0' or data['split']!='heldout':raise ContractError('CALIBRATION_NOT_HELDOUT')
    for f in ('calibration_id','model_id','model_version','domain','language','issued_at'):
        if type(data[f]) is not type(getattr(artifact,f)) or data[f]!=getattr(artifact,f):raise ContractError('CALIBRATION_BINDING_MISMATCH',f)
    token(data['dataset_id'],'dataset_id')
    hashes=data['source_hashes']
    if type(hashes) is not list or not 1<=len(hashes)<=10000:raise ContractError('CALIBRATION_SOURCE_INVENTORY')
    for h in hashes:sha256(h,'calibration.source_hash')
    if len(set(hashes))!=len(hashes):raise ContractError('DUPLICATE_CALIBRATION_SOURCE')
    if set(hashes)&set(excluded_hashes):raise ContractError('CALIBRATION_CANDIDATE_LEAKAGE')
    rows=data['samples']
    if type(rows) is not list or not 1<=len(rows)<=10000:raise ContractError('CALIBRATION_SAMPLE_LIMIT')
    ids=set();groups=set();counts=[0]*10;pred=[0]*10;correct=[0]*10;errors=0;samples=[]
    for r in rows:
        if type(r) is not dict or set(r)!={'sample_id','group_id','confidence_ppm','correct'}:raise ContractError('CALIBRATION_SAMPLE_FIELDS')
        token(r['sample_id'],'sample_id');token(r['group_id'],'group_id')
        if r['sample_id'] in ids or r['group_id'] in groups:raise ContractError('DUPLICATE_CALIBRATION_SAMPLE_OR_GROUP')
        ids.add(r['sample_id']);groups.add(r['group_id'])
        p=integer(r['confidence_ppm'],'sample.confidence_ppm',0,1000000)
        if type(r['correct']) is not bool:raise ContractError('NONBOOLEAN_CALIBRATION_LABEL')
        y=int(r['correct']);b=min(p//100000,9);counts[b]+=1;pred[b]+=p;correct[b]+=y;errors+=(p-y*1000000)**2
        samples.append(CalibrationSample(p/1000000,r['correct'],r['sample_id']))
    n=len(rows)
    # Ceiling rounding for error metrics: rounding cannot pass a failing floor.
    ece=(sum(abs(pred[b]-correct[b]*1000000) for b in range(10))+n-1)//n
    brier=(errors+n*1000000-1)//(n*1000000)
    canonical=calibration_report(tuple(samples),bin_count=10,calibration_version='qa16-bound-diagnostics-v1')
    bins=tuple((b,counts[b],pred[b],correct[b]) for b in range(10) if counts[b])
    return CalibrationMetrics(n,ece,brier,bins,data['dataset_id'],round(canonical.ece*1000000),round(canonical.brier_score*1000000))
