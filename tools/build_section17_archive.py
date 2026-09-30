#!/usr/bin/env python3
"""Write a deterministic ZIP and exact manifest of an operator-owned folder.

Output must be outside the input tree. Existing output files and symbolic links
are refused. The manifest authenticates no one: compare it with a trusted digest.
"""
import argparse,hashlib,json,stat,zipfile
from pathlib import Path

def write_manifest(root):
    root=Path(root).resolve();paths=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('SYMLINK_REFUSED')
        if p.is_file() and p!=root/'MANIFEST.json':paths.append(p)
        elif not p.is_file() and not p.is_dir():raise ValueError('SPECIAL_FILE_REFUSED')
    files={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (root/'MANIFEST.json').write_text(json.dumps({'schema_version':'1.0.0','files':files},indent=2)+'\n')
    return files

def pack(root,output):
    root=Path(root).resolve();output=Path(output).absolute()
    if output.exists() or output.is_symlink() or output.is_relative_to(root):raise ValueError('UNSAFE_OR_EXISTING_OUTPUT')
    write_manifest(root);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if not p.is_file():continue
            zi=zipfile.ZipInfo(root.name+'/'+p.relative_to(root).as_posix(),date_time=(2026,9,29,0,0,0))
            zi.create_system=3;zi.external_attr=(stat.S_IFREG|0o644)<<16;zi.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(zi,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return hashlib.sha256(output.read_bytes()).hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps({'archive_sha256':pack(a.root,a.output)},indent=2))
