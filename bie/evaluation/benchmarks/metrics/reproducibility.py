"""METRIC-016: exact output-byte equality across separately captured workspaces.
Input/recipe/environment/seed bindings and full output rosters cannot be omitted.
"""
from ..models import BenchmarkError,digest,digest_string
from ..domains.structured import record,sequence
from .common import ids,indexed,weight
from .collectors import safe_relative
from .delivery_common import integer,observation,used_artifacts,result_unit

def measure(reference,candidate,artifacts):
    record(reference,{'outputs','inputs_sha256','recipe_sha256','environment_sha256','seed','minimum_runs'})
    record(candidate,{'observation_ids'})
    refs=indexed(reference['outputs'],{'id','path','weight'},lower=1)
    paths=set()
    for r in refs.values():
        p=safe_relative(r['path']);weight(r)
        if p.casefold() in paths:raise BenchmarkError('DUPLICATE_REFERENCE_OUTPUT_PATH')
        paths.add(p.casefold())
    for k in ['inputs_sha256','recipe_sha256','environment_sha256']:digest_string(reference[k])
    seed=integer(reference['seed'],0,2**32-1);minimum=integer(reference['minimum_runs'],2,8)
    keys=ids(candidate['observation_ids']);used_artifacts(artifacts,keys)
    runs=[];workspaces=set();run_ids=set();global_reasons=[]
    if len(keys)<minimum:global_reasons.append('INSUFFICIENT_INDEPENDENT_RUNS')
    if len(keys)>8:raise BenchmarkError('REPRODUCIBILITY_RUN_LIMIT')
    expected={r['path'] for r in refs.values()}
    for key in keys:
        o=observation(artifacts,key,'output-snapshot');f=o['facts']
        record(f,{'workspace_sha256','inputs_sha256','recipe_sha256','environment_sha256','seed','outputs'})
        integer(f['seed'],0,2**32-1)
        for k in ['workspace_sha256','inputs_sha256','recipe_sha256','environment_sha256']:digest_string(f[k])
        if o['run_id'] in run_ids or f['workspace_sha256'] in workspaces:raise BenchmarkError('REPRODUCIBILITY_RUN_REUSED')
        run_ids.add(o['run_id']);workspaces.add(f['workspace_sha256'])
        if any(f[k]!=reference[k] for k in ['inputs_sha256','recipe_sha256','environment_sha256','seed']):global_reasons.append('REPRODUCIBILITY_CONTEXT_CHANGED')
        outputs={};case=set()
        for row in sequence(f['outputs'],upper=128):
            record(row,{'path','sha256','bytes'});p=safe_relative(row['path']);digest_string(row['sha256']);integer(row['bytes'],0,50000000)
            if p.casefold() in case:raise BenchmarkError('DUPLICATE_CAPTURED_OUTPUT_PATH')
            case.add(p.casefold());outputs[p]=row
        if digest(f['outputs'])!=o['subject_sha256']:raise BenchmarkError('OUTPUT_MANIFEST_SUBJECT_MISMATCH')
        if set(outputs)!=expected:global_reasons.append('REPRODUCIBILITY_OUTPUT_ROSTER_MISMATCH')
        runs.append(outputs)
    units=[];diffs={}
    for k,r in sorted(refs.items()):
        why=list(global_reasons);path=r['path'];values=[]
        for output in runs:
            if path not in output:why.append('REPRODUCIBILITY_OUTPUT_MISSING')
            else:values.append((output[path]['sha256'],output[path]['bytes']))
        if len(set(values))>1:why.append('OUTPUT_BYTES_NOT_REPRODUCIBLE')
        diffs[path]=[{'sha256':s,'bytes':n} for s,n in values]
        units.append(result_unit(k,why,weight(r)))
    return units,[],{'assessment_scope':'EXACT_BYTES_WITH_FIXED_CONTEXT','run_count':len(runs),'observed_outputs':diffs,
                     'build_execution_proven_by_hashing_alone':False,'cross_platform_reproducibility_certified':False}
