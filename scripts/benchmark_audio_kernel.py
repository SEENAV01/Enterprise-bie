#!/usr/bin/env python3
"""Synthetic H4-R1 Linux evidence, cold CLI restart and negative boundaries.

Not a real-book benchmark, security certification or production voice evaluation.
Private signing key exists only in a temporary directory and is never bundled.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))


def boundary_probe(root,profile):
    """Actual canonical worker boundary checks, distinct from acoustic API."""
    from bie.compiler.linux_worker import run_isolated,WorkerPolicy
    from bie.audio.kernel_runtime import validate_kernel_proof
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    work=root/'work';engine=root/'engine';work.mkdir();engine.mkdir();(work/'output').mkdir()
    canary=root/'host-private-canary';canary.write_text('NOT_EXPOSED_TEST_CANARY')
    (work/'readonly-input').write_text('ORIGINAL');(engine/'readonly-code').write_text('ORIGINAL')
    code='''import json,os,socket,ctypes,errno
from pathlib import Path
checks={}
checks['host_file_unavailable']=not Path(HOST_CANARY).exists()
checks['host_proc_unavailable']=not Path('/proc/self/stat').exists()
checks['private_env_not_inherited']='BIE_H4R_CANARY_SECRET' not in os.environ
for name,path in [('workspace_read_only','/work/readonly-input'),('engine_read_only','/engine/readonly-code')]:
    try:Path(path).write_text('BAD');checks[name]=False
    except OSError:checks[name]=True
try:
    with socket.create_connection(('1.1.1.1',443),timeout=1):pass
    checks['external_network_blocked']=False
except OSError:checks['external_network_blocked']=True
lib=ctypes.CDLL(None,use_errno=True)
lib.mount.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulong,ctypes.c_char_p]
checks['mount_syscall_denied']=lib.mount(b'tmpfs',b'/tmp',b'tmpfs',0,None)==-1 and ctypes.get_errno()==errno.EPERM
Path('/work/output/allowed').write_text('ALLOWED')
checks['declared_output_writable']=Path('/work/output/allowed').read_text()=='ALLOWED'
Path('/work/output/checks.json').write_text(json.dumps(checks,sort_keys=True))
'''.replace('HOST_CANARY',repr(str(canary)))
    script=work/'probe.py';script.write_text(code)
    host={k:os.readlink('/proc/self/ns/'+k) for k in ('net','mnt','pid','user')}
    old=os.environ.get('BIE_H4R_CANARY_SECRET');os.environ['BIE_H4R_CANARY_SECRET']='test-never-forward'
    try:
        proc,proof=run_isolated([profile['executables']['python']['path'],'-I','-B',str(script)],
            workspace=work,engine=engine,writable=('output',),policy=WorkerPolicy(**profile['worker_policy']),
            timeout_s=15,lock_root=root/'slots')
    finally:
        if old is None:os.environ.pop('BIE_H4R_CANARY_SECRET',None)
        else:os.environ['BIE_H4R_CANARY_SECRET']=old
    if not proc.process.passed:raise RuntimeError('BOUNDARY_NATIVE_FAILED: '+proc.process.stderr)
    validate_kernel_proof(proof,profile,host)
    checks=json.loads((work/'output/checks.json').read_text())
    checks['input_bytes_unchanged']=(work/'readonly-input').read_text()=='ORIGINAL'
    checks['engine_bytes_unchanged']=(engine/'readonly-code').read_text()=='ORIGINAL'
    if not checks or not all(v is True for v in checks.values()):raise RuntimeError('BOUNDARY_FAILED')
    return {'passed':True,'scope':'BOUNDED_ADVERSARIAL_NATIVE_FIXTURES_NOT_SECURITY_CERTIFICATION',
        'checks':checks,'kernel_proof':proof,'host_namespaces':host,
        'process_exit':proc.process.exit_code,'product_accepted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.absolute();out.mkdir(parents=True,exist_ok=False)
    from scripts.audio_kernel import verify_dependencies
    verify_dependencies()
    from tests.audio.kernel_test_support import context,KEY_ID,RUN_ID
    from tests.audio.qa_test_support import native
    from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,NoEncryption
    from bie.audio.acoustic_contract import canonical
    from bie.audio.mix_io import publish_mix
    from bie.audio.kernel_io import verify_kernel_publication
    c=context()
    (out/'RUNTIME.json').write_bytes(canonical(c['runtime']))
    (out/'PROFILE.json').write_bytes(canonical(c['profile']))
    (out/'TRUST_TEST_ONLY.json').write_bytes(canonical(c['trust']))
    summary={'scope':'SYNTHETIC_AUDIO_NATIVE_KERNEL_AND_RESTART_DIAGNOSTIC',
        'production_authority':False,'private_key_bundled':False,'product_accepted':False,
        'github_write_performed':False,'cases':[]}
    with tempfile.TemporaryDirectory(prefix='bie-h4r-key-') as d:
        private=Path(d)/'signer';private.write_bytes(c['key'].private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption()));private.chmod(0o600)
        for language,runs,expected in (('english',2,3),('hindi',1,2)):
            case=out/language;case.mkdir();sync,mixed,_=native(language=language)
            publish_mix(mixed,case/'input',sync=sync,allow_review=True)
            rows=[];hashes=[]
            for i in range(runs):
                command=[sys.executable,'-B',str(ROOT/'scripts/audio_kernel.py'),'evaluate','--with-dir-snapshot',
                    '--allow-local-diagnostic','--store',str(case/'store'),'--input',str(case/'input'),
                    '--output',str(case/f'export-{i+1}'),'--runtime',str(out/'RUNTIME.json'),'--profile',str(out/'PROFILE.json'),
                    '--trust-file',str(out/'TRUST_TEST_ONLY.json'),'--private-key-file',str(private),
                    '--key-id',KEY_ID,'--run-id',RUN_ID,'--job-id',language,'--revision','H4-R1-benchmark']
                r=subprocess.run(command,capture_output=True,text=True,timeout=180)
                (case/f'run-{i+1}.stdout.txt').write_text(r.stdout);(case/f'run-{i+1}.stderr.txt').write_text(r.stderr)
                if r.returncode!=expected:raise RuntimeError(f'BENCHMARK {language}: {r.returncode}: {r.stderr}')
                row=json.loads(r.stdout);row['returncode']=r.returncode
                if row['cache_hit']!=(i>0) or row['native_evaluations']!=(0 if i else 1):raise RuntimeError('REUSE_INVALID')
                if not verify_kernel_publication(case/f'export-{i+1}',mixed,sync,c['runtime'],c['profile'],c['trust'])['verified']:
                    raise RuntimeError('PUBLICATION_INVALID')
                rows.append(row)
                hashes.append({q.relative_to(case/f'export-{i+1}').as_posix():hashlib.sha256(q.read_bytes()).hexdigest()
                    for q in (case/f'export-{i+1}').rglob('*') if q.is_file() and not q.name.endswith('.lock') and not q.name.endswith('SHA256.json')})
            receipt=json.loads((case/'export-1/KERNEL_RECEIPT.json').read_text())
            m=receipt['payload']['compatibility_receipt']['payload']['measurement']
            unchanged=hashlib.sha256(mixed.wav_bytes).hexdigest()==hashlib.sha256((case/'input/master.wav').read_bytes()).hexdigest()
            if not unchanged or (runs==2 and (hashes[0]!=hashes[1] or rows[0]['artifact_ref']!=rows[1]['artifact_ref'])):
                raise RuntimeError('RESTART_OR_SOURCE_MUTATION')
            summary['cases'].append({'language':language,'runs':rows,'source_media_unchanged':unchanged,
                'cold_restart_payload_identical':hashes[0]==hashes[1] if runs==2 else None,
                'native_search_passes':sum(len(s['native_passes']) for s in m['segments']),
                'segment_statuses':[s['status'] for s in m['segments']],
                'kernel_proof':receipt['payload']['execution']['kernel_proof']})
    with tempfile.TemporaryDirectory(prefix='bie-h4r-boundary-') as d:
        summary['boundaries']=boundary_probe(Path(d),c['profile'])
    summary['tested_source']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('bie','scripts','tests','dependency_snapshot') for p in sorted((ROOT/folder).rglob('*.py'))}
    summary['passed']=True
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='tested_source'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
