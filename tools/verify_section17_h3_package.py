#!/usr/bin/env python3
"""Bounded outer-archive extraction for cumulative masters with large parent ZIPs.

The caller pins the OUTER SHA256. Archives inside history/ are not recursively
extracted. Manifest hashes establish file identity, not authorship or acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,re,shutil,stat,zipfile
from verify_section17_package import PackageError,relative_name,path_key,reject_symlink_chain,pairs

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()

def verify(root):
    root=reject_symlink_chain(root)
    if not root.is_dir():raise PackageError('ROOT_DIRECTORY_REQUIRED')
    manifest=root/'MANIFEST.json'
    if manifest.is_symlink() or not manifest.is_file():raise PackageError('MANIFEST_MISSING_OR_SYMLINK')
    if manifest.stat().st_size>10_000_000:raise PackageError('MANIFEST_SIZE_LIMIT')
    value=json.loads(manifest.read_text('utf-8'),object_pairs_hook=pairs)
    if set(value)!={'schema_version','files'} or value['schema_version']!='1.0.0' or type(value['files']) is not dict or not value['files']:
        raise PackageError('INVALID_MANIFEST')
    expected=value['files'];keys=set()
    for name,h in expected.items():
        relative_name(name)
        if name=='MANIFEST.json' or type(h) is not str or not re.fullmatch('[0-9a-f]{64}',h):raise PackageError('INVALID_MANIFEST_ENTRY')
        if path_key(name) in keys:raise PackageError('CASE_COLLIDING_PATHS')
        keys.add(path_key(name))
    actual=set()
    for path in root.rglob('*'):
        if path.is_symlink():raise PackageError('SYMLINK_FORBIDDEN')
        if path==manifest:continue
        if path.is_file():actual.add(path.relative_to(root).as_posix())
        elif not path.is_dir():raise PackageError('SPECIAL_FILE_FORBIDDEN')
    if actual!=set(expected):raise PackageError('FILE_INVENTORY_MISMATCH')
    for name in sorted(expected):
        if sha(root/name)!=expected[name]:raise PackageError('FILE_HASH_MISMATCH: '+name)
    return {'status':'VERIFIED','files':len(expected),'manifest_sha256':sha(manifest)}

def extract(archive,destination,*,expected_sha256,max_total_bytes=1024**3,max_member_bytes=512*1024**2):
    source=reject_symlink_chain(archive);destination=reject_symlink_chain(destination)
    if not source.is_file():raise PackageError('ARCHIVE_NOT_REGULAR')
    if type(expected_sha256) is not str or not re.fullmatch('[0-9a-f]{64}',expected_sha256):raise PackageError('OUTER_SHA256_REQUIRED')
    for value in (max_total_bytes,max_member_bytes):
        if type(value) is not int or not 1<=value<=4*1024**3:raise PackageError('INVALID_EXTRACTION_LIMIT')
    if max_member_bytes>max_total_bytes:raise PackageError('INVALID_EXTRACTION_LIMIT')
    if destination.exists() or destination.is_symlink():raise PackageError('DESTINATION_ALREADY_EXISTS')
    # Freeze the outer file identity around preflight and extraction. This is not
    # a sandbox against a hostile owner of source/destination directories.
    before=source.stat()
    if sha(source)!=expected_sha256:raise PackageError('OUTER_ARCHIVE_HASH_MISMATCH')
    with zipfile.ZipFile(source) as z:
        entries=z.infolist()
        if not entries or len(entries)>100000:raise PackageError('MEMBER_COUNT_LIMIT')
        seen=set();total=0;file_names=set()
        for entry in entries:
            name=entry.filename.rstrip('/') if entry.is_dir() else entry.filename
            relative_name(name);key=path_key(name)
            if key in seen:raise PackageError('DUPLICATE_ZIP_MEMBER')
            seen.add(key)
            if stat.S_IFMT(entry.external_attr>>16) not in (0,stat.S_IFREG,stat.S_IFDIR):raise PackageError('ZIP_SPECIAL_FILE_FORBIDDEN')
            if entry.flag_bits&1:raise PackageError('ENCRYPTED_MEMBER_FORBIDDEN')
            total+=entry.file_size
            if total>max_total_bytes or entry.file_size>max_member_bytes or entry.file_size>max(1,entry.compress_size)*2000:
                raise PackageError('ARCHIVE_SIZE_LIMIT')
            if not entry.is_dir():file_names.add(key)
        for entry in entries:
            parts=entry.filename.rstrip('/').split('/')
            if any(path_key('/'.join(parts[:n])) in file_names for n in range(1,len(parts))):raise PackageError('ZIP_FILE_DIRECTORY_CONFLICT')
        destination.mkdir(parents=True,exist_ok=False)
        try:
            written=0
            for entry in entries:
                target=destination/entry.filename
                if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True);count=0
                with z.open(entry) as src,target.open('xb') as out:
                    while block:=src.read(1024*1024):
                        written+=len(block);count+=len(block)
                        if written>max_total_bytes or count>entry.file_size or count>max_member_bytes:raise PackageError('EXTRACTION_BYTE_LIMIT')
                        out.write(block)
                if count!=entry.file_size:raise PackageError('EXTRACTION_SIZE_MISMATCH')
            after=source.stat()
            sig=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            if sig(before)!=sig(after) or sha(source)!=expected_sha256:raise PackageError('ARCHIVE_CHANGED_DURING_EXTRACTION')
        except BaseException:
            shutil.rmtree(destination);raise
    return {'status':'EXTRACTED','outer_sha256':expected_sha256,'members':len(entries),'uncompressed_bytes':total,
            'max_total_bytes':max_total_bytes,'max_member_bytes':max_member_bytes,'recursive_extraction':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='cmd',required=True)
    v=s.add_parser('verify');v.add_argument('root')
    x=s.add_parser('extract');x.add_argument('archive');x.add_argument('destination');x.add_argument('--expected-sha256',required=True)
    x.add_argument('--max-total-bytes',type=int,default=1024**3);x.add_argument('--max-member-bytes',type=int,default=512*1024**2)
    a=p.parse_args()
    try:
        r=verify(a.root) if a.cmd=='verify' else extract(a.archive,a.destination,expected_sha256=a.expected_sha256,max_total_bytes=a.max_total_bytes,max_member_bytes=a.max_member_bytes)
        print(json.dumps(r));return 0
    except (OSError,ValueError,zipfile.BadZipFile) as e:
        print(json.dumps({'status':'BLOCKED','reason':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
