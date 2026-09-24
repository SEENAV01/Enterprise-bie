"""Explicit synthetic ElevenLabs API-contract fixtures. NOT service responses."""
from dataclasses import replace
from pathlib import Path
from threading import Event
import base64,json,math,struct,tempfile,sys
from bie.audio.common import fingerprint
from bie.audio.neural_policy import NeuralDeployment
from bie.audio.neural_transport import HTTPReply
from bie.audio.neural_store import NeuralResponseStore,canonical
from bie.audio.elevenlabs_provider import ElevenLabsProvider
from bie.audio.speech_contract import SpeechPlan,SpeechSegment,SpeechSpan
from bie.audio.voice_selection import SelectionPolicy,select_voices,requests_for
from bie.audio.tts_contract import AudioFormat,SynthesisSettings

VOICE='voice_fixture_01'
MODEL={'model_id':'eleven_flash_v2_5','can_do_text_to_speech':True,'languages':[{'language_id':'en'},{'language_id':'hi'}],
       'maximum_text_length_per_request':40000,'can_use_style':True,'can_use_speaker_boost':True}
VOICE_META={'voice_id':VOICE,'name':'Synthetic contract fixture, not a provider voice','category':'premade'}
KEY=b'f'*32


def config(language='en',**kw):
    c=NeuralDeployment(VOICE,'synthetic-deployment-v1',language,fingerprint(MODEL),fingerprint(VOICE_META),('synthetic:voice-policy',),
                        deadline_seconds=5.0,socket_timeout_seconds=1.0,model_id='eleven_flash_v2_5',language_mode='enforced')
    return replace(c,**kw)


def plan(text='First observe the graph.',language='en',pause=0):
    span=SpeechSpan(0,len(text),text,text,language,fingerprint('literal'),('synthetic:source',))
    segment=SpeechSegment('segment-1','u1',fingerprint('utterance'),fingerprint('script'),'scene-1','teacher',language,0,len(text),text,(span,),('obj-1',),pause,('synthetic:pause',) if pause else ())
    return SpeechPlan('batch001-144',fingerprint('prep'),fingerprint('lang'),(segment,))


def multi_plan(language='en'):
    texts=('First observe the graph.','Now trace the change.','The next scene follows.');segments=[]
    for i,t in enumerate(texts):
        s=plan(t,language,300 if i==0 else 0).segments[0]
        segments.append(replace(s,segment_id=f'segment-{i}',utterance_id=f'u{i}',scene_id='scene-1' if i<2 else 'scene-2'))
    return replace(plan(),segments=tuple(segments))


def wire_response(text,rate=24000):
    # Fixed synthetic chirp and fabricated timestamps for API-shape testing only.
    dt=.05;frames=max(rate,round((len(text)*dt+.2)*rate))
    pcm=b''.join(struct.pack('<h',int(2400*math.sin(2*math.pi*220*i/rate))) for i in range(frames))
    alignment={'characters':list(text),'character_start_times_seconds':[round(i*dt,8) for i in range(len(text))],
               'character_end_times_seconds':[round((i+1)*dt,8) for i in range(len(text))]}
    return {'audio_base64':base64.b64encode(pcm).decode(),'alignment':alignment,'normalized_alignment':alignment}


class FixtureTransport:
    evidence_scope='CONTRACT_FIXTURE'
    def __init__(self):self.calls=[];self.mutation=None;self.status=200;self.reply_scope=self.evidence_scope;self.model=MODEL;self.voice=VOICE_META;self.delay=0
    def request(self,method,path,body,**kw):
        import time
        self.calls.append((method,path,body));time.sleep(self.delay)
        if method=='GET':row=[self.model] if path=='/v1/models' else self.voice
        else:
            payload=json.loads(body);rate=int(path.split('pcm_')[1].split('&')[0]);row=wire_response(payload['text'],rate)
            if self.mutation:row=self.mutation(row)
        return HTTPReply(self.status,canonical(row),'fixture-request-'+str(len(self.calls)),self.reply_scope)


def setup(root,*,p=None,c=None,transport=None,context=False):
    p=p or plan();c=c or config(p.segments[0].language);t=transport or FixtureTransport()
    store=NeuralResponseStore(Path(root)/'response',key=KEY)
    provider=ElevenLabsProvider(c,store,transport=t,fixture=True,context_plan=p if context else None)
    catalog=provider.catalog();settings=SynthesisSettings(format=AudioFormat(c.sample_rate,1))
    policy=SelectionPolicy((provider.provider_id,),('provider-fixture',))
    selection=select_voices(p,catalog,policy,settings);requests=requests_for(p,catalog,selection)
    return p,provider,requests,t


def sleeper(send,args):
    import time
    time.sleep(args[0]);send.send_bytes(b'{"status":200,"request_id":"fixture"}\n{}');send.close()

def die(send,args):
    import os
    os._exit(7)

def huge_packet(send,args):
    send.send_bytes(b'x'*10000);send.close()


def enter_fixture_scope(testcase):
    from bie.audio.fixture_scope import synthetic_timing_scope
    cm=synthetic_timing_scope();cm.__enter__();testcase.addCleanup(cm.__exit__,None,None,None)
