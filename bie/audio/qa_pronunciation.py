"""QA-001 source-bound pronunciation review queue; no self-certified listening."""
from dataclasses import asdict,dataclass
from .common import AudioError,fingerprint,text,refs,digest
from .mix_pipeline import verify_mixed_source
from .qa_contract import Finding,check,TASKS

@dataclass(frozen=True)
class PronunciationObservation:
    target_fingerprint: str
    media_sha256: str
    observed_text: str
    verdict: str
    method: str
    reviewer_id: str
    evidence_refs: tuple[str,...]
    def __post_init__(self):
        digest(self.target_fingerprint)
        if len(self.media_sha256)!=64 or any(c not in '0123456789abcdef' for c in self.media_sha256): raise AudioError('QA_OBSERVATION_HASH')
        for k in ('observed_text','reviewer_id'):text(getattr(self,k),k)
        if self.verdict not in ('MATCH','MISMATCH','UNCERTAIN') or self.method not in ('human_reported','asr_reported','synthetic_test'): raise AudioError('QA_OBSERVATION_KIND')
        refs(self.evidence_refs,'observation evidence')

def pronunciation_targets(mixed,sync):
    verify_mixed_source(mixed,sync);c=mixed.clock();out=[]
    for asset in sync.assets:
        s=asset.request.segment
        for n,span in enumerate(s.spans):
            # Literal words need listening too; transformed spans add explicit reading obligations.
            words=[w for w in c['words'] if w['segment_id']==s.segment_id and any(v['start']<span.end and span.start<v['end'] for v in w['source'])]
            row={'segment_id':s.segment_id,'span_index':n,'start':span.start,'end':span.end,'display':span.original,
                 'expected_spoken':span.spoken,'language':span.language,'kind':span.kind,'source_refs':list(span.source_refs),
                 'rule_fingerprint':span.rule_fingerprint,'voice_fingerprint':asset.request.voice.fingerprint(),
                 'media_sha256':c['output_audio_sha256'],'phonemes':span.phonemes,
                 'start_sample':words[0]['start_sample'] if words else None,'end_sample':words[-1]['end_sample'] if words else None}
            row['target_fingerprint']=fingerprint(row);out.append(row)
    return out

def pronunciation_qa(mixed,sync,observations=()):
    targets=pronunciation_targets(mixed,sync);known={t['target_fingerprint']:t for t in targets};fs=[];seen=set()
    if type(observations)is not tuple or len(observations)>20000:raise AudioError('QA_OBSERVATION_LIST')
    for o in observations:
        if type(o)is not PronunciationObservation:raise AudioError('QA_OBSERVATION_TYPE')
        PronunciationObservation(**asdict(o))
        if o.target_fingerprint not in known or o.media_sha256!=mixed.clock()['output_audio_sha256'] or o.target_fingerprint in seen:
            raise AudioError('QA_OBSERVATION_STALE_OR_DUPLICATE')
        seen.add(o.target_fingerprint)
        if o.verdict=='MISMATCH':fs.append(Finding('REPORTED_MISPRONUNCIATION','FAIL','AUDIO/VO',o.target_fingerprint,'Reported mismatch requires resynthesis/review, not transcript replacement.',o.evidence_refs))
        else:fs.append(Finding('UNAUTHENTICATED_LISTENING_RECORD','REVIEW','AUDIO/QA',o.target_fingerprint,'A caller report or ASR transcript cannot establish phonetic correctness.',o.evidence_refs))
    for t in targets:
        if '\ufffd' in t['expected_spoken']:fs.append(Finding('REPLACEMENT_CHARACTER','FAIL','AUDIO/VO',t['target_fingerprint'],'Replacement character appears in spoken preparation.',tuple(t['source_refs'])))
    fs.append(Finding('INDEPENDENT_PRONUNCIATION_UNVERIFIED','REVIEW','AUDIO/QA','listening','No authenticated independent phonetic/listening validation is established by this component.'))
    if any(a.request.voice.quality_class=='technical_formant' for a in sync.assets):fs.append(Finding('TECHNICAL_VOICE_NOT_CINEMATIC','REVIEW','AUDIO/VO','voice','Technical formant speech is not the final cinematic voice.'))
    return check(TASKS[0],'Prepared readings and exact media/source binding, not acoustic acceptance',fs,
        {'targets':targets,'reported_observations':[asdict(o) for o in observations],'pronunciation_verified':False})
