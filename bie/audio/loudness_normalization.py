"""BIE-AUDIO-MIX-001: actual measured constant-gain normalization, not hidden compression."""
from dataclasses import dataclass,asdict
from .common import AudioError,fingerprint
from .mix_contract import number
@dataclass(frozen=True)
class LoudnessPolicy:
    target_lufs:float=-23.0
    tolerance_lu:float=.5
    true_peak_ceiling_dbtp:float=-1.0
    max_boost_db:float=18.0
    max_attenuation_db:float=60.0
    unreachable:str='review'
    dual_mono:bool=False
    def __post_init__(self):
        for k,lo,hi in (('target_lufs',-40,-10),('tolerance_lu',.1,1),('true_peak_ceiling_dbtp',-9,-.1),('max_boost_db',0,24),('max_attenuation_db',0,80)):
            number(getattr(self,k),k,lo,hi)
        if self.unreachable not in ('review','fail') or type(self.dual_mono)is not bool:raise AudioError('LOUDNESS_POLICY')
def normalize_loudness(pcm,meter,policy=LoudnessPolicy(),*,cancellation=None):
    if type(policy)is not LoudnessPolicy:raise AudioError('LOUDNESS_POLICY')
    LoudnessPolicy(**asdict(policy));before=meter.measure(pcm,dual_mono=policy.dual_mono,cancellation=cancellation)
    if before.integrated_lufs is None or pcm.frames*10<4*pcm.sample_rate:raise AudioError('LOUDNESS_NOT_MEASURABLE')
    requested=policy.target_lufs-before.integrated_lufs
    gain=min(requested,policy.max_boost_db,policy.true_peak_ceiling_dbtp-before.true_peak_dbtp-.1)
    if gain < -policy.max_attenuation_db:raise AudioError('LOUDNESS_ATTENUATION_LIMIT')
    if abs(gain-requested)>policy.tolerance_lu and policy.unreachable=='fail':raise AudioError('LOUDNESS_TARGET_UNREACHABLE')
    out=pcm.gain(gain);after=meter.measure(out,dual_mono=policy.dual_mono,cancellation=cancellation)
    if after.integrated_lufs is None:raise AudioError('LOUDNESS_MEASUREMENT_LOST')
    reached=abs(after.integrated_lufs-policy.target_lufs)<=policy.tolerance_lu
    if after.true_peak_dbtp>policy.true_peak_ceiling_dbtp+.02:raise AudioError('LOUDNESS_TRUE_PEAK_EXCEEDED')
    if not reached and policy.unreachable=='fail':raise AudioError('LOUDNESS_TARGET_UNREACHABLE')
    r={'schema_version':'bie.audio.loudness-transform/1','input':pcm.info(),'output':out.info(),'policy':asdict(policy),
       'requested_gain_db':requested,'applied_gain_db':gain,'before':asdict(before),'after':asdict(after),
       'target_reached':reached,'requires_review':not reached,'status':'TARGET_REACHED' if reached else 'CONSTRAINED_TARGET_UNMET_REVIEW',
       'dynamic_compression_applied':False,'time_transform':'IDENTITY','product_accepted':False}
    r['fingerprint']=fingerprint(r);return out,r
