from node import node,valid
from dependency_graph import topological_order
from incremental import scope
from batch import batch,valid as bvalid
from scheduler import levels
from cache import entry,reusable
from provenance import provenance,traceable
from verification import verification,passed
def build():
 ns=[node("chapter-1","CHAPTER","source://ch1"),node("lesson-1","LESSON","source://l1",["chapter-1"],"3"),node("lesson-2","LESSON","source://l2",["chapter-1"],"2"),node("lesson-3","LESSON","source://l3",["lesson-1","lesson-2"]),node("lesson-4","LESSON","source://l4",["lesson-3"])]
 order=topological_order(ns); sched=levels(ns,order,2); b=batch("batch-1","course-1",order,2); sc=scope(["lesson-2"],ns)
 caches=[entry("lesson-1","h1",["a1"]),entry("lesson-2","h2",["a2"]),entry("lesson-3","h3",["a3"]),entry("lesson-4","h4",["a4"])]
 rebuilt=sc["affected_nodes"]; prov=provenance(b["batch_id"],b["course_ref"],order,["lesson-2"],rebuilt,["artifact://"+x for x in rebuilt]); v=verification("verify-batch","batch-1","PASS")
 return {"schema_version":"6.62","course_manifest":{"course_id":"course-1","title":"Physics Foundations","nodes":ns},"dependency_graph":{"nodes":ns},"topological_order":order,"parallel_schedule":sched,"batch_job":b,"change_detection":{"changed_node_ids":["lesson-2"]},"incremental_scope":sc,"cache_entries":caches,"rebuilt_nodes":rebuilt,"provenance":prov,"verification":v,"quality_gate":{"valid":all(valid(n) for n in ns) and bvalid(b) and traceable(prov) and passed(v)}}
