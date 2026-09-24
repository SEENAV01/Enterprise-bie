"""SYNC-001 native callback worker. Run only as a bounded child process.

Uses installed eSpeak ABI; no library, font or voice data is redistributed.
No audio playback, HTTP, user SSML interpretation beyond parent-owned serialization.
"""
from __future__ import annotations
import ctypes as C
import hashlib, json, os, resource, sys, wave
from pathlib import Path

class EventID(C.Union):
    _fields_ = [('number', C.c_int), ('name', C.c_char_p), ('string', C.c_char * 8)]
class EspeakEvent(C.Structure):
    _fields_ = [('type', C.c_int), ('unique_identifier', C.c_uint),
                ('text_position', C.c_int), ('length', C.c_int),
                ('audio_position', C.c_int), ('sample', C.c_int),
                ('user_data', C.c_void_p), ('id', EventID)]
CALLBACK = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_short), C.c_int, C.POINTER(EspeakEvent))


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    raw = (root/'request.json').read_bytes()
    if len(raw)>200000: raise ValueError('WORKER_INPUT_LIMIT')
    req=json.loads(raw); required={'markup','library','library_sha256','voice','rate','pitch','amplitude'}
    if type(req) is not dict or set(req)!=required: raise ValueError('WORKER_FIELDS')
    library=Path(req['library']).resolve(strict=True)
    if not str(library).startswith(('/usr/lib/','/lib/')) or not library.name.startswith('libespeak.so'):
        raise ValueError('WORKER_LIBRARY_NOT_INSTALLED_ESPEAK')
    if hashlib.sha256(library.read_bytes()).hexdigest()!=req['library_sha256']: raise ValueError('WORKER_LIBRARY_CHANGED')
    if type(req['markup']) is not str or len(req['markup'].encode())>160000 or '\0' in req['markup']:
        raise ValueError('WORKER_MARKUP_LIMIT')
    for key,lo,hi in (('rate',80,300),('pitch',0,99),('amplitude',1,100)):
        if type(req[key]) is not int or not lo<=req[key]<=hi: raise ValueError('WORKER_PARAMETER')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(20,20))
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(32000000,32000000))
    lib=C.CDLL(str(library))
    lib.espeak_Initialize.argtypes=[C.c_int,C.c_int,C.c_char_p,C.c_int]; lib.espeak_Initialize.restype=C.c_int
    lib.espeak_SetSynthCallback.argtypes=[CALLBACK]
    lib.espeak_SetVoiceByName.argtypes=[C.c_char_p]; lib.espeak_SetVoiceByName.restype=C.c_int
    lib.espeak_SetParameter.argtypes=[C.c_int,C.c_int,C.c_int]; lib.espeak_SetParameter.restype=C.c_int
    lib.espeak_Synth.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_int,C.c_uint,C.c_uint,C.POINTER(C.c_uint),C.c_void_p]
    lib.espeak_Synth.restype=C.c_int
    rate=lib.espeak_Initialize(2,0,None,0x8000)
    if rate!=22050: raise ValueError('WORKER_RATE_UNSUPPORTED')
    audio=[]; events=[]; size=0; errors=[]
    @CALLBACK
    def callback(samples,n,ev):
        nonlocal size
        try:
            if n<0 or n>100000: raise ValueError('CALLBACK_SAMPLE_LIMIT')
            if samples and n:
                size+=n*2
                if size>32000000: raise ValueError('CALLBACK_OUTPUT_LIMIT')
                audio.append(C.string_at(samples,n*2))
            i=0
            while ev and ev[i].type:
                e=ev[i]
                if i>20000 or len(events)>=20000: raise ValueError('CALLBACK_EVENT_LIMIT')
                events.append({'type':e.type,'text_position':e.text_position,'length':e.length,'audio_ms':e.audio_position, **({'mark':e.id.name.decode('utf-8')} if e.type==3 and e.id.name else {})})
                i+=1
            return 0
        except Exception as exc:
            errors.append(str(exc)); return 1
    lib.espeak_SetSynthCallback(callback)
    try:
        if lib.espeak_SetVoiceByName(req['voice'].encode()): raise ValueError('WORKER_VOICE')
        for code,key in ((1,'rate'),(2,'amplitude'),(3,'pitch')):
            if lib.espeak_SetParameter(code,req[key],0): raise ValueError('WORKER_PARAMETER')
        value=req['markup'].encode()+b'\0'; buffer=C.create_string_buffer(value); uid=C.c_uint()
        # UTF8 | SSML | final sentence pause: identical to the governed CLI adapter.
        result=lib.espeak_Synth(buffer,len(value),0,1,0,1|0x10|0x1000,C.byref(uid),None)
        if result or errors or not audio: raise ValueError('WORKER_SYNTHESIS:'+str(errors))
    finally: lib.espeak_Terminate()
    pcm=b''.join(audio)
    with wave.open(str(root/'replay.wav'),'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate); f.writeframes(pcm)
    report={'schema_version':'bie.espeak-callback/1','request_sha256':hashlib.sha256(raw).hexdigest(),
            'library_sha256':req['library_sha256'],'sample_rate':rate,'samples':len(pcm)//2,
            'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'events':events,
            'event_time_unit':'public_audio_position_integer_ms','completed':True}
    (root/'events.json').write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(str(exc),file=sys.stderr); raise SystemExit(2)
