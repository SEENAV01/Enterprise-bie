"""Restore exact originals from a hash-bound data-only capsule. No input code runs.

The capsule is a transport format, not a replacement for the original archives.
Every reconstructed object and each final file must match its SHA-256 and size.
"""
from __future__ import annotations
import argparse, hashlib, json, lzma, re, shutil, struct, tarfile, tempfile, zlib
from pathlib import Path, PurePosixPath
HEX=re.compile(r'^[0-9a-f]{64}$')
MAX_TAR=600*1024*1024

def sha(data: bytes) -> str:return hashlib.sha256(data).hexdigest()
def compress(data: bytes, level: int, window: int=-15) -> bytes:
    obj=zlib.compressobj(level,zlib.DEFLATED,window)
    return obj.compress(data)+obj.flush()

def unpack_capsule(archive: Path, root: Path, expected_sha: str) -> None:
    if not HEX.fullmatch(expected_sha) or sha(archive.read_bytes())!=expected_sha:
        raise ValueError('CAPSULE_SHA256_MISMATCH')
    root.mkdir(parents=True,exist_ok=False)
    count=0;total=0;seen=set()
    with tarfile.open(archive,'r:xz') as tf:
        for m in tf:
            name=m.name.removeprefix('./');p=PurePosixPath(name)
            if m.isdir() and name in ('','.','raw'):continue
            if not m.isfile() or p.is_absolute() or '..' in p.parts or '\\' in name or name in seen:
                raise ValueError('UNSAFE_CAPSULE_MEMBER:'+m.name)
            if not (name in ('recipes.json','top_files.json','zip_members.json','summary.json','plan.json') or len(p.parts)==2 and p.parts[0]=='raw' and HEX.fullmatch(p.parts[1])):
                raise ValueError('UNKNOWN_CAPSULE_MEMBER:'+name)
            count+=1;total+=m.size
            if count>100000 or total>MAX_TAR or m.size>100*1024*1024:
                raise ValueError('CAPSULE_BUDGET_EXCEEDED')
            seen.add(name);dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            src=tf.extractfile(m)
            if src is None:raise ValueError('CAPSULE_MEMBER_UNREADABLE')
            with dest.open('xb') as out:shutil.copyfileobj(src,out)
            if dest.stat().st_size!=m.size:raise ValueError('CAPSULE_MEMBER_TRUNCATED')

def restore(extracted: Path, output: Path) -> dict:
    recipes=json.loads((extracted/'recipes.json').read_text())
    top=json.loads((extracted/'top_files.json').read_text())
    if not isinstance(recipes,dict) or len(recipes)>20000 or not isinstance(top,list) or len(top)>2000:
        raise ValueError('CAPSULE_SCHEMA_OR_BUDGET')
    output.mkdir(parents=True,exist_ok=False)
    cache=output/'objects';cache.mkdir();active=set();verified_raw=set();verified_obj=set()
    def raw(key: str) -> bytes:
        if not isinstance(key,str) or not HEX.fullmatch(key):raise ValueError('BAD_RAW_KEY')
        p=extracted/'raw'/key
        if p.is_symlink() or not p.is_file():raise ValueError('RAW_UNAVAILABLE')
        b=p.read_bytes()
        if key not in verified_raw and sha(b)!=key:raise ValueError('RAW_HASH_MISMATCH')
        verified_raw.add(key);return b
    def obj(key: str, depth: int=0) -> bytes:
        if not isinstance(key,str) or not HEX.fullmatch(key) or key not in recipes:raise ValueError('BAD_OBJECT_KEY')
        if key in active or depth>40:raise ValueError('CYCLIC_OR_TOO_DEEP')
        target=cache/key
        if key in verified_obj:return target.read_bytes()
        r=recipes[key];size=r.get('size')
        if type(size)is not int or not 0<=size<=100*1024*1024:raise ValueError('OBJECT_SIZE_LIMIT')
        active.add(key)
        try:
            if r['kind']=='raw':b=raw(r['raw'])
            elif r['kind']=='zip':
                parts=r['parts']
                if not isinstance(parts,list) or len(parts)>200001:raise ValueError('PART_LIMIT')
                segments=[];used=0
                for item in parts:
                    if item[0]=='r' and len(item)==2:piece=raw(item[1])
                    elif item[0]=='o' and len(item)==2:piece=obj(item[1],depth+1)
                    elif item[0]=='d' and len(item)==3 and type(item[2])is int and 0<=item[2]<=9:piece=compress(obj(item[1],depth+1),item[2])
                    else:raise ValueError('UNKNOWN_RECIPE_OPERATION')
                    used+=len(piece)
                    if used>size:raise ValueError('OBJECT_EXPANSION_LIMIT')
                    segments.append(piece)
                b=b''.join(segments)
            elif r['kind']=='png':
                data=compress(raw(r['scan']),r['level'],15);offset=0;segments=[b'\x89PNG\r\n\x1a\n']
                for item in r['chunks']:
                    if item[0]=='r':segments.append(raw(item[1]))
                    elif item[0]=='i' and type(item[1])is int and item[1]>=0:
                        payload=data[offset:offset+item[1]];offset+=item[1]
                        if len(payload)!=item[1]:raise ValueError('PNG_CHUNK_LENGTH')
                        tag=b'IDAT'+payload
                        segments.append(struct.pack('>I',len(payload))+tag+struct.pack('>I',zlib.crc32(tag)&0xffffffff))
                    else:raise ValueError('PNG_RECIPE')
                if offset!=len(data):raise ValueError('PNG_STREAM_LENGTH')
                b=b''.join(segments)
            else:raise ValueError('UNKNOWN_RECIPE_KIND')
            if len(b)!=size or sha(b)!=key:raise ValueError('RECONSTRUCTION_HASH_MISMATCH:'+key)
            target.write_bytes(b);verified_obj.add(key);return b
        finally:active.remove(key)
    names=set();files=[];total=0
    for row in top:
        name=row['name'];key=row['sha256'];size=row['bytes']
        if not isinstance(name,str) or not name or name in names or Path(name).name!=name or '\\' in name or '\0' in name or name in ('.','..'):
            raise ValueError('TOP_LEVEL_NAME_INVALID')
        names.add(name);b=obj(key)
        if len(b)!=size:raise ValueError('TOP_LEVEL_SIZE_MISMATCH')
        total+=size
        if total>1024**3:raise ValueError('FINAL_CORPUS_SIZE_LIMIT')
        files.append({'name':name,'sha256':key,'bytes':size,'object_path':'objects/'+key})
    if (extracted/'plan.json').exists():
        plan=json.loads((extracted/'plan.json').read_text())
        for phase in plan['phases']:
            for change in phase['operations']:
                data=obj(change['sha256'])
                if len(data)!=change['bytes']:raise ValueError('OPERATION_SIZE_MISMATCH')
    report={'schema_version':'bie.restored-corpus.v1','files':files,'files_verified':len(files),'unique_original_files':len(set(x['sha256'] for x in files)),'objects_verified':len(verified_obj),'raw_objects_verified':len(verified_raw),'total_original_bytes':total,'all_originals_exact':True,'zlib_runtime':zlib.ZLIB_RUNTIME_VERSION,'accepted':False}
    (output/'RESTORATION_RECEIPT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='bie-binary-transport-') as td:
        root=Path(td)/'capsule';unpack_capsule(args.archive,root,args.sha256);r=restore(root,args.output)
    print(json.dumps({k:v for k,v in r.items() if k!='files'},indent=2))
if __name__=='__main__':main()
