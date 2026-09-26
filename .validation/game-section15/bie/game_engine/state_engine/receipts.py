from __future__ import annotations
from ..canonical import fingerprint
from .contracts import TransitionReceipt

def transition_receipt_id(command_id,rule_id,before,deltas,implementation_material):
    seed={'command_id':command_id,'rule_id':rule_id,'before_snapshot_id':before.snapshot_id,'deltas':deltas,'implementation_fingerprint':fingerprint(implementation_material)}
    return 'transition:'+fingerprint(seed)[7:31]

def make_transition_receipt(command_id,rule_id,before,after,deltas,implementation_material):
    impl=fingerprint(implementation_material);rid=transition_receipt_id(command_id,rule_id,before,deltas,implementation_material)
    r=TransitionReceipt(rid,command_id,rule_id,before.snapshot_id,after.snapshot_id,tuple(deltas),fingerprint(before),fingerprint(after),impl,True,False)
    return r.validate()
