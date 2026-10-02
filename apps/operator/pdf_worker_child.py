"""Trusted one-job child. Resource enforcement precedes engine imports."""
from pathlib import Path
import argparse
import json
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from apps.operator.process_limits import PdfProcessBudget, enforce_current_process


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--memory', type=int, required=True)
    parser.add_argument('--cpu', type=int, required=True)
    args = parser.parse_args()
    enforcement = enforce_current_process(PdfProcessBudget(memory_bytes=args.memory, cpu_seconds=args.cpu))
    from apps.operator.contracts import Credentials, Principal, PERMISSIONS
    from apps.operator.service import Service
    credentials = Credentials()
    principal = Principal('local-operator', 'local', PERMISSIONS, time.time() + 3600)
    credentials.grant(os.environ.get('BIE_OPERATOR_TOKEN', ''), principal)
    result = Service(args.data_root, credentials).work_once(principal, args.run_id)
    print(json.dumps(dict(enforcement=enforcement, result=result), sort_keys=True))


if __name__ == '__main__':
    try:main()
    except Exception:raise SystemExit(2) from None
