"""Fixed no-input native identity discovery, inside the canonical namespace."""
from pathlib import Path
from .timed_espeak_provider import TimedEspeakProvider
from .mix_meter import FFmpegMeter
from .acoustic_contract import canonical

def main():
    import numpy as np
    p=TimedEspeakProvider('/usr/bin/espeak');m=FFmpegMeter('/usr/bin/ffmpeg')
    result={'provider_runtime_fingerprint':p.runtime,'catalog_fingerprint':p.catalog().fingerprint(),
        'meter_runtime_fingerprint':m.runtime_fingerprint,'numpy_version':np.__version__}
    with Path('/work/output/discovery.json').open('xb') as f:f.write(canonical(result))
    return 0
