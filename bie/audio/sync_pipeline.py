"""AUDIO SYNC batch composition over BOTH reconciled preparation profiles.

Uses real VO-009 speech, VO-010 cache and SYNC-001 replay. It does not mutate
old speech receipts or promote their acceptance flags. Word timing is a new artifact.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
from .common import AudioError, fingerprint
from .tts_contract import SynthesisSettings
from .voice_selection import select_voices,requests_for
from .word_timestamps import align_espeak_asset
from .timed_espeak_provider import TimedEspeakProvider,align_timed_asset
from .caption_alignment import CaptionPolicy,align_captions
from .scene_sync import FrameRate,assemble_scenes
from .animation_sync import AnimationBinding,synchronize_animations
from .pause_sync import synchronize_pauses

@dataclass(frozen=True)
class SynchronizedAudio:
    plan: object
    selection: object
    assets: tuple
    alignments: tuple
    engine_evidence: tuple
    captions: tuple
    timeline: object
    wav_bytes: bytes
    pauses: object
    cache_hits: tuple[bool,...]
    def receipt(self):
        return {'schema_version':'bie.audio.sync-run/1','plan':asdict(self.plan),'plan_fingerprint':self.plan.fingerprint(),
                'selection':asdict(self.selection),'timeline':asdict(self.timeline),'timeline_fingerprint':self.timeline.fingerprint(),
                'word_timings':[a.receipt() for a in self.alignments],
                'caption_tracks':[asdict(c) for c in self.captions], 'pause_sync':asdict(self.pauses),
                'speech_receipts':[a.receipt() for a in self.assets],'cache_hits':list(self.cache_hits),
                'timing_basis':self.alignments[0].basis,'engine_replay_calls':0 if self.alignments[0].basis in ('ELEVENLABS_CHARACTER_EVENTS_SAME_RESPONSE','NEURAL_CHARACTER_FIXTURE_SAME_PCM') else len(self.alignments),
                'scene_clock_verified':True,'pause_samples_verified':True,
                'acoustic_alignment_verified':False,'real_video_render_verified':False,
                'cinematic_quality_verified':False,'product_accepted':False}


def prepare_sync(plan,provider,cache,selection_policy,*,settings=SynthesisSettings(),caption_policy=CaptionPolicy(),
                 fps=FrameRate(),budgets=(),cancellation=None):
    plan.require_ready();catalog=provider.catalog();selection=select_voices(plan,catalog,selection_policy,settings)
    requests=requests_for(plan,catalog,selection)
    assets=[];alignments=[];events=[];captions=[];hits=[]
    for request in requests:
        outcome=cache.get_or_generate(request,provider,cancellation=cancellation)
        aligned,evidence=(align_timed_asset if type(provider)is TimedEspeakProvider else align_espeak_asset)(outcome.asset,provider,cancellation=cancellation)
        assets.append(outcome.asset);alignments.append(aligned);events.append(evidence)
        captions.append(align_captions(outcome.asset,aligned,caption_policy));hits.append(outcome.cache_hit)
    assets,alignments,captions=tuple(assets),tuple(alignments),tuple(captions)
    timeline,wav=assemble_scenes(plan,assets,alignments,fps=fps,budgets=budgets)
    pauses=synchronize_pauses(timeline,wav,assets,alignments,captions)
    return SynchronizedAudio(plan,selection,assets,alignments,tuple(events),captions,timeline,wav,pauses,tuple(hits))


def bind_sync_spec(result,raw):
    """Consume explicit authored animation anchors, not invented visual plans.

    The spec is source-plan pinned; anchors also echo their exact observed words.
    Scene/target ownership remains upstream; this does not generate a lesson plan.
    """
    from .common import exact_fields
    exact_fields(raw,('schema_version','plan_fingerprint','bindings'))
    if raw['schema_version']!='bie.audio.word-anchor-input/1' or raw['plan_fingerprint']!=result.plan.fingerprint():
        raise AudioError('SYNC_SPEC_SOURCE_CHANGED')
    if type(raw['bindings'])is not list or len(raw['bindings'])>4096:raise AudioError('SYNC_SPEC_BINDINGS')
    fields=tuple(k for k in AnimationBinding.__dataclass_fields__ if k!='timeline_fingerprint')+('expected_first_word','expected_last_word')
    index={p.segment_id:a for p,a in zip(result.timeline.segments,result.alignments)};bindings=[]
    for row in raw['bindings']:
        exact_fields(row,fields)
        try:
            start=index[row['start_segment_id']].words[row['first_word']]
            end=index[row['end_segment_id']].words[row['last_word']]
        except (KeyError,IndexError,TypeError):raise AudioError('SYNC_SPEC_WORD_UNKNOWN')
        if start.spoken!=row['expected_first_word'] or end.spoken!=row['expected_last_word']:raise AudioError('SYNC_SPEC_WORD_CHANGED')
        values={k:row[k] for k in AnimationBinding.__dataclass_fields__ if k!='timeline_fingerprint'}
        for k in ('source_refs','reasoning_refs','after'):
            if type(values[k])is not list:raise AudioError('SYNC_SPEC_ARRAY')
            values[k]=tuple(values[k])
        bindings.append(AnimationBinding(**values,timeline_fingerprint=result.timeline.fingerprint()))
    return synchronize_animations(result.timeline,result.alignments,tuple(bindings))
