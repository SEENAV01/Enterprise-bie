"""H3-002: POSIX descriptor-walk confinement and immutable bundle snapshots.

Requires operator-owned root/parents. Does not claim OS namespace isolation.
No Windows fallback pretends to provide POSIX no-follow guarantees.
"""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import hashlib,os,stat,tempfile
from ..models import BenchmarkError,digest,digest_string,strict_loads
from .contracts import relative_path,artifact

@contextmanager
def open_root(root):
    if os.name!='posix' or not hasattr(os,'O_NOFOLLOW'):raise BenchmarkError('POSIX_CUSTODY_REQUIRED')
    p=Path(root).absolute()
    if any(q.is_symlink() for q in (p,*p.parents)) or not p.is_dir():raise BenchmarkError('ADOPTION_ROOT_UNSAFE')
    fds=[]
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY);fds.append(fd)
        for part in p.parts[1:]:
            if part in ('.','..'):raise BenchmarkError('ADOPTION_ROOT_UNSAFE')
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd)
        yield fd
    except OSError as exc:raise BenchmarkError('ADOPTION_ROOT_UNAVAILABLE') from exc
    finally:
        for fd in reversed(fds):os.close(fd)

@contextmanager
def confined_stream(root_fd,relative):
    parts=relative_path(relative).split('/');fds=[]
    try:
        fd=root_fd
        for part in parts[:-1]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd)
        fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        with os.fdopen(fd,'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):raise BenchmarkError('ADOPTION_NOT_REGULAR')
            yield stream
    except OSError as exc:raise BenchmarkError('ADOPTION_FILE_UNAVAILABLE') from exc
    finally:
        for fd in reversed(fds):os.close(fd)

def signature(st):return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def capture(root_fd,row,*,maximum,destination=None,allow_empty=False):
    relative_path(row['path']);digest_string(row['sha256'])
    if type(row['size_bytes']) is not int or not (0 if allow_empty else 1)<=row['size_bytes']<=maximum:
        raise BenchmarkError('ADOPTION_BYTE_LIMIT')
    h=hashlib.sha256();size=0
    with confined_stream(root_fd,row['path']) as stream:
        before=os.fstat(stream.fileno())
        if before.st_size!=row['size_bytes']:raise BenchmarkError('ADOPTION_SIZE_MISMATCH')
        while block:=stream.read(min(1024*1024,maximum+1-size)):
            size+=len(block)
            if size>maximum:raise BenchmarkError('ADOPTION_BYTE_LIMIT')
            h.update(block)
            if destination is not None:destination.write(block)
        after=os.fstat(stream.fileno())
    if signature(before)!=signature(after) or size!=before.st_size:raise BenchmarkError('ADOPTION_FILE_CHANGED')
    if h.hexdigest()!=row['sha256']:raise BenchmarkError('ADOPTION_HASH_MISMATCH')
    # Compare with a new confined open, detecting replacement during capture.
    with confined_stream(root_fd,row['path']) as stream:
        if signature(os.fstat(stream.fileno()))!=signature(after):raise BenchmarkError('ADOPTION_FILE_REPLACED')
    return {'path':row['path'],'sha256':h.hexdigest(),'size_bytes':size}

@contextmanager
def frozen_bundle(root,candidate,limits):
    with open_root(root) as fd,tempfile.TemporaryDirectory(prefix='bie-av-adopt-') as temp:
        files={};inventory={}
        for key,maximum in (('media',limits.max_input_bytes),('captions',1_000_000)):
            row=candidate[key]
            if row is None:files[key]=None;continue
            path=Path(temp)/('media.bin' if key=='media' else 'captions.txt')
            with path.open('xb') as out:
                inventory[key]=capture(fd,row,maximum=maximum,destination=out)
                out.flush();os.fsync(out.fileno())
            path.chmod(0o400);files[key]=path
        yield files,{'files':inventory,'inventory_sha256':digest(inventory),'custody':'POSIX_CONFINED_PRIVATE_COPY'}

def read_confined_json(root,relative,maximum=2_000_000):
    with open_root(root) as fd,confined_stream(fd,relative) as stream:
        before=os.fstat(stream.fileno());raw=stream.read(maximum+1);after=os.fstat(stream.fileno())
    if len(raw)>maximum:raise BenchmarkError('ADOPTION_JSON_LIMIT')
    if signature(before)!=signature(after):raise BenchmarkError('ADOPTION_FILE_CHANGED')
    try:return strict_loads(raw.decode('utf-8')),hashlib.sha256(raw).hexdigest(),len(raw)
    except UnicodeError as exc:raise BenchmarkError('ADOPTION_JSON_ENCODING') from exc
