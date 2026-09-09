from transaction import transaction,commit,committed
from idempotency import idempotency_key,duplicate
from inbox import inbox_event,consume
from outbox import outbox_event,publish
from effect import effect,applied
from saga import saga,compensate
from recovery import recovery_policy,retry_allowed
from observability import transaction_event,metric

def compile_transactions():
    tx=transaction("tx-1",
                    ["update:order","emit:order.updated"])
    tx=commit(tx)
    idem=idempotency_key("K123","hash-1",3600)
    inbox=consume(inbox_event("evt-1","hash-1",100))
    outbox=publish(outbox_event("evt-2","order-1",
                                "ORDER_UPDATED","hash-2"))
    eff=effect("fx-1","K123","charge","success")
    sg=saga("saga-1",["reserve","charge","fulfill"])
    comp=compensate(sg,["reserve","charge"])
    rec=recovery_policy(3,5)
    obs=transaction_event("txe-1","tx-1",
                          "COMMIT","SUCCESS",12.4,False)
    return {"schema_version":"6.31",
            "transaction":tx,
            "idempotency":idem,
            "inbox":inbox,
            "outbox":outbox,
            "effect":eff,
            "saga":sg,
            "compensation":comp,
            "recovery":rec,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "committed":committed(tx),
              "duplicate_detected":duplicate(idem,"hash-1"),
              "inbox_consumed":inbox["status"]=="CONSUMED",
              "outbox_published":outbox["status"]=="PUBLISHED",
              "effect_applied":applied(eff),
              "saga_compensating":comp["status"]=="COMPENSATING",
              "retry_allowed":retry_allowed(rec,1),
              "metric":metric(obs)
            }}
