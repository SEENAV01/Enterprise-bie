"""H5-002 isolated invocation; H4 canonical proof validation is reused unchanged."""
from __future__ import annotations
from pathlib import Path
import hashlib
import os
import secrets
import stat
import tempfile
from .common import AudioError, fingerprint, integer, strict_json
from .acoustic_contract import canonical, fields, plain, sha
from .kernel_runtime import validate_kernel_proof
from .kernel_profile import read_source
from .durable_store import private_root
from .pipeline_contract import OPERATION, SCOPE, BOUNDARIES, PipelineLimits, validate_request
from .pipeline_profile import validate_profile,engine_sources
from .pipeline_bundle import NAMES,validate_bundle

RUNTIME_KEYS=('provider_runtime_fingerprint','catalog_fingerprint','meter_runtime_fingerprint','numpy_version')


def read_output(path,limit):
    try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    except OSError as exc:raise AudioError('PIPELINE_OUTPUT_PATH') from exc
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or not 0<st.st_size<=limit:
            raise AudioError('PIPELINE_OUTPUT_TYPE_OR_BUDGET')
        with os.fdopen(fd,'rb',closefd=False) as f:data=f.read(limit+1)
        after=os.fstat(fd)
        if len(data)!=st.st_size or (st.st_size,st.st_ino,st.st_mtime_ns)!=(after.st_size,after.st_ino,after.st_mtime_ns):
            raise AudioError('PIPELINE_OUTPUT_CHANGED')
        return data
    finally:os.close(fd)


def _wrapper(request,profile,nonce):
    return {'operation':OPERATION,'nonce':nonce,'request':request,
        'selected_runtime':{k:profile[k] for k in RUNTIME_KEYS}}


def run_local_pipeline(request,profile,*,cancellation=None,lock_root=None):
    from bie.compiler.linux_worker import WorkerPolicy,run_isolated
    request,profile=plain(request),plain(profile)
    validate_request(request);validate_profile(profile)
    if request['profile_fingerprint']!=profile['fingerprint']:raise AudioError('PIPELINE_PROFILE_BINDING')
    if cancellation is not None and cancellation.is_set():raise AudioError('PIPELINE_CANCELLED')
    limits=PipelineLimits(**request['limits'])
    root=private_root(lock_root or '/tmp/bie-audio-h5-worker-slots')
    nonce=secrets.token_hex(32);wrapper=canonical(_wrapper(request,profile,nonce))
    if len(wrapper)>4_000_000:raise AudioError('PIPELINE_REQUEST_BUDGET')
    host_ns={k:os.readlink('/proc/self/ns/'+k) for k in ('net','mnt','pid','user')}
    with tempfile.TemporaryDirectory(prefix='bie-audio-h5-') as td:
        td=Path(td);engine=td/'engine';work=td/'work';engine.mkdir();work.mkdir();(work/'output').mkdir()
        paths=engine_sources()
        if set(paths)!=set(profile['engine_files']):raise AudioError('PIPELINE_ENGINE_SET')
        for rel,path in paths.items():
            data=read_source(path);expected=profile['engine_files'][rel]
            if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:
                raise AudioError('PIPELINE_ENGINE_CHANGED')
            target=engine/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        (work/'request.json').write_bytes(wrapper)
        process,proof=run_isolated([profile['executables']['python']['path'],'-I','-B',str(engine/'scripts/audio_pipeline_worker.py')],
            workspace=work,engine=engine,writable=('output',),policy=WorkerPolicy(**profile['worker_policy']),
            timeout_s=limits.deadline_seconds,cancel_event=cancellation,max_output_bytes=profile['max_output_bytes'],lock_root=root)
        if process.outcome!='SUCCEEDED' or process.process.exit_code!=0 or not process.process.passed:
            raise AudioError('PIPELINE_'+process.outcome)
        if cancellation is not None and cancellation.is_set():raise AudioError('PIPELINE_CANCELLED')
        validate_kernel_proof(proof,profile,host_ns)
        if {p.name for p in (work/'output').iterdir()}!=NAMES|{'result.json'}:
            raise AudioError('PIPELINE_OUTPUT_FILE_SET')
        files={n:read_output(work/'output'/n,limits.max_file_bytes) for n in sorted(NAMES)}
        data=read_output(work/'output/result.json',1_000_000);answer=strict_json(data.decode())
        expected={'operation':OPERATION,'nonce':nonce,'request_fingerprint':request['fingerprint'],
            'files':validate_bundle(files,request,profile)['index']}
        if answer!=expected:raise AudioError('PIPELINE_RESULT_BINDING')
        if (work/'request.json').read_bytes()!=wrapper:raise AudioError('PIPELINE_INPUT_MUTATED')
        for rel,row in profile['engine_files'].items():
            if hashlib.sha256(read_source(engine/rel)).hexdigest()!=row['sha256']:
                raise AudioError('PIPELINE_STAGED_CODE_MUTATED')
    validate_profile(profile)
    execution={'schema_version':'bie.audio.pipeline-execution/1','operation':OPERATION,'scope':SCOPE,
        'request_fingerprint':request['fingerprint'],'profile_fingerprint':profile['fingerprint'],
        'nonce':nonce,'request_sha256':hashlib.sha256(wrapper).hexdigest(),
        'result_sha256':hashlib.sha256(data).hexdigest(),'files':expected['files'],
        'host_namespaces':host_ns,'kernel_proof':plain(proof),
        'process':{'outcome':process.outcome,'exit_code':process.process.exit_code,'started':process.started,
            'duration_ms':process.process.duration_ms,'stdout_bytes':process.stdout_bytes,'stderr_bytes':process.stderr_bytes},**BOUNDARIES}
    execution['fingerprint']=fingerprint(execution)
    validate_execution(execution,files,request,profile)
    return files,execution


