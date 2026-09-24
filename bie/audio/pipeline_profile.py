"""H5-001: selected source/tool identities and explicit Linux worker profile.

Discovery does not authorize execution. These are selected runtime identities,
not whole-host attestation. Existing canonical worker modules stay unchanged.
"""
from __future__ import annotations
import ast
from dataclasses import asdict
import hashlib
import importlib
from pathlib import Path
import platform
import shutil
import sys
import os
import tempfile
from functools import lru_cache
from .common import AudioError, fingerprint, integer
from .acoustic_contract import canonical, plain
from .kernel_profile import canonical_identity, read_source, ROOT
from .pipeline_contract import OPERATION, SCOPE, BOUNDARIES


def engine_sources():
    # Resolve a closed, code-selected set of BIE imports. Never import data-specified code.
    pending=['bie.audio.pipeline_worker','bie.audio.pipeline_contract','scripts.audio_prepare',
        'bie.audio.pipeline_discovery','scripts.audio_pipeline_discover',
        # Canonical APIs named by durable_contract.canonical_api_identity at runtime.
        'bie.infrastructure.artifact_store','bie.infrastructure.idempotency_store',
        'bie.director.director_durable_recovery','bie.director.director_artifacts',
        'bie.bie_core.artifact_contracts']
    found={}
    while pending:
        name=pending.pop()
        if name in found or not (name.startswith('bie.') or name.startswith('scripts.')):continue
        spec=importlib.util.find_spec(name)
        if spec is None or not spec.origin:continue
        path=Path(spec.origin)
        found[name]=path
        package=name.rsplit('.',1)[0]
        for node in ast.walk(ast.parse(read_source(path))):
            if isinstance(node,ast.ImportFrom):
                if node.level:
                    parts=package.split('.')
                    prefix='.'.join(parts[:len(parts)-node.level+1])
                    target=prefix+('.'+node.module if node.module else '')
                else:target=node.module or ''
                if target.startswith(('bie.','scripts.')):pending.append(target)
            elif isinstance(node,ast.Import):
                pending.extend(x.name for x in node.names if x.name.startswith(('bie.','scripts.')))
    # Native child selected by a path, not a Python import.
    found['bie.audio.espeak_timing_worker']=ROOT/'bie/audio/espeak_timing_worker.py'
    found['scripts.audio_pipeline_worker']=ROOT/'scripts/audio_pipeline_worker.py'
    found['bie.audio.__init__']=ROOT/'bie/audio/__init__.py'
    found['bie.audio.compat204.__init__']=ROOT/'bie/audio/compat204/__init__.py'
    return {name.replace('.','/')+'.py':path for name,path in sorted(found.items())}


def file_identity(path):
    path=Path(path).resolve(strict=True)
    if not path.is_file():raise AudioError('PIPELINE_RUNTIME_FILE')
    h=hashlib.sha256()
    before=path.stat()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise AudioError('PIPELINE_RUNTIME_CHANGED')
    return {'path':str(path),'bytes':after.st_size,'sha256':h.hexdigest()}


def identities(paths):
    return {n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
        for n,p in sorted(paths.items()) for b in (read_source(p),)}


