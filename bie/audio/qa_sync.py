"""QA-004 exact clock revalidation, separate from acoustic/video observation."""
from .qa_contract import Finding,check,TASKS
from .mix_pipeline import verify_mixed_source
from .sync_contract import FrameRate
from .mix_clock import state_at_sample

def sync_qa(mixed,sync):
    verify_mixed_source(mixed,sync);c=mixed.clock();fps=FrameRate(**c['fps']);points={0,c['total_samples']}
    for family in ('words','captions','pauses','scenes','animations'):
        for row in c[family]:
            for p in (row['start_sample'],row['end_sample']):points.update((max(0,p-1),p,min(c['total_samples'],p+1)))
    ordered=sorted(points);forward=[state_at_sample(c,p) for p in ordered];backward=list(reversed([state_at_sample(c,p) for p in reversed(ordered)]))
    fs=[]
    if forward!=backward:fs.append(Finding('SEEK_STATE_NONDETERMINISTIC','FAIL','AUDIO/SYNC','clock','Boundary state changed on reverse seek.'))
    fs.extend((Finding('INDEPENDENT_ACOUSTIC_ALIGNMENT_UNVERIFIED','REVIEW','AUDIO/SYNC','word-timing','Engine word onsets/end windows are not independently detected phonetic word offsets.'),
        Finding('ACTUAL_RENDERED_AV_SYNC_UNVERIFIED','REVIEW','AUDIO/COMP','render','No actual rendered video playback measurements were supplied to this check.')))
    return check(TASKS[3],'Exact typed source/derived clock replay and boundary seek checks',fs,
        {'boundary_sample_positions':len(ordered),'forward_reverse_equal':forward==backward,'frames':c['duration_frames'],
         'sample_rate':c['sample_rate'],'frame_rate':{'numerator':fps.numerator,'denominator':fps.denominator},
         'acoustic_alignment_verified':False,'rendered_video_verified':False})
