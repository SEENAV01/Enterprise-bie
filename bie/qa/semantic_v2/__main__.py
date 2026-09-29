"""Offline audit CLI. Trust defaults to denial; no credentials accepted in JSON."""
import argparse, sys
from pathlib import Path
from ..release_v2.contracts import ContractError, canonical_bytes
from ..source_v2.codec import load_assessments as load_source_assessments, MAX_REQUEST_JSON_BYTES
from .codec import load_request, load_policy, load_assessments
from .evaluator import evaluate


def read_bounded(path):
    with Path(path).open('rb') as f:
        data = f.read(MAX_REQUEST_JSON_BYTES + 1)
    if len(data) > MAX_REQUEST_JSON_BYTES: raise ContractError('WIRE_FILE_TOO_LARGE')
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', required=True); p.add_argument('--policy', required=True,
        help='Operator-provisioned policy file, separate from generated request.')
    p.add_argument('--artifact-root', required=True); p.add_argument('--as-of', required=True, type=int)
    p.add_argument('--assessments'); p.add_argument('--source-assessments')
    args = p.parse_args(argv)
    try:
        result = evaluate(load_request(read_bounded(args.request)), args.artifact_root,
            load_policy(read_bounded(args.policy)), as_of=args.as_of,
            assessments=load_assessments(read_bounded(args.assessments)) if args.assessments else (),
            source_assessments=load_source_assessments(read_bounded(args.source_assessments)) if args.source_assessments else ())
        sys.stdout.buffer.write(canonical_bytes(result.to_dict()) + b'\n')
        return {'CHECKS_PASSED': 0, 'REVIEW_REQUIRED': 3, 'BLOCKED': 2}[result.status]
    except (ContractError, OSError) as exc:
        sys.stderr.write((exc.code if isinstance(exc, ContractError) else 'INPUT_IO_ERROR') + '\n')
        return 64

if __name__ == '__main__': raise SystemExit(main())
