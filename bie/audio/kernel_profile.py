"""H4-R1-001: approved, content-bound profile for the existing BIE Linux worker.

Profile discovery is not approval. Only out-of-band kernel trust authorizes it.
The eight canonical modules are pinned, not a replacement worker or orchestrator.
"""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
import hashlib
import importlib
import os
import platform
import sys
from .common import AudioError, fingerprint, integer
from .acoustic_contract import BOUNDARIES, canonical, fields, plain
from .acoustic_runtime import verify_runtime, file_record

COMMIT = '16d4d87824e77db3565a231a332e7977d39d7117'
OPERATION = 'AUDIO_ACOUSTIC_DIAGNOSTIC_V1'
PROFILE_SCHEMA = 'bie.audio.kernel-profile/1'
KERNEL_SCOPE = 'CANONICAL_LINUX_ISOLATED_ACOUSTIC_DIAGNOSTIC'
PINNED_BLOBS = {
    'artifact_hashing': '50303c4228dc0d5388928f0240206000f44f45d8',
    'build_common': '574b1a26dc3a3eb6dbd6a58eb8b70f721e72b305',
    'host_toolchain': '9c113ec948a9324cf76032f2de937a6ae27e8cf5',
    'linux_worker': 'c73f537dc0945bb691d40b75a68d7dafa55928ab',
    'namespace_launcher': 'c2c7fd2a52682aca5af8cc1e333d8402e80cf32c',
    'qa_common': '94f6ac7c55d5ba4752c65fc0c1e0dbb27d91a6be',
    'render_logs': 'd92d279094d9aedd34792525875c1f3d11710165',
    'render_process': 'b140256eb6eb62cfc4d18dc7142911a5d356020d',
}
ROOT = Path(__file__).resolve().parents[2]


def read_source(path: Path) -> bytes:
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise AudioError('KERNEL_SOURCE_PATH')
    before = path.stat()
    if not 0 < before.st_size <= 2_000_000:
        raise AudioError('KERNEL_SOURCE_BUDGET')
    data = path.read_bytes()
    after = path.stat()
    sig = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if sig(before) != sig(after) or len(data) != before.st_size:
        raise AudioError('KERNEL_SOURCE_CHANGED')
    return data


def canonical_identity() -> dict:
    worker = importlib.import_module('bie.compiler.linux_worker')
    folder = Path(worker.__file__).absolute().parent
    out = {}
    for name, expected in sorted(PINNED_BLOBS.items()):
        path = folder / (name + '.py')
        data = read_source(path)
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != expected:
            raise AudioError('KERNEL_CANONICAL_DEPENDENCY_DRIFT', name)
        if name != 'namespace_launcher':
            loaded = importlib.import_module('bie.compiler.' + name)
            if Path(loaded.__file__).absolute() != path:
                raise AudioError('KERNEL_CANONICAL_MODULE_SHADOW', name)
        out['bie/compiler/' + name + '.py'] = {
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'git_blob': blob}
    return out


def engine_sources() -> dict[str, Path]:
    """Only measurement code is mounted. No signer/store/tests/source repository."""
    folder = Path(__file__).parent
    paths = {('bie/audio/' + p.name): p for p in folder.glob('acoustic_*.py')}
    for name in ('__init__.py', 'common.py', 'kernel_entry.py'):
        paths['bie/audio/' + name] = folder / name
    paths['scripts/audio_acoustic_worker.py'] = ROOT / 'scripts/audio_acoustic_worker.py'
    paths['scripts/audio_kernel_worker.py'] = ROOT / 'scripts/audio_kernel_worker.py'
    timing = importlib.import_module('bie.director.timing_contract')
    paths['bie/director/timing_contract.py'] = Path(timing.__file__).absolute()
    return paths


def _identities(paths: dict[str, Path]) -> dict:
    out = {}
    for name, path in sorted(paths.items()):
        data = read_source(path)
        out[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return out


def probe_profile(runtime: dict, *, concurrent_jobs: int = 2) -> dict:
    """Collect selected identities; the caller must approve separately."""
    verify_runtime(runtime)
    integer(concurrent_jobs, 'concurrent jobs', 1, 8)
    if sys.platform != 'linux':
        raise AudioError('KERNEL_LINUX_REQUIRED')
    from bie.compiler.linux_worker import WorkerPolicy
    # A deliberately narrow no-proc measurement profile; wall time comes from job.
    policy = WorkerPolicy(procfs=False, concurrent_jobs=concurrent_jobs, cpu_seconds=300,
        address_space_bytes=768*1024**2, file_bytes=8_000_000,
        descriptors=128, processes=64, tmpfs_bytes=128*1024**2)
    selected = {}
    for role, path in (('python', Path(sys.executable).resolve()),
                       ('unshare', Path('/usr/bin/unshare').resolve())):
        selected[role] = file_record(path)
    # Runtime paths must be available at the same paths inside canonical mounts.
    for row in runtime['files'].values():
        if not Path(row['path']).is_relative_to('/usr'):
            raise AudioError('KERNEL_RUNTIME_OUTSIDE_SYSTEM_MOUNT')
    host_paths = {'bie/audio/' + p.name: p for p in Path(__file__).parent.glob('kernel_*.py')}
    value = {'schema_version': PROFILE_SCHEMA, 'operation': OPERATION,
        'scope': KERNEL_SCOPE, 'canonical_commit': COMMIT,
        'canonical_files': canonical_identity(), 'engine_files': _identities(engine_sources()),
        'adapter_files': _identities(host_paths), 'executables': selected,
        'runtime_fingerprint': runtime['fingerprint'], 'worker_policy': asdict(policy),
        'max_result_bytes': 4_000_000, 'max_output_bytes': 1_000_000,
        'kernel_release': platform.release(), 'machine': platform.machine(),
        'authority': 'SELECTED_CODE_AND_RUNTIME_IDENTITIES_NOT_WHOLE_HOST_ATTESTATION',
        **BOUNDARIES}
    value['fingerprint'] = fingerprint(value)
    return value


def validate_profile(profile: dict, runtime: dict) -> dict:
    if type(profile) is not dict or type(profile.get('worker_policy')) is not dict:
        raise AudioError('KERNEL_PROFILE_FIELDS')
    current = probe_profile(runtime, concurrent_jobs=profile['worker_policy'].get('concurrent_jobs'))
    if canonical(profile) != canonical(current):
        raise AudioError('KERNEL_PROFILE_DRIFT')
    return plain(current)
