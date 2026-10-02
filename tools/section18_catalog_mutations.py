"""Baseline-qualified catalogue faults, not additional distinct tests."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator.catalog import Catalog
from apps.operator.catalog_budget import CatalogBudget
from apps.operator.contracts import digest
tests=load('tests/section18/test_batchh1b.py')
reserve=Catalog.reserve_worker;inventory=CatalogBudget.inventory
def insufficient_credits(self,db,worker):
    reserve(self,db,worker);db.execute('UPDATE audit_reservations SET credits=2 WHERE id=?',(worker,))
def row_bypass(self,db):
    old=self.max_row_bytes;object.__setattr__(self,'max_row_bytes',65536)
    try:return inventory(self,db)
    finally:object.__setattr__(self,'max_row_bytes',old)
def no_reservation_projection(self,db):
    self.budget.inventory(db)
    state={t:[list(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1,2')] for t in ('sources','intents','graphs')}
    for t in ('provider_versions','workers','governance_versions','governance_active'):
        order='1,2,3,4' if t=='governance_versions' else '1,2,3'
        rows=[list(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY '+order)]
        if rows:state[t]=rows
    return digest(state)
def no_reserved_admission(self,stats,reserved_credits=0):
    if stats['reserved']:return None
    return admit(self,stats,reserved_credits)
admit=CatalogBudget.admit
controls=[
 ('pre_external_admission','test_old_source_producer_cannot_bypass_global_cap',patch.object(CatalogBudget,'admit',lambda *args:None)),
 ('worker_receipt_credits','test_worker_succeeds_at_exact_reserved_capacity',patch.object(Catalog,'reserve_worker',insufficient_credits)),
 ('files_before_sqlite','test_oversized_database_rejected_before_sqlite_connection',patch.object(CatalogBudget,'files',lambda *args:None)),
 ('row_before_decode','test_oversized_history_row_rejected_before_json_decoding',patch.object(CatalogBudget,'inventory',row_bypass)),
 ('authoritative_replay','test_integrity_is_replayed_not_cached',patch.object(Catalog,'verify',lambda self,db:self.budget.inventory(db))),
 ('reservation_seal','test_reservation_tamper_is_detected',patch.object(Catalog,'projection',no_reservation_projection)),
 ('protected_credit_admission','test_other_producer_cannot_steal_worker_completion_credits',patch.object(CatalogBudget,'admit',no_reserved_admission)),
]
rows=[]
for name,method,mutation in controls:
    transcript=io.StringIO()
    baseline=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([tests.CatalogHardening(method)]))
    assert baseline.wasSuccessful() and not baseline.skipped,'BASELINE_NOT_PASS:'+name
    with mutation:result=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([tests.CatalogHardening(method)]))
    rows.append(dict(control=name,method=method,baseline_passed=True,killed=bool(result.failures),
        harness_error=bool(result.errors),transcript=transcript.getvalue(),new_distinct_tests=0))
receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,
    new_distinct_tests=0,product_accepted=False)
path=Path(sys.argv[1]);assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)))
raise SystemExit(not receipt['passed'])
