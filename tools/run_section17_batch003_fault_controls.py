#!/usr/bin/env python3
"""Inject ten controlled faults in memory; record test sensitivity before/after.

Fault detections are not extra passing test methods or independent correctness
proof. Each selected named test must pass before, fail under its fault, and pass
again after automatic restoration; physical source bytes stay unchanged.
"""
from pathlib import Path
import argparse,hashlib,importlib,io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17')];sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import canonical_json

def run_test(name):
    stream=io.StringIO();suite=unittest.TestLoader().loadTestsFromName(name)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return {'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skips':len(result.skipped),'passed':result.wasSuccessful() and result.testsRun==1 and not result.skipped,'log':stream.getvalue()}
def inventory():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((ROOT/'bie').rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def domain_fault(module,transform):
    m=importlib.import_module('bie.evaluation.benchmarks.domains.'+module);real=m.solve
    def wrong(data):
        result=real(data);transform(result);return result
    return patch.object(m,'solve',wrong)
def metric_fault(module):
    m=importlib.import_module('bie.evaluation.benchmarks.metrics.'+module);real=m.measure
    def wrong(*a,**k):
        units,defects,details=real(*a,**k)
        for unit in units:unit['credit']='1';unit['reasons']=[]
        return units,[],details
    return patch.object(m,'measure',wrong)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False);before=inventory();records=[]
    domain_specs=[('GEO002_SCALE_FAULT','maps','test_geo_002.GEO002Tests.test_scale_units_equivalent',lambda d:d.update(ground_m='0')),
        ('GEO003_BUDGET_FAULT','climate','test_geo_003.GEO003Tests.test_global_budget_energy_conserved',lambda d:d.update(absorbed_W_m2='0')),
        ('CIV001_PREMATURE_ACT_FAULT','civics','test_civ_001.CIV001Tests.test_assent_after_only_one_house_not_act',lambda d:d.update(act_in_this_profile=True)),
        ('DATA001_MEAN_FAULT','tables_charts','test_data_001.DATA001Tests.test_summary_negative_values_exact',lambda d:d.update(mean='0'))]
    specs=[(label,test,lambda m=module,t=transform:domain_fault(m,t)) for label,module,test,transform in domain_specs]
    for i,module in enumerate(('grounding','semantic','prerequisites','reasoning','mathematics','causality'),1):
        specs.append((f'METRIC{i:03d}_FALSE_PERFECT_CREDIT',f'test_metric_{i:03d}.METRIC{i:03d}Tests.test_authored_candidate_002',lambda m=module:metric_fault(m)))
    for label,test,context in specs:
        clean=run_test(test)
        with context():injected=run_test(test)
        restored=run_test(test)
        detected=clean['passed'] and not injected['passed'] and injected['tests_run']==1 and injected['failures']>=1 and injected['errors']==0 and restored['passed']
        records.append({'fault_id':label,'test_id':test,'detected':detected,'before':clean,'fault':injected,'restored':restored})
    summary={'scope':'TEN_CONTROLLED_IN_MEMORY_FAULT_SENSITIVITY_CHECKS','faults':len(records),'detected':sum(r['detected'] for r in records),
        'source_bytes_unchanged':before==inventory(),'source_inventory_sha256':hashlib.sha256(canonical_json(before).encode()).hexdigest(),
        'records':records,'additional_distinct_test_methods':0,'product_accepted':False}
    (out/'FAULT_CONTROLS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
    return 0 if all(r['detected'] for r in records) and before==inventory() else 1
if __name__=='__main__':raise SystemExit(main())
