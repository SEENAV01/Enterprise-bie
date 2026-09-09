import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from transaction import transaction,commit,committed,abort
from idempotency import idempotency_key,duplicate
from inbox import inbox_event,consume
from outbox import outbox_event,publish
from effect import effect,applied
from saga import saga,compensate
from recovery import recovery_policy,retry_allowed
from observability import transaction_event,metric

def test_transaction_idempotency():
 tx=commit(transaction("t",["a"]))
 assert committed(tx)
 assert not committed(abort(transaction("t",["a"])))
 k=idempotency_key("k","h")
 assert duplicate(k,"h") and not duplicate(k,"other")

def test_inbox_outbox_effect():
 assert consume(inbox_event("e","h"))["status"]=="CONSUMED"
 assert publish(outbox_event("e","a","T","h"))["status"]=="PUBLISHED"
 assert applied(effect("f","k","op"))

def test_saga_recovery_observability():
 s=saga("s",["a","b"])
 assert compensate(s,["a"])["status"]=="COMPENSATING"
 assert retry_allowed(recovery_policy(2,1),1)
 e=transaction_event("e","t","COMMIT","OK",1.0,False)
 assert metric(e)["status"]=="OK"
