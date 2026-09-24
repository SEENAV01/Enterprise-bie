"""BIE-AUDIO-SYNC-005: verify/coordinate declared additional silence intervals.

Native synthesizer silence is not silently reclassified as a teacher's requested
pause. Intra-word pauses require upstream resegmentation/resynthesis, not splicing.
"""
from dataclasses import dataclass
import hashlib
from .common import AudioError,fingerprint,refs,text
from .sync_contract import validate_asset,validate_alignment
from .scene_sync import AudioTimeline,validate_timeline_media

@dataclass(frozen=True)
class PauseWindow:
    segment_id: str
    scene_id: str
    start_sample: int
    end_sample: int
    requested_ms: int
    pause_refs: tuple[str,...]
    zero_pcm_sha256: str

@dataclass(frozen=True)
class PauseSync:
    timeline_fingerprint: str
    windows: tuple[PauseWindow,...]
    def fingerprint(self):return fingerprint(self)
    def at_sample(self,sample):return tuple(p for p in self.windows if p.start_sample<=sample<p.end_sample)


def synchronize_pauses(timeline:AudioTimeline,wav,assets,alignments,caption_tracks=(),*,require_measured=True):
    validate_timeline_media(timeline,wav)
    if type(assets)is not tuple or type(alignments)is not tuple or len(assets)!=len(timeline.segments) or len(alignments)!=len(assets):raise AudioError('PAUSE_ASSET_COVERAGE')
    if caption_tracks and (type(caption_tracks)is not tuple or len(caption_tracks)!=len(assets)):raise AudioError('PAUSE_CAPTION_COVERAGE')
    windows=[];raw_parts=[]
    for i,(placement,asset,alignment) in enumerate(zip(timeline.segments,assets,alignments)):
        validate_alignment(asset,alignment,require_measured=require_measured)
        info,pcm,prefix=validate_asset(asset);raw_parts.append(pcm)
        if placement.request_fingerprint!=asset.request.fingerprint() or placement.alignment_fingerprint!=alignment.fingerprint() or placement.media_sha256!=info.sha256:raise AudioError('PAUSE_STALE_ASSET')
        if placement.provider_end_sample-placement.start_sample!=alignment.provider_samples or placement.end_sample-placement.provider_end_sample!=asset.requested_pause_samples:raise AudioError('PAUSE_PLACEMENT_CHANGED')
        if caption_tracks:
            caption=caption_tracks[i]
            if caption.alignment_fingerprint!=alignment.fingerprint() or any(c.end_sample>alignment.provider_samples for c in caption.cues):raise AudioError('CAPTION_OVER_PEDAGOGICAL_PAUSE')
        if not asset.requested_pause_samples:continue
        segment=asset.request.segment;refs(segment.pause_refs,'pause source')
        silence=pcm[len(prefix):]
        if any(silence) or len(silence)!=asset.requested_pause_samples*info.channels*2:raise AudioError('PAUSE_NOT_EXACT_SILENCE')
        windows.append(PauseWindow(segment.segment_id,segment.scene_id,placement.provider_end_sample,placement.end_sample,
            segment.pause_after_ms,segment.pause_refs,hashlib.sha256(silence).hexdigest()))
    from .pcm_audio import validate_wav
    from .tts_contract import AudioFormat
    _,whole=validate_wav(wav,AudioFormat(timeline.sample_rate,timeline.channels),max_bytes=64001000,max_seconds=1800)
    if whole!=b''.join(raw_parts):raise AudioError('PAUSE_ASSEMBLY_CHANGED')
    return PauseSync(timeline.fingerprint(),tuple(windows))
