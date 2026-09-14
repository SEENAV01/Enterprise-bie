"""Run every preserved DIR test plus batch-014 completion hardening gates."""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,io,json,platform,sys,time,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/director'))
NEW={
 'BIE-DIR-HARD-RICH-CODECS-001':('test_hard_rich_codecs_001.py',),
 'BIE-DIR-HARD-TEACHING-MODES-001':('test_hard_teaching_modes_001.py',),
 'BIE-DIR-HARD-AUTH-GRADING-001':('test_hard_authenticated_grading_001.py',),
 'BIE-DIR-HARD-SCENE-CORRECTION-001':('test_hard_scene_correction_001.py','test_hard_selective_annotation_reuse_001.py'),
 'BIE-DIR-HARD-DURABLE-RECOVERY-001':('test_hard_durable_recovery_001.py',),
 'BIE-DIR-HARD-HIERARCHICAL-DISCOURSE-001':('test_hard_hierarchical_discourse_001.py','test_hard_hierarchical_review_001.py'),
 'BIE-DIR-HARD-PRODUCTION-ADOPTION-001':('test_hard_production_adoption_001.py',),
 'BIE-DIR-HARD-BENCHMARK-CALIBRATION-001':('test_hard_benchmark_calibration_001.py',),
}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'verification/dir_completion_tests.json')
    args=parser.parse_args();records=[];started=time.monotonic()
    for path in sorted((ROOT/'tests/director').glob('test_*.py')):
        spec=importlib.util.spec_from_file_location(path.stem,path);module=importlib.util.module_from_spec(spec)
        sys.modules[path.stem]=module;spec.loader.exec_module(module)
        log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        records.append({'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'passed':result.wasSuccessful(),'log':log.getvalue()})
    summary={key:sum(row[key] for row in records) for key in ('tests','failures','errors','skipped')}
    by_name={Path(row['file']).name:row for row in records}
    task_counts={task:sum(by_name[name]['tests'] for name in names) for task,names in NEW.items()}
    new_names={name for names in NEW.values() for name in names}
    summary.update(test_files=len(records),passed=bool(records) and all(row['passed'] for row in records),
        python=platform.python_version(),previous_DIR_tests=sum(row['tests'] for row in records if Path(row['file']).name not in new_names),
        new_completion_tests=sum(task_counts.values()),new_task_tests=task_counts,duration_seconds=round(time.monotonic()-started,3))
    report={'executed_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'All preserved DIR tests plus implementation-completion hardening; authored/protocol fixtures are not live-provider, real-PDF, rendered-media, gameplay or product-acceptance evidence.',
        'accepted':False,'summary':summary,'files':records}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(summary))
    for row in records:
        if not row['passed']:print(row['log'])
    return 0 if summary['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
