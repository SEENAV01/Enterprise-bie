"""H4-R1-005: exclusive kernel-evidence publication, independently reverified.

An export is a local diagnostic, not a canonical application release. Its v2
receipt must pass before the inherited acoustic/QA export is considered usable.
"""
from __future__ import annotations
from pathlib import Path, PurePosixPath
import hashlib
import os
import shutil
import tempfile
from .common import AudioError, strict_json
from .acoustic_contract import AcousticPolicy, build_job, canonical, fields, plain
from .acoustic_io import publish_evaluation, verify_publication
from .durable_contract import validate_request
from .kernel_evidence import verify_kernel_receipt
from .kernel_profile import validate_profile, KERNEL_SCOPE
from .tts_cache import key_lock, read_regular


def read_kernel_publication(folder):
    root=Path(folder).absolute()
    if any(p.is_symlink() for p in (root,*root.parents)) or not root.is_dir():
        raise AudioError('KERNEL_PUBLICATION_DIRECTORY')
    index=strict_json(read_regular(root/'KERNEL_OUTPUT_SHA256.json',1_000_000).decode())
    if type(index) is not dict or not 1 <= len(index) <= 40:
        raise AudioError('KERNEL_PUBLICATION_MANIFEST')
    actual={}
    for p in root.rglob('*'):
        if p.is_symlink() or not (p.is_dir() or p.is_file()):
            raise AudioError('KERNEL_PUBLICATION_NONREGULAR')
        if p.is_file():
            if p.stat().st_nlink != 1:
                raise AudioError('KERNEL_PUBLICATION_HARDLINK')
            actual[p.relative_to(root).as_posix()]=p
    if set(actual)!=set(index)|{'KERNEL_OUTPUT_SHA256.json'}:
        raise AudioError('KERNEL_PUBLICATION_FILE_SET')
    if not {'KERNEL_RECEIPT.json','KERNEL_PROFILE.json','REQUEST.json','acoustic/OUTPUT_SHA256.json'} <= set(index):
        raise AudioError('KERNEL_PUBLICATION_MISSING_EVIDENCE')
    out={};total=0
    for name,row in index.items():
        if (type(name) is not str or '\\' in name or PurePosixPath(name).is_absolute()
            or any(s in ('','.','..') for s in name.split('/'))):
            raise AudioError('KERNEL_PUBLICATION_UNSAFE_PATH')
        fields(row,('bytes','sha256'),'KERNEL_PUBLICATION_ROW')
        if type(row['bytes']) is not int or not 0 <= row['bytes'] <= 8_000_000:
            raise AudioError('KERNEL_PUBLICATION_BUDGET')
        total+=row['bytes']
        if total>40_000_000:
            raise AudioError('KERNEL_PUBLICATION_BUDGET')
        data=read_regular(root/name,row['bytes'])
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise AudioError('KERNEL_PUBLICATION_HASH_MISMATCH')
        out[name]=data
    return out


def verify_kernel_publication(folder,mixed,sync,runtime,profile,trust,*,now=None):
    validate_profile(profile,runtime)
    files=read_kernel_publication(folder)
    request=strict_json(files['REQUEST.json'].decode())
    receipt=strict_json(files['KERNEL_RECEIPT.json'].decode())
    validate_request(request,mixed.wav_bytes)
    job=build_job(mixed,sync,AcousticPolicy(**request['job']['policy']))
    if (request['job']!=job or request['runtime_fingerprint']!=runtime['fingerprint']
        or strict_json(files['KERNEL_PROFILE.json'].decode())!=profile):
        raise AudioError('KERNEL_PUBLICATION_BINDING')
    if receipt.get('payload',{}).get('key_id')!=request['key_id']:
        raise AudioError('KERNEL_PUBLICATION_ISSUER_BINDING')
    verify_kernel_receipt(receipt,job,runtime,profile,trust,now=now,
        request_fingerprint=request['fingerprint'])
    inner=strict_json(files['acoustic/EVALUATOR_RECEIPT.json'].decode())
    if inner!=receipt['payload']['compatibility_receipt']:
        raise AudioError('KERNEL_PUBLICATION_INNER_RECEIPT')
    result=verify_publication(Path(folder)/'acoustic',mixed,sync,trust['evaluator_trust'],
        AcousticPolicy(**job['policy']),now=now)
    return {'verified':True,'scope':KERNEL_SCOPE,'kernel_signature_reverified':True,
        'profile_fingerprint':profile['fingerprint'],'media_sha256':job['binding']['media_sha256'],
        'acoustic_verification':result,'product_accepted':False}


def publish_kernel_evaluation(result,mixed,sync,runtime,profile,trust,report,captions,destination,*,now=None):
    result,runtime,profile,trust=map(plain,(result,runtime,profile,trust))
    receipt=result['kernel_receipt'];request=result['request']
    validate_profile(profile,runtime);validate_request(request,mixed.wav_bytes)
    verify_kernel_receipt(receipt,request['job'],runtime,profile,trust,now=now,
        request_fingerprint=request['fingerprint'])
    if receipt['payload']['compatibility_receipt']!=result['receipt']:
        raise AudioError('KERNEL_PUBLICATION_INNER_RECEIPT')
    dest=Path(destination).absolute()
    if any(p.is_symlink() for p in (dest,*dest.parents)):
        raise AudioError('KERNEL_PUBLICATION_SYMLINK')
    if dest.exists():raise AudioError('KERNEL_PUBLICATION_EXISTS')
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.bie-kernel-publish-',dir=dest.parent))
    try:
        publish_evaluation(mixed,sync,request['job'],result['receipt'],trust['evaluator_trust'],
            report,captions,tmp/'acoustic',now=now)
        # Inherited publication's parent-side lock is not part of this export.
        for lock in tmp.glob('.acoustic-publish-*.lock'):
            lock.unlink()
        for name,value in (('KERNEL_RECEIPT.json',receipt),('KERNEL_PROFILE.json',profile),('REQUEST.json',request)):
            (tmp/name).write_bytes(canonical(value)+b'\n')
        index={p.relative_to(tmp).as_posix():{'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(tmp.rglob('*')) if p.is_file()}
        (tmp/'KERNEL_OUTPUT_SHA256.json').write_bytes(canonical(index)+b'\n')
        # Verify content before the atomic directory commit, not after promotion.
        verify_kernel_publication(tmp,mixed,sync,runtime,profile,trust,now=now)
        lock=dest.parent/('.kernel-publish-'+hashlib.sha256(str(dest).encode()).hexdigest()+'.lock')
        with key_lock(lock,timeout=30):
            if dest.exists() or dest.is_symlink():raise AudioError('KERNEL_PUBLICATION_EXISTS')
            os.rename(tmp,dest)
        return index
    finally:
        if tmp.exists():shutil.rmtree(tmp)


def audit_kernel_mix(mixed,sync,*,asset_wavs=(),caption_intent=None,output=None,**options):
    from .kernel_durable import evaluate_kernel_durable
    from .qa_pipeline import audit_mix
    result=evaluate_kernel_durable(mixed,sync,**options)
    report,captions=audit_mix(mixed,sync,asset_wavs=asset_wavs,intent=caption_intent,
        acoustic_receipt=result['receipt'],evaluator_trust=options['trust']['evaluator_trust'],
        acoustic_policy=options.get('policy',AcousticPolicy()))
    if output is not None:
        publish_kernel_evaluation(result,mixed,sync,options['runtime'],options['profile'],
            options['trust'],report,captions,output)
    return result,report,captions
