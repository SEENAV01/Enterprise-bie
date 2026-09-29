"""Offline unsigned QA: python -m bie.qa.source_v2 --help.

CLI intentionally has no trust-key flag: receipts cannot bring their own
trust. Use the Python API from an operator-provisioned runtime for assessments.
"""
import argparse
from pathlib import Path
import sys
from ..release_v2.contracts import ContractError, canonical_bytes
from .codec import load_request, MAX_REQUEST_JSON_BYTES
from .models import Policy
from .evaluator import evaluate


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--expected-output', action='append', required=True)
    p.add_argument('--as-of', type=int, required=True, help='explicit Unix timestamp for replay')
    args = p.parse_args(argv)
    try:
        with args.request.open('rb') as handle:
            data = handle.read(MAX_REQUEST_JSON_BYTES + 1)
        request = load_request(data)
        policy = Policy('bie-source-operator-policy-v1', tuple(args.expected_output))
        pair = evaluate(request, args.root, policy, as_of=args.as_of)
        sys.stdout.buffer.write(canonical_bytes(pair.to_dict()) + b'\n')
        return 0 if pair.grounding.status == pair.provenance.status == 'CHECKS_PASSED' else 2
    except (ContractError, OSError) as exc:
        code = exc.code if isinstance(exc, ContractError) else 'REQUEST_READ_FAILED'
        sys.stdout.buffer.write(canonical_bytes({'error': code, 'product_accepted': False}) + b'\n')
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