def probe_profile(*, concurrent_jobs=2):
    if sys.platform!='linux':raise AudioError('PIPELINE_LINUX_REQUIRED')
    integer(concurrent_jobs,'concurrent jobs',1,8)
    if not shutil.which('unshare') or Path(shutil.which('unshare')).resolve()!=Path('/usr/bin/unshare').resolve():
        raise AudioError('PIPELINE_LAUNCHER_PATH')
    from bie.compiler.linux_worker import WorkerPolicy
    from .timed_espeak_provider import TimedEspeakProvider
    from .mix_meter import FFmpegMeter
    import numpy as np
    provider=TimedEspeakProvider('/usr/bin/espeak')
    meter=FFmpegMeter('/usr/bin/ffmpeg')
    policy=WorkerPolicy(procfs=False,concurrent_jobs=concurrent_jobs,cpu_seconds=300,
        address_space_bytes=2*1024**3,file_bytes=64_000_000,descriptors=128,
        processes=64,tmpfs_bytes=256*1024**2)
    runtime_files={n:file_identity(p) for n,p in (
        ('python',sys.executable),('unshare','/usr/bin/unshare'),('espeak','/usr/bin/espeak'),
        ('ffmpeg','/usr/bin/ffmpeg'),('numpy_init',np.__file__),
        ('numpy_core',importlib.import_module('numpy._core._multiarray_umath').__file__))}
    host_identity={'provider_runtime_fingerprint':provider.runtime,'catalog_fingerprint':provider.catalog().fingerprint(),
        'meter_runtime_fingerprint':meter.runtime_fingerprint,'numpy_version':np.__version__}
    chosen=_discover(canonical({'host':host_identity,'executables':runtime_files,
        'engine':identities(engine_sources()),'canonical':canonical_identity(),'worker_policy':asdict(policy)}).decode())
    value={'schema_version':'bie.audio.pipeline-profile/1','operation':OPERATION,'scope':SCOPE,
        'canonical_files':canonical_identity(),'engine_files':identities(engine_sources()),
        'adapter_files':identities({'bie/audio/'+p.name:p for p in (ROOT/'bie/audio').glob('pipeline_*.py')}),
        'executables':runtime_files,'worker_policy':asdict(policy),
        'host_discovery_identity':host_identity,**chosen,
        'discovery_scope':'ACTUAL_CANONICAL_NAMESPACE_CATALOG_PROBE_NO_SYNTHESIS',
        'max_output_bytes':1_000_000,'kernel_release':platform.release(),'machine':platform.machine(),
        'authority':'SELECTED_IDENTITIES_NOT_WHOLE_HOST_ATTESTATION',**BOUNDARIES}
    value['fingerprint']=fingerprint(value)
    return value


def validate_profile(profile):
    if type(profile)is not dict or type(profile.get('worker_policy'))is not dict:
        raise AudioError('PIPELINE_PROFILE_FIELDS')
    current=probe_profile(concurrent_jobs=profile['worker_policy'].get('concurrent_jobs'))
    if canonical(current)!=canonical(profile):raise AudioError('PIPELINE_PROFILE_DRIFT')
    return plain(current)


@lru_cache(maxsize=8)
def _discover(identity_json):
    """Cache discovery only under freshly rehashed host/code identities.

    Host and namespace paths can differ for identical shared-library bytes.
    Discover the unchanged provider's actual namespace identity, do not normalize
    away meaningful identity fields or substitute the host catalog.
    """
    from .common import strict_json
    from .kernel_runtime import validate_kernel_proof
    from .tts_cache import read_regular
    from bie.compiler.linux_worker import WorkerPolicy,run_isolated
    descriptor=strict_json(identity_json)
    host_ns={k:os.readlink('/proc/self/ns/'+k) for k in ('net','mnt','pid','user')}
    with tempfile.TemporaryDirectory(prefix='audio-profile-discovery-') as td:
        td=Path(td);work=td/'work';engine=td/'engine';work.mkdir();engine.mkdir();(work/'output').mkdir()
        for n,p in engine_sources().items():
            b=read_source(p)
            if {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}!=descriptor['engine'][n]:
                raise AudioError('PIPELINE_DISCOVERY_CODE_CHANGED')
            target=engine/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
        process,proof=run_isolated([descriptor['executables']['python']['path'],'-I','-B',str(engine/'scripts/audio_pipeline_discover.py')],
            workspace=work,engine=engine,writable=('output',),policy=WorkerPolicy(**descriptor['worker_policy']),
            timeout_s=30,max_output_bytes=100_000,lock_root=td/'slots')
        if process.outcome!='SUCCEEDED' or process.process.exit_code!=0:raise AudioError('PIPELINE_DISCOVERY_FAILED')
        validate_kernel_proof(proof,{'worker_policy':descriptor['worker_policy'],'canonical_files':descriptor['canonical']},host_ns)
        if {p.name for p in (work/'output').iterdir()}!={'discovery.json'}:raise AudioError('PIPELINE_DISCOVERY_OUTPUT')
        result=strict_json(read_regular(work/'output/discovery.json',10_000).decode())
    from .acoustic_contract import fields
    from .common import digest
    fields(result,('provider_runtime_fingerprint','catalog_fingerprint','meter_runtime_fingerprint','numpy_version'))
    for k in ('provider_runtime_fingerprint','catalog_fingerprint','meter_runtime_fingerprint'):digest(result[k])
    if result['numpy_version']!=descriptor['host']['numpy_version'] or result['meter_runtime_fingerprint']!=descriptor['host']['meter_runtime_fingerprint']:
        raise AudioError('PIPELINE_DISCOVERY_RUNTIME_CHANGED')
    return result
