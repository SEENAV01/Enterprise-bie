"""H2-001: immutable evaluation requests from verified existing MIX/SYNC records.

Independent measurements do not overwrite provider clocks. Unicode offsets and
pronunciation source bindings stay in the existing canonical fingerprint scheme.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, io, json, re, wave
from .common import AudioError, digest, fingerprint, integer, text, strict_json

SCHEMA = 'bie.audio.acoustic-job/1'
RESULT_SCHEMA = 'bie.audio.acoustic-measurement/1'
SCOPE = 'LOCAL_INDEPENDENT_DIAGNOSTIC'
ENGINE = 'pocketsphinx-legacy-fsg-allphone-lm/1'
BOUNDARIES = {'pronunciation_verified': False, 'alignment_accepted': False,
              'product_accepted': False, 'calibration_status': 'NOT_ESTABLISHED'}


def canonical(value: object) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise AudioError('ACOUSTIC_JSON_INVALID') from exc


def plain(value):
    return strict_json(canonical(value).decode())


def fields(value, expected, code='ACOUSTIC_FIELDS'):
    if type(value) is not dict or set(value) != set(expected):
        raise AudioError(code)


def sha(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise AudioError('ACOUSTIC_SHA256')
    return value


@dataclass(frozen=True)
class AcousticPolicy:
    revision: str = 'audio-h2-diagnostic-v1'
    max_segments: int = 32
    max_segment_seconds: int = 60
    max_total_seconds: int = 180
    max_words_per_segment: int = 256
    max_source_bytes: int = 70_000_000
    deadline_seconds: int = 180
    disagreement_ms: int = 150
    # This is a triage threshold, NOT a calibrated pronunciation classifier.
    max_phone_edit_percent: int = 45
    def __post_init__(self):
        text(self.revision, 'acoustic policy revision', 160)
        for k, lo, hi in [('max_segments',1,128), ('max_segment_seconds',1,60),
                         ('max_total_seconds',1,300), ('max_words_per_segment',1,512),
                         ('max_source_bytes',1024,100_000_000), ('deadline_seconds',1,300),
                         ('disagreement_ms',10,2000), ('max_phone_edit_percent',0,100)]:
            integer(getattr(self,k), k, lo, hi)
    def fingerprint(self):
        return fingerprint(asdict(self))


def pcm_info(data: bytes, policy: AcousticPolicy):
    if type(data) is not bytes or not 44 <= len(data) <= policy.max_source_bytes:
        raise AudioError('ACOUSTIC_MEDIA_BUDGET')
    # Disallow trailing bytes and files with inconsistent RIFF envelopes.
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE' or int.from_bytes(data[4:8],'little')+8 != len(data):
        raise AudioError('ACOUSTIC_WAV_ENVELOPE')
    try:
        with wave.open(io.BytesIO(data), 'rb') as w:
            rate, ch, width, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
            if w.getcomptype() != 'NONE' or width != 2 or ch not in (1,2) or not 8000 <= rate <= 96000:
                raise AudioError('ACOUSTIC_PCM16_REQUIRED')
            if n <= 0 or n > rate * policy.max_total_seconds:
                raise AudioError('ACOUSTIC_DURATION_BUDGET')
            pcm=w.readframes(n)
            if len(pcm) != n*ch*2:
                raise AudioError('ACOUSTIC_TRUNCATED_WAV')
    except (wave.Error, EOFError) as exc:
        raise AudioError('ACOUSTIC_INVALID_WAV') from exc
    return {'sample_rate':rate, 'channels':ch, 'frames':n,
            'media_sha256':hashlib.sha256(data).hexdigest()}, pcm


def validate_job(job, wav: bytes | None = None):
    fields(job, ('schema_version','binding','policy','segments','fingerprint'))
    if job['schema_version'] != SCHEMA:
        raise AudioError('ACOUSTIC_JOB_VERSION')
    policy=AcousticPolicy(**job['policy'])
    fields(job['binding'], ('media_sha256','sample_rate','channels','frames',
        'mix_receipt_fingerprint','clock_fingerprint','source_sync_fingerprint',
        'plan_fingerprint','pronunciation_targets_fingerprint'))
    b=job['binding'];sha(b['media_sha256'])
    for key in ('mix_receipt_fingerprint','clock_fingerprint','source_sync_fingerprint',
                'plan_fingerprint','pronunciation_targets_fingerprint'):
        digest(b[key])
    integer(b['sample_rate'],'rate',8000,96000);integer(b['channels'],'channels',1,2)
    integer(b['frames'],'frames',1,b['sample_rate']*policy.max_total_seconds)
    if type(job['segments']) is not list or not 1 <= len(job['segments']) <= policy.max_segments:
        raise AudioError('ACOUSTIC_SEGMENT_BUDGET')
    seen=set();end=-1;all_words=0
    for s in job['segments']:
        fields(s, ('segment_id','request_fingerprint','voice_fingerprint','producer_id',
             'start_sample','end_sample','spoken_text','languages','source_spans',
             'provider_words','timing_basis','segment_fingerprint','dry_source_media_sha256','dry_source_has_signal'))
        text(s['segment_id'],'segment',512)
        if s['segment_id'] in seen:
            raise AudioError('ACOUSTIC_DUPLICATE_SEGMENT')
        seen.add(s['segment_id'])
        sha(s['dry_source_media_sha256'])
        if type(s['dry_source_has_signal']) is not bool:raise AudioError('ACOUSTIC_DRY_SOURCE_SIGNAL_TYPE')
        for key in ('request_fingerprint','voice_fingerprint','segment_fingerprint'):
            digest(s[key])
        text(s['producer_id'],'producer',256);text(s['timing_basis'],'timing basis',160)
        if 'pocketsphinx' in s['producer_id'].lower():
            raise AudioError('ACOUSTIC_EVALUATOR_NOT_INDEPENDENT')
        text(s['spoken_text'],'spoken',16384)
        integer(s['start_sample'],'start',0,b['frames']-1)
        integer(s['end_sample'],'end',s['start_sample']+1,b['frames'])
        if s['start_sample'] < end or s['end_sample']-s['start_sample'] > b['sample_rate']*policy.max_segment_seconds:
            raise AudioError('ACOUSTIC_SEGMENT_RANGE')
        end=s['end_sample']
        if type(s['languages']) is not list or not s['languages'] or len(set(s['languages'])) != len(s['languages']):
            raise AudioError('ACOUSTIC_LANGUAGES')
        for language in s['languages']:text(language,'language',64)
        if type(s['source_spans']) is not list or not s['source_spans']:
            raise AudioError('ACOUSTIC_SOURCE_REQUIRED')
        source=''
        for span in s['source_spans']:
            if type(span) is not dict or not {'spoken','original','start','end','source_refs','rule_fingerprint'} <= set(span):
                raise AudioError('ACOUSTIC_SOURCE_SPAN')
            text(span['spoken'],'span spoken');source+=span['spoken']
            digest(span['rule_fingerprint'])
            if type(span['source_refs']) is not list or not span['source_refs']:
                raise AudioError('ACOUSTIC_SOURCE_REFS')
            for ref in span['source_refs']:text(ref,'source reference',2048)
            integer(span['start'],'source start');integer(span['end'],'source end',span['start']+1)
            if span['end']-span['start'] != len(span['original']):
                raise AudioError('ACOUSTIC_SOURCE_RANGE')
        if source != s['spoken_text']:
            raise AudioError('ACOUSTIC_PREPARED_TEXT_CHANGED')
        if type(s['provider_words']) is not list or not s['provider_words'] or len(s['provider_words'])>policy.max_words_per_segment:
            raise AudioError('ACOUSTIC_WORD_BUDGET')
        last=-1
        for word in s['provider_words']:
            if type(word) is not dict or not {'spoken','spoken_start','spoken_end','start_sample','end_sample','source'} <= set(word):
                raise AudioError('ACOUSTIC_PROVIDER_WORD')
            integer(word['spoken_start'],'spoken start',0,len(source)-1)
            integer(word['spoken_end'],'spoken end',word['spoken_start']+1,len(source))
            if source[word['spoken_start']:word['spoken_end']] != word['spoken']:
                raise AudioError('ACOUSTIC_WORD_TEXT_CHANGED')
            integer(word['start_sample'],'word start',s['start_sample'],s['end_sample']-1)
            integer(word['end_sample'],'word end',word['start_sample']+1,s['end_sample'])
            if word['start_sample']<last:raise AudioError('ACOUSTIC_WORD_ORDER')
            last=word['end_sample']
        all_words+=len(s['provider_words'])
    body={k:v for k,v in job.items() if k!='fingerprint'}
    if fingerprint(body) != job['fingerprint']:
        raise AudioError('ACOUSTIC_JOB_TAMPER')
    if len(canonical(job))>4_000_000:
        raise AudioError('ACOUSTIC_JOB_BUDGET')
    if wav is not None:
        info,_=pcm_info(wav,policy)
        if any(info[k]!=b[k] for k in info):
            raise AudioError('ACOUSTIC_MEDIA_BINDING')
    return policy


def build_job(mixed, sync, policy=AcousticPolicy()):
    from .mix_pipeline import verify_mixed_source
    from .qa_pronunciation import pronunciation_targets
    if type(policy) is not AcousticPolicy:raise AudioError('ACOUSTIC_POLICY_TYPE')
    verify_mixed_source(mixed,sync)
    info,_=pcm_info(mixed.wav_bytes,policy);clock=mixed.clock();segments=[]
    by_id={s['segment_id']:s for s in clock['segments']}
    for asset,alignment in zip(sync.assets,sync.alignments):
        s=asset.request.segment;c=by_id[s.segment_id]
        dry_info,dry_pcm=pcm_info(asset.wav_bytes,policy)
        segments.append({'segment_id':s.segment_id,
            'request_fingerprint':asset.request.fingerprint(),
            'voice_fingerprint':asset.request.voice.fingerprint(),
            'producer_id':asset.request.voice.provider_id,
            'start_sample':c['start_sample'],'end_sample':c['end_sample'],
            'spoken_text':s.spoken_text,'languages':list(s.languages),
            'source_spans':plain([asdict(x) for x in s.spans]),
            'provider_words':plain([w for w in clock['words'] if w['segment_id']==s.segment_id]),
            'timing_basis':alignment.basis,'segment_fingerprint':s.fingerprint(),
            'dry_source_media_sha256':dry_info['media_sha256'],'dry_source_has_signal':bool(any(dry_pcm))})
    job={'schema_version':SCHEMA, 'binding':{**info,
         'mix_receipt_fingerprint':fingerprint(mixed.receipt()),
         'clock_fingerprint':fingerprint(clock), 'source_sync_fingerprint':fingerprint(sync.receipt()),
         'plan_fingerprint':sync.plan.fingerprint(),
         'pronunciation_targets_fingerprint':fingerprint(pronunciation_targets(mixed,sync))},
         'policy':asdict(policy),'segments':segments}
    job['fingerprint']=fingerprint(job);validate_job(job,mixed.wav_bytes)
    return plain(job)


def english_tokens(value):
    """Evaluation-only map. Never normalizes or rewrites prepared/source narration."""
    matches=list(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)*",value))
    covered={i for m in matches for i in range(m.start(),m.end())}
    # Reject unprepared numerals, symbols and foreign script, not silently discard.
    if any(i not in covered and not (ch.isspace() or ch in '.,;:!?-()\"') for i,ch in enumerate(value)):
        raise AudioError('ACOUSTIC_TOKENIZATION_UNSUPPORTED')
    if not matches:raise AudioError('ACOUSTIC_NO_LEXICAL_TOKENS')
    return [{'word':m.group().lower(),'spoken_start':m.start(),'spoken_end':m.end()} for m in matches]


def edit_distance(a,b):
    if len(a)>4096 or len(b)>4096 or len(a)*len(b)>2_000_000:
        raise AudioError('ACOUSTIC_EDIT_BUDGET')
    row=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        new=[i]
        for j,y in enumerate(b,1):new.append(min(row[j]+1,new[-1]+1,row[j-1]+(x!=y)))
        row=new
    return row[-1]
