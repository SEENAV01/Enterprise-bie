#!/usr/bin/env python3
"""Verify an exact extracted file manifest, or safely extract a ZIP to a new directory.

Hashes prove identity against a trusted manifest, not the truth of benchmark
claims. Keep evaluator directories private from untrusted candidate workers.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import re
import shutil
import stat
import zipfile

class PackageError(ValueError): pass

def relative_name(name):
    if type(name) is not str or not name or '\\' in name or ':' in name or '\x00' in name:
        raise PackageError('UNSAFE_MEMBER_NAME')
    parts=name.split('/')
    if name.startswith('/') or any(p in ('','.','..') for p in parts):
        raise PackageError('UNSAFE_MEMBER_NAME')
    return PurePosixPath(name)

def pairs(items):
    output={}
    for k,v in items:
        if k in output:raise PackageError('DUPLICATE_MANIFEST_KEY')
        output[k]=v
    return output

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(root):
    root=Path(root).resolve()
    manifest=root/'MANIFEST.json'
    if manifest.is_symlink() or not manifest.is_file():raise PackageError('MANIFEST_MISSING_OR_SYMLINK')
    if manifest.stat().st_size>10_000_000:raise PackageError('MANIFEST_SIZE_LIMIT')
    body=json.loads(manifest.read_text('utf-8'),object_pairs_hook=pairs)
    if set(body)!={'schema_version','files'} or body['schema_version']!='1.0.0' or type(body['files']) is not dict:
        raise PackageError('INVALID_MANIFEST')
    expected=set(body['files'])
    if not expected:raise PackageError('EMPTY_MANIFEST')
    if len({k.casefold() for k in expected})!=len(expected):raise PackageError('CASE_COLLIDING_PATHS')
    for name,value in body['files'].items():
        relative_name(name)
        if name=='MANIFEST.json' or type(value) is not str or not re.fullmatch('[0-9a-f]{64}',value):raise PackageError('INVALID_MANIFEST_ENTRY')
    actual=set()
    for path in root.rglob('*'):
        if path.is_symlink():raise PackageError('SYMLINK_FORBIDDEN')
        if path.is_file() and path!=manifest:actual.add(path.relative_to(root).as_posix())
        elif not path.is_dir() and path!=manifest:raise PackageError('SPECIAL_FILE_FORBIDDEN')
    if actual!=expected:raise PackageError('FILE_INVENTORY_MISMATCH')
    for name in sorted(expected):
        if sha(root/name)!=body['files'][name]:raise PackageError('FILE_HASH_MISMATCH: '+name)
    return {'status':'VERIFIED','files':len(expected),'manifest_sha256':sha(manifest)}

def extract(archive,destination):
    destination=Path(destination)
    if destination.exists() or destination.is_symlink():raise PackageError('DESTINATION_ALREADY_EXISTS')
    with zipfile.ZipFile(archive) as zf:
        members=zf.infolist()
        if not members or len(members)>100_000:raise PackageError('MEMBER_COUNT_LIMIT')
        seen=set();total=0
        for item in members:
            name=item.filename[:-1] if item.is_dir() else item.filename
            relative_name(name)
            if name.casefold() in seen:raise PackageError('DUPLICATE_ZIP_MEMBER')
            seen.add(name.casefold())
            kind=stat.S_IFMT(item.external_attr>>16)
            if kind not in (0,stat.S_IFREG,stat.S_IFDIR):raise PackageError('ZIP_SPECIAL_FILE_FORBIDDEN')
            if item.flag_bits & 1:raise PackageError('ENCRYPTED_MEMBER_FORBIDDEN')
            total+=item.file_size
            if total>512_000_000 or item.file_size>100_000_000 or item.file_size>max(1,item.compress_size)*2000:
                raise PackageError('ARCHIVE_SIZE_LIMIT')
        # Validate ancestor conflicts before writing, including names differing only in case.
        file_names={i.filename.casefold() for i in members if not i.is_dir()}
        for i in members:
            components=i.filename.rstrip('/').split('/')
            if any('/'.join(components[:n]).casefold() in file_names for n in range(1,len(components))):
                raise PackageError('ZIP_FILE_DIRECTORY_CONFLICT')
        destination.mkdir(parents=True,exist_ok=False)
        try:
            for item in members:
                target=destination/item.filename
                if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                target.parent.mkdir(parents=True,exist_ok=True)
                with zf.open(item) as source,target.open('xb') as out:shutil.copyfileobj(source,out)
        except BaseException:
            shutil.rmtree(destination)
            raise
    return {'status':'EXTRACTED','member_count':len(members),'uncompressed_bytes':total}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    v=sub.add_parser('verify');v.add_argument('root')
    x=sub.add_parser('extract');x.add_argument('archive');x.add_argument('destination')
    args=parser.parse_args()
    try:
        result=verify(args.root) if args.command=='verify' else extract(args.archive,args.destination)
        print(json.dumps(result));return 0
    except (PackageError,OSError,ValueError,zipfile.BadZipFile) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc)}));return 1
if __name__=='__main__':raise SystemExit(main())
