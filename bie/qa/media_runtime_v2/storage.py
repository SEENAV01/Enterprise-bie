"""Streaming content-addressed snapshots. No in-memory whole-video read.

POSIX directory-descriptor traversal prevents symlink ancestor races. Temporary
snapshots are private and consumed instead of reopening a mutable source path.
This is not a hostile decoder sandbox or a distributed immutable object store.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib, os, stat, tempfile
from .common import require, integer, token, safe_relative_path, sha256, digest, ContractError

@dataclass(frozen=True)
class StreamArtifact:
    artifact_id: str
    path: str
    sha256: str
    size: int
    role: str = 'video'
    def __post_init__(self):
        token(self.artifact_id, 'artifact'); safe_relative_path(self.path)
        sha256(self.sha256, 'artifact'); integer(self.size, 'size', 1, 16*1024**3)
        require(self.role in ('video','source','support','game'), 'H5_ARTIFACT_ROLE')


def open_confined(root, relative, *, allow_hardlinks=False):
    """Return a read-only regular-file descriptor, forbidding symbolic/hard links."""
    safe_relative_path(relative)
    root = Path(root).absolute()
    require(hasattr(os,'O_NOFOLLOW') and hasattr(os,'O_DIRECTORY'), 'H5_POSIX_REQUIRED')
    fd = os.open('/', os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in root.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd=next_fd
        parts = relative.split('/')
        for part in parts[:-1]:
            next_fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=next_fd
        file_fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        st=os.fstat(file_fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 and not allow_hardlinks:
            os.close(file_fd); raise ContractError('H5_REGULAR_SINGLE_LINK_REQUIRED')
        return file_fd
    except OSError as exc:
        raise ContractError('H5_CONFINED_READ') from exc
    finally: os.close(fd)


def _identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)


@contextmanager
def snapshot(root, ref, *, maximum=2*1024**3, chunk_bytes=1024**2):
    require(type(ref) is StreamArtifact, 'H5_STREAM_REF')
    integer(maximum,'maximum',1,16*1024**3);integer(chunk_bytes,'chunk_bytes',4096,8*1024**2)
    require(ref.size<=maximum, 'H5_INPUT_BUDGET')
    fd=open_confined(root,ref.path)
    try:
        before=os.fstat(fd);require(before.st_size==ref.size,'H5_INPUT_SIZE')
        with tempfile.TemporaryDirectory(prefix='bie-h5-snapshot-') as td:
            dest=Path(td)/'payload';total=0;hasher=hashlib.sha256();chunks=[]
            with dest.open('xb') as out:
                while True:
                    data=os.read(fd,chunk_bytes)
                    if not data:break
                    require(total+len(data)<=ref.size,'H5_INPUT_GROWTH')
                    out.write(data);hasher.update(data)
                    chunks.append({'offset':total,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
                    total+=len(data)
                out.flush();os.fsync(out.fileno())
            require(_identity(before)==_identity(os.fstat(fd)),'H5_INPUT_CHANGED_DURING_COPY')
            require(total==ref.size and hasher.hexdigest()==ref.sha256,'H5_INPUT_HASH')
            os.chmod(dest,0o400)
            receipt={'artifact':asdict(ref),'chunk_bytes':chunk_bytes,'chunks':chunks,
                     'whole_sha256':hasher.hexdigest(),'bytes':total}
            receipt['inventory_digest']=digest(receipt)
            yield dest,receipt
    finally:os.close(fd)


def hash_file(path, *, max_bytes=16*1024**3):
    p=Path(path);fd=open_confined(p.parent,p.name)
    try:
        before=os.fstat(fd);require(0<before.st_size<=max_bytes,'H5_HASH_SIZE')
        h=hashlib.sha256();n=0
        while b:=os.read(fd,1024**2):h.update(b);n+=len(b)
        require(_identity(before)==_identity(os.fstat(fd)) and n==before.st_size,'H5_HASH_MUTATION')
        return h.hexdigest(),n
    finally:os.close(fd)


def verify_chunk_manifest(receipt):
    base={k:v for k,v in receipt.items() if k!='inventory_digest'}
    require(receipt.get('inventory_digest')==digest(base),'H5_CHUNK_MANIFEST_DIGEST')
    ref=StreamArtifact(**receipt['artifact']);integer(receipt['chunk_bytes'],'chunk',4096,8*1024**2)
    require(receipt['whole_sha256']==ref.sha256 and receipt['bytes']==ref.size,'H5_CHUNK_WHOLE_BINDING')
    offset=0
    require(type(receipt['chunks']) is list and receipt['chunks'],'H5_CHUNKS_EMPTY')
    for i,row in enumerate(receipt['chunks']):
        require(set(row)=={'offset','bytes','sha256'} and row['offset']==offset,'H5_CHUNK_COVERAGE')
        integer(row['bytes'],'chunk_bytes',1,receipt['chunk_bytes']);sha256(row['sha256'],'chunk_hash')
        if i<len(receipt['chunks'])-1:require(row['bytes']==receipt['chunk_bytes'],'H5_SHORT_INTERIOR_CHUNK')
        offset+=row['bytes']
    require(offset==ref.size,'H5_CHUNK_COVERAGE')
    return True


def import_native_output(root, ref, destination, *, allow_linked_native_output=False):
    """Copy a native hard-linked publication into a new independent snapshot file.

    The canonical compiler publishes with a hard link. Ordinary reads still reject
    aliases. This explicit operator import verifies the exact expected bytes and
    stable inode, then exclusively publishes a one-link copy; no originals change.
    Destination is an operator-owned directory, not a hostile concurrent filesystem.
    """
    require(allow_linked_native_output is True,'H5_NATIVE_LINK_IMPORT_OPT_IN')
    require(type(ref)is StreamArtifact,'H5_STREAM_REF')
    dest=Path(destination);require(dest.parent.is_dir() and not dest.parent.is_symlink() and not dest.exists() and not dest.is_symlink(),'H5_IMPORT_DESTINATION')
    fd=open_confined(root,ref.path,allow_hardlinks=True);temporary=None
    try:
        before=os.fstat(fd);require(before.st_size==ref.size,'H5_INPUT_SIZE')
        tmpfd,name=tempfile.mkstemp(prefix='.bie-h5-import-',dir=dest.parent);temporary=Path(name);h=hashlib.sha256();size=0
        with os.fdopen(tmpfd,'wb') as out:
            while data:=os.read(fd,1024**2):
                size+=len(data);require(size<=ref.size,'H5_INPUT_GROWTH');out.write(data);h.update(data)
            out.flush();os.fsync(out.fileno())
        require(_identity(before)==_identity(os.fstat(fd)),'H5_INPUT_CHANGED_DURING_COPY')
        require(size==ref.size and h.hexdigest()==ref.sha256,'H5_NATIVE_IMPORT_HASH')
        os.chmod(temporary,0o400);os.link(temporary,dest,follow_symlinks=False);temporary.unlink();temporary=None
        imported=StreamArtifact(ref.artifact_id,dest.name,ref.sha256,ref.size,ref.role)
        require(hash_file(dest)==(ref.sha256,ref.size),'H5_NATIVE_IMPORTED_IDENTITY')
        return {'original':asdict(ref),'original_link_count':before.st_nlink,'imported':asdict(imported),'original_mutated':False,'native_origin_authenticated':False}
    finally:
        os.close(fd)
        if temporary is not None:temporary.unlink(missing_ok=True)
