#!/usr/bin/env python3
"""Verify every delivered package member; extra, missing or changed bytes fail."""
import argparse,hashlib,json
from pathlib import Path,PurePosixPath

def verify(root):
    root=Path(root).resolve();m=json.loads((root/'PACKAGE_MANIFEST.json').read_text());expected=m['files'];errors=[]
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(expected)|{'PACKAGE_MANIFEST.json'}:errors.append('FILE_SET_MISMATCH')
    for path,info in expected.items():
        rel=PurePosixPath(path);p=root.joinpath(*rel.parts)
        if rel.is_absolute() or '..' in rel.parts or '\\' in path or p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root):
            errors.append('INVALID_PATH:'+path);continue
        if any(a.is_symlink() for a in p.parents if a!=root and a.is_relative_to(root)):
            errors.append('SYMLINK_PARENT:'+path);continue
        b=p.read_bytes()
        if len(b)!=info['bytes'] or hashlib.sha256(b).hexdigest()!=info['sha256']:errors.append('HASH_MISMATCH:'+path)
    return {'passed':not errors,'files_verified':len(expected),'errors':errors,'scope':'Exact local package bytes, not production acceptance'}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]);args=a.parse_args();r=verify(args.root);print(json.dumps(r,indent=2));raise SystemExit(0 if r['passed'] else 1)
