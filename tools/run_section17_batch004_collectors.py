#!/usr/bin/env python3
"""Fresh real tool execution on authored fixtures; not a native BIE/Remotion run."""
import argparse,json,sys,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from bie.evaluation.benchmarks.models import BenchmarkError,digest
from bie.evaluation.benchmarks.metrics.collectors import compile_source,decode_media,snapshot_outputs
from bie.evaluation.benchmarks.metrics import evaluate,evaluator_code_sha256
from bie.evaluation.benchmarks.metrics.service import MetricRunStore

def fixture(i):return json.loads((ROOT/'bie/evaluation/benchmarks/metrics/fixtures'/f'BIE-EVAL-METRIC-{i:03d}.json').read_text())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=False)
    source='def square(value: int) -> int:\n    return value * value\n'
    py=compile_source('python',source,'fresh-python',out/'python')
    ts=compile_source('typescript','export const square = (x: number): number => x * x;\n','fresh-typescript',out/'typescript')
    badpy=compile_source('python','def broken(:\n','invalid-python',out/'invalid-python')
    badts=compile_source('typescript','const invalid: number = "bad";\n','invalid-typescript',out/'invalid-typescript')
    second=compile_source('python',source,'fresh-python-second',out/'python-second')
    media,frames=decode_media(ROOT/'tests/section17/assets/batch004/reference_video.mkv','fresh-media',[0,6,11],out/'media')
    malformed=out/'invalid.media';malformed.write_bytes(b'not a valid video');block=None
    try:decode_media(malformed,'invalid-media')
    except BenchmarkError as exc:block=exc.code
    bindings={'inputs_sha256':hashlib.sha256(source.encode()).hexdigest(),'recipe_sha256':digest({'profile':'python-checked-hash-bytecode-v1'}),
              'environment_sha256':digest({'python':sys.version,'platform':sys.platform}),'seed':0}
    one=snapshot_outputs(out/'python/output','fresh-snapshot-one',**bindings)
    two=snapshot_outputs(out/'python-second/output','fresh-snapshot-two',**bindings)
    submissions=[(11,fixture(11)['reference'],{'artifacts':[{'id':'python','observation_id':'python','source_sha256':py['subject_sha256']},{'id':'typescript','observation_id':'typescript','source_sha256':ts['subject_sha256']}]},{'python':py,'typescript':ts}),
                 (12,fixture(12)['reference'],{'artifacts':[{'id':'lesson','observation_id':'render','media_sha256':media['subject_sha256']}]},{'render':media}),
                 (13,fixture(13)['reference'],{'observation_id':'frames','media_sha256':frames['subject_sha256']},{'frames':frames})]
    repro=fixture(16)['reference'];repro['payload'].update(bindings)
    # Authored reference provenance changes together with the changed build context.
    repro['source_refs'][0]['basis_sha256']=digest(repro['payload'])
    submissions.append((16,repro,{'observation_ids':['first','second']},{'first':one,'second':two}))
    reports=[]
    with MetricRunStore(out/'actual_collector_metric_runs.sqlite3') as store:
        for i,r,c,art in submissions:
            task=f'BIE-EVAL-METRIC-{i:03d}'
            for name,obj in [('REFERENCE',r),('CANDIDATE',c),('OBSERVATIONS',art)]:(out/f'{task}_{name}.json').write_text(json.dumps(obj,indent=2)+'\n')
            receipt=store.execute(run_id='actual:'+task,campaign_id='actual:'+task,metric_id=task,reference=r,candidate=c,
                   expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),source_artifacts=art)
            (out/f'{task}_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n');reports.append(receipt['report'])
    summary={'actual_compiler_invocations':5,'valid_python_emitted':py['facts']['exit_code']==0 and py['facts']['output_bytes']>0,
             'valid_typescript_emitted':ts['facts']['exit_code']==0 and ts['facts']['output_bytes']>0,
             'invalid_python_rejected':badpy['facts']['exit_code']!=0 and badpy['facts']['output_bytes']==0,
             'invalid_typescript_rejected':badts['facts']['exit_code']!=0 and badts['facts']['output_bytes']==0,
             'fully_decoded_video_frames':media['facts']['decoded_frames'],'rgb_frame_samples':len(frames['facts']['frames']),
             'corrupt_media_blocked':block=='MEDIA_PROBE_FAILED','separately_compiled_python_bytes_equal':one['facts']['outputs']==two['facts']['outputs'],
             'four_metric_outcomes':[r.get('outcome',r['status']) for r in reports],'actual_store_used':True,
             'evaluator_code_sha256':evaluator_code_sha256(),'native_bie':False,'remotion':False,'product_accepted':False}
    ok=all(summary[k] for k in ['valid_python_emitted','valid_typescript_emitted','invalid_python_rejected','invalid_typescript_rejected','corrupt_media_blocked','separately_compiled_python_bytes_equal']) and all(r.get('outcome')=='PASS' for r in reports)
    summary['all_expected_behaviors_matched']=ok
    (out/'ACTUAL_COLLECTOR_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
