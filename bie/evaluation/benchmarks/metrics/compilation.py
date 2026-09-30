"""METRIC-011: actual evaluator-collected compiler exits and emitted artifacts."""
from ..models import BenchmarkError,ident,digest_string,text
from ..domains.structured import record,choice
from .common import indexed,weight
from .delivery_common import integer,unknown,result_unit,observation,used_artifacts
PROFILES={'python':'python-checked-hash-bytecode-v1','typescript':'typescript-strict-emit-v1'}
def measure(reference,candidate,artifacts):
    record(reference,{'targets'});record(candidate,{'artifacts'})
    refs=indexed(reference['targets'],{'id','language','weight'},lower=1)
    actual=indexed(candidate['artifacts'],{'id','observation_id','source_sha256'});unknown(actual,refs)
    units=[];used=[];runs=[]
    for k,r in sorted(refs.items()):
        choice(r['language'],PROFILES);weight(r);reasons=[]
        if k not in actual:reasons=['REQUIRED_COMPILE_TARGET_MISSING']
        else:
            a=actual[k];o=observation(artifacts,a['observation_id'],'compile',a['source_sha256']);used.append(a['observation_id']);runs.append(o['run_id'])
            f=o['facts'];record(f,{'language','command_profile','compiler_version','exit_code','source_bytes','output_bytes','output_sha256','stdout_sha256','stderr_sha256'})
            choice(f['language'],PROFILES);text(f['compiler_version']);integer(f['exit_code'],-255,255);integer(f['source_bytes'],1,200000)
            integer(f['output_bytes'],0,2000000)
            for key in ['output_sha256','stdout_sha256','stderr_sha256']:digest_string(f[key])
            if f['language']!=r['language'] or f['command_profile']!=PROFILES[r['language']]:reasons.append('COMPILER_PROFILE_MISMATCH')
            if f['exit_code']!=0:reasons.append('ACTUAL_COMPILE_FAILED')
            if f['output_bytes']==0:reasons.append('COMPILED_ARTIFACT_MISSING')
        units.append(result_unit(k,reasons,weight(r)))
    if len(set(used))!=len(used):raise BenchmarkError('OBSERVATION_REUSED_FOR_MULTIPLE_TARGETS')
    used_artifacts(artifacts,used)
    return units,[],{'assessment_scope':'LOCAL_COMPILER_EXIT_AND_EMITTED_BYTES','collector_run_ids':sorted(runs),
                     'candidate_runtime_executed':False,'remotion_bundle_verified':False}
