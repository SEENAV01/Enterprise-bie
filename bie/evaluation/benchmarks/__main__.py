"""Offline Section 17 diagnostic/structured-output CLI; no native acceptance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from .models import BenchmarkError, canonical_json, digest, strict_loads
from .registry import Registry
from .versioning import VersionStore
from .anti_gaming import AttemptLedger
from .runner import PACK_MODULES, load_pack, reference_output
from .session import grade_submission


def write_json(path: Path, value: object) -> None:
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def prepare(registry: Registry, cases):
    existing = {c.case_id:c for c in registry.all_cases()}
    fresh=[]
    for c in cases:
        if c.case_id in existing and c != existing[c.case_id]:
            raise BenchmarkError('EXISTING_FIXTURE_CONFLICT')
        if c.case_id not in existing: fresh.append(c)
    if fresh: registry.register(fresh)
    store=VersionStore(registry)
    dataset_id='section17-authored-'+digest(sorted(c.content_sha256 for c in cases))[:16]
    try: snapshot=store.get(dataset_id,'1.0.0')
    except BenchmarkError as exc:
        if exc.code!='SNAPSHOT_NOT_FOUND': raise
        snapshot=store.create(dataset_id,'1.0.0',[c.case_id for c in cases])
    if tuple(sorted(c.content_sha256 for c in snapshot.cases)) != tuple(sorted(c.content_sha256 for c in cases)):
        raise BenchmarkError('FIXTURE_SNAPSHOT_MISMATCH')
    return snapshot


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    diag=sub.add_parser('diagnostic',help='Replay authored references, not BIE/golden scores')
    diag.add_argument('--output-dir',required=True)
    export=sub.add_parser('export-prompts',help='Export development inputs without expected answers')
    export.add_argument('--output',required=True)
    grade=sub.add_parser('grade',help='Grade supplied structured answers; identity is operator-attested only')
    grade.add_argument('--answers',required=True)
    grade.add_argument('--candidate-sha',required=True)
    grade.add_argument('--database',required=True,help='Operator-owned persistent SQLite ledger')
    grade.add_argument('--campaign-id',required=True)
    grade.add_argument('--run-id',required=True)
    grade.add_argument('--output-dir',required=True)
    args=parser.parse_args(argv)
    output=None
    try:
        cases=[c for task in PACK_MODULES for c in load_pack(task)]
        if args.command=='export-prompts':
            write_json(Path(args.output),{'schema_version':'1.0.0','split':'DEVELOPMENT',
                'evidence_grade':'AUTHORED_DIAGNOSTIC','cases':[c.candidate_view() for c in cases]})
            return 0
        output=Path(args.output_dir).resolve()
        output.mkdir(parents=True,exist_ok=False)
        database=output/'diagnostic.sqlite3' if args.command=='diagnostic' else Path(args.database)
        if args.command=='diagnostic':
            answers=[{'case_id':c.case_id,'output':reference_output(c.task_id,c.inputs)} for c in cases]
            modules=Path(__file__).parent
            code_identity={p.relative_to(modules).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(modules.rglob('*.py'))}
            candidate_sha=digest(code_identity)
            campaign='AUTHORED_REFERENCE_REPLAY';run_id='diagnostic-run'
        else:
            with Path(args.answers).open('rb') as stream: raw=stream.read(2_000_001)
            if len(raw)>2_000_000: raise BenchmarkError('SUBMISSION_SIZE_LIMIT')
            answers=strict_loads(raw)
            candidate_sha=args.candidate_sha;campaign=args.campaign_id;run_id=args.run_id
        with Registry(database) as registry:
            snapshot=prepare(registry,cases)
            ledger=AttemptLedger(registry)
            policy=digest({'schema_version':'1.0.0','grading':'strict-schema-and-case-tolerance',
                'roster':'complete-frozen-development-split','release_authorized':False})
            ledger.start(run_id=run_id,campaign_id=campaign,candidate_sha256=candidate_sha,
                policy_sha256=policy,snapshot=snapshot,split='DEVELOPMENT')
            result=grade_submission(ledger,run_id,snapshot,answers)
            if args.command=='diagnostic':
                result['scope']='AUTHORED_REFERENCE_REPLAY_NOT_BIE_BENCHMARK'
            result['operator_supplied_candidate_identity']=args.command=='grade'
            result['registry_audit_head']=registry.audit_head()
            write_json(output/'RESULT.json',result)
            write_json(output/'CASE_GRADES.json',result['case_grades'])
            write_json(output/'DATASET_MANIFEST.json',snapshot.public_manifest())
        print(json.dumps({'status':result['report']['status'],
            'passed':result['report']['passed_count'],'denominator':result['report']['denominator'],
            'scope':result['scope'],'product_accepted':False}))
        return 0 if result['report']['status']=='PASS' else 1
    except (BenchmarkError,OSError) as exc:
        code=exc.code if isinstance(exc,BenchmarkError) else type(exc).__name__
        error={'status':'BLOCKED','error_code':code,'product_accepted':False,'release_authorized':False}
        if output is not None and output.is_dir() and not (output/'ERROR.json').exists() and not (output/'RESULT.json').exists():
            # A newly created output directory is the only place we write diagnostics.
            # Existing output directories are refused before any processing.
            if not isinstance(exc,FileExistsError): write_json(output/'ERROR.json',error)
        print(json.dumps(error),file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(main())
