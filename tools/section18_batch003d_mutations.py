"""Qualified seeded fault controls: baseline pass first, no test inflation."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator import administration as module
tests=load('tests/section18/test_batch003d.py');original=module.require
def bypass(code):return patch.object(module,'require',lambda cond,c,status=409:None if c==code else original(cond,c,status))
original_queue=module.Administration.queue
def mutating_read(self,p,*args,**kwargs):
    with self.s.catalog.tx(read_only=True) as db:
        run=db.execute('SELECT id FROM intents WHERE tenant=?',(p.tenant,)).fetchone()[0]
        _,body=self.s.catalog.intent(db,p,run)
        with self.s.native(body) as native:native.queue.stats()
    return original_queue(self,p,*args,**kwargs)
original_recovery=module.Administration.recover_dead_letter
def unsafe_redrive(self,p,run_id,*args,**kwargs):
    with self.s.catalog.tx(read_only=True) as db:
        _,body=self.s.catalog.intent(db,p,run_id)
        with self.s.native(body) as native:native.queue.redrive('inspect-'+body['native_job_id'][4:])
    return original_recovery(self,p,run_id,*args,**kwargs)
def false_replay_state(self,*args,**kwargs):
    result=original_recovery(self,*args,**kwargs)
    if result['replayed']:result['child_status']='READY'
    return result
controls=[('no_synthetic_health_promotion',tests.Admin001,'test_health_origin_cannot_promote_test_provider',bypass('admin_origin_promotion')),
 ('no_plaintext_secret_reference',tests.Admin001,'test_raw_secret_reference_rejected',bypass('secret_reference_invalid')),
 ('no_enable_without_bound_adapter',tests.Admin001,'test_restart_cannot_enable_unbound_provider',bypass('provider_adapter_not_bound')),
 ('queue_get_must_not_mutate',tests.Admin003,'test_queue_get_does_not_recover_expired_or_poll',patch.object(module.Administration,'queue',mutating_read)),
 ('no_terminal_parent_redrive',tests.Admin004,'test_recovery_never_calls_unsafe_native_redrive',patch.object(module.Administration,'recover_dead_letter',unsafe_redrive)),
 ('replay_current_state_truthful',tests.Admin004,'test_completed_child_replay_not_falsely_ready',patch.object(module.Administration,'recover_dead_letter',false_replay_state))]
rows=[]
for name,cls,method,mutant in controls:
    transcript=io.StringIO();baseline=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
    assert baseline.wasSuccessful(),'MUTATION_BASELINE_NOT_PASS:'+name
    with mutant:result=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
    rows.append(dict(control=name,killed=bool(result.failures),harness_error=bool(result.errors),baseline_passed=True,
                     transcript=transcript.getvalue(),new_distinct_tests=0))
receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,new_distinct_tests=0,product_accepted=False)
path=Path(sys.argv[1]);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)))
raise SystemExit(not receipt['passed'])
