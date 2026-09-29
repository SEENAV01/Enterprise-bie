"""Strict receipt reads and private snapshot-copy checks; no persisted source edits."""
from pathlib import Path
import os,stat,shutil,tempfile
from ..release_v2.contracts import ContractError,canonical_bytes,digest
from ..source_v2.codec import loads
from ..source_v2.io import SnapshotStore

def object_bytes(store,ref,limit):
    if ref.size>limit: raise ContractError('AUDIT_RECEIPT_LIMIT')
    obj=loads(store.read(ref))
    if type(obj) is not dict: raise ContractError('AUDIT_OBJECT_REQUIRED')
    return obj

def fields(obj,expected,code):
    if type(obj) is not dict or set(obj)!=set(expected): raise ContractError(code)

def equal(actual,expected,code):
    # True == 1 is deliberately NOT evidence equality.
    if canonical_bytes(actual)!=canonical_bytes(expected): raise ContractError(code)

def verify_files(root,snapshot,*,exact=False):
    root=Path(root)
    if root.is_symlink() or not root.is_dir(): raise ContractError('AUDIT_SNAPSHOT_ROOT')
    if exact:
        actual=set()
        for directory,dirs,files_ in os.walk(root,followlinks=False):
            for name in dirs+files_:
                p=Path(directory)/name;s=p.lstat()
                if stat.S_ISLNK(s.st_mode): raise ContractError('AUDIT_UNSAFE_ENTRY')
                if stat.S_ISDIR(s.st_mode): continue
                if not stat.S_ISREG(s.st_mode) or s.st_nlink!=1: raise ContractError('AUDIT_UNSAFE_ENTRY')
                actual.add(p.relative_to(root).as_posix())
        if actual!={a.path for a in snapshot.artifacts}: raise ContractError('AUDIT_SNAPSHOT_FILE_SET')
    with SnapshotStore(root) as store:
        for a in snapshot.artifacts: store.read(a)
    return snapshot.content_digest

def copy_snapshot(source,snapshot,parent):
    root=Path(tempfile.mkdtemp(prefix='audit-private-',dir=parent));os.chmod(root,0o700)
    try:
        with SnapshotStore(source) as store:
            for a in snapshot.artifacts:
                data=store.read(a);p=root/a.path;p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as stream:stream.write(data)
        verify_files(root,snapshot,exact=True)
        return root
    except BaseException:
        shutil.rmtree(root,ignore_errors=True);raise

def write_new(path,data):
    path=Path(path)
    if type(data) is not bytes: raise ContractError('AUDIT_OUTPUT_TYPE')
    if not path.parent.is_dir() or path.parent.is_symlink(): raise ContractError('AUDIT_OUTPUT_PARENT')
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    except OSError as exc: raise ContractError('AUDIT_OUTPUT_EXISTS_OR_UNSAFE') from exc
