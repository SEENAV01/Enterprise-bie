"""Explicit synthetic timing/provider fixtures. NEVER evidence of real speech."""
from dataclasses import replace
import re,math,struct,hashlib
from bie.audio.common import fingerprint
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.speech_timing import utterances_from_script
from bie.audio.preparation_bridge import from_v144
from bie.audio.tts_contract import ProviderAudio
from bie.audio.tts_generation import generate_speech
from bie.audio.voice_selection import SelectionPolicy,select_voices,requests_for
from bie.audio.pcm_audio import encode_pcm
from bie.audio.word_timestamps import reported_word_timings
from bie.audio.timed_espeak_provider import lexical_ranges
from bie.audio.scene_sync import assemble_scenes
from tests.audio.tts_test_support import TestProvider
from tests.audio.audio_test_support import empty_options

class SyntheticProvider(TestProvider):
    def __init__(self):
        super().__init__()
        self.voices=replace(self.voices,voices=self.voices.voices+(replace(self.voices.voices[0],voice_id='fixture-hi',primary_language='hi'),))
    def synthesize(self,request,*,cancellation=None):
        self.calls+=1
        raw=b''.join(struct.pack('<h',int(1500*math.sin(2*math.pi*100*i/22050))) for i in range(66150))
        return ProviderAudio(request.fingerprint(),self.provider_id,request.voice.fingerprint(),request.voice.runtime_fingerprint,
            encode_pcm(raw,request.settings.format),'SYNTHETIC:'+str(self.calls),('NOT_SPEECH_TIMING_TEST_DOUBLE',))


def fixture(values=('Alpha beta gamma.',),*,scenes=None,pause=0,language='en'):
    scenes=scenes or tuple('scene:'+str(i) for i in range(len(values)))
    segs=tuple(ScriptSegment('u'+str(i),scenes[i],'EXPLAIN','explain relation',('source:p1',),('objective:test',)) for i in range(len(values)))
    script=build_script_plan('synthetic:sync',segs,'voice:teacher')
    drafts=tuple(generate_voiceover(s.segment_id,(t,),{t:('source:p1',)}) for s,t in zip(segs,values))
    utter=tuple(utterances_from_script(script,drafts,tuple(s.segment_id for s in segs),language))
    plan=from_v144(utter,**empty_options(language));plan=replace(plan,segments=tuple(replace(s,pause_after_ms=pause,pause_refs=('source:pause',) if pause else ()) for s in plan.segments))
    provider=SyntheticProvider();cat=provider.catalog();sel=select_voices(plan,cat,SelectionPolicy((provider.provider_id,),('fixture',)))
    assets=tuple(generate_speech(r,provider) for r in requests_for(plan,cat,sel));aligned=[]
    for a in assets:
        ranges=lexical_ranges(a.request.segment.spoken_text);step=60000//len(ranges)
        intervals=tuple((x,y,100+i*step,100+(i+1)*step) for i,(x,y) in enumerate(ranges))
        aligned.append(replace(reported_word_timings(a,intervals),basis='SYNTHETIC_TEST_DOUBLE'))
    return plan,assets,tuple(aligned)


def timeline_fixture(**kw):
    p,a,t=fixture(**kw);timeline,wav=assemble_scenes(p,a,t,require_measured=False)
    return p,a,t,timeline,wav
