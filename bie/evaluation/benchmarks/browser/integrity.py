"""H4-010: explicit code-recovery accounting and bounded ZIP validation.
Never labels a reconstructed source tree as the missing original archive bytes.
"""
from pathlib import Path,PurePosixPath
import hashlib,zipfile,stat
from ..models import BenchmarkError,digest_string

def verify_inventory(root,inventory):
    if type(inventory) is not dict or not inventory:raise BenchmarkError('RECOVERY_EMPTY_INVENTORY')
    missing=[];changed=[];matched=[]
    for name,expected in sorted(inventory.items()):
        digest_string(expected);p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:raise BenchmarkError('RECOVERY_PATH_INVALID')
        f=Path(root)/name
        if f.is_symlink():changed.append(name)
        elif not f.is_file():missing.append(name)
        elif hashlib.sha256(f.read_bytes()).hexdigest()!=expected:changed.append(name)
        else:matched.append(name)
    return {'expected':len(inventory),'matched':len(matched),'missing':missing,'changed':changed,
            'all_matched':not missing and not changed,'original_master_bytes_recovered':False}

def inspect_zip(path,*,expected_sha256,max_bytes=2_000_000_000,max_members=20000):
    digest_string(expected_sha256)
    with Path(path).open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=expected_sha256:raise BenchmarkError('ZIP_OUTER_HASH_MISMATCH')
    seen=set();total=0
    with zipfile.ZipFile(path) as z:
        infos=z.infolist()
        if len(infos)>max_members:raise BenchmarkError('ZIP_MEMBER_LIMIT')
        for i in infos:
            n=i.filename;p=PurePosixPath(n)
            if (p.is_absolute() or '\\' in n or '..' in p.parts or ':' in n or '\x00' in n
                or n.casefold() in seen or stat.S_ISLNK(i.external_attr>>16)):
                raise BenchmarkError('ZIP_UNSAFE_MEMBER')
            seen.add(n.casefold());total+=i.file_size
            if total>max_bytes:raise BenchmarkError('ZIP_BYTE_LIMIT')
        bad=z.testzip()
        if bad is not None:raise BenchmarkError('ZIP_CRC_MISMATCH')
    return {'members':len(seen),'uncompressed_bytes':total,'outer_sha256':expected_sha256,'verified':True}
