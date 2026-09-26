#!/usr/bin/env python3
"""Real TypeScript language probe, NOT BIE render or product-acceptance evidence."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def invoke(command: list[str], root: Path) -> dict:
    p = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30, check=False)
    return {"command": command, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
            "execution_kind": "REAL_TSC_PROCESS"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tsc', required=True, help='Use the generated project node_modules/.bin/tsc for the pinned probe')
    parser.add_argument('--expected-version', default='5.9.3')
    parser.add_argument('--output', type=Path, required=True, help='New report path; never overwrites an existing result')
    args = parser.parse_args()
    version = subprocess.run([args.tsc, '--version'], capture_output=True, text=True, timeout=15, check=False)
    if version.returncode != 0 or version.stdout.strip() != 'Version ' + args.expected_version:
        raise SystemExit('TYPECHECK_PROBE_VERSION_MISMATCH:' + version.stdout + version.stderr)
    rows = []
    with tempfile.TemporaryDirectory(prefix='bie-r04-language-probe-') as temp:
        parent = Path(temp)
        for name in ('original_include_only', 'candidate_explicit_helper', 'candidate_excluded_user_file',
                     'candidate_strict_type_error', 'candidate_preserves_existing_files'):
            root = parent/name; root.mkdir()
            helper = 'export const measure = (options) => [options];\n'
            declaration = 'export function measure(options: {frame:number}):unknown[];\n'
            entry = 'import {measure} from "./qa-paint-helper"; export const values = measure({frame:1});\n'
            (root/'qa-paint-helper.js').write_text(helper)
            (root/'qa-paint-helper.d.ts').write_text(declaration)
            (root/'entry.ts').write_text(entry)
            cfg = {'compilerOptions': {'strict': True, 'allowJs': True, 'checkJs': False, 'noEmit': True,
                                      'module': 'ESNext', 'moduleResolution': 'Bundler'},
                   'include': ['entry.ts', 'qa-paint-helper.js', 'qa-paint-helper.d.ts']}
            if name == 'candidate_preserves_existing_files':
                (root/'extra.ts').write_text('export const extra: number = 1;\n')
                cfg['files'] = ['extra.ts']
            original_options = copy.deepcopy(cfg['compilerOptions'])
            if name != 'original_include_only':
                cfg['files'] = list(dict.fromkeys([*cfg.get('files', []), 'qa-paint-helper.js']))
            if name == 'candidate_excluded_user_file':
                (root/'uninspected.ts').write_text('export const unseen = 1;\n')
            if name == 'candidate_strict_type_error':
                (root/'entry.ts').write_text(entry + 'export const bad: number = "not a number";\n')
            (root/'tsconfig.json').write_text(json.dumps(cfg, indent=2)+'\n')
            listing = invoke([args.tsc, '--project', str(root/'tsconfig.json'), '--listFilesOnly', '--pretty', 'false'], root)
            checking = invoke([args.tsc, '--project', str(root/'tsconfig.json'), '--noEmit', '--pretty', 'false'], root)
            expected = {str(p.resolve()) for p in root.rglob('*') if p.is_file() and p.suffix in {'.ts','.tsx','.js','.jsx'}}
            included = set(listing['stdout'].splitlines())
            missing = sorted(Path(p).name for p in expected-included)
            coverage = listing['returncode'] == 0 and bool(expected) and expected <= included
            type_ok = checking['returncode'] == 0
            if name == 'original_include_only':
                observed = not coverage and missing == ['qa-paint-helper.js'] and type_ok
            elif name == 'candidate_excluded_user_file':
                observed = not coverage and missing == ['uninspected.ts']
            elif name == 'candidate_strict_type_error':
                observed = coverage and not type_ok and 'TS2322' in checking['stdout']
            else:
                observed = coverage and type_ok
            observed = observed and cfg['compilerOptions'] == original_options
            rows.append({'case': name, 'expectation_met': observed, 'configuration': cfg,
                         'coverage_satisfied': coverage, 'missing_sources': missing,
                         'strict_options_unchanged': cfg['compilerOptions'] == original_options,
                         'listing': listing, 'checking': checking})
    result = {'scope': 'MINIMAL_TYPESCRIPT_LANGUAGE_BEHAVIOR_ONLY', 'typescript_version': args.expected_version,
              'pinned_5_9_3_language_probe': args.expected_version == '5.9.3',
              'bie_actual_paint_validated': False, 'bie_render_validated': False, 'accepted': False,
              'cases_run': len(rows), 'cases_passed': sum(r['expectation_met'] for r in rows),
              'all_expectations_met': all(r['expectation_met'] for r in rows), 'cases': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'cases'}, indent=2))
    return 0 if result['all_expectations_met'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
