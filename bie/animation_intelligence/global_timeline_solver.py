from dataclasses import dataclass
class TimelineSolveError(ValueError):pass
@dataclass(frozen=True)
class TrackRequest: track_id:str;desired_start_ms:int;duration_ms:int;cue_start_ms:int;cue_end_ms:int;priority:float=.5;exclusive_group:str|None=None;can_shift:bool=True
@dataclass(frozen=True)
class ScheduledTrack: track_id:str;start_ms:int;end_ms:int
@dataclass(frozen=True)
class TimelineResult: scheduled:tuple[ScheduledTrack,...];unsat_core:tuple[str,...];solved:bool
def solve(requests):
    requests=tuple(requests)
    if not requests:raise TimelineSolveError("requests required")
    seen=set();out=[];unsat=[]
    for r in sorted(requests,key=lambda x:(-x.priority,x.desired_start_ms,x.track_id)):
        if r.track_id in seen:raise TimelineSolveError("duplicate")
        seen.add(r.track_id)
        if r.duration_ms<1 or r.cue_end_ms<=r.cue_start_ms:raise TimelineSolveError("bad request")
        s=max(r.desired_start_ms,r.cue_start_ms);e=s+r.duration_ms
        conflicts=[x for x in out if r.exclusive_group and any(q.track_id==x.track_id and q.exclusive_group==r.exclusive_group for q in requests) and max(s,x.start_ms)<min(e,x.end_ms)]
        if conflicts and r.can_shift:
            s=max(x.end_ms for x in conflicts);e=s+r.duration_ms
        if e>r.cue_end_ms or any(max(s,x.start_ms)<min(e,x.end_ms) and r.exclusive_group and any(q.track_id==x.track_id and q.exclusive_group==r.exclusive_group for q in requests) for x in out):
            unsat.append(r.track_id);continue
        out.append(ScheduledTrack(r.track_id,s,e))
    return TimelineResult(tuple(sorted(out,key=lambda x:(x.start_ms,x.track_id))),tuple(sorted(unsat)),not unsat)
