"""Validation and seek evaluation of the derived MIX clock.

Integrity and reference consistency are not authenticity or acoustic acceptance.
The source-aware validator in mix_pipeline checks the clock against actual SYNC.
"""
from fractions import Fraction
from .common import AudioError, fingerprint, integer, text, digest
from .mix_contract import hash64
from .sync_contract import FrameRate


def _interval(row,total,name):
    if type(row)is not dict:raise AudioError('MIX_CLOCK_RECORD',name)
    a=row['start_sample'];b=row['end_sample']
    integer(a,name+' start',0,total);integer(b,name+' end',a+1,total)
    return a,b


def validate_mixed_clock(clock,receipt,pcm):
    c,r=clock,receipt
    n=integer(c['total_samples'],'total samples',1,pcm.sample_rate*1800)
    for key in ('source_timeline_fingerprint','plan_fingerprint'):digest(c[key])
    hash64(c['source_audio_sha256']);hash64(c['output_audio_sha256'])
    fps=FrameRate(**c['fps']);rate=pcm.sample_rate
    integer(c['source_start_sample'],'trim start',0,rate*1800)
    integer(c['source_end_sample'],'trim end',c['source_start_sample']+1,rate*1800)
    if c['source_end_sample']-c['source_start_sample']!=n:raise AudioError('MIX_TRIM_CLOCK')
    if c['duration_frames']!=fps.at_or_after(n,rate):raise AudioError('MIX_FRAME_DURATION')
    if c['source_timeline_fingerprint']!=r['source_timeline_fingerprint'] or c['source_audio_sha256']!=r['source_audio_sha256']:raise AudioError('MIX_SOURCE_IDENTITY')
    tr=r['trim']['plan']
    if tr['keep_start']!=c['source_start_sample'] or tr['keep_end']!=c['source_end_sample'] or tr['sample_rate']!=rate:raise AudioError('MIX_TRIM_RECEIPT')
    scenes={};cursor=0;segment_ids=[]
    if type(c['scenes'])is not list or not c['scenes']:raise AudioError('MIX_SCENES')
    for row in c['scenes']:
        a,b=_interval(row,n,'scene');text(row['scene_id'],'scene id',2048)
        if row['scene_id']in scenes or a!=cursor:raise AudioError('MIX_SCENE_COVERAGE')
        if row['start_frame']!=fps.at_or_after(a,rate) or row['end_frame']!=fps.at_or_after(b,rate) or row['start_frame']>=row['end_frame']:raise AudioError('MIX_SCENE_FRAMES')
        scenes[row['scene_id']]=row;cursor=b;segment_ids.extend(row['segment_ids'])
    if cursor!=n:raise AudioError('MIX_SCENE_COVERAGE')
    if type(c['segments'])is not list or [p['segment_id'] for p in c['segments']]!=segment_ids or len(set(segment_ids))!=len(segment_ids):raise AudioError('MIX_SEGMENT_COVERAGE')
    cursor=0;segments={}
    for p in c['segments']:
        a,b=_interval(p,n,'segment');s=scenes[p['scene_id']]
        if a!=cursor or not s['start_sample']<=a<b<=s['end_sample'] or not a<p['provider_end_sample']<=b:raise AudioError('MIX_SEGMENT_CLOCK')
        segments[p['segment_id']]=p;cursor=b
    if cursor!=n:raise AudioError('MIX_SEGMENT_COVERAGE')
    for field in ('words','captions','pauses'):
        rows=c[field]
        if type(rows)is not list or len(rows)>200000:raise AudioError('MIX_EVENT_BUDGET')
        last=0
        for row in rows:
            a,b=_interval(row,n,field);p=segments[row['segment_id']]
            if a<last or not p['start_sample']<=a<b<=p['end_sample']:raise AudioError('MIX_EVENT_CLOCK',field)
            last=b
            if field=='words':text(row['spoken'],'spoken word')
            elif field=='captions':
                text(row['text'],'caption text')
                if type(row['lines'])is not list or not row['lines']:raise AudioError('MIX_CAPTION_LINES')
                for line in row['lines']:text(line,'caption line')
    if type(c['animations'])is not list or len(c['animations'])>4096:raise AudioError('MIX_ANIMATION_BUDGET')
    seen=set()
    for row in c['animations']:
        a,b=_interval(row,n,'animation');identifier=row['binding']['binding_id']
        if identifier in seen:raise AudioError('MIX_ANIMATION_DUPLICATE')
        seen.add(identifier)
        if row['start_frame']!=fps.at_or_after(a,rate) or row['end_frame']!=fps.at_or_after(b,rate):raise AudioError('MIX_ANIMATION_FRAMES')
        holds=row['holds'];end=a
        if type(holds)is not list:raise AudioError('MIX_ANIMATION_HOLDS')
        for lo,hi in holds:
            integer(lo,'hold start',end,b);integer(hi,'hold end',lo+1,b);end=hi
        if sum(y-x for x,y in holds)>=b-a:raise AudioError('MIX_ANIMATION_NO_ACTIVE_TIME')
        keys=[]
        for s in sorted({a,b,*(v for pair in holds for v in pair)}):
            q=track_progress(row,s);keys.append([s,q.numerator,q.denominator])
        if keys!=row['keyframes']:raise AudioError('MIX_ANIMATION_KEYFRAMES')
    final=r['peak_control']['after']
    if final['pcm_fingerprint']!=pcm.fingerprint() or (final['sample_rate'],final['channels'],final['frames'])!=(pcm.sample_rate,pcm.channels,n):raise AudioError('MIX_METER_BINDING')
    if r['peak_control']['output']!=pcm.info():raise AudioError('MIX_METER_OUTPUT')
    if r['policy']['pause_mode']=='all_stems_silent':
        for row in c['pauses']:
            if pcm.array()[row['start_sample']:row['end_sample']].any():raise AudioError('MIX_REQUIRED_SILENCE_LOST')


def track_progress(track,sample):
    a,b=track['start_sample'],track['end_sample'];holds=track['holds']
    if sample<=a:return Fraction(0)
    if sample>=b:return Fraction(1)
    total=b-a-sum(y-x for x,y in holds)
    elapsed=sample-a-sum(max(0,min(sample,y)-x) for x,y in holds if sample>x)
    return Fraction(elapsed,total)


def state_at_sample(clock,sample):
    integer(sample,'sample',0,192000*1800)
    c=clock
    return {'scene':next((s['scene_id'] for s in c['scenes'] if s['start_sample']<=sample<s['end_sample']),None),
            'captions':[x['text'] for x in c['captions'] if x['start_sample']<=sample<x['end_sample']],
            'words':[x['spoken'] for x in c['words'] if x['start_sample']<=sample<x['end_sample']],
            'pause':any(x['start_sample']<=sample<x['end_sample'] for x in c['pauses']),
            'animations':[{'binding_id':t['binding']['binding_id'],'target_id':t['binding']['target_id'],
                           'active':t['start_sample']<=sample<t['end_sample'], 'progress':float(track_progress(t,sample))} for t in c['animations']]}
