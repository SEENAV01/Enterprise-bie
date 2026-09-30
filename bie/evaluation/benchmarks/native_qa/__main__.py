"""Operator CLI: read pinned requests, execute local QA component, retain exact reports.

External Python packages, artifact-root parents, input/output parents and approved
runtime binaries must be operator controlled. This command never provisions keys,
alters browser policy, publishes, installs packages or modifies a repository.
"""
from __future__ import annotations
import argparse
from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from ..models import BenchmarkError, canonical_json, strict_loads
from ..av.custody import Limits
from ..adoption.contracts import ExecutionContext
from .bridge import execute, verify_native_runtime, VERSION


def read_bounded(path, maximum):
    """No final symlink/FIFO/hardlink; caller owns immutable parent directories."""
    if not hasattr(os, 'O_NOFOLLOW'):
        raise BenchmarkError('NATIVE_QA_UNSUPPORTED_FILESYSTEM')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise BenchmarkError('NATIVE_QA_INPUT_NOT_REGULAR')
        if not 0 < before.st_size <= maximum:
            raise BenchmarkError('NATIVE_QA_INPUT_SIZE')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(maximum + 1)
        after = os.fstat(fd)
        identity = lambda s: (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)
        if len(raw) > maximum or len(raw) != before.st_size or identity(before) != identity(after):
            raise BenchmarkError('NATIVE_QA_INPUT_CHANGED')
        return raw
    finally:
        os.close(fd)


def _write(path, raw):
    with path.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())


def persist(output, result):
    """A fresh directory and receipt manifest; hashes are not authentication."""
    bodies = {'RESULT.json': (canonical_json(result) + '\n').encode('utf-8')}
    if result.get('native_component_consumer_executed') is True:
        raw = result['report_json'].encode('utf-8')
        if hashlib.sha256(raw).hexdigest() != result['report_sha256']:
            raise BenchmarkError('NATIVE_QA_REPORT_EXPORT_HASH')
        bodies['BENCHMARK_REPORT.json'] = raw
        bodies['NATIVE_ENVELOPE.json'] = (canonical_json(result['envelope']) + '\n').encode()
        bodies['NATIVE_QA_REPORT.json'] = (canonical_json(result['native_qa_report']) + '\n').encode()
    manifest = {name: {'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)}
                for name, raw in sorted(bodies.items())}
    for name, raw in bodies.items(): _write(output/name, raw)
    _write(output/'RECEIPT_MANIFEST.json', (canonical_json(manifest)+'\n').encode())
    return manifest


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate-bundle', 'checks', 'limits', 'artifact-root', 'expected-candidate-digest',
                 'expected-policy-digest', 'expected-checks-digest', 'output-dir'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--as-of', type=int, required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    output = Path(args.output_dir)
    # Never overwrite another attempt, including through a final symlink.
    try:
        output.mkdir(mode=0o700, parents=False, exist_ok=False)
    except OSError as exc:
        print(json.dumps({'status':'BLOCKED','error_code':'NATIVE_QA_OUTPUT_NOT_FRESH',
                          'exception_type':type(exc).__name__,'release_authorized':False}), file=sys.stderr)
        return 2
    try:
        verify_native_runtime()
        from bie.qa.release_v2.codec import loads
        bundle = loads(read_bounded(args.candidate_bundle, 4*1024**2))
        if bundle.evidence:
            raise BenchmarkError('NATIVE_QA_INJECTED_EVIDENCE_REJECTED')
        checks = strict_loads(read_bounded(args.checks, 2_000_000).decode('utf-8'))
        raw_limits = strict_loads(read_bounded(args.limits, 16_384).decode('utf-8'))
        if type(raw_limits) is not dict or set(raw_limits) != {f.name for f in fields(Limits)}:
            raise BenchmarkError('NATIVE_QA_EXPLICIT_LIMITS_REQUIRED')
        context = ExecutionContext(Path(args.artifact_root), Limits(**raw_limits))
        result = execute(bundle.candidate, checks, execution_context=context, as_of=args.as_of,
                         expected_candidate_digest=args.expected_candidate_digest,
                         expected_policy_digest=args.expected_policy_digest,
                         expected_checks_digest=args.expected_checks_digest)
    except Exception as exc:
        # Known validation codes are retained; unknown failures cannot emit PASS.
        result = {'schema_version':VERSION,'status':'BLOCKED',
                  'error_code':getattr(exc,'code','NATIVE_QA_OPERATOR_EXCEPTION'),
                  'exception_type':type(exc).__name__,
                  'native_component_consumer_executed':False,
                  'canonical_application_caller_adopted':False,
                  'release_authorized':False,'product_accepted':False}
    try:
        persist(output, result)
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','error_code':'NATIVE_QA_PERSISTENCE_FAILED',
                          'exception_type':type(exc).__name__,'release_authorized':False}), file=sys.stderr)
        return 2
    print(json.dumps({'status':'BLOCKED','native_component_consumer_executed':
                     result.get('native_component_consumer_executed', False),
                     'measurement_outcomes':result.get('measurement_outcomes',{}),
                     'error_code':result.get('error_code'),
                     'release_authorized':False,'product_accepted':False},sort_keys=True))
    # All current slice outcomes are release-blocking, including technical positives.
    return 2

if __name__ == '__main__':
    raise SystemExit(main())
