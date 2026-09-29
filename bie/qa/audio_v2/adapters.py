"""Inspection-only adapter for the pinned native AlignedSpeech.receipt() shape.

Native source ranges, engine metadata and fingerprints are not promoted to
independent acoustic truth. Caller must validate native assets before exporting;
this adapter additionally demands original approved spoken text and PCM identity.
No native module is overwritten, copied incompletely or reclassified as executed.
"""
import hashlib
from ..release_v2.contracts import ContractError
from .models import TimingReceipt,Word

def from_native_alignment(receipt,*,clip_id,spoken_text,audio_sha256):
    if type(receipt) is not dict or receipt.get('schema_version')!='bie.audio.word-timing/1':raise ContractError('AUDIO_NATIVE_SCHEMA')
    if receipt.get('media_sha256')!=audio_sha256:raise ContractError('AUDIO_NATIVE_MEDIA_BINDING')
    for f in ('acoustic_alignment_verified','pronunciation_verified','product_accepted'):
        if receipt.get(f) is not False:raise ContractError('AUDIO_NATIVE_UNSUPPORTED_ACCEPTANCE')
    basis=receipt.get('basis')
    bases={'ESPEAK_ENGINE_EVENTS_PCM_REPLAY':'engine_events','ESPEAK_MARK_EVENTS_SAME_PCM':'engine_events','ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE':'engine_events','NEURAL_CHARACTER_FIXTURE_SAME_PCM':'synthetic','SYNTHETIC_TEST_DOUBLE':'synthetic','REPORTED_UNVERIFIED':'reported'}
    if basis not in bases:raise ContractError('AUDIO_NATIVE_TIMING_BASIS')
    words=receipt.get('words')
    if type(words) is not list or not 1<=len(words)<=8192:raise ContractError('AUDIO_NATIVE_WORD_COLLECTION')
    out=[]
    for w in words:
        if type(w) is not dict:raise ContractError('AUDIO_NATIVE_WORD_TYPE')
        try:a=Word(w['index'],w['spoken_start'],w['spoken_end'],w['spoken'],w['start_sample'],w['end_sample'])
        except (KeyError,TypeError) as exc:raise ContractError('AUDIO_NATIVE_WORD_FIELDS') from exc
        if spoken_text[a.start_char:a.end_char]!=a.text:raise ContractError('AUDIO_NATIVE_TEXT_MAPPING')
        out.append(a)
    provider=receipt.get('provider_samples');pause=receipt.get('pause_samples')
    if type(provider) is not int or type(pause) is not int or provider<=0 or pause<0:raise ContractError('AUDIO_NATIVE_SAMPLE_COUNT')
    if any(w.end_sample>provider for w in out):raise ContractError('AUDIO_NATIVE_PROVIDER_BOUNDS')
    return TimingReceipt('bie.qa.audio-timing/1',clip_id,audio_sha256,hashlib.sha256(spoken_text.encode()).hexdigest(),receipt.get('sample_rate'),provider+pause,'native-audio-adapter',bases[basis],tuple(out))
