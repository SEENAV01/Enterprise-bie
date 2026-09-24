#!/usr/bin/env python3
"""AUDIO H4-R1: canonical Linux-isolated diagnostics, not section acceptance.

Use externally provisioned runtime/profile/trust/key. Discovery never authorizes
an issuer. Exit 3 is REVIEW, 2 BLOCKED, 0 discovery/storage-only inspection.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
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
    for name in ('DEPENDENCY_SNAPSHOT.json','CANONICAL_AUDIO_DEPENDENCIES.json',
                 'CANONICAL_AUDIO_KERNEL_DEPENDENCIES.json'):
        manifest=json.loads((ROOT/name).read_text())
        for row in manifest['files']:
            path=ROOT/'dependency_snapshot'/row['path']
            if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file():
                raise ValueError('KERNEL_DEPENDENCY_PATH')
            data=path.read_bytes()
            if (len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']
                or hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!=row['expected_git_blob']):
                raise ValueError('KERNEL_DEPENDENCY_IDENTITY')
    sys.path.append(str(ROOT/'dependency_snapshot'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('probe-profile','evaluate','inspect'))
    for name in ('store','input','output','runtime','profile','trust-file','private-key-file'):
        p.add_argument('--'+name,type=Path)
    for name in ('key-id','run-id','job-id','revision'):
        p.add_argument('--'+name)
    p.add_argument('--allow-local-diagnostic',action='store_true')
    p.add_argument('--with-dir-snapshot',action='store_true')
    a=p.parse_args()
    try:
        if a.with_dir_snapshot:verify_dependencies()
        from bie.audio.common import AudioError,strict_json
        from bie.audio.tts_cache import read_regular
        from bie.audio.kernel_profile import probe_profile,validate_profile
        def read(path):
            if path is None:raise AudioError('KERNEL_ARGUMENTS_REQUIRED')
            return strict_json(read_regular(path,4_000_000).decode())
        if a.mode=='probe-profile':
            value=probe_profile(read(a.runtime))
            print(json.dumps(value,sort_keys=True,indent=2));return 0
        if a.mode=='inspect':
            if not a.store:raise AudioError('KERNEL_ARGUMENTS_REQUIRED')
            from bie.audio.durable_store import AudioArtifactStore
            print(json.dumps(AudioArtifactStore(a.store/'artifacts').inspect(),indent=2));return 0
        if not a.allow_local_diagnostic:
            raise AudioError('KERNEL_DIAGNOSTIC_OPT_IN_REQUIRED')
        if not all((a.store,a.input,a.output,a.runtime,a.profile,a.trust_file,a.private_key_file,
                    a.key_id,a.run_id,a.job_id,a.revision)):
            raise AudioError('KERNEL_ARGUMENTS_REQUIRED')
        paths=[x.absolute() for x in (a.input,a.output,a.store,a.runtime,a.profile,a.trust_file,a.private_key_file)]
        for i,x in enumerate(paths):
            if any(q.is_symlink() for q in (x,*x.parents)):raise AudioError('KERNEL_PATH_SYMLINK')
            for y in paths[i+1:]:
                if x==y or x.is_relative_to(y) or y.is_relative_to(x):
                    raise AudioError('KERNEL_PATH_OVERLAP')
        if a.output.exists():raise AudioError('KERNEL_OUTPUT_EXISTS')
        from bie.audio.acoustic_evidence import load_private_key
        from bie.audio.qa_source import load_published_mix
        from bie.audio.kernel_io import audit_kernel_mix
        runtime,profile,trust=read(a.runtime),read(a.profile),read(a.trust_file)
        validate_profile(profile,runtime)
        signer=load_private_key(a.private_key_file)
        mixed,sync,files=load_published_mix(a.input)
        stems=tuple(v for n,v in files.items() if n.startswith('inputs/') and n.endswith('.wav'))
        result,report,_=audit_kernel_mix(mixed,sync,asset_wavs=stems,output=a.output,
            root=a.store,run_id=a.run_id,job_id=a.job_id,revision=a.revision,runtime=runtime,
            profile=profile,trust=trust,signer=signer,key_id=a.key_id)
        print(json.dumps({'status':report['status'],'cache_hit':result['cache_hit'],
            'native_evaluations':result['native_evaluations'],'artifact_ref':result['artifact_ref'],
            'kernel_signature_reverified':result['kernel_signature_reverified'],
            'canonical_kernel_worker_adopted':True,'execution':result['execution'],
            'scope':result['scope'],'product_accepted':False},indent=2))
        return 3 if report['status']=='REVIEW' else 2
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,ImportError) as exc:
        print(json.dumps({'status':'BLOCKED','code':getattr(exc,'code','KERNEL_SETUP_OR_STATE_ERROR'),
                          'product_accepted':False}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
