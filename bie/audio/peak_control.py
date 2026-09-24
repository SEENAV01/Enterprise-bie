"""BIE-AUDIO-MIX-005: measured linked attenuation; zero latency, no hard clipping."""
from dataclasses import dataclass,asdict
from .common import AudioError,fingerprint
from .mix_contract import MixBuffer,number
from .tts_contract import AudioFormat
@dataclass(frozen=True)
class PeakPolicy:
    ceiling_dbtp:float=-1.0
    guard_db:float=.15
    maximum_attenuation_db:float=60.0
    def __post_init__(self):
        number(self.ceiling_dbtp,'ceiling',-9,-.1);number(self.guard_db,'guard',.05,1);number(self.maximum_attenuation_db,'attenuation limit',0,80)
def control_peaks(pcm,meter,policy=PeakPolicy(),*,dual_mono=False,cancellation=None):
    if type(pcm)is not MixBuffer or type(policy)is not PeakPolicy:raise AudioError('PEAK_POLICY')
    PeakPolicy(**asdict(policy));before=meter.measure(pcm,dual_mono=dual_mono,cancellation=cancellation)
    peak=max(x for x in (before.true_peak_dbtp,before.sample_peak_dbfs) if x is not None) if pcm.sample_peak else None
    gain=0 if peak is None or peak<=policy.ceiling_dbtp-policy.guard_db else policy.ceiling_dbtp-policy.guard_db-peak
    if -gain>policy.maximum_attenuation_db:raise AudioError('PEAK_ATTENUATION_LIMIT')
    out=pcm.gain(gain);wav=out.to_wav();quantized=MixBuffer.from_wav(wav,AudioFormat(out.sample_rate,out.channels))
    after=meter.measure(quantized,dual_mono=dual_mono,cancellation=cancellation)
    if after.true_peak_dbtp is not None and after.true_peak_dbtp>policy.ceiling_dbtp:raise AudioError('PEAK_CEILING_NOT_MET')
    if after.sample_peak_dbfs is not None and after.sample_peak_dbfs>policy.ceiling_dbtp:raise AudioError('SAMPLE_PEAK_CEILING_NOT_MET')
    r={'schema_version':'bie.audio.peak-control/1','input':pcm.info(),'output':quantized.info(),'policy':asdict(policy),'applied_gain_db':gain,
       'before':asdict(before),'after':asdict(after),'algorithm':'linked constant attenuation and nearest-even PCM16 quantization',
       'time_transform':'IDENTITY','latency_samples':0,'hard_clipped_samples':0,'product_accepted':False}
    r['fingerprint']=fingerprint(r);return wav,r
