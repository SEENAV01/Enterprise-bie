#!/usr/bin/env python3
"""Independent AUDIO acoustic diagnostics. No paid calls, source edits or GitHub writes.

Exit 3: diagnostics completed but acceptance remains REVIEW. Exit 2: blocked/fail.
Verification exit 0 verifies integrity/authentication only, NOT sound quality.
"""
from pathlib import Path
import argparse, json, sys, time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('probe-runtime','evaluate','verify'))
    p.add_argument('input',nargs='?',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--runtime',type=Path)
    p.add_argument('--private-key-file',type=Path);p.add_argument('--key-id')
    p.add_argument('--trust-file',type=Path);p.add_argument('--policy',type=Path)
    p.add_argument('--evidence',type=Path)
    p.add_argument('--allow-local-diagnostic',action='store_true')
    p.add_argument('--with-dir-snapshot',action='store_true')
    a=p.parse_args()
    if a.with_dir_snapshot:sys.path.append(str(ROOT/'dependency_snapshot'))
    try:
        from bie.audio.common import AudioError, strict_json
        from bie.audio.acoustic_contract import AcousticPolicy, build_job, canonical
        from bie.audio.acoustic_runtime import probe_local_runtime, verify_runtime
        from bie.audio.acoustic_evidence import load_private_key, issue_evaluation, validate_trust
        from bie.audio.acoustic_io import publish_evaluation, verify_publication
        from bie.audio.qa_source import load_published_mix
        from bie.audio.qa_pipeline import audit_mix
        if a.mode=='probe-runtime':
            if not a.output:raise AudioError('ACOUSTIC_OUTPUT_REQUIRED')
            if a.output.exists() or any(x.is_symlink() for x in (a.output,*a.output.parents)):
                raise AudioError('ACOUSTIC_OUTPUT_EXISTS_OR_SYMLINK')
            a.output.parent.mkdir(parents=True,exist_ok=True)
            with a.output.open('xb') as f:f.write(canonical(probe_local_runtime())+b'\n')
            print(json.dumps({'status':'SNAPSHOT_ONLY_NOT_APPROVAL','output':str(a.output)}));return 0
        if not a.input or not a.trust_file:raise AudioError('ACOUSTIC_INPUT_AND_EXTERNAL_TRUST_REQUIRED')
        trust=strict_json(a.trust_file.read_text());validate_trust(trust)
        policy=AcousticPolicy(**strict_json(a.policy.read_text())) if a.policy else AcousticPolicy()
        mixed,sync,files=load_published_mix(a.input)
        if a.mode=='verify':
            if not a.evidence:raise AudioError('ACOUSTIC_EVIDENCE_REQUIRED')
            print(json.dumps(verify_publication(a.evidence,mixed,sync,trust,policy),indent=2));return 0
        if not a.allow_local_diagnostic:raise AudioError('ACOUSTIC_LOCAL_DIAGNOSTIC_OPT_IN_REQUIRED')
        if not a.output or not a.runtime or not a.private_key_file or not a.key_id:
            raise AudioError('ACOUSTIC_RUNTIME_SIGNER_AND_OUTPUT_REQUIRED')
        for candidate in (a.input,a.private_key_file,a.trust_file,a.runtime):
            if candidate.absolute().is_relative_to(a.output.absolute()) or a.output.absolute().is_relative_to(candidate.absolute()):
                raise AudioError('ACOUSTIC_OUTPUT_OVERLAPS_INPUT_OR_AUTHORITY')
        if a.output.exists() or any(x.is_symlink() for x in (a.output,*a.output.parents)):
            raise AudioError('ACOUSTIC_OUTPUT_EXISTS_OR_SYMLINK')
        runtime=strict_json(a.runtime.read_text());verify_runtime(runtime)
        signer=load_private_key(a.private_key_file)
        from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
        public=signer.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
        issuer=next((i for i in trust['issuers'] if i['key_id']==a.key_id),None)
        now=int(time.time())
        if (issuer is None or issuer['revoked'] or issuer['public_key_hex']!=public
            or runtime['fingerprint'] not in issuer['runtime_fingerprints']
            or not issuer['not_before']<=now<issuer['not_after']):
            raise AudioError('ACOUSTIC_SIGNER_NOT_EXTERNALLY_TRUSTED')
        job=build_job(mixed,sync,policy)
        receipt=issue_evaluation(job,mixed.wav_bytes,runtime,signer,a.key_id)
        stems=tuple(b for n,b in files.items() if n.startswith('inputs/') and n.endswith('.wav'))
        report,captions=audit_mix(mixed,sync,asset_wavs=stems,acoustic_receipt=receipt,
                                  evaluator_trust=trust,acoustic_policy=policy)
        publish_evaluation(mixed,sync,job,receipt,trust,report,captions,a.output)
        verify_publication(a.output,mixed,sync,trust,policy)
        print(json.dumps({'status':report['status'],'receipt_written':True,
                          'product_accepted':False,'section_exit_permitted':False},indent=2))
        return 3 if report['status']=='REVIEW' else 2
    except (ValueError,TypeError,KeyError,OSError,ImportError) as e:
        print(json.dumps({'status':'BLOCKED','error_code':getattr(e,'code','ACOUSTIC_SETUP_OR_INPUT_ERROR'),
                          'product_accepted':False}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
