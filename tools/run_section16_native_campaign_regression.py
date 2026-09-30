#!/usr/bin/env python3
"""Run the unchanged upstream durable/worker module against this staged runtime.

Separate native component regression, not a canonical repository test census.
"""
from pathlib import Path
import argparse,hashlib,io,json,os,sys,time,unittest
ROOT=Path(__file__).resolve().parents[1]
TESTS=ROOT.parent/'native_tests/qa_hardening_h6'
sys.path[:0]=[str(ROOT),str(TESTS),str(ROOT/'tools')]
sys.dont_write_bytecode=True
from run_section17_native_campaign_tests import RecordedResult

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 a.output_dir.mkdir(parents=True,exist_ok=False)
 os.environ['PYTHONPATH']=os.pathsep.join([str(ROOT),str(TESTS)])
 before={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in TESTS.glob('*.py')}
 suite=unittest.defaultTestLoader.discover(str(TESTS),pattern='test_durable_workers.py');f=io.StringIO();start=time.time()
 r=unittest.TextTestRunner(stream=f,verbosity=2,resultclass=RecordedResult).run(suite)
 result=dict(scope='UNCHANGED_SECTION16_H6_DURABLE_WORKERS_AGAINST_COMBINED_SOURCE',command=sys.argv,
  tests_run=r.testsRun,records=list(r.records.values()),all_passed=r.wasSuccessful() and not r.skipped,
  duration_seconds=time.time()-start,source_tests=before,full_repository_regression=False,product_accepted=False)
 (a.output_dir/'TEST_RESULT.txt').write_text(f.getvalue());(a.output_dir/'TEST_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'tests_run':r.testsRun,'all_passed':result['all_passed']}));return 0 if result['all_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
