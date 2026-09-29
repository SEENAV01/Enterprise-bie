"""H7 shared contracts. All outputs are local evidence, never release permission.

Configuration and callbacks are operator-owned. No executable is selected from
untrusted book text. Existing Binding, artifact and review contracts are reused.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib, os, stat, uuid
from ..native_quality_v2.common import Binding, Finding, report, require, fields, items, text
from ..release_v2.contracts import ContractError, canonical_bytes, digest, token, integer, sha256, safe_relative_path, ArtifactRef
from ..publication_v2.contracts import strict_json
from ..lifecycle_quality_v2.common import RepairScope, Change, authorize

SCHEMA = 'bie.qa.operational-quality/1'

def identity(data: bytes) -> str:
    require(type(data) is bytes, 'H7_BYTES_REQUIRED')
    return hashlib.sha256(data).hexdigest()

def object_digest(value):
    return digest(value)

def new_id():
    return uuid.uuid4().hex

def local_report(task, binding, details, errors=()):
    findings = [Finding(str(e), task, 'BLOCKER') for e in sorted(set(errors))]
    findings.append(Finding('OPERATIONAL_CLOSURE_AND_INDEPENDENT_REVIEW_REQUIRED', task))
    return dict(schema_version=SCHEMA, report=report(task,binding,findings,details=details).to_dict(),
                details=details, technical_checks_clear=not errors,
                production_authorized=False, product_accepted=False)

def real_dir(path):
    p=Path(path).absolute()
    require(p.is_dir(), 'H7_ROOT_MISSING')
    for q in (p,)+tuple(p.parents): require(not q.is_symlink(), 'H7_LINKED_ROOT')
    return p

def regular_bytes(root, relative, maximum=64*1024*1024):
    """Read with directory-FD traversal; reject links, devices and concurrent edits."""
    safe_relative_path(relative); root=real_dir(root)
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        parts=relative.split('/')
        for part in parts[:-1]:
            nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=nxt
        f=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
        try:
            before=os.fstat(f)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'H7_UNSAFE_FILE')
            require(before.st_size<=maximum,'H7_FILE_LIMIT')
            chunks=[];total=0
            while True:
                b=os.read(f,min(1024*1024,maximum-total+1))
                if not b:break
                chunks.append(b);total+=len(b)
                require(total<=maximum,'H7_FILE_LIMIT')
            after=os.fstat(f)
            require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                    (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'H7_FILE_CHANGED')
            data=b''.join(chunks);require(len(data)==before.st_size,'H7_SHORT_READ');return data
        finally:os.close(f)
    except OSError as exc:raise ContractError('H7_FILE_ACCESS',relative) from exc
    finally:os.close(fd)

def file_row(root,relative):
    data=regular_bytes(root,relative)
    return dict(path=relative,sha256=identity(data),bytes=len(data))

def inventory(root, *, max_files=20000, max_total=256*1024*1024):
    root=real_dir(root);rows=[];total=0
    for base,dirs,files in os.walk(root,followlinks=False):
        for d in dirs:require(not (Path(base)/d).is_symlink(),'H7_LINKED_DIRECTORY')
        for name in sorted(files):
            path=(Path(base)/name).relative_to(root).as_posix();row=file_row(root,path)
            rows.append(row);total+=row['bytes']
            require(len(rows)<=max_files and total<=max_total,'H7_INVENTORY_LIMIT')
    return sorted(rows,key=lambda r:r['path'])

def copy_verified(source,destination,rows):
    """No hard links or mutable shared inputs. Destination is always newly created."""
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    for row in rows:
        fields(row,('path','sha256','bytes'),'H7_FILE_ROW')
        data=regular_bytes(source,row['path']);require(identity(data)==row['sha256'] and len(data)==row['bytes'],'H7_COPY_CHANGED')
        p=destination/row['path'];p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    require(inventory(destination)==rows,'H7_COPY_INVENTORY')
    return destination

def strict_object(data):
    d=strict_json(data);require(type(d) is dict,'H7_OBJECT_REQUIRED');return d

def check_binding(binding,policy):
    require(type(binding) is Binding and binding.policy_digest==policy.content_digest,'H7_POLICY_BINDING')

def exact_ids(values,code,minimum=1):
    require(type(values) in (tuple,list) and minimum<=len(values)<=20000,code)
    for v in values:token(v,code)
    require(len(set(values))==len(values),code+'_DUPLICATE')
    return tuple(values)


def tool_identity(path,maximum=512*1024*1024):
    """Hash a pinned executable incrementally, without importing or running it.

    Tool binaries can be larger than ordinary report artifacts. Symlinked launch
    names are resolved once, then the resolved regular file is checked through an
    O_NOFOLLOW descriptor; ownership of that tool directory remains an operator
    trust requirement. This is not an atomic anti-administrator execution lock.
    """
    p=Path(path).resolve(strict=True);real_dir(p.parent)
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        a=os.fstat(fd);require(stat.S_ISREG(a.st_mode) and a.st_nlink==1,'H7_UNSAFE_TOOL')
        require(a.st_size<=maximum,'H7_TOOL_LIMIT');h=hashlib.sha256();total=0
        while True:
            b=os.read(fd,1024*1024)
            if not b:break
            total+=len(b);require(total<=maximum,'H7_TOOL_LIMIT');h.update(b)
        z=os.fstat(fd)
        require((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns) and total==a.st_size,'H7_TOOL_CHANGED_DURING_READ')
        return {'sha256':h.hexdigest(),'bytes':total}
    finally:os.close(fd)
