"""H4-R1-002: fixed acoustic execution through the unchanged canonical worker."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib
import os
import secrets
import stat
import tempfile
import time
from .common import AudioError, fingerprint, integer, strict_json
from .acoustic_contract import canonical, fields, plain, sha, validate_job
from .acoustic_evidence import validate_measurement
from .acoustic_runtime import verify_runtime
from .kernel_profile import (KERNEL_SCOPE, OPERATION, engine_sources, read_source,
                             validate_profile)

DENIED = ['mount','umount2','pivot_root','chroot','unshare','setns','ptrace',
    'process_vm_readv','process_vm_writev','bpf','keyctl','add_key','request_key',
    'perf_event_open','open_by_handle_at','reboot','kexec_load','init_module',
    'finit_module','delete_module','swapon','swapoff','iopl','ioperm']


def validate_kernel_proof(proof, profile, host_namespaces):
    fields(proof, ('schema_version','kernel_enforced','namespaces','private_procfs',
        'private_network','read_only_workspace_except_declared','capabilities_dropped',
        'no_new_privileges','seccomp_denied_syscalls','resource_limits','launcher_sha256',
        'accepted','process_outcome'), 'KERNEL_PROOF_FIELDS')
    if (proof['schema_version'] != 'bie.linux-worker-proof.v1'
        or proof['kernel_enforced'] is not True or proof['private_procfs'] is not False
        or proof['private_network'] != 'LOOPBACK_ONLY_NO_HOST_ROUTE'
        or proof['read_only_workspace_except_declared'] is not True
        or proof['capabilities_dropped'] is not True or proof['no_new_privileges'] is not True
        or proof['accepted'] is not False or proof['process_outcome'] != 'SUCCEEDED'
        or canonical(proof['resource_limits']) != canonical(profile['worker_policy'])
        or proof['seccomp_denied_syscalls'] != DENIED
        or proof['launcher_sha256'] != profile['canonical_files']['bie/compiler/namespace_launcher.py']['sha256']):
        raise AudioError('KERNEL_PROOF_NOT_ENFORCED')
    fields(host_namespaces, ('net','mnt','pid','user'), 'KERNEL_HOST_NAMESPACE_FIELDS')
    fields(proof['namespaces'], ('net','mnt','pid','user'), 'KERNEL_NAMESPACE_FIELDS')
    import re
    for name in host_namespaces:
        before, after = host_namespaces[name], proof['namespaces'][name]
        pattern = re.escape(name) + r':\[\d+\]'
        if (type(before) is not str or type(after) is not str
            or not re.fullmatch(pattern, before) or not re.fullmatch(pattern, after)
            or before == after):
            raise AudioError('KERNEL_NAMESPACE_NOT_PRIVATE')


def _stage_engine(target, profile):
    paths = engine_sources()
    if set(paths) != set(profile['engine_files']):
        raise AudioError('KERNEL_ENGINE_FILE_SET')
    for relative, source in paths.items():
        data = read_source(source)
        expected = profile['engine_files'][relative]
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise AudioError('KERNEL_ENGINE_CHANGED')
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def _result_bytes(path, maximum):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or not 0 < st.st_size <= maximum:
            raise AudioError('KERNEL_RESULT_PATH_OR_BUDGET')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(maximum + 1)
        if len(data) != st.st_size:
            raise AudioError('KERNEL_RESULT_CHANGED')
        return data
    finally:
        os.close(fd)


def run_kernel(job, wav, runtime, profile, *, cancellation=None, lock_root=None):
    job, runtime, profile = plain(job), plain(runtime), plain(profile)
    policy = validate_job(job, wav)
    validate_profile(profile, runtime)
    if cancellation is not None and cancellation.is_set():
        raise AudioError('KERNEL_CANCELLED')
    from bie.compiler.linux_worker import WorkerPolicy, run_isolated
    from .durable_store import private_root
    root = private_root(lock_root or '/tmp/bie-audio-h4r-worker-slots')
    host_ns = {k: os.readlink('/proc/self/ns/' + k) for k in ('net','mnt','pid','user')}
    nonce = secrets.token_hex(32)
    request = {'operation': OPERATION, 'nonce': nonce, 'job': job, 'runtime': runtime}
    request_bytes = canonical(request)
    if len(request_bytes) > 4_000_000:
        raise AudioError('KERNEL_REQUEST_BUDGET')
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='bie-audio-kernel-') as td:
        work = Path(td)/'work'; engine = Path(td)/'engine'
        work.mkdir(); engine.mkdir(); (work/'output').mkdir()
        _stage_engine(engine, profile)
        (work/'request.json').write_bytes(request_bytes)
        (work/'source.wav').write_bytes(wav)
        process, proof = run_isolated(
            [profile['executables']['python']['path'], '-I', '-B', str(engine/'scripts/audio_kernel_worker.py')],
            workspace=work, engine=engine, writable=('output',),
            policy=WorkerPolicy(**profile['worker_policy']), timeout_s=policy.deadline_seconds,
            cancel_event=cancellation, max_output_bytes=profile['max_output_bytes'], lock_root=root)
        if process.outcome != 'SUCCEEDED' or not process.process.passed or process.process.exit_code != 0:
            raise AudioError('KERNEL_' + process.outcome)
        if cancellation is not None and cancellation.is_set():
            raise AudioError('KERNEL_CANCELLED')
        validate_kernel_proof(proof, profile, host_ns)
        # Fixed-operation debris is bounded and never imported into the host.
        for debris in (work/'output').iterdir():
            if debris.name not in {'result.json','native.log','exact.fsg'}:
                raise AudioError('KERNEL_OUTPUT_FILE_SET')
            _result_bytes(debris, profile['worker_policy']['file_bytes'])
        data = _result_bytes(work/'output/result.json', profile['max_result_bytes'])
        answer = strict_json(data.decode())
        fields(answer, ('operation','nonce','measurement'), 'KERNEL_RESULT_FIELDS')
        if answer['operation'] != OPERATION or answer['nonce'] != nonce:
            raise AudioError('KERNEL_RESULT_REPLAY_OR_OPERATION')
        # Both input hashes and selected code/runtime are checked after execution.
        if (work/'request.json').read_bytes() != request_bytes or (work/'source.wav').read_bytes() != wav:
            raise AudioError('KERNEL_INPUT_MUTATED')
        for relative, expected in profile['engine_files'].items():
            staged = read_source(engine/relative)
            if len(staged) != expected['bytes'] or hashlib.sha256(staged).hexdigest() != expected['sha256']:
                raise AudioError('KERNEL_ENGINE_MUTATED')
    validate_profile(profile, runtime)
    validate_measurement(answer['measurement'], job, runtime['fingerprint'])
    execution = {'schema_version':'bie.audio.kernel-execution/1', 'operation':OPERATION,
        'scope':KERNEL_SCOPE, 'profile_fingerprint':profile['fingerprint'],
        'runtime_fingerprint':runtime['fingerprint'], 'job_fingerprint':job['fingerprint'],
        'media_sha256':hashlib.sha256(wav).hexdigest(), 'nonce':nonce,
        'request_sha256':hashlib.sha256(request_bytes).hexdigest(),
        'result_sha256':hashlib.sha256(data).hexdigest(),
        'measurement_fingerprint':answer['measurement']['fingerprint'],
        'host_namespaces':host_ns, 'kernel_proof':plain(proof),
        'process':{'outcome':process.outcome,'exit_code':process.process.exit_code,
            'started':process.started, 'duration_ms':process.process.duration_ms,
            'stdout_bytes':process.stdout_bytes,'stderr_bytes':process.stderr_bytes},
        'product_accepted':False}
    execution['fingerprint'] = fingerprint(execution)
    return answer['measurement'], execution


def validate_execution(execution, job, runtime, profile, measurement):
    fields(execution, ('schema_version','operation','scope','profile_fingerprint',
        'runtime_fingerprint','job_fingerprint','media_sha256','nonce','request_sha256',
        'result_sha256','measurement_fingerprint','host_namespaces','kernel_proof',
        'process','product_accepted','fingerprint'), 'KERNEL_EXECUTION_FIELDS')
    if (execution['schema_version'] != 'bie.audio.kernel-execution/1'
        or execution['operation'] != OPERATION or execution['scope'] != KERNEL_SCOPE
        or execution['profile_fingerprint'] != profile['fingerprint']
        or execution['runtime_fingerprint'] != runtime['fingerprint']
        or execution['job_fingerprint'] != job['fingerprint']
        or execution['measurement_fingerprint'] != measurement['fingerprint']
        or execution['product_accepted'] is not False):
        raise AudioError('KERNEL_EXECUTION_BINDING')
    for k in ('media_sha256','nonce','request_sha256','result_sha256'):
        sha(execution[k])
    expected_request = {'operation':OPERATION,'nonce':execution['nonce'],'job':job,'runtime':runtime}
    expected_output = {'operation':OPERATION,'nonce':execution['nonce'],'measurement':measurement}
    if (execution['request_sha256'] != hashlib.sha256(canonical(expected_request)).hexdigest()
        or execution['result_sha256'] != hashlib.sha256(canonical(expected_output)).hexdigest()
        or execution['fingerprint'] != fingerprint({k:v for k,v in execution.items() if k != 'fingerprint'})):
        raise AudioError('KERNEL_EXECUTION_HASH')
    p = execution['process']
    fields(p, ('outcome','exit_code','started','duration_ms','stdout_bytes','stderr_bytes'))
    if p['outcome'] != 'SUCCEEDED' or p['exit_code'] != 0 or type(p['exit_code']) is not int or p['started'] is not True:
        raise AudioError('KERNEL_EXECUTION_PROCESS')
    integer(p['duration_ms'],'duration ms',0,400_000)
    for k in ('stdout_bytes','stderr_bytes'):
        integer(p[k],k,0,profile['max_output_bytes'])
    if p['stdout_bytes'] + p['stderr_bytes'] > profile['max_output_bytes']:
        raise AudioError('KERNEL_EXECUTION_OUTPUT_BUDGET')
    validate_kernel_proof(execution['kernel_proof'], profile, execution['host_namespaces'])
