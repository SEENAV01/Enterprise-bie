"""H5-005 exclusive interoperable MIX export with external trust verification."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from .common import AudioError,strict_json
from .acoustic_contract import canonical,plain
from .durable_store import private_root
from .tts_cache import key_lock
from .pipeline_bundle import NAMES
from .pipeline_runtime import read_output
from .pipeline_evidence import verify_receipt

EXTRA=frozenset({'PIPELINE_REQUEST.json','PIPELINE_PROFILE.json','EXECUTION_RECEIPT.json'})


def read_json(path,limit=4_000_000):
    return strict_json(read_output(Path(path),limit).decode('utf-8'))


def read_private_key(path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    import stat
    p=Path(path).absolute()
    if any(x.is_symlink() for x in (p,*p.parents)):raise AudioError('PIPELINE_KEY_SYMLINK')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077 or st.st_nlink!=1 or st.st_size!=32:
            raise AudioError('PIPELINE_KEY_FILE_POLICY')
        data=os.read(fd,33)
        if len(data)!=32:raise AudioError('PIPELINE_KEY_FILE_SIZE')
        return Ed25519PrivateKey.from_private_bytes(data)
    finally:os.close(fd)


def verify_export(folder,request,profile,trust,*,now=None):
    root=Path(folder).absolute()
    if not root.is_dir() or any(p.is_symlink() for p in (root,*root.parents)):
        raise AudioError('PIPELINE_EXPORT_ROOT')
    expected=NAMES|EXTRA|{'OUTPUT_SHA256.json'}
    if {p.name for p in root.iterdir()}!=expected:raise AudioError('PIPELINE_EXPORT_FILES')
    index=read_json(root/'OUTPUT_SHA256.json',1_000_000)
    if type(index)is not dict or set(index)!=NAMES|EXTRA:raise AudioError('PIPELINE_EXPORT_INDEX')
    all_files={}
    total=0
    for n in sorted(NAMES|EXTRA):
        # Neither a forged index size nor a forged manifest widens the limits.
        b=read_output(root/n,request['limits']['max_file_bytes']);total+=len(b)
        if total>request['limits']['max_bundle_bytes']+8_000_000:raise AudioError('PIPELINE_EXPORT_BUDGET')
        if index[n]!={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}:
            raise AudioError('PIPELINE_EXPORT_HASH')
        all_files[n]=b
    if all_files['PIPELINE_REQUEST.json']!=canonical(request) or all_files['PIPELINE_PROFILE.json']!=canonical(profile):
        raise AudioError('PIPELINE_EXPORT_EXPECTED_IDENTITY')
    receipt=strict_json(all_files['EXECUTION_RECEIPT.json'].decode())
    verified=verify_receipt(receipt,{n:all_files[n] for n in NAMES},request,profile,trust,now=now)
    return {**verified,'files_verified':len(index),'exclusive_output':True}


def publish_export(result,request,profile,trust,destination,*,allow_technical_voice=False,allow_review=False):
    if allow_technical_voice is not True or allow_review is not True:
        raise AudioError('PIPELINE_TECHNICAL_REVIEW_OPT_IN_REQUIRED')
    files=dict(result['files']);verify_receipt(result['receipt'],files,request,profile,trust)
    destination=Path(destination).absolute()
    if destination.exists() or destination.is_symlink():raise AudioError('PIPELINE_EXPORT_EXISTS')
    parent=private_root(destination.parent)
    files.update({'PIPELINE_REQUEST.json':canonical(request),'PIPELINE_PROFILE.json':canonical(profile),
        'EXECUTION_RECEIPT.json':canonical(result['receipt'])})
    files['OUTPUT_SHA256.json']=canonical({n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in sorted(files.items())})
    tmp=Path(tempfile.mkdtemp(prefix='.audio-pipeline-',dir=parent))
    try:
        for n,b in files.items():
            with (tmp/n).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        verify_export(tmp,request,profile,trust)
        fd=os.open(tmp,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        lock=parent/('.pipeline-publish-'+hashlib.sha256(str(destination).encode()).hexdigest()+'.lock')
        with key_lock(lock,timeout=30):
            if destination.exists() or destination.is_symlink():raise AudioError('PIPELINE_EXPORT_EXISTS')
            os.rename(tmp,destination)
            fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return verify_export(destination,request,profile,trust)
