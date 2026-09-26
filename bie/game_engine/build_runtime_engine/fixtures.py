from __future__ import annotations
from dataclasses import replace
import hashlib,io,wave
from ..compiler_engine.fixtures import compiler_context
from ..compiler_engine.contracts import AssetDescriptor

def wav_bytes():
    b=io.BytesIO()
    with wave.open(b,'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(8000);w.writeframes(b'\x00\x00'*80)
    return b.getvalue()
def build_inputs():
    data=wav_bytes();ctx=compiler_context();desc=AssetDescriptor('asset:sfx:success','audio/wav',hashlib.sha256(data).hexdigest(),'Success sound').validate();ctx=replace(ctx,assets={'asset:sfx:success':desc});return ctx,{'asset:sfx:success':data}
