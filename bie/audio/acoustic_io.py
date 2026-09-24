"""H2-005: exclusive local publication and re-verification, using existing QA IO."""
from pathlib import Path, PurePosixPath
import hashlib, os, shutil, tempfile
from .common import AudioError, strict_json, fingerprint
from .tts_cache import key_lock, read_regular
from .acoustic_contract import AcousticPolicy, build_job, canonical
from .acoustic_assessment import assess_receipt, verify_augmented_qa
from .acoustic_repair import plan_repairs
from .qa_io import publish_qa


def publish_evaluation(mixed,sync,job,receipt,trust,report,captions,destination,*,now=None):
    policy=AcousticPolicy(**job['policy'])
    current=build_job(mixed,sync,policy)
    if current!=job:raise AudioError('ACOUSTIC_PUBLICATION_JOB_CHANGED')
    verify_augmented_qa(report,mixed,sync,receipt,trust,policy,now=now)
    assessment=assess_receipt(receipt,job,trust,now=now)
    repairs=plan_repairs(job,receipt,trust,now=now)
    dest=Path(destination).absolute()
    if any(p.is_symlink() for p in (dest,*dest.parents)):raise AudioError('ACOUSTIC_OUTPUT_SYMLINK')
    if dest.exists():raise AudioError('ACOUSTIC_OUTPUT_EXISTS')
    dest.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.bie-acoustic-publish-',dir=dest.parent))
    os.chmod(tmp,0o700)
    try:
        data={'JOB.json':job,'EVALUATOR_RECEIPT.json':receipt,
              'MEASUREMENT.json':receipt['payload']['measurement'],
              'ASSESSMENT.json':assessment,'REPAIR_PLAN.json':repairs}
        for name,value in data.items():(tmp/name).write_bytes(canonical(value)+b'\n')
        publish_qa(report,captions,tmp/'qa')
        index={p.relative_to(tmp).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                'bytes':p.stat().st_size} for p in sorted(tmp.rglob('*')) if p.is_file()}
        (tmp/'OUTPUT_SHA256.json').write_bytes(canonical(index)+b'\n')
        lock=dest.parent/('.acoustic-publish-'+hashlib.sha256(str(dest).encode()).hexdigest()+'.lock')
        with key_lock(lock,timeout=30):
            if dest.exists() or dest.is_symlink():raise AudioError('ACOUSTIC_OUTPUT_EXISTS')
            os.rename(tmp,dest)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return index


def read_evaluation(folder):
    root=Path(folder).absolute()
    if any(p.is_symlink() for p in (root,*root.parents)) or not root.is_dir():raise AudioError('ACOUSTIC_INPUT_DIRECTORY')
    index=strict_json(read_regular(root/'OUTPUT_SHA256.json',4_000_000).decode())
    if type(index) is not dict or not index or len(index)>30:raise AudioError('ACOUSTIC_OUTPUT_MANIFEST')
    members={}
    for p in root.rglob('*'):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):raise AudioError('ACOUSTIC_OUTPUT_NONREGULAR')
        if p.is_file():members[p.relative_to(root).as_posix()]=p
    if set(members)!=set(index)|{'OUTPUT_SHA256.json'}:raise AudioError('ACOUSTIC_OUTPUT_FILE_SET')
    required={'JOB.json','EVALUATOR_RECEIPT.json','MEASUREMENT.json','ASSESSMENT.json','REPAIR_PLAN.json','qa/QA_REPORT.json','qa/OUTPUT_SHA256.json'}
    if not required<=set(index):raise AudioError('ACOUSTIC_OUTPUT_MISSING_EVIDENCE')
    files={};total=0
    for name,row in index.items():
        q=PurePosixPath(name)
        if q.is_absolute() or '\\' in name or any(x in ('','.','..') for x in name.split('/')):
            raise AudioError('ACOUSTIC_OUTPUT_UNSAFE_PATH')
        if type(row) is not dict or set(row)!={'sha256','bytes'} or type(row['bytes']) is not int or not 0<=row['bytes']<=8_000_000:
            raise AudioError('ACOUSTIC_OUTPUT_MANIFEST')
        total+=row['bytes']
        if total>40_000_000:raise AudioError('ACOUSTIC_OUTPUT_BUDGET')
        data=read_regular(root/name,row['bytes'])
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise AudioError('ACOUSTIC_OUTPUT_HASH_MISMATCH')
        files[name]=data
    return files


def verify_publication(folder,mixed,sync,trust,policy=AcousticPolicy(),*,now=None):
    files=read_evaluation(folder)
    data={k:strict_json(v.decode()) for k,v in files.items() if k.endswith('.json')}
    job=build_job(mixed,sync,policy)
    if data['JOB.json']!=job:raise AudioError('ACOUSTIC_PUBLICATION_STALE_JOB')
    receipt=data['EVALUATOR_RECEIPT.json']
    assessment=assess_receipt(receipt,job,trust,now=now)
    if data['MEASUREMENT.json']!=receipt['payload']['measurement'] or data['ASSESSMENT.json']!=assessment or data['REPAIR_PLAN.json']!=plan_repairs(job,receipt,trust,now=now):
        raise AudioError('ACOUSTIC_PUBLICATION_DERIVED_EVIDENCE_TAMPER')
    verify_augmented_qa(data['qa/QA_REPORT.json'],mixed,sync,receipt,trust,policy,now=now)
    caption_name='qa/ACCESSIBLE_CAPTIONS.json'
    if caption_name in data:
        from .qa_accessibility import export_accessible
        captions=data[caption_name]
        expected_fp=data['qa/QA_REPORT.json']['checks'][4]['metrics'].get('caption_artifact_fingerprint')
        if captions.get('fingerprint')!=expected_fp or captions.get('media_sha256')!=job['binding']['media_sha256']:
            raise AudioError('ACOUSTIC_CAPTION_BINDING_CHANGED')
        for ext in ('vtt','srt'):
            if files.get('qa/accessible.'+ext)!=export_accessible(captions,ext).encode():
                raise AudioError('ACOUSTIC_CAPTION_EXPORT_CHANGED')
    nested=data['qa/OUTPUT_SHA256.json']
    expected={n.removeprefix('qa/'): {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in files.items() if n.startswith('qa/') and n!='qa/OUTPUT_SHA256.json'}
    if nested!=expected:raise AudioError('ACOUSTIC_NESTED_QA_MANIFEST')
    return {'passed':True,'scope':'Current-media local diagnostic signature and publication verification',
            'job_fingerprint':job['fingerprint'],'receipt_fingerprint':fingerprint(receipt),'product_accepted':False}
