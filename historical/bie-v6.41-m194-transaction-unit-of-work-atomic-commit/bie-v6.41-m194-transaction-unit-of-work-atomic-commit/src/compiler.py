from transaction import transaction,open_tx
from unit_of_work import unit_of_work,add_operation
from read_write_set import read_write_set,overlaps
from prepare import prepare,prepared
from commit import commit,committed
from rollback import rollback,rolled_back
from conflict import conflict,detected
from idempotency import idempotency,matches
from savepoint import savepoint,valid
from audit import transaction_event,successful
from observability import transaction_metric,healthy

def compile_transaction():
    tx=transaction("tx-1","SERIALIZABLE",5000,"idem-1")
    uow=unit_of_work("uow-1","tx-1")
    uow=add_operation(uow,{"operation":"UPDATE","resource":"artifact:1"})
    rw=read_write_set(["artifact:1"],["artifact:1"])
    prep=prepare("tx-1",rw,"validation-1")
    cm=commit("tx-1","commit-1")
    rb=rollback("tx-2","CONFLICT")
    cf=conflict("tx-2","tx-1","artifact:1")
    idem=idempotency("idem-1","hash-1","result-1")
    sp=savepoint("tx-1","before-update",1)
    ev=transaction_event("txe-1","tx-1","COMMIT","SUCCESS","service-1")
    met=transaction_metric("txm-1","tx-1","COMMIT","SUCCESS",24,0)
    return {"schema_version":"6.41","transaction":tx,
            "unit_of_work":uow,"read_write_set":rw,
            "prepare":prep,"commit":cm,"rollback":rb,
            "conflict":cf,"idempotency":idem,"savepoint":sp,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "transaction_open":open_tx(tx),
              "uow_operation_count":len(uow["operations"])==1,
              "rw_overlap":overlaps(rw,rw),
              "prepared":prepared(prep),
              "committed":committed(cm),
              "rolled_back":rolled_back(rb),
              "conflict_detected":detected(cf),
              "idempotency_match":matches(idem,"idem-1","hash-1"),
              "savepoint_valid":valid(sp),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
