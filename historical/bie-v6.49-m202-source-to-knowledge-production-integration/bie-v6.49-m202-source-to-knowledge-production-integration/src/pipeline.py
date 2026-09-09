from source import source,valid
from segments import segment,ordered
from evidence import evidence,grounded as evidence_grounded
from knowledge import concept,relationship,grounded as concept_grounded
from provenance import provenance,traceable
from verification import verification,passed

def build_source_to_knowledge():
    src=source("book-1","file://book.pdf","application/pdf","Physics Book","sha256:book")
    segs=ordered([
        segment("seg-2","book-1",2,1,"Electric charge is quantized."),
        segment("seg-1","book-1",1,1,"Charge is a conserved property.")
    ])
    ev=evidence("ev-1","book-1",["seg-1","seg-2"],
                "Charge is conserved and quantized.",0.98)
    c=concept("c-1","Electric Charge",
              "A conserved and quantized physical property.",["ev-1"])
    rel=relationship("r-1","c-1","c-1","SELF_REFERENCE",["ev-1"])
    pv=provenance("c-1",["book-1"],["ev-1"],"extract+normalize")
    vf=verification("v-1","c-1","PASS",["ev-1"])
    return {"schema_version":"6.49","source":src,"segments":segs,"evidence":ev,
            "concept":c,"relationship":rel,"provenance":pv,"verification":vf,
            "quality_gate":{"valid":valid(src) and evidence_grounded(ev)
             and concept_grounded(c) and traceable(pv) and passed(vf),"errors":[]}}
