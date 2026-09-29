"""Capture bounded synthetic H8 process diagnostics after a failed hosted gate."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests/qa_hardening_h8'))

from h8_helpers import pipeline_fixture  # noqa: E402
from bie.qa.assurance_quality_v2.harness import run_book  # noqa: E402


def diagnostic(all_stages: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix='bie-h8-diagnostic-') as folder:
        root = Path(folder)
        try:
            source, plan, binding = pipeline_fixture(root, all_stages=all_stages)
            result = run_book(source, root/'out', plan, binding)
        except Exception as exc:
            return {'fixture': 'all_15' if all_stages else 'first_2',
                    'exception_type': type(exc).__name__,
                    'exception_code': getattr(exc, 'code', None),
                    'exception_message': str(exc)[:300],
                    'completed_stages': None, 'product_accepted': False}
        records = result['details']['pipeline_records']
        first = records[0] if records else {}
        process = first.get('process', {})
        return {'fixture': 'all_15' if all_stages else 'first_2',
                'completed_stages': result['details']['completed_stages'],
                'report_status': result['report']['status'],
                'finding_codes': [row['code'] for row in result['report']['findings']],
                'first_record_stage': first.get('stage'),
                'first_record_error': first.get('error'),
                'first_process_error': process.get('error'),
                'first_process_exit_code': process.get('exit_code'),
                'first_process_stderr': process.get('stderr', '')[:1200],
                'first_process_stdout': process.get('stdout', '')[:1200],
                'product_accepted': False}


if __name__ == '__main__':
    evidence = {'schema_version': 'bie.qa.h8-synthetic-diagnostic/1',
                'runs': [diagnostic(False), diagnostic(True)],
                'not_a_test_result': True, 'product_accepted': False}
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(evidence, indent=2))
