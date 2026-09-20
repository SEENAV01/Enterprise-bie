from .representation_core import *
H={'physics':('diagram','simulation','graph','equation','2d_model','3d_model'),'mathematics':('graph','equation','diagram'),'biology':('diagram','simulation','2d_model','3d_model'),'chemistry':('diagram','equation','2d_model','3d_model'),'geography':('map','diagram','graph'),'history':('timeline','map','diagram'),'economics':('graph','diagram','table')}
def generate(intent,max_candidates=8):
 if isinstance(max_candidates,bool) or not isinstance(max_candidates,int) or max_candidates<1:raise RepresentationError('max_candidates')
 reps=[]
 def add(r,why,c,caps=()):
  if r not in [x[0] for x in reps]:reps.append((r,why,c,caps))
 tags=set(intent.semantic_tags)
 if intent.spatial or {'location','route','region','geographic'}&tags:add('map','spatial/geographic semantics',.92,('2d',))
 if intent.temporal or {'chronology','sequence','period','event'}&tags:add('timeline','temporal ordering semantics',.92,('2d',))
 if intent.quantitative or {'function','trend','data','comparison'}&tags:add('graph','quantitative relation semantics',.90,('2d',))
 if intent.equation_present or {'formula','derivation','equation'}&tags:add('equation','symbolic relation is material',.94,('math_text',))
 if intent.dynamic:add('simulation','dynamic state/mechanism semantics',.88,('simulation',))
 if {'structure','relation','process','causal','system'}&tags or not reps:add('diagram','structural/relational explanation',.86,('2d',))
 for r in H.get(intent.domain,()):
  if len(reps)>=max_candidates:break
  add(r,'domain-compatible fallback',.70,('3d',) if r=='3d_model' else ())
 return tuple(Candidate(f'{intent.intent_id}:{i}:{r}',r,intent.evidence_refs,intent.reasoning_refs,tuple(caps),(why,),max(0,min(1,c-intent.uncertainty*.2))) for i,(r,why,c,caps) in enumerate(reps[:max_candidates],1))
