"""Fixed native child for H2. No signing keys, downloads or narration synthesis."""
from __future__ import annotations
import ctypes as C
import hashlib, io, json, math, os, re, resource, subprocess, sys, wave
from pathlib import Path
from bie.audio.common import AudioError, fingerprint
from bie.audio.acoustic_contract import (RESULT_SCHEMA, SCOPE, BOUNDARIES,
    canonical, english_tokens, pcm_info, validate_job, edit_distance)
from bie.audio.acoustic_runtime import verify_runtime


class LegacyDecoder:
    """Only public legacy C API; ctypes pointers never cross process boundaries."""
    def __init__(self,runtime):
        self.files=runtime['files']
        self.sb=C.CDLL(self.files['sphinxbase']['path'],mode=C.RTLD_GLOBAL)
        self.ps=C.CDLL(self.files['pocketsphinx']['path'])
        p=C.c_void_p;i=C.c_int;s=C.c_char_p;ip=C.POINTER(i)
        for lib,name,out,args in [
            (self.ps,'ps_args',p,[]),(self.sb,'cmd_ln_parse_r',p,[p,p,i,C.POINTER(s),i]),
            (self.ps,'ps_init',p,[p]),(self.ps,'ps_free',i,[p]),(self.sb,'cmd_ln_free_r',i,[p]),
            (self.ps,'ps_start_utt',i,[p,s]),(self.ps,'ps_process_raw',i,[p,C.POINTER(C.c_int16),C.c_size_t,i,i]),
            (self.ps,'ps_end_utt',i,[p]),(self.ps,'ps_seg_iter',p,[p,ip]),
            (self.ps,'ps_seg_next',p,[p]),(self.ps,'ps_seg_free',None,[p]),
            (self.ps,'ps_seg_word',s,[p]),(self.ps,'ps_seg_frames',None,[p,ip,ip]),
            (self.ps,'ps_seg_prob',i,[p,ip,ip,ip]),(self.ps,'ps_get_hyp',s,[p,ip,C.POINTER(s)])]:
            f=getattr(lib,name);f.restype=out;f.argtypes=args
    def decode(self,pcm,mode,root,tokens):
        f=self.files
        args=['h2','-hmm',str(Path(f['hmm/mdef']['path']).parent),'-dict',f['dictionary']['path'],
              '-samprate','16000','-frate','100','-logfn',str(root/'native.log'),
              '-remove_silence','no','-remove_noise','yes','-cmn','batch']
        if mode=='fsg':
            grammar='FSG_BEGIN exact\nNUM_STATES %d\nSTART_STATE 0\nFINAL_STATE %d\n'%(len(tokens)+1,len(tokens))
            grammar+=''.join('TRANSITION %d %d 1.0 %s\n'%(i,i+1,t['word']) for i,t in enumerate(tokens))+'FSG_END\n'
            (root/'exact.fsg').write_text(grammar)
            args+=['-fsg',str(root/'exact.fsg')]
        elif mode=='allphone':
            args+=['-allphone',f['phone_lm']['path'],'-allphone_ci','yes','-beam','1e-20','-pbeam','1e-20','-lw','2.0']
        elif mode=='lm':args+=['-lm',f['word_lm']['path']]
        else:raise AudioError('ACOUSTIC_SEARCH_MODE')
        encoded=[x.encode() for x in args];argv=(C.c_char_p*len(encoded))(*encoded)
        cfg=self.sb.cmd_ln_parse_r(None,self.ps.ps_args(),len(encoded),argv,1)
        if not cfg:raise AudioError('ACOUSTIC_NATIVE_CONFIG')
        decoder=None;it=None
        try:
            decoder=self.ps.ps_init(cfg)
            if not decoder:raise AudioError('ACOUSTIC_NATIVE_INIT')
            buf=(C.c_int16*(len(pcm)//2)).from_buffer_copy(pcm)
            if self.ps.ps_start_utt(decoder,None)<0 or self.ps.ps_process_raw(decoder,buf,len(buf),0,1)<0 or self.ps.ps_end_utt(decoder)<0:
                raise AudioError('ACOUSTIC_NATIVE_DECODE')
            score=C.c_int();uid=C.c_char_p();hyp=self.ps.ps_get_hyp(decoder,C.byref(score),C.byref(uid))
            words=[];it=self.ps.ps_seg_iter(decoder,None)
            while it:
                if len(words)>=8192:raise AudioError('ACOUSTIC_NATIVE_ROW_BUDGET')
                a=C.c_int();b=C.c_int();ac=C.c_int();lm=C.c_int();back=C.c_int()
                self.ps.ps_seg_frames(it,C.byref(a),C.byref(b))
                self.ps.ps_seg_prob(it,C.byref(ac),C.byref(lm),C.byref(back))
                name=self.ps.ps_seg_word(it)
                if not name:raise AudioError('ACOUSTIC_NATIVE_SEGMENT')
                words.append({'label':name.decode('utf-8'),'start_frame':a.value,
                    'end_frame_exclusive':b.value+1,'acoustic_score_raw':ac.value,'language_score_raw':lm.value})
                it=self.ps.ps_seg_next(it)
            return {'hypothesis':hyp.decode('utf-8') if hyp else '', 'score_raw':score.value,
                    'segments':words,'mode':mode,'confidence':None}
        finally:
            if it:self.ps.ps_seg_free(it)
            if decoder:self.ps.ps_free(decoder)
            self.sb.cmd_ln_free_r(cfg)


def normalized_pcm(pcm,rate,channels,runtime):
    if rate==16000 and channels==1:return pcm
    # Resampling is analysis-only. Delivered media and its clock are never changed.
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as w:
        w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm)
    run=subprocess.run([runtime['files']['ffmpeg']['path'],'-nostdin','-v','error','-i','pipe:0',
        '-ac','1','-af','aresample=16000:resampler=swr:dither_method=none','-ar','16000',
        '-c:a','pcm_s16le','-f','s16le','pipe:1'],input=buffer.getvalue(),capture_output=True,timeout=30)
    if run.returncode or not run.stdout or len(run.stdout)>2_000_000 or len(run.stdout)%2:
        raise AudioError('ACOUSTIC_RESAMPLE_FAILED')
    expected=(len(pcm)//(channels*2))*16000/rate
    if abs(len(run.stdout)//2-expected)>2:raise AudioError('ACOUSTIC_RESAMPLE_CLOCK')
    return run.stdout


def measure(job,wav,runtime,root):
    policy=validate_job(job,wav);verify_runtime(runtime);info,pcm=pcm_info(wav,policy)
    rate=info['sample_rate'];ch=info['channels'];rows=[];decoder=None;dictionary={}
    for line in Path(runtime['files']['dictionary']['path']).read_text().splitlines():
        parts=line.split()
        if len(parts)<2:continue
        word=re.sub(r'\(\d+\)$','',parts[0]).lower()
        dictionary.setdefault(word,[]).append(parts[1:])
    for s in job['segments']:
        segment={'segment_id':s['segment_id'],'request_fingerprint':s['request_fingerprint'],
                 'status':'MEASURED','native_passes':[],'tokens':[], 'words':[],
                 'phone_comparisons':[],'signals':[], 'crop_sha256':'',
                 'analysis_pcm_sha256':None,'analysis_samples':0}
        a,b=s['start_sample'],s['end_sample'];crop=pcm[a*ch*2:b*ch*2]
        segment['crop_sha256']=hashlib.sha256(crop).hexdigest()
        if s['languages'] not in (['en'],['en-US']):
            segment['status']='UNSUPPORTED_LANGUAGE';rows.append(segment);continue
        try:tokens=english_tokens(s['spoken_text'])
        except AudioError:
            segment['status']='UNSUPPORTED_TOKENIZATION';rows.append(segment);continue
        segment['tokens']=tokens
        if len(tokens)>policy.max_words_per_segment:
            segment['status']='TOKEN_BUDGET';rows.append(segment);continue
        if any(any(sp.get(k) for k in ('phonemes','alphabet')) for sp in s['source_spans']):
            segment['status']='UNSUPPORTED_PHONETIC_OVERRIDE';rows.append(segment);continue
        if any(t['word'] not in dictionary for t in tokens):
            segment['status']='OUT_OF_VOCABULARY';rows.append(segment);continue
        if not any(crop):
            segment['status']='NO_SIGNAL';rows.append(segment);continue
        analysis=normalized_pcm(crop,rate,ch,runtime)
        segment['analysis_pcm_sha256']=hashlib.sha256(analysis).hexdigest()
        segment['analysis_samples']=len(analysis)//2
        if not any(analysis):
            segment['status']='ANALYSIS_CHANNEL_CANCELLATION';rows.append(segment);continue
        if decoder is None:decoder=LegacyDecoder(runtime)
        passes=[decoder.decode(analysis,mode,root,tokens) for mode in ('fsg','allphone','lm')]
        segment['native_passes']=passes
        forced=[w for w in passes[0]['segments'] if not w['label'].startswith(('<','['))]
        if [re.sub(r'\(\d+\)$','',w['label']) for w in forced] != [t['word'] for t in tokens]:
            segment['status']='ALIGNMENT_INCOMPLETE';rows.append(segment);continue
        phones=[p for p in passes[1]['segments'] if p['label'] not in ('SIL','<sil>','<s>','</s>')]
        previous=a
        for token,observed in zip(tokens,forced):
            # One 10-ms frame index maps to one half-up sample boundary. Precision
            # remains the model frame grid, NOT a claimed sample-accurate phoneme.
            start=a+(observed['start_frame']*rate+50)//100
            end=min(b,a+(observed['end_frame_exclusive']*rate+50)//100)
            if start<previous or not a<=start<end<=b:raise AudioError('ACOUSTIC_NATIVE_CLOCK_BOUNDS')
            previous=end
            segment['words'].append({**token,'start_sample':start,'end_sample':end,
                                      'acoustic_score_raw':observed['acoustic_score_raw']})
            assigned=[p['label'] for p in phones if 2*observed['start_frame']<=p['start_frame']+p['end_frame_exclusive']<2*observed['end_frame_exclusive']]
            variants=dictionary[token['word']]
            dist,idx=min((edit_distance(v,assigned),i) for i,v in enumerate(variants))
            segment['phone_comparisons'].append({'word':token['word'], 'spoken_start':token['spoken_start'],
                'expected_variants':variants,'observed_phones':assigned,'minimum_edit_distance':dist,
                'selected_variant_index':idx,'denominator':max(1,len(variants[idx])), 'confidence':None})
        rows.append(segment)
    out={'schema_version':RESULT_SCHEMA,'scope':SCOPE,'job_fingerprint':job['fingerprint'],
         'runtime_fingerprint':runtime['fingerprint'],'segments':rows,'frame_resolution_ms':10,
         'method':'TRANSCRIPT_CONSTRAINED_WORD_FSG_PLUS_UNCONSTRAINED_ALLPHONE_AND_NGRAM',
         'score_interpretation':'Raw native decoder scores; not calibrated probabilities or pronunciation grades',
         **BOUNDARIES}
    out['fingerprint']=fingerprint(out);verify_runtime(runtime)
    return out


def main():
    root=Path(sys.argv[1]).resolve()
    request=json.loads((root/'request.json').read_text());deadline=request['job']['policy']['deadline_seconds']
    resource.setrlimit(resource.RLIMIT_CPU,(deadline,deadline+1))
    resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,768*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(8_000_000,8_000_000))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    out=measure(request['job'],(root/'source.wav').read_bytes(),request['runtime'],root)
    (root/'result.json').write_bytes(canonical(out))
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
        print(getattr(exc,'code','ACOUSTIC_NATIVE_FAILURE'),file=sys.stderr)
        raise SystemExit(2)
