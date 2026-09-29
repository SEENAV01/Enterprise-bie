"""H8 assurance interfaces. Operator policy is never read from source content."""
from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from ..operational_quality_v2.common import (
    Binding, Finding, report, require, fields, items, text, ContractError,
    canonical_bytes, digest, token, integer, sha256, safe_relative_path, ArtifactRef,
    identity, regular_bytes, inventory, copy_verified, strict_object, real_dir,
)

def exact_strings(values, code, minimum=0, maximum=4096):
    require(type(values) in (list,tuple) and minimum <= len(values) <= maximum, code)
    for v in values: token(v,code)
    require(len(set(values)) == len(values),code+'_DUPLICATE')
    return tuple(values)

def checked_rows(rows):
    require(type(rows) in (list,tuple) and 1 <= len(rows) <= 20000,'H8_FILE_CENSUS')
    names=[]
    for r in rows:
        fields(r,('path','bytes','sha256'),'H8_FILE_ROW')
        safe_relative_path(r['path']);integer(r['bytes'],'bytes',0,64*1024*1024)
        sha256(r['sha256'],'file');names.append(r['path'])
    require(len(set(names))==len(names),'H8_FILE_ALIAS')
    return tuple(dict(r) for r in sorted(rows,key=lambda x:x['path']))

def check_files(root,rows):
    expected=checked_rows(rows);actual=inventory(root)
    require(actual==list(expected),'H8_FILE_INVENTORY_CHANGED')
    return actual

def outcome(task,binding,details,errors=(),reviews=()):
    fs=[Finding(c,task,'BLOCKER') for c in sorted(set(errors))]
    fs += [Finding(c,task,'REVIEW') for c in sorted(set(reviews))]
    # A diagnostic never supplies an automatic release certificate.
    if not fs: fs=[Finding('OPERATIONAL_INDEPENDENT_ACCEPTANCE_REQUIRED',task)]
    return {'schema_version':'bie.qa.assurance-quality/1',
        'report':report(task,binding,fs,details=details).to_dict(),
        'details':details,'technical_checks_clear':not errors,
        'production_authorized':False,'product_accepted':False}

def write_new(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f: f.write(canonical_bytes(value)+b'\n')
    return p
