"""Create a deterministic source backup associated with a verified Git commit."""
from pathlib import Path
import argparse, hashlib, json, re, zipfile

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--commit',required=True,help='Full GitHub commit SHA verified for this source tree')
    p.add_argument('--output',required=True)
    args=p.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.commit):p.error('--commit must be a full commit SHA')
    output=Path(args.output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_suffix(output.suffix+'.tmp')
    records=[]
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in sorted(ROOT.rglob('*')):
            if not path.is_file() or path.resolve() in (output,tmp):continue
            rel=path.relative_to(ROOT)
            if any(x in ('.git','__pycache__','.pytest_cache','node_modules','.venv') for x in rel.parts) or path.suffix in ('.pyc','.pyo','.tmp'):continue
            data=path.read_bytes()
            records.append({'path':rel.as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)})
            info=zipfile.ZipInfo('Enterprise-bie/'+rel.as_posix(),(2026,9,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
        manifest={'repository':'https://github.com/SEENAV01/Enterprise-bie','commit_sha':args.commit,'note':'The commit is a verified source checkpoint, not production acceptance.','files':records}
        info=zipfile.ZipInfo('BACKUP_MANIFEST.json',(2026,9,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(tmp) as z:
        if z.testzip() is not None:raise RuntimeError('Backup CRC validation failed')
    tmp.replace(output)
    print(json.dumps({'path':str(output),'commit_sha':args.commit,'file_count':len(records),'size_bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
