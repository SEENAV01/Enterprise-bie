#!/usr/bin/env python3
"""Run actual task tests and save candidate-bound, non-inflated evidence."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sqlite3
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


def inventory():
    paths = sorted(p for folder in ('bie','tests','tools') for p in (ROOT/folder).rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.records={}
    def startTest(self,test):
        super().startTest(test); self.records[test.id()]={'test_id':test.id(),'status':'RUNNING'}
    def addSuccess(self,test):
        super().addSuccess(test)
        if self.records[test.id()]['status']=='RUNNING': self.records[test.id()]['status']='PASS'
    def addFailure(self,test,err):
        super().addFailure(test,err);self.records[test.id()]['status']='FAIL'
    def addError(self,test,err):
        super().addError(test,err);self.records[test.id()]['status']='ERROR'
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.records[test.id()]['status']='SKIP'
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err is not None:self.records[test.id()]['status']='FAIL'
    def stopTest(self,test):
        if self.records[test.id()]['status']=='RUNNING': self.records[test.id()]['status']='PASS'
        super().stopTest(test)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--pattern',default='test_*.py')
    args=parser.parse_args()
    output=Path(args.output_dir).resolve()
    output.mkdir(parents=True,exist_ok=False)
    before=inventory()
    started=time.time();stream=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/section17'),pattern=args.pattern)
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult).run(suite)
    records=sorted(result.records.values(),key=lambda r:r['test_id'])
    changed=inventory()!=before
    outcome={
        'schema_version':'1.0.0','command':sys.argv,'python':sys.version,'platform':platform.platform(),
        'sqlite_version':sqlite3.sqlite_version,'scope':'LOCAL_SECTION17_CUMULATIVE_THROUGH_BATCH004',
        'started_unix':started,'duration_seconds':time.time()-started,
        'tests_run':result.testsRun,'unique_test_method_ids':len(records),
        'passed':sum(r['status']=='PASS' for r in records),
        'failed':sum(r['status']=='FAIL' for r in records),'errors':sum(r['status']=='ERROR' for r in records),
        'skipped':sum(r['status']=='SKIP' for r in records),
        'source_changed_during_run':changed,'records':records,
        'candidate_inventory_sha256':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'all_passed':result.wasSuccessful() and not changed and not result.skipped,
        'canonical_regression_run':False,'native_bie_run':False,'product_accepted':False,
        'counting_note':'Subtests, repeated verification runs and diagnostic replay cases are not additional test methods.'}
    (output/'TEST_RESULT.txt').write_text(stream.getvalue(),encoding='utf-8')
    (output/'TEST_RESULT.json').write_text(json.dumps(outcome,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (output/'CANDIDATE_INVENTORY.json').write_text(json.dumps(before,indent=2)+'\n')
    print(json.dumps({k:outcome[k] for k in ('tests_run','passed','failed','errors','skipped','all_passed','candidate_inventory_sha256')},indent=2))
    return 0 if outcome['all_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
