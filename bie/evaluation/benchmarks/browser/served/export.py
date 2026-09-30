"""H5-009: portable, self-checking evidence export from the existing ledger.
Only verify integrity; never upgrade a BLOCKED run or certify production.
"""
from pathlib import Path,PurePosixPath
import base64,hashlib,zipfile,stat
from ...models import BenchmarkError,canonical_json,strict_loads,digest

MAX_BYTES=64_000_000

def export_run(store,run_id,output):
    rec=store.get(run_id);data={'run.json':canonical_json(rec).encode('utf-8')};r=rec['result']
    receipt=r.get('details',{}).get('browser_receipt',r.get('browser_receipt'))
    if receipt is not None:
        data['collector.json']=canonical_json(receipt).encode('utf-8')
        for i,run in enumerate(receipt.get('observed',{}).get('runs',[])):
            data[f'screenshots/{i:03d}.png']=base64.b64decode(run['screenshot']['png_base64'],validate=True)
            data[f'transcripts/{i:03d}.json']=canonical_json({k:run[k] for k in ('http_responses','http_server','ax','readiness') if k in run}).encode('utf-8')
    if sum(map(len,data.values()))>MAX_BYTES:raise BenchmarkError('HTTP_EXPORT_LIMIT')
    manifest={'schema_version':'browser-portable-evidence-1','run_sha256':digest(rec),'product_accepted':False,
        'files':{k:{'size_bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in sorted(data.items())}}
    data['MANIFEST.json']=canonical_json(manifest).encode()
    p=Path(output)
    # Exclusive create avoids silently replacing a prior evidence release.
    with p.open('xb') as raw:
      with zipfile.ZipFile(raw,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,value in sorted(data.items()):
            info=zipfile.ZipInfo(name,(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,value)
    return verify_export(p)

def verify_export(path):
    try:
      with zipfile.ZipFile(path) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)>1000 or len(set(n.casefold() for n in names))!=len(names) or sum(i.file_size for i in infos)>MAX_BYTES:
            raise BenchmarkError('HTTP_EXPORT_ARCHIVE_LIMIT')
        for info in infos:
            n=info.filename;p=PurePosixPath(n)
            if (p.is_absolute() or '..' in p.parts or '\\' in n or ':' in n or not n or stat.S_ISLNK(info.external_attr>>16)):
                raise BenchmarkError('HTTP_EXPORT_UNSAFE_PATH')
        manifest=strict_loads(z.read('MANIFEST.json').decode('utf-8'))
        if manifest.get('schema_version')!='browser-portable-evidence-1' or manifest.get('product_accepted') is not False:
            raise BenchmarkError('HTTP_EXPORT_MANIFEST_INVALID')
        if set(names)!=set(manifest['files'])|{'MANIFEST.json'}:raise BenchmarkError('HTTP_EXPORT_MEMBER_MISMATCH')
        for n,row in manifest['files'].items():
            raw=z.read(n)
            if len(raw)!=row['size_bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise BenchmarkError('HTTP_EXPORT_HASH_MISMATCH')
        rec=strict_loads(z.read('run.json').decode('utf-8'))
        if digest(rec)!=manifest['run_sha256'] or rec['result'].get('product_accepted') is not False:
            raise BenchmarkError('HTTP_EXPORT_RUN_MISMATCH')
        original=rec['result'].get('details',{}).get('browser_receipt',rec['result'].get('browser_receipt'))
        allowed={'MANIFEST.json','run.json'}
        if original is not None:
            allowed.add('collector.json')
            from ..service import verify_receipt
            verify_receipt(original)
            if strict_loads(z.read('collector.json').decode())!=original:raise BenchmarkError('HTTP_EXPORT_COLLECTOR_MISMATCH')
            for i,run in enumerate(original.get('observed',{}).get('runs',[])):
                allowed.update({f'screenshots/{i:03d}.png',f'transcripts/{i:03d}.json'})
                if z.read(f'screenshots/{i:03d}.png')!=base64.b64decode(run['screenshot']['png_base64'],validate=True):
                    raise BenchmarkError('HTTP_EXPORT_SCREENSHOT_MISMATCH')
                expected={k:run[k] for k in ('http_responses','http_server','ax','readiness') if k in run}
                if strict_loads(z.read(f'transcripts/{i:03d}.json').decode())!=expected:raise BenchmarkError('HTTP_EXPORT_TRANSCRIPT_MISMATCH')
        if set(names)!=allowed:raise BenchmarkError('HTTP_EXPORT_UNEXPECTED_MEMBER')
        return {'verified':True,'members':len(names),'run_id':rec['reservation']['run_id'],
                'result_status':rec['result']['status'],'production_approval':False}
    except BenchmarkError:raise
    except (KeyError,TypeError,ValueError,zipfile.BadZipFile) as exc:raise BenchmarkError('HTTP_EXPORT_INVALID') from exc
