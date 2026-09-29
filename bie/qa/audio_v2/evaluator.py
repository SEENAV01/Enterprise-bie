"""Evaluate actual PCM/caption bytes and authenticated timing/pronunciation records.

A decoded waveform proves neither that words were spoken nor that they were
pronounced correctly. Reported/engine-event times never become acoustic proof.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from fractions import Fraction
import hashlib,unicodedata
from ..release_v2.contracts import ContractError,digest,integer
from ..source_v2.evaluator import evaluate as evaluate_source,EvaluationPair
from ..source_v2.models import Finding,Report
from ..source_v2.io import SnapshotStore
from .models import AudioRequest,AudioPolicy,TimingReceipt,PronunciationReceipt
from .codec import decode,loads
from .pcm import read_pcm
from .captions import parse_captions,normalized
from .attestation import Review,ReviewVerifier,review_targets

AREAS=('sync','captions','pronunciation')
TASKS=dict(zip(AREAS,('BIE-QA-AUDIO-001','BIE-QA-AUDIO-002','BIE-QA-AUDIO-003')))
LIMITATIONS=(
 'PCM16 mono/stereo sample measurements and approved placement/cue checks; not final mux, live playback, music masking, native Remotion/game or complete audiovisual alignment.',
 'Engine times are display/source boundaries, not independently measured phonetic offsets. Silence and clipping diagnostics do not certify speech intelligibility.',
 'Plain-text SRT/WebVTT caption records, not rendered caption geometry or actual player behavior. Code-point rate limits are operator guardrails, not universal multilingual readability thresholds.',
 'Pronunciation requires authorized acoustic/listening observations for every operator-listed occurrence. Transcript match, lexicon intent or TTS success is not phonetic proof.',
 'Authentication proves provisioned reviewer identity, not correctness, independence in practice or calibration. No product acceptance or full-media gate PASS.')

@dataclass(frozen=True,slots=True)
class AudioResult:
    source:EvaluationPair
    sync:Report
    captions:Report
    pronunciation:Report
    measured_clip_ids:tuple[str,...]
    @property
    def status(self):
        ss=[self.source.grounding.status,self.source.provenance.status]+[getattr(self,k).status for k in AREAS]
        return 'BLOCKED' if 'BLOCKED' in ss else 'REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in ss else 'CHECKS_PASSED'
    @property
    def product_accepted(self):return False
    def to_dict(self):return dict(source=self.source.to_dict(),**{k:getattr(self,k).to_dict() for k in AREAS},measured_clip_ids=self.measured_clip_ids,status=self.status,product_accepted=False,complete_media_verified=False)
    @property
    def content_digest(self):return digest(self.to_dict())

def evaluate(request,artifact_root,policy,*,as_of,reviews=(),verifier=None,source_assessments=(),source_verifier=None):
    if type(request) is not AudioRequest or type(policy) is not AudioPolicy:raise ContractError('AUDIO_EVALUATION_TYPE')
    integer(as_of,'as_of')
    if type(reviews) is not tuple or len(reviews)>4096 or any(type(r) is not Review for r in reviews):raise ContractError('AUDIO_REVIEW_COLLECTION')
    if len({r.review_id for r in reviews})!=len(reviews) or len({(r.purpose,r.subject_id,r.evaluator_id) for r in reviews})!=len(reviews):raise ContractError('AUDIO_DUPLICATE_REVIEW')
    verifier=ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier:raise ContractError('AUDIO_VERIFIER_TYPE')
    source=evaluate_source(request.source,artifact_root,policy.source,as_of=as_of,assessments=source_assessments,verifier=source_verifier)
    groups={k:[] for k in ('common',)+AREAS};groups['common'].extend(source.grounding.findings+source.provenance.findings)
    def add(k,code,subject,detail,severity='BLOCKER'):groups[k].append(Finding(code,severity,subject,'AUDIO',detail))
    targets=review_targets(request,policy);votes={};tainted=set()
    for r in reviews:
        t=(r.purpose,r.subject_id)
        if t not in targets:add('common','AUDIO_UNKNOWN_REVIEW_TARGET',r.subject_id,'Review target is not in approved scope.');continue
        if set(r.evidence_ids)!=set(targets[t]):add('common','AUDIO_REVIEW_EVIDENCE_MISMATCH',r.subject_id,'Exact inspected evidence identities required.');tainted.add(t);continue
        a=verifier.verify_bound(r,request.content_digest,policy.content_digest,policy.max_receipt_age_seconds,as_of)
        if not a.authenticated:add('common','AUDIO_'+a.code,r.subject_id,'Review authentication failed.');tainted.add(t)
        elif not a.operational:add('common','AUDIO_TEST_ONLY_REVIEW',r.subject_id,'Test-only keys cannot establish operational review.','REVIEW');tainted.add(t)
        elif r.verdict=='REJECTED':add('common','AUDIO_REVIEW_REJECTED',r.subject_id,'An authenticated rejection cannot be outvoted.');tainted.add(t)
        elif r.verdict!='VERIFIED' or r.confidence_ppm<policy.minimum_review_confidence_ppm:add('common','AUDIO_REVIEW_UNCERTAIN',r.subject_id,'Assessment is uncertain or below threshold.','REVIEW');tainted.add(t)
        else:votes.setdefault(t,set()).add(a.independence_group)
    for t in sorted(targets):
        if t in tainted or len(votes.get(t,()))<policy.minimum_independent_assessors:add('common','AUDIO_REVIEW_MISSING',t[1],'Current, scoped and authorized review required.','REVIEW')
    if request.lesson_id!=policy.lesson_id:add('common','AUDIO_LESSON_SCOPE','audio-scope','Lesson identity is operator-controlled.')
    ns={n.clip_id:n for n in policy.narrations};clips={c.clip_id:c for c in request.clips}
    if set(ns)!=set(clips):add('common','AUDIO_CLIP_INVENTORY','audio-scope','Missing or added narration cannot change approved coverage.')
    expected=set().union(*(set(n.claim_ids) for n in policy.narrations))
    if expected!={c.claim_id for c in request.source.claims}:add('common','AUDIO_CLAIM_COVERAGE','audio-scope','Narration must account for every source/output claim.')
    inspected=set(source.provenance.inspected_artifact_ids)|set(source.grounding.inspected_artifact_ids)
    measured={};timings={};pstats={};caption_count=0;pron_count=0;intervals=[]
    with SnapshotStore(artifact_root) as store:
        for c in request.clips:
            n=ns.get(c.clip_id)
            if n is None:continue
            if (c.language,c.voice_id)!=(n.language,n.voice_id):add('sync','AUDIO_VOICE_OR_LANGUAGE',c.clip_id,'Required language and voice were changed.')
            if abs(c.start_ms-n.start_ms)>policy.placement_tolerance_ms:add('sync','AUDIO_PLACEMENT',c.clip_id,'Audio placement differs from approved timeline.')
            try:
                pcm=read_pcm(store.read(c.wav));inspected.add(c.wav.artifact_id);measured[c.clip_id]=pcm;pstats[c.clip_id]=pcm.stats()
            except ContractError as exc:add('common',exc.code,c.clip_id,'Audio bytes cannot be verified/decoded.');continue
            st=pstats[c.clip_id]
            if pcm.sample_rate!=n.sample_rate:add('sync','AUDIO_SAMPLE_RATE',c.clip_id,'Actual rate differs from approved clock.')
            if Fraction(c.start_ms)+pcm.duration_ms>n.end_ms+policy.placement_tolerance_ms:add('sync','AUDIO_SLOT_OVERFLOW',c.clip_id,'Decoded PCM extends past its approved slot.')
            intervals.append((Fraction(c.start_ms),Fraction(c.start_ms)+pcm.duration_ms,c.clip_id))
            if st['nonzero']==0:add('common','AUDIO_SILENT_CLIP',c.clip_id,'Decoded clip contains no nonzero PCM signal.')
            if st['clipped']*1000000>policy.max_clipped_ppm*st['values']:add('sync','AUDIO_CLIPPING',c.clip_id,'PCM full-scale sample fraction exceeds operator threshold.')
            try:
                raw=store.read(c.timing);inspected.add(c.timing.artifact_id);t=decode(loads(raw),TimingReceipt)
            except ContractError as exc:add('common',exc.code,c.clip_id,'Timing receipt cannot be verified/decoded.');continue
            transcript_sha=hashlib.sha256(n.spoken_text.encode()).hexdigest()
            if (t.clip_id,t.audio_sha256,t.transcript_sha256,t.sample_rate,t.samples)!=(c.clip_id,c.wav.sha256,transcript_sha,pcm.sample_rate,pcm.samples):add('common','AUDIO_TIMING_BINDING',c.clip_id,'Receipt is not bound to exact PCM/transcript/clock.');continue
            timings[c.clip_id]=t
            if t.basis not in ('forced_alignment','human_alignment'):add('common','AUDIO_ACOUSTIC_ALIGNMENT_UNPROVEN',c.clip_id,'Reported or engine boundaries are not independent acoustic alignment.','REVIEW')
            covered=set()
            for w in t.words:
                if n.spoken_text[w.start_char:w.end_char]!=w.text:add('common','AUDIO_WORD_TEXT_MISMATCH',c.clip_id,'Timed text does not match approved narration.')
                covered.update(range(w.start_char,w.end_char))
                if not pcm.has_signal(w.start_sample,w.end_sample):add('sync','AUDIO_SILENT_WORD_WINDOW',c.clip_id,'A declared spoken interval is entirely zero PCM.')
            if any(not ch.isspace() and i not in covered for i,ch in enumerate(n.spoken_text)):add('common','AUDIO_WORD_COVERAGE',c.clip_id,'Timing omits part of approved narration including punctuation/symbols.')
        for a,b in zip(sorted(intervals),sorted(intervals)[1:]):
            if a[1]>b[0]:add('sync','AUDIO_NARRATION_OVERLAP',a[2]+':'+b[2],'Simultaneous narration is not supported by this lane.')
        for cue in policy.cues:
            t=timings.get(cue.clip_id);c=clips.get(cue.clip_id)
            if t is None or cue.word_index>=len(t.words):add('sync','AUDIO_CUE_WORD_MISSING',cue.cue_id,'Required cue has no inspected timed word.');continue
            w=t.words[cue.word_index];a=Fraction(c.start_ms)+Fraction(w.start_sample*1000,t.sample_rate);b=Fraction(c.start_ms)+Fraction(w.end_sample*1000,t.sample_rate)
            if abs(a-cue.start_ms)>cue.tolerance_ms or abs(b-cue.end_ms)>cue.tolerance_ms:add('sync','AUDIO_CUE_MISALIGNMENT',cue.cue_id,'Word start/end differs from approved visual/animation cue.')
        tracks_by_clip={}
        for track in request.captions:
            tracks_by_clip.setdefault(track.clip_id,[]).append(track)
            n=ns.get(track.clip_id);c=clips.get(track.clip_id);t=timings.get(track.clip_id)
            if n is None or c is None or t is None:add('captions','AUDIO_CAPTION_REFERENCE',track.track_id,'Caption lacks a verified clip/timing reference.');continue
            if track.language!=n.language:add('captions','AUDIO_CAPTION_LANGUAGE',track.track_id,'Translation needs a separately reviewed mapping; not silently accepted.')
            try:
                cs=parse_captions(store.read(track.artifact),track.format);inspected.add(track.artifact.artifact_id)
            except ContractError as exc:add('captions',exc.code,track.track_id,'Caption artifact failed parsing or byte verification.');continue
            caption_count+=len(cs);cursor=0;last_end=-1
            for cap in cs:
                if cap.start_ms<last_end:add('captions','AUDIO_CAPTION_OVERLAP',track.track_id,'Caption order/overlap violates the supported single-stream lane.')
                last_end=cap.end_ms;duration=cap.end_ms-cap.start_ms
                if not policy.min_caption_ms<=duration<=policy.max_caption_ms:add('captions','AUDIO_CAPTION_DURATION',track.track_id,'Cue exposure falls outside operator limits.')
                if len(cap.text.splitlines())>policy.max_caption_lines or any(len(x)>policy.max_caption_line_chars for x in cap.text.splitlines()):add('captions','AUDIO_CAPTION_LINE_LIMIT',track.track_id,'Line count/length exceeds declared readability limits.')
                if len(normalized(cap.text))*1000>policy.max_caption_chars_per_second*duration:add('captions','AUDIO_CAPTION_READING_RATE',track.track_id,'Exact code-point rate exceeds operator threshold.')
                end=cursor;acc=[]
                while end<len(t.words) and len(normalized(' '.join(acc)))<len(normalized(cap.text)):
                    acc.append(t.words[end].text);end+=1
                if not acc or normalized(' '.join(acc))!=normalized(cap.text):add('captions','AUDIO_CAPTION_TEXT_MISMATCH',track.track_id,'Caption does not represent the next contiguous narration words.');continue
                a=Fraction(c.start_ms)+Fraction(t.words[cursor].start_sample*1000,t.sample_rate);b=Fraction(c.start_ms)+Fraction(t.words[end-1].end_sample*1000,t.sample_rate)
                if abs(cap.start_ms-a)>policy.caption_tolerance_ms or abs(cap.end_ms-b)>policy.caption_tolerance_ms:add('captions','AUDIO_CAPTION_SYNC',track.track_id,'Cue boundaries differ from inspected timing intervals.')
                if cap.start_ms<c.start_ms-policy.caption_tolerance_ms or cap.end_ms>Fraction(c.start_ms)+measured[c.clip_id].duration_ms+policy.caption_tolerance_ms:add('captions','AUDIO_CAPTION_OUTSIDE_MEDIA',track.track_id,'Cue lies outside inspected audio.')
                cursor=end
            if cursor!=len(t.words):add('captions','AUDIO_CAPTION_COVERAGE',track.track_id,'Missing, repeated or reordered captions cannot manufacture coverage.')
        for cid in ns:
            if len(tracks_by_clip.get(cid,()))!=1:add('captions','AUDIO_CAPTION_TRACK_INVENTORY',cid,'Exactly one required same-language caption track per narration in this lane.')
        pe={p.clip_id:p for p in request.pronunciation};termclips={t.clip_id for t in policy.terms}
        for cid in set(pe)-termclips:add('pronunciation','AUDIO_UNEXPECTED_PRONUNCIATION_EVIDENCE',cid,'Evidence is outside operator-required term scope.')
        for cid in sorted(termclips):
            expected_terms={t.term_id:t for t in policy.terms if t.clip_id==cid};p=pe.get(cid);c=clips.get(cid);n=ns[cid];tim=timings.get(cid)
            if p is None:add('pronunciation','AUDIO_PRONUNCIATION_EVIDENCE_MISSING',cid,'Lexicon intent or transcript match is not acoustic evidence.','REVIEW');continue
            if c is None or tim is None:add('pronunciation','AUDIO_PRONUNCIATION_REFERENCE',cid,'A verified PCM/timing reference is required.');continue
            try:
                receipt=decode(loads(store.read(p.artifact)),PronunciationReceipt);inspected.add(p.artifact.artifact_id)
            except ContractError as exc:add('pronunciation',exc.code,cid,'Pronunciation evidence cannot be inspected.');continue
            if (receipt.clip_id,receipt.audio_sha256,receipt.transcript_sha256,receipt.language,receipt.voice_id)!=(cid,c.wav.sha256,hashlib.sha256(n.spoken_text.encode()).hexdigest(),n.language,n.voice_id):add('pronunciation','AUDIO_PRONUNCIATION_BINDING',cid,'Assessment belongs to different bytes, script, voice or language.');continue
            if receipt.basis not in ('acoustic_assessment','human_listening'):add('pronunciation','AUDIO_PRONUNCIATION_NOT_ACOUSTIC',cid,'ASR text, synthetic fixtures or text-only evidence cannot establish pronunciation.','REVIEW')
            obs={o.term_id:o for o in receipt.observations}
            if set(obs)!=set(expected_terms):add('pronunciation','AUDIO_TERM_COVERAGE',cid,'Every required occurrence must be assessed without extra/missing observations.')
            for tid,term in expected_terms.items():
                o=obs.get(tid)
                if o is None:continue
                pron_count+=1;ws=[w for w in tim.words if w.start_char<term.end_char and term.start_char<w.end_char]
                if not ws or (o.start_sample,o.end_sample)!=(ws[0].start_sample,ws[-1].end_sample):add('pronunciation','AUDIO_TERM_WINDOW',tid,'Assessment must target the required occurrence, not a different word window.')
                if o.verdict=='incorrect' or o.heard_form not in term.allowed_forms:add('pronunciation','AUDIO_PRONUNCIATION_MISMATCH',tid,'Observed pronunciation is not an approved contextual form.')
                elif o.verdict=='uncertain':add('pronunciation','AUDIO_PRONUNCIATION_UNCERTAIN',tid,'Listening/acoustic assessment is uncertain.','REVIEW')
    ev=digest(dict(source=source.to_dict(),reviews=[asdict(x) for x in sorted(reviews,key=lambda x:x.review_id)],trust=verifier.configuration_digest,pcm_stats=pstats))
    metrics={'sync':(('decoded_clips',len(measured)),('timing_receipts',len(timings)),('cue_rules',len(policy.cues))), 'captions':(('parsed_caption_cues',caption_count),), 'pronunciation':(('required_occurrences',len(policy.terms)),('observations_checked',pron_count))}
    def report(area):
        fs=tuple(sorted(set(groups['common']+groups[area]),key=lambda f:(f.subject_id,f.code,f.severity,f.detail)))
        return Report(TASKS[area],request.content_digest,policy.content_digest,ev,as_of,fs,metrics[area],tuple(sorted(inspected)),LIMITATIONS)
    return AudioResult(source,*(report(k) for k in AREAS),tuple(sorted(measured)))

def verify_reports(actual,*args,**kwargs):
    expected=evaluate(*args,**kwargs)
    if type(actual) is not AudioResult or actual!=expected:raise ContractError('AUDIO_STALE_OR_EDITED_REPORT')
    return actual

def evaluate_sync(*args,**kwargs):return evaluate(*args,**kwargs).sync

def evaluate_captions(*args,**kwargs):return evaluate(*args,**kwargs).captions

def evaluate_pronunciation(*args,**kwargs):return evaluate(*args,**kwargs).pronunciation