def validate_execution(execution,files,request,profile):
    fields(execution,('schema_version','operation','scope','request_fingerprint','profile_fingerprint',
        'nonce','request_sha256','result_sha256','files','host_namespaces','kernel_proof','process',*BOUNDARIES,'fingerprint'))
    index=validate_bundle(files,request,profile)['index']
    if (execution['schema_version']!='bie.audio.pipeline-execution/1' or execution['operation']!=OPERATION
        or execution['scope']!=SCOPE or execution['request_fingerprint']!=request['fingerprint']
        or execution['profile_fingerprint']!=profile['fingerprint'] or execution['files']!=index
        or any(execution[k] is not v for k,v in BOUNDARIES.items())):
        raise AudioError('PIPELINE_EXECUTION_BINDING')
    for k in ('nonce','request_sha256','result_sha256'):sha(execution[k])
    wrapper=canonical(_wrapper(request,profile,execution['nonce']))
    answer=canonical({'operation':OPERATION,'nonce':execution['nonce'],'request_fingerprint':request['fingerprint'],'files':index})
    if execution['request_sha256']!=hashlib.sha256(wrapper).hexdigest() or execution['result_sha256']!=hashlib.sha256(answer).hexdigest():
        raise AudioError('PIPELINE_EXECUTION_HASH')
    if execution['fingerprint']!=fingerprint({k:v for k,v in execution.items() if k!='fingerprint'}):
        raise AudioError('PIPELINE_EXECUTION_FINGERPRINT')
    p=execution['process'];fields(p,('outcome','exit_code','started','duration_ms','stdout_bytes','stderr_bytes'))
    if p['outcome']!='SUCCEEDED' or type(p['exit_code'])is not int or p['exit_code']!=0 or p['started']is not True:
        raise AudioError('PIPELINE_EXECUTION_PROCESS')
    integer(p['duration_ms'],'duration',0,request['limits']['deadline_seconds']*1000+2000)
    for k in ('stdout_bytes','stderr_bytes'):integer(p[k],k,0,profile['max_output_bytes'])
    validate_kernel_proof(execution['kernel_proof'],profile,execution['host_namespaces'])
    return execution
