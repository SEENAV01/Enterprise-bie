#!/usr/bin/env python3
"""Opt-in dependency install, strict compile, CLI discovery, smoke and full render.

For the generated technical fixture only. Never grants product acceptance.
Install is explicit, not hidden inside a render API. Stage failures stop the run.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from bie.compiler.artifact_hashing import manifest_from_dict, verify_artifacts
from bie.compiler.render_process import run_bounded_process
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.smoke_render import smoke_render
from bie.compiler.full_render import full_render
from bie.compiler.render_logs import verify_render_log
from bie.compiler.generated_lint import lint_generated_sources
from bie.compiler.generated_static_analysis import analyze_generated_sources
from bie.compiler.build_common import BuildError

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--install', action='store_true', help='explicitly permit npm dependency installation')
    parser.add_argument('--browser', default='/usr/bin/chromium')
    parser.add_argument('--timeout', type=float, default=300, help='per-process budget in seconds')
    args=parser.parse_args()
    root=args.project.resolve();run_id='validation-'+uuid.uuid4().hex[:16]
    stages=[];passed=False;failure=None
    record_dir=root/'validation-runs'/run_id
    try:
        if not root.is_dir():raise BuildError('project directory missing')
        fixture=json.loads((root/'FIXTURE_SOURCE.json').read_text())
        if fixture.get('kind')!='TECHNICAL_COMPILER_FIXTURE_NOT_A_LESSON':
            raise BuildError('this validation harness requires the explicitly labelled generated fixture')
        record_dir.mkdir(parents=True,exist_ok=False)
        def process(stage,command):
            r=run_bounded_process(command,cwd=root,timeout_s=args.timeout)
            (record_dir/(stage+'.json')).write_text(json.dumps(asdict(r),indent=2))
            stages.append({'stage':stage,'passed':r.process.passed,'outcome':r.outcome})
            if not r.process.passed:raise BuildError(stage+' failed: '+r.outcome)
            return r
        if args.install:
            command=('npm','ci' if (root/'package-lock.json').exists() else 'install',
                     '--ignore-scripts','--no-audit','--no-fund','--fetch-retries=0','--fetch-timeout=15000')
            process('dependency-install',command)
        else:
            stages.append({'stage':'dependency-install','status':'NOT_REQUESTED_EXISTING_LOCAL_DEPENDENCIES_REQUIRED'})
        process('typescript',(str(root/'node_modules/.bin/tsc'),'--noEmit','--pretty','false'))
        for name,gate in (('lint',lint_generated_sources),('static-analysis',analyze_generated_sources)):
            r=gate(root/'src');(record_dir/(name+'.json')).write_text(json.dumps(asdict(r),indent=2))
            stages.append({'stage':name,'passed':r.passed})
            if not r.passed:raise BuildError(name+' failed')
        discovery=process('composition-discovery',('node',str(root/'node_modules/@remotion/cli/remotion-cli.js'),
                          'compositions','src/index.ts','--log=info',f'--browser-executable={args.browser}'))
        if fixture['composition_id'] not in discovery.process.stdout:
            raise BuildError('CLI did not report the expected fixture composition ID')
        for mode in ('smoke','full'):
            raw=json.loads((root/(mode+'-request.json')).read_text())
            raw['workspace']=str(root);raw['composition']=CompositionDescriptor(**raw['composition'])
            raw['run_id']=run_id+'-'+mode;raw['output_path']='out/'+raw['run_id']+'.mp4'
            raw['browser_executable']=args.browser;raw['timeout_s']=args.timeout
            request=RenderRequest(**raw)
            receipt=smoke_render(request,frame_count=12) if mode=='smoke' else full_render(request)
            stages.append({'stage':mode,'passed':receipt.passed,'receipt':asdict(receipt)})
            if not receipt.passed:raise BuildError(mode+' failed: '+str(receipt.failure_code))
            evidence=root/receipt.evidence_directory
            manifest=manifest_from_dict(json.loads((evidence/'ARTIFACT_MANIFEST.json').read_text()))
            if not verify_render_log(evidence/'events.jsonl') or not verify_artifacts(root,manifest).passed:
                raise BuildError(mode+' evidence integrity failed')
        passed=True
    except (BuildError,OSError,ValueError,TypeError,KeyError) as exc:
        failure=str(exc)
    result={'schema_version':'bie.technical-render-validation.v1','run_id':run_id,'passed':passed,
            'accepted':False,'scope':'GENERATED_TECHNICAL_COMPILER_FIXTURE_ONLY','stages':stages,
            'failure':failure,'real_book_e2e':'NOT_RUN','learning_quality':'NOT_EVALUATED'}
    if record_dir.is_dir():
        (record_dir/'VALIDATION_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
