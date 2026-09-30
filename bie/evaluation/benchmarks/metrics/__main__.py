"""Offline candidate-driven metric CLI. This is not a native BIE adapter."""
from __future__ import annotations
import argparse,json,sqlite3,sys
from pathlib import Path
from ..models import BenchmarkError,MAX_BYTES,digest,strict_loads
from . import ALL_MODULES
from .service import MetricRunStore

def load(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise BenchmarkError('INPUT_NOT_REGULAR_FILE')
    if path.stat().st_size>MAX_BYTES:raise BenchmarkError('INPUT_SIZE_LIMIT')
    return strict_loads(path.read_bytes())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metric',required=True,choices=sorted(ALL_MODULES));p.add_argument('--reference',required=True)
    p.add_argument('--candidate',required=True);p.add_argument('--reference-sha',required=True)
    p.add_argument('--candidate-sha',required=True);p.add_argument('--source-artifacts')
    p.add_argument('--database',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--campaign-id',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args()
    try:
        reference=load(a.reference);candidate=load(a.candidate)
        artifacts=load(a.source_artifacts) if a.source_artifacts else {}
        out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False)
        with MetricRunStore(a.database) as store:
            receipt=store.execute(run_id=a.run_id,campaign_id=a.campaign_id,metric_id=a.metric,
                reference=reference,candidate=candidate,expected_reference_sha256=a.reference_sha,
                expected_candidate_sha256=a.candidate_sha,source_artifacts=artifacts)
        with (out/'METRIC_RESULT.json').open('x',encoding='utf-8') as f:
            json.dump(receipt,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
        report=receipt['report'];print(json.dumps({'status':report['status'],'outcome':report.get('outcome'),
            'score_exact':report.get('score_exact'),'product_accepted':False}))
        return 2 if report['status']=='BLOCKED' else 0 if report['outcome']=='PASS' else 1
    except (BenchmarkError,OSError,sqlite3.Error) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'product_accepted':False}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
