"""Exclusive QA diagnostic output; never overwrites the source MIX directory."""
from pathlib import Path
import hashlib,json,os,shutil,tempfile
from .common import AudioError
from .tts_cache import key_lock
from .qa_contract import validate_report
from .qa_accessibility import export_accessible


def publish_qa(report,captions,destination):
    validate_report(report);dest=Path(destination).absolute()
    if any(p.is_symlink() for p in (dest,*dest.parents)):raise AudioError('QA_OUTPUT_SYMLINK')
    if dest.exists():raise AudioError('QA_OUTPUT_EXISTS')
    dest.parent.mkdir(parents=True,exist_ok=True)
    data={'QA_REPORT.json':(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()}
    if captions is not None:
        if captions['media_sha256']!=report['binding']['media_sha256']:raise AudioError('QA_CAPTION_REPORT_BINDING')
        expected=report['checks'][4]['metrics'].get('caption_artifact_fingerprint')
        if expected!=captions['fingerprint']:raise AudioError('QA_CAPTION_REPORT_BINDING')
        data.update({'ACCESSIBLE_CAPTIONS.json':(json.dumps(captions,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode(),
            'accessible.vtt':export_accessible(captions,'vtt').encode(),'accessible.srt':export_accessible(captions,'srt').encode()})
    index={n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in data.items()}
    data['OUTPUT_SHA256.json']=(json.dumps(index,sort_keys=True,indent=2)+'\n').encode();tmp=Path(tempfile.mkdtemp(prefix='.bie-qa-',dir=dest.parent))
    try:
        for n,b in data.items():(tmp/n).write_bytes(b)
        lock=dest.parent/('.qa-publish-'+hashlib.sha256(str(dest).encode()).hexdigest()+'.lock')
        with key_lock(lock,timeout=30):
            if dest.exists() or dest.is_symlink():raise AudioError('QA_OUTPUT_EXISTS')
            os.rename(tmp,dest)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return index
