#!/usr/bin/env python3
"""Ten reversible, in-memory fault controls; not extra test-method counts."""
import argparse,base64,hashlib,io,json,sys,unittest
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17')];sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.metrics import representation
from bie.evaluation.benchmarks.metrics.common import unit

def inventory():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for d in ['bie','tests','tools'] for p in sorted((ROOT/d).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def bypass(key,reasons,w=1):return unit(key,w,1,[])
original_box=representation.box
def clamp_box(value):
    x,y,w,h=original_box(value);return max(x,0),max(y,0),w,h

def raw_pixels_without_hash(row):return base64.b64decode(row['rgb_base64'])
CASES=[
('pedagogy-missing-activity-gate','pedagogy.result_unit',bypass,'test_metric_007.METRIC007Tests.test_authored_contract_002'),
('director-gap-coverage','direction.covered',lambda *a,**k:True,'test_metric_008.METRIC008Tests.test_authored_contract_005'),
('representation-clips-offscreen-boxes','representation.box',clamp_box,'test_metric_009.METRIC009Tests.test_negative_y_fails_visibility'),
('animation-interpolation-zero','animation.interpolate',lambda *a:Fraction(0),'test_metric_010.METRIC010Tests.test_authored_contract_001'),
('compile-exit-gate-bypass','compilation.result_unit',bypass,'test_metric_011.METRIC011Tests.test_authored_contract_002'),
('render-audio-requirement-ignored','rendering.boolean',lambda v:False,'test_metric_012.METRIC012Tests.test_required_audio_absent_fails'),
('frame-pixel-hash-not-verified','frame_quality.pixels',raw_pixels_without_hash,'test_metric_013.METRIC013Tests.test_authored_contract_005'),
('game-gain-floor-disabled','game_learning.amount',lambda *a,**k:Fraction(-1),'test_metric_014.METRIC014Tests.test_authored_contract_006'),
('accessibility-contrast-always-high','accessibility.contrast',lambda *a:21,'test_metric_015.METRIC015Tests.test_standard_text_777777_is_below_4_5'),
('reproducibility-difference-gate-bypassed','reproducibility.result_unit',bypass,'test_metric_016.METRIC016Tests.test_authored_contract_002')]

def run(name):
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromName(name)
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return result,stream.getvalue()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False);before=inventory();rows=[]
    for key,target,replacement,test in CASES:
        clean,log1=run(test)
        with patch('bie.evaluation.benchmarks.metrics.'+target,replacement):bad,log2=run(test)
        restored,log3=run(test)
        detected=clean.wasSuccessful() and len(bad.failures)>0 and not bad.errors and restored.wasSuccessful()
        rows.append({'fault_id':key,'patch_target':target,'test_id':test,'clean_passed':clean.wasSuccessful(),
                     'fault_assertion_failures':len(bad.failures),'fault_errors':len(bad.errors),'restored_passed':restored.wasSuccessful(),'detected':detected})
        (out/(key+'.txt')).write_text('CLEAN\n'+log1+'\nFAULT INJECTED\n'+log2+'\nRESTORED\n'+log3)
    result={'fault_count':len(rows),'detected':sum(x['detected'] for x in rows),'source_bytes_unchanged':before==inventory(),
            'extra_distinct_test_methods':0,'controls':rows,'independent_correctness_proof':False}
    (out/'FAULT_CONTROL_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return 0 if all(r['detected'] for r in rows) and result['source_bytes_unchanged'] else 1
if __name__=='__main__':raise SystemExit(main())
