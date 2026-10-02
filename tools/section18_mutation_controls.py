"""Seeded bypasses must be killed by existing authored tests; not new tests."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load

def main():
    t=load('tests/section18/test_batch001.py')
    from apps.operator.contracts import Credentials
    from apps.operator.service import Service
    import apps.operator.service as svc
    import apps.operator.graphs as graph
    native_require=svc.require;graph_require=graph.require
    def unsafe_worker(service,p,run_id):
        with service.catalog.tx() as db:_,body=service.catalog.intent(db,p,run_id)
        with service.native(body) as native:return dict(outcome=native.run_once().outcome,dispatched=True)
    rows=[('authorization_bypass',t.Run001,'test_no_create_permission',patch.object(Credentials,'check',lambda *a:None)),
          ('pause_admission_bypass',t.Run008,'test_pause_stops_real_dispatch_not_just_ui',patch.object(Service,'work_once',unsafe_worker)),
          ('graph_source_bypass',t.Graph001,'test_graph_source_mismatch_rejected',
           patch.object(svc,'require',lambda cond,code,status=409:None if code=='graph_source_mismatch' else native_require(cond,code,status))),
          ('prerequisite_relation_bypass',t.Graph002,'test_wrong_relation_type_rejected',
           patch.object(graph,'require',lambda cond,code,status=409:None if code=='invalid_prerequisite_relation' else graph_require(cond,code,status)))]
    receipts=[]
    for name,cls,method,mutant in rows:
        stream=io.StringIO()
        with mutant:result=unittest.TextTestRunner(stream=stream).run(unittest.TestSuite([cls(method)]))
        receipts.append(dict(mutation=name,authored_test=cls.__name__+'.'+method,killed=bool(result.failures),
                             harness_error=bool(result.errors),counted_as_new_test=False))
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
    value=dict(passed=all(r['killed'] and not r['harness_error'] for r in receipts),controls=receipts,
               new_distinct_tests=0,product_accepted=False)
    out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value))
    return 0 if value['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
