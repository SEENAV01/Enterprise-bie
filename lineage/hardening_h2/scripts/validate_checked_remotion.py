#!/usr/bin/env python3
"""Opt-in real execution for an H1 checked Scene-IR project, not the legacy fixture.

No network operation unless --install is supplied. Source, full pinned typecheck,
CLI composition discovery, real smoke/full rendering, and evidence verification
must all pass. Successful technical execution never grants product acceptance.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import re
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from bie.compiler.artifact_hashing import manifest_from_dict, verify_artifacts
from bie.compiler.checked_scene_compile import verify_checked_workspace
from bie.compiler.generated_code_regression import typecheck_generated_workspace
from bie.compiler.qa_common import digest
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.render_process import run_bounded_process
from bie.compiler.render_logs import verify_render_log
from bie.compiler.smoke_render import smoke_render
from bie.compiler.full_render import full_render


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project', type=Path)
    p.add_argument('--install', action='store_true', help='explicit permission to install pinned npm dependencies')
    p.add_argument('--browser', help='absolute operator-controlled browser executable')
    p.add_argument('--timeout', type=float, default=300)
    args = p.parse_args()
    root = args.project.absolute()
    run_id = 'checked-' + uuid.uuid4().hex[:16]
    stages = []
    record_dir = None
    failure = None
    passed = False
    try:
        if not 0 < args.timeout <= 86400:
            raise ValueError('timeout must be finite and between zero and 86400 seconds')
        if args.browser is not None and not Path(args.browser).is_absolute():
            raise ValueError('browser path must be absolute')
        checked = verify_checked_workspace(root)
        raw = json.loads((root / 'CHECKED_SCENE.json').read_text())
        doc, target = raw['document'], raw['target']
        descriptor = CompositionDescriptor('BieQA' + digest(doc['scene_id'])[:16],
            target['width'], target['height'], target['fps'],
            (doc['duration_ms'] * target['fps'] + 999) // 1000)
        stages.append({'stage': 'checked-source', 'passed': True, 'receipt': asdict(checked)})
        record_dir = root / 'validation-runs' / run_id
        record_dir.mkdir(parents=True, exist_ok=False)

        def process(stage, command):
            result = run_bounded_process(tuple(command), cwd=root, timeout_s=args.timeout)
            (record_dir / (stage + '.json')).write_text(json.dumps(asdict(result), indent=2))
            stages.append({'stage': stage, 'passed': result.process.passed,
                           'outcome': result.outcome, 'execution_kind': 'REAL_CHILD_PROCESS'})
            if not result.process.passed:
                raise ValueError(stage + ' failed: ' + result.outcome)
            return result

        if args.install:
            process('dependency-install', ['npm', 'ci' if (root / 'package-lock.json').exists() else 'install',
                    '--ignore-scripts', '--no-audit', '--no-fund', '--fetch-retries=0', '--fetch-timeout=15000'])
            verify_checked_workspace(root)
        else:
            stages.append({'stage': 'dependency-install', 'status': 'NOT_REQUESTED'})
        typed = typecheck_generated_workspace(root, timeout_s=args.timeout)
        stages.append({'stage': 'full-pinned-typecheck', 'passed': typed.status == 'PASS', 'receipt': asdict(typed)})
        if typed.status != 'PASS':
            raise ValueError('FULL_TYPECHECK_BLOCKED: ' + typed.status)
        command = ['node', str(root / 'node_modules/@remotion/cli/remotion-cli.js'),
                   'compositions', 'src/index.ts', '--log=info']
        if args.browser:
            command.append('--browser-executable=' + args.browser)
        discovery = process('real-cli-composition-discovery', command)
        if not re.search(r'(?<![A-Za-z0-9-])' + re.escape(descriptor.composition_id) + r'(?![A-Za-z0-9-])',
                         discovery.process.stdout):
            raise ValueError('expected composition ID not reported by the real CLI')
        for mode in ('smoke', 'full'):
            request = RenderRequest(str(root), 'src/index.ts', descriptor,
                'out/' + run_id + '-' + mode + '.mp4', checked.scene_fingerprint,
                run_id + '-' + mode, timeout_s=args.timeout, browser_executable=args.browser)
            verify_checked_workspace(root, render_request=request)
            result = (smoke_render(request, frame_count=min(12, descriptor.duration_in_frames))
                      if mode == 'smoke' else full_render(request))
            stages.append({'stage': mode, 'passed': result.passed, 'receipt': asdict(result)})
            if not result.passed:
                raise ValueError(mode + ' failed: ' + str(result.failure_code))
            evidence = root / result.evidence_directory
            manifest = manifest_from_dict(json.loads((evidence / 'ARTIFACT_MANIFEST.json').read_text()))
            if not verify_render_log(evidence / 'events.jsonl') or not verify_artifacts(root, manifest).passed:
                raise ValueError(mode + ' artifact/log evidence failed verification')
        passed = True
    except (OSError, ValueError, TypeError, KeyError) as exc:
        failure = str(exc)
    result = {'schema_version': 'bie.checked-render-validation.v1', 'run_id': run_id,
              'scope': 'CHECKED_SCENE_IR_TECHNICAL_EXECUTION', 'stages': stages,
              'passed': passed, 'failure': failure, 'accepted': False,
              'frame_visual_inspection': 'NOT_PERFORMED_BY_THIS_HARNESS',
              'real_book_e2e': 'NOT_RUN', 'learning_quality': 'NOT_EVALUATED'}
    if record_dir is not None:
        (record_dir / 'VALIDATION_RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if passed else 2

if __name__ == '__main__':
    raise SystemExit(main())
