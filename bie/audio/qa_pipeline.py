"""One AUDIO QA entry: actual source/MIX bytes -> five scoped checks -> findings.

A correct diagnostic can return REVIEW or FAIL. No self-graded release gate.
"""
from dataclasses import asdict
from pathlib import Path
import hashlib
from .common import AudioError,fingerprint
from .tts_contract import AudioFormat
from .qa_contract import TASKS,Finding,check,aggregate
from .qa_pronunciation import pronunciation_qa
from .qa_clipping import clipping_qa,ClippingPolicy
from .qa_missing_audio import missing_audio_qa
from .qa_sync import sync_qa
from .qa_accessibility import accessibility_qa,CaptionQAPolicy


def implementation_identity():
    root=Path(__file__).resolve().parent
    return fingerprint({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*.py'))})


def audit_mix(mixed,sync,*,asset_wavs=(),intent=None,observations=(),clipping_policy=ClippingPolicy(),caption_policy=CaptionQAPolicy(),meter=None,cancellation=None,acoustic_receipt=None,evaluator_trust=None,acoustic_policy=None,acoustic_now=None):
    c=mixed.clock();artifact=None;results=[]
    functions=(lambda:pronunciation_qa(mixed,sync,observations),
        lambda:clipping_qa(mixed.wav_bytes,AudioFormat(c['sample_rate'],c['channels']),clipping_policy,meter=meter,cancellation=cancellation),
        lambda:missing_audio_qa(mixed,sync,asset_wavs),lambda:sync_qa(mixed,sync),
        lambda:accessibility_qa(mixed,sync,intent,caption_policy))
    for task,fn in zip(TASKS,functions):
        if cancellation is not None and cancellation.is_set():raise AudioError('QA_CANCELLED')
        try:
            result=fn()
            if task==TASKS[4]:result,artifact=result
        except (AudioError,KeyError,TypeError,ValueError,OSError) as e:
            code=getattr(e,'code','QA_INVALID_INPUT')
            environmental=any(x in code for x in ('UNAVAILABLE','TIMEOUT','METER_PROCESS','METER_FAILED','CANCELLED'))
            result=check(task,'Check failed before complete evidence; see precise error',
                (Finding(code,'BLOCKED' if environmental else 'FAIL',task,'input',str(e)[:2048] or type(e).__name__),),executed=False)
        results.append(result)
    binding={'media_sha256':hashlib.sha256(mixed.wav_bytes).hexdigest(),'mix_receipt_fingerprint':fingerprint(mixed.receipt()),
             'clock_fingerprint':fingerprint(c),'source_sync_fingerprint':fingerprint(sync.receipt()),
             'qa_implementation_fingerprint':implementation_identity(),'clipping_policy':asdict(clipping_policy),'caption_policy':asdict(caption_policy),
             'caption_intent_fingerprint':fingerprint(intent),'observation_fingerprint':fingerprint(observations)}
    if acoustic_receipt is not None or evaluator_trust is not None or acoustic_policy is not None:
        if acoustic_receipt is None or evaluator_trust is None:
            raise AudioError('ACOUSTIC_RECEIPT_AND_TRUST_REQUIRED')
        from .acoustic_contract import AcousticPolicy
        from .acoustic_assessment import adopt_into_qa
        policy=AcousticPolicy() if acoustic_policy is None else acoustic_policy
        results,binding=adopt_into_qa(tuple(results),binding,mixed,sync,acoustic_receipt,
            evaluator_trust,policy,now=acoustic_now)
    return aggregate(tuple(results),binding),artifact
