from __future__ import annotations
from ..canonical import fingerprint
from .contracts import BuildReceipt

def make_receipt(task_id,input_value,output_value,toolchain_fingerprint,evidence_refs):
    body={'task_id':task_id,'input':fingerprint(input_value),'output':fingerprint(output_value),'toolchain':toolchain_fingerprint};rid='build:'+fingerprint(body)[7:31]
    return BuildReceipt(rid,task_id,fingerprint(input_value),fingerprint(output_value),toolchain_fingerprint,tuple(sorted(set(evidence_refs))),True,False).validate()
