"""Source-exact AUDIO -> existing DIR reported-timing handoff.

DIR deliberately retains its REPORTED_ALIGNMENT review semantics. A single
unchanged whole utterance can be transferred; expansions/chunks are not lied
about as identical spoken words. Richer cross-profile handoff stays in AUDIO.
"""
from .common import AudioError
from .sync_contract import validate_alignment
from bie.director.speech_timing import ReportedAlignment,align_reported_speech
from bie.director.timing_contract import spoken_words


def to_dir_timing(utterance,asset,alignment,*,require_measured=True):
    validate_alignment(asset,alignment,require_measured=require_measured);s=asset.request.segment
    if (s.utterance_fingerprint!=utterance.fingerprint() or s.utterance_id!=utterance.utterance_id
        or s.start!=0 or s.end!=len(utterance.text) or s.spoken_text!=utterance.text):
        raise AudioError('DIR_EXACT_UTTERANCE_REQUIRED','Transformed/chunked speech must retain the AUDIO source map')
    tokens=spoken_words(utterance.text)
    if tuple((w.start_char,w.end_char,w.text) for w in tokens)!=tuple((w.spoken_start,w.spoken_end,w.spoken) for w in alignment.words):
        raise AudioError('DIR_TOKENIZER_CONTRACT_MISMATCH')
    rate=alignment.sample_rate
    intervals=tuple(((w.start_sample*1000+rate//2)//rate,(w.end_sample*1000+rate//2)//rate) for w in alignment.words)
    duration=(alignment.total_samples*1000+rate-1)//rate
    record=ReportedAlignment(utterance.fingerprint(),'sha256:'+asset.info.sha256,duration,intervals,
        'bie.audio.sync001/'+alignment.producer_fingerprint)
    return align_reported_speech((utterance,),(record,))
