"""Exact declared-plan measures. These are not cognitive-capacity estimates."""
from collections import defaultdict
from fractions import Fraction
from ..release_v2.contracts import digest

def text_identity(claims,ids):
    # Merge overlapping spans first; ID aliases and replayed events must not
    # manufacture distinct examples/questions. This is textual deduplication,
    # not a claim of semantic novelty or paraphrase detection.
    grouped=defaultdict(list)
    for cid in ids:
        if cid in claims:grouped[claims[cid].output_id].append(claims[cid])
    parts=[]
    for rows in grouped.values():
        end=-1;piece=''
        for c in sorted(rows,key=lambda c:(c.start,c.end,c.claim_id)):
            if c.start>end:
                if piece:parts.append(' '.join(piece.split()).casefold())
                piece=c.text;end=c.end
            elif c.end>end:
                piece+=c.text[end-c.start:];end=c.end
        if piece:parts.append(' '.join(piece.split()).casefold())
    return digest(' '.join(sorted(set(parts))))

def text_codepoints(claims,ids):
    # Union spans per actual output; overlapping declarations cannot inflate count.
    grouped=defaultdict(list)
    for cid in ids:
        if cid in claims:
            c=claims[cid];grouped[c.output_id].append(c)
    total=0
    for rows in grouped.values():
        end=-1
        for c in sorted(rows,key=lambda c:(c.start,c.end,c.claim_id)):
            begin=max(c.start,end)
            if begin<c.end:
                total+=sum(not ch.isspace() for ch in c.text[begin-c.start:])
                end=c.end
    return total

def overlaps(a,b):
    return a.output_id==b.output_id and max(a.start,b.start)<min(a.end,b.end)

def event_windows(events):
    """Half-open intervals; exits are applied before entries at the same instant."""
    changes=defaultdict(lambda:[[],[]]);index={e.event_id:e for e in events}
    for e in events:changes[e.start_ms][1].append(e.event_id);changes[e.end_ms][0].append(e.event_id)
    active=set();times=sorted(changes)
    for i,t in enumerate(times[:-1]):
        off,on=changes[t];active.difference_update(off);active.update(on)
        if active and times[i+1]>t:
            es=[index[k] for k in sorted(active)]
            yield (t,times[i+1],sum(e.visual_units for e in es),sum(e.motion_units for e in es),len(set().union(*(set(e.new_concept_ids) for e in es))),tuple(sorted(active)))

def rate(codepoints,duration_ms):return Fraction(codepoints*60000,duration_ms)
