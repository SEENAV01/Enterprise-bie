#!/usr/bin/env python3
"""Fixed synthetic H6 source-contract benchmark, not audio/learning acceptance.

Every case is compiled in three independent processes. Expected outcomes are
versioned in the corpus before execution, never learned from the result.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT)]

def worker(path: Path) -> int:
    from bie.compiler.hardened_scene_compile import compile_h3_scene
    from bie.compiler.qa_common import CompilerQAError
    from tests.compiler.h6_test_support import BIG
    case=json.loads(path.read_text())
    try:
        r=compile_h3_scene(case['document'],target=BIG)
        result={'source_passed':r.receipt.source_gate_passed,'manifest_sha256':r.codegen.manifest_sha256,
                'codes':sorted({f.code for f in r.receipt.findings})}
    except CompilerQAError as e:
        result={'source_passed':False,'manifest_sha256':None,'codes':[str(e).split(':',1)[0]]}
    print(json.dumps(result,sort_keys=True));return 0

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path);p.add_argument('--worker',type=Path)
    a=p.parse_args()
    if a.worker:return worker(a.worker)
    if a.output is None:p.error('--output is required')
    if a.output.exists():raise ValueError('Output must be fresh')
    a.output.mkdir(parents=True)
    corpus=json.loads((ROOT/'fixtures/comp_h6/source_corpus.json').read_text())
    rows=[]
    env={**os.environ,'PYTHONPATH':str(ROOT/'app')+os.pathsep+str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'}
    for case in corpus['cases']:
        source=a.output/(case['case_id']+'.input.json');source.write_text(json.dumps(case,ensure_ascii=False))
        outcomes=[]
        for i in range(3):
            q=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(source)],
                             cwd=ROOT,env=env,capture_output=True,text=True,timeout=45)
            (a.output/(case['case_id']+f'.run{i}.log')).write_text(q.stdout+'\nSTDERR\n'+q.stderr)
            if q.returncode:raise RuntimeError(q.stderr or 'Worker failure')
            outcomes.append(json.loads(q.stdout))
        want=case['expected_source_pass']
        matched=all(o==outcomes[0] for o in outcomes) and outcomes[0]['source_passed']==want
        if not want:matched=matched and case['expected_code'] in outcomes[0]['codes']
        rows.append({'case_id':case['case_id'],'expected_source_pass':want,'expected_code':case.get('expected_code'),
                     'outcomes':outcomes,'matched':matched,'expected_content_fit':case.get('expected_content_fit')})
    result={'scope':'SYNTHETIC_SOURCE_CONTRACTS_NOT_RENDER_OR_SPEECH','cases':rows,'runs_per_case':3,
            'independent_processes':3*len(rows),'all_matched':all(r['matched'] for r in rows),
            'source_pass_cases':sum(r['expected_source_pass'] for r in rows),
            'expected_source_rejections':sum(not r['expected_source_pass'] for r in rows),
            'accepted':False}
    (a.output/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps(result,indent=2));return 0 if result['all_matched'] else 2
if __name__=='__main__':raise SystemExit(main())
