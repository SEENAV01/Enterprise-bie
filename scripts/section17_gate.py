"""Run the adopted Section 17 suite and require its complete test identity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_METHODS = 2023  # 2018 recovered originals + 5 checkout-pin integration tests.


def complete(receipt: dict, returncode: int) -> bool:
    records = receipt.get('records', [])
    return (
        returncode == 0
        and receipt.get('all_passed') is True
        and receipt.get('source_changed_during_run') is False
        and receipt.get('tests_run') == EXPECTED_METHODS
        and receipt.get('unique_test_method_ids') == EXPECTED_METHODS
        and len(records) == EXPECTED_METHODS
        and len({row['test_id'] for row in records}) == EXPECTED_METHODS
        and all(row.get('status') == 'PASS' for row in records)
        and all(receipt.get(key) == 0 for key in ('failed', 'errors', 'skipped'))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    command = [sys.executable, '-B', str(ROOT / 'tools/run_section17_native_api_tests.py'),
               '--output-dir', str(output)]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    receipt_path = output / 'TEST_RESULT.json'
    if not receipt_path.is_file():
        return completed.returncode or 2
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    passed = complete(receipt, completed.returncode)
    result = {
        'schema_version': 'bie.section17.canonical-gate/1',
        'section17_methods_required': EXPECTED_METHODS,
        'section17_methods_observed': receipt.get('tests_run'),
        'suite_passed': passed,
        'source_inventory_sha256': receipt.get('candidate_inventory_sha256'),
        'section_complete': False,
        'product_accepted': False,
    }
    (output / 'GATE_RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
