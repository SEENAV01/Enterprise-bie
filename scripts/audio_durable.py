#!/usr/bin/env python3
"""Persist/reuse current acoustic evidence using existing canonical BIE stores.

Exit 3 means diagnostic REVIEW; 2 means blocked/fail; 0 is storage inspection,
never phonetic or product acceptance. No paid service or GitHub write.
"""
from pathlib import Path
import argparse, hashlib, importlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def verify_dependencies():
    binding=ROOT/"docs/evidence/audio-integration-001/CANONICAL_DEPENDENCY_BINDING.json"
    snapshot=ROOT/"dependency_snapshot"
    if binding.is_file() and not snapshot.exists():
        manifest=json.loads(binding.read_text())
        for row in manifest["files"]:
            path=ROOT/row["path"]
            if path.is_symlink() or not path.is_file():raise ValueError("CANONICAL_DEPENDENCY_PATH")
            data=path.read_bytes();blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            if len(data)!=row["bytes"] or hashlib.sha256(data).hexdigest()!=row["sha256"] or blob!=row["expected_git_blob"]:raise ValueError("CANONICAL_DEPENDENCY_IDENTITY")
        return
    """Standalone setup pins both inherited DIR and new canonical APIs."""
    for name in ('DEPENDENCY_SNAPSHOT.json','CANONICAL_AUDIO_DEPENDENCIES.json'):
        manifest=json.loads((ROOT/name).read_text())
        for row in manifest['files']:
            path=ROOT/'dependency_snapshot'/row['path']
            if path.is_symlink() or not path.is_file():raise ValueError('DEPENDENCY_PATH')
            data=path.read_bytes()
            if (len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']
                or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=row['expected_git_blob']):
                raise ValueError('DEPENDENCY_IDENTITY')
    sys.path.append(str(ROOT/'dependency_snapshot'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('evaluate','inspect'))
    p.add_argument('--store',type=Path,required=True)
    p.add_argument('--input',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--runtime',type=Path);p.add_argument('--trust-file',type=Path)
    p.add_argument('--private-key-file',type=Path);p.add_argument('--key-id')
    p.add_argument('--run-id');p.add_argument('--job-id');p.add_argument('--revision')
    p.add_argument('--allow-local-diagnostic',action='store_true')
    p.add_argument('--with-dir-snapshot',action='store_true')
    a=p.parse_args()
    try:
        if a.with_dir_snapshot:verify_dependencies()
        from bie.audio.common import AudioError,strict_json
        from bie.audio.durable_store import AudioArtifactStore,private_root
        from bie.audio.durable_pipeline import audit_durable_mix
        from bie.audio.acoustic_evidence import load_private_key
        from bie.audio.qa_source import load_published_mix
        if a.mode=='inspect':
            print(json.dumps(AudioArtifactStore(a.store/'artifacts').inspect(),indent=2));return 0
        if not a.allow_local_diagnostic:raise AudioError('DURABLE_LOCAL_DIAGNOSTIC_OPT_IN_REQUIRED')
        if not all((a.input,a.output,a.runtime,a.trust_file,a.private_key_file,a.key_id,a.run_id,a.job_id,a.revision)):
            raise AudioError('DURABLE_ARGUMENTS_REQUIRED')
        paths=[x.absolute() for x in (a.input,a.output,a.store,a.runtime,a.trust_file,a.private_key_file)]
        for i,x in enumerate(paths):
            if any(k.is_symlink() for k in (x,*x.parents)):raise AudioError('DURABLE_INPUT_SYMLINK')
            for y in paths[i+1:]:
                if x==y or x.is_relative_to(y) or y.is_relative_to(x):raise AudioError('DURABLE_PATH_OVERLAP')
        if a.output.exists():raise AudioError('DURABLE_OUTPUT_EXISTS')
        private_root(a.store)
        mixed,sync,files=load_published_mix(a.input)
        runtime=strict_json(a.runtime.read_text());trust=strict_json(a.trust_file.read_text())
        signer=load_private_key(a.private_key_file)
        stems=tuple(v for n,v in files.items() if n.startswith('inputs/') and n.endswith('.wav'))
        result,report,captions=audit_durable_mix(mixed,sync,root=a.store,run_id=a.run_id,
            job_id=a.job_id,revision=a.revision,runtime=runtime,trust=trust,signer=signer,
            key_id=a.key_id,asset_wavs=stems,output=a.output)
        print(json.dumps({'status':report['status'],'cache_hit':result['cache_hit'],
            'native_evaluations':result['native_evaluations'],'artifact_ref':result['artifact_ref'],
            'signature_reverified':result['signature_reverified'],'execution':result['execution'],
            'product_accepted':False,'canonical_kernel_worker_adopted':False},indent=2))
        return 3 if report['status']=='REVIEW' else 2
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,ImportError) as exc:
        print(json.dumps({'status':'BLOCKED','code':getattr(exc,'code','DURABLE_SETUP_OR_STATE_ERROR'),
            'product_accepted':False}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
