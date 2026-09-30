"""H5-010: admit an existing built static app; never run candidate build commands.
A manifest is byte identity, not CI provenance, a native BIE run or trust grant.
"""
from pathlib import Path
import hashlib,os
from ...adoption.custody import open_root,confined_stream,signature
from ..contracts import path,candidate,BrowserLimits
from ...models import BenchmarkError
from .contracts import LOAD_MODE

def build_candidate(root,*,entrypoint='index.html',limits=BrowserLimits()):
    limits.validate();path(entrypoint);root=Path(root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():raise BenchmarkError('HTTP_IMPORT_ROOT_INVALID')
    # Require each root ancestor to be a real directory, not a symlink alias.
    for parent in (root,*root.parents):
        if parent.is_symlink():raise BenchmarkError('HTTP_IMPORT_ROOT_INVALID')
    rows=[];total=0
    for directory,dirs,files in os.walk(root,followlinks=False):
        for item in sorted(dirs+files):
            p=Path(directory)/item
            if p.is_symlink():raise BenchmarkError('HTTP_IMPORT_SYMLINK')
        for name in sorted(files):
            p=Path(directory)/name;rel=p.relative_to(root).as_posix();path(rel)
            if not p.is_file():raise BenchmarkError('HTTP_IMPORT_SPECIAL_FILE')
            size=p.stat().st_size
            if not 1<=size<=limits.max_file_bytes:raise BenchmarkError('HTTP_IMPORT_FILE_LIMIT')
            total+=size
            if total>limits.max_bundle_bytes or len(rows)>=limits.max_files:raise BenchmarkError('HTTP_IMPORT_BUNDLE_LIMIT')
            # The runtime re-reads descriptor-confined bytes against this digest.
            with open_root(root) as fd,confined_stream(fd,rel) as f:
                before=os.fstat(f.fileno());raw=f.read(limits.max_file_bytes+1);after=os.fstat(f.fileno())
                if signature(before)!=signature(after) or len(raw)!=size or len(raw)>limits.max_file_bytes:
                    raise BenchmarkError('HTTP_IMPORT_FILE_CHANGED')
                sha=hashlib.sha256(raw).hexdigest()
            rows.append({'path':rel,'size_bytes':size,'sha256':sha})
    return candidate({'schema_version':'browser-candidate-1','entrypoint':entrypoint,'files':sorted(rows,key=lambda r:r['path']),
                      'origin_kind':'AUTHORED_FIXTURE','load_mode':LOAD_MODE},limits)
