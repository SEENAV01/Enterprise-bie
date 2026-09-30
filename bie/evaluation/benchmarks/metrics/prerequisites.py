"""METRIC-003: prerequisite closure and teach-before-use on a trusted DAG."""
from ..models import BenchmarkError,ident
from ..domains.structured import record
from .common import ids,indexed,topological,unit,weight

def measure(reference,candidate,artifacts):
    record(reference, {'nodes','edges','targets','known_prior'});record(candidate, {'teaching_order'})
    nodes=set(ids(reference['nodes'],lower=1));targets=set(ids(reference['targets'],lower=1));known=set(ids(reference['known_prior']))
    if not targets<=nodes or not known<=nodes:raise BenchmarkError('UNKNOWN_REFERENCE_NODE')
    refs=indexed(reference['edges'],{'id','weight','prerequisite','dependent'})
    edges=[];parents={n:[] for n in nodes}
    for row in refs.values():
        weight(row);a,b=ident(row['prerequisite']),ident(row['dependent']);edges.append((a,b))
        if b in parents:parents[b].append(a)
    topological(nodes,edges)
    order=ids(candidate['teaching_order']);pos={n:i for i,n in enumerate(order)}
    if not set(pos)<=nodes:raise BenchmarkError('UNKNOWN_CANDIDATE_NODE')
    required=set();todo=list(targets-known)
    while todo:
        n=todo.pop()
        if n in required or n in known:continue
        required.add(n);todo.extend(parents[n])
    # At least one actual learning target is required; not vacuously perfect.
    if not required:raise BenchmarkError('NO_UNMASTERED_TARGET_IN_PROFILE')
    units=[]
    for n in sorted(required):
        units.append(unit('node:'+n,1,1 if n in pos else 0,[] if n in pos else ['REQUIRED_NODE_MISSING']))
    for key,row in sorted(refs.items()):
        a,b=row['prerequisite'],row['dependent']
        if b not in required:continue
        reasons=[]
        if b not in pos:reasons=['DEPENDENT_NOT_TAUGHT']
        elif a not in known and (a not in pos or pos[a]>=pos[b]):reasons=['PREREQUISITE_NOT_BEFORE_USE']
        units.append(unit('edge:'+key,weight(row),0 if reasons else 1,reasons))
    return units,[],{'assessment_scope':'DECLARED_TEACHING_ORDER_AND_TRUSTED_PRIOR_KNOWLEDGE',
                     'required_nodes':sorted(required),'learner_mastery_measured':False}
