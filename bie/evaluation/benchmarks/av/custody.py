"""H2-001: bounded frozen file custody and strict operator policy primitives."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import contextmanager
import hashlib, os, stat, tempfile, math
from ..models import BenchmarkError, digest, digest_string, strict_loads

@dataclass(frozen=True)
class Limits:
    max_input_bytes: int = 4 * 1024**3
    max_width: int = 3840
    max_height: int = 2160
    max_duration_s: int = 7200
    max_frames: int = 864000
    max_decoded_bytes: int = 64 * 1024**3
    max_audio_channels: int = 8
    max_audio_rate: int = 96000
    max_metadata_bytes: int = 2_000_000
    max_timing_bytes: int = 128_000_000
    max_stderr_bytes: int = 262144
    deadline_s: float = 900.0
    def __post_init__(self):
        for k,v in asdict(self).items():
            if k == 'deadline_s':
                if type(v) not in (int,float) or not math.isfinite(v) or not 0 < v <= 86400:
                    raise BenchmarkError('INVALID_DEADLINE')
            elif type(v) is not int or not 0 < v <= 2**50:
                raise BenchmarkError('INVALID_RESOURCE_LIMIT')
        if self.max_width > 7680 or self.max_height > 4320 or self.max_audio_channels > 32 or self.max_audio_rate > 192000 or self.max_duration_s > 7200 or self.max_frames > 864000:
            raise BenchmarkError('UNSUPPORTED_RESOURCE_PROFILE')

def regular_path(path, *, allow_missing=False):
    p=Path(path)
    if any(x in ('.','..') for x in os.fspath(path).split('/')) or '\\' in str(p) or ':' in str(p):
        raise BenchmarkError('UNSAFE_ARTIFACT_PATH')
    if any(q.is_symlink() for q in (p,*p.parents)):
        raise BenchmarkError('ARTIFACT_SYMLINK')
    if not p.exists() and allow_missing: return p.absolute()
    if not p.is_file(): raise BenchmarkError('ARTIFACT_NOT_REGULAR')
    return p.absolute()

def sha_file(path, maximum=4*1024**3):
    p=regular_path(path); h=hashlib.sha256(); total=0
    with p.open('rb') as f:
        while b:=f.read(1024*1024):
            total+=len(b)
            if total>maximum: raise BenchmarkError('ARTIFACT_BYTE_LIMIT')
            h.update(b)
    return h.hexdigest(), total

@contextmanager
def frozen_artifact(path, expected_sha256, limits=Limits()):
    """Freeze once and verify pinned content; private directory, no shared inputs.

    Caller must own source parents. The final-component O_NOFOLLOW and stat
    comparison detect common races; this is not a hostile-filesystem sandbox.
    """
    digest_string(expected_sha256); p=regular_path(path)
    with tempfile.TemporaryDirectory(prefix='bie-av-') as td:
        dst=Path(td)/'input.media';h=hashlib.sha256();total=0
        flags=os.O_RDONLY | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_NONBLOCK',0)
        fd=os.open(p,flags)
        try:
            before=os.fstat(fd)
            if not stat.S_ISREG(before.st_mode): raise BenchmarkError('ARTIFACT_NOT_REGULAR')
            if not 0<before.st_size<=limits.max_input_bytes: raise BenchmarkError('ARTIFACT_BYTE_LIMIT')
            with os.fdopen(fd,'rb',closefd=False) as source, dst.open('xb') as out:
                while b:=source.read(1024*1024):
                    total+=len(b)
                    if total>limits.max_input_bytes: raise BenchmarkError('ARTIFACT_BYTE_LIMIT')
                    h.update(b);out.write(b)
                out.flush();os.fsync(out.fileno())
            after=os.fstat(fd)
        finally: os.close(fd)
        if (before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_size,after.st_mtime_ns,after.st_ctime_ns):
            raise BenchmarkError('ARTIFACT_CHANGED_DURING_CAPTURE')
        if total!=before.st_size or h.hexdigest()!=expected_sha256: raise BenchmarkError('ARTIFACT_HASH_MISMATCH')
        dst.chmod(0o400)
        yield dst, {'sha256':h.hexdigest(),'bytes':total}

def read_json(path, maximum=2_000_000):
    p=regular_path(path)
    with p.open('rb') as f: b=f.read(maximum+1)
    if len(b)>maximum: raise BenchmarkError('JSON_BYTE_LIMIT')
    try: return strict_loads(b.decode('utf-8'))
    except UnicodeError as e: raise BenchmarkError('JSON_ENCODING') from e

def exact_fields(value, fields):
    if type(value) is not dict or set(value)!=set(fields): raise BenchmarkError('INVALID_AV_FIELDS')
    return value

def finite(value, lo=0, hi=1e12):
    if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:
        raise BenchmarkError('INVALID_AV_NUMBER')
    return float(value)

def integer(value, lo=0, hi=1_000_000):
    if type(value) is not int or not lo<=value<=hi: raise BenchmarkError('INVALID_AV_INTEGER')
    return value
