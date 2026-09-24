"""Explicit synthesis TEST DOUBLE for contract/failure tests; waveform is not speech."""
from dataclasses import replace
import math,struct
from bie.audio.common import fingerprint
from bie.audio.preparation_bridge import from_v144
from bie.audio.tts_contract import *
from bie.audio.voice_selection import *
from bie.audio.pcm_audio import encode_pcm
from tests.audio.audio_test_support import utterance,empty_options


def plan(value='The force acts along the line.',language='en'):
    return from_v144((utterance(value,language),),**empty_options(language))


class TestProvider:
    provider_id='fixture-provider'
    def __init__(self):
        self.calls=0;self.failures=[];self.mutate=None
        voice=Voice('fixture-en',self.provider_id,'fixture/1',fingerprint('fixture runtime'),'en',
            (LocaleBinding('en','en'),LocaleBinding('hi','hi')),(AudioFormat(),),('language-switch',),
            'fixture',('synthetic:provider-test',),same_voice_code_switching=True)
        self.voices=VoiceCatalog('fixture/1',(voice,))
    def catalog(self):return self.voices
    def synthesize(self,request,*,cancellation=None):
        self.calls+=1
        if self.failures:raise self.failures.pop(0)
        raw=b''.join(struct.pack('<h',int(2000*math.sin(2*math.pi*440*i/22050))) for i in range(2205))
        result=ProviderAudio(request.fingerprint(),self.provider_id,request.voice.fingerprint(),request.voice.runtime_fingerprint,
            encode_pcm(raw,request.settings.format),'test-double:'+str(self.calls),('NOT_SPEECH_TEST_DOUBLE',))
        return self.mutate(result) if self.mutate else result


def request(p=None,provider=None,**setting):
    p=p or plan();provider=provider or TestProvider()
    selection=select_voices(p,provider.catalog(),SelectionPolicy((provider.provider_id,),('fixture',)),SynthesisSettings(**setting))
    return requests_for(p,provider.catalog(),selection)[0],provider
