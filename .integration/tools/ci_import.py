"""Read-only-token validation job. It creates local commits, never pushes."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
from import_plan import BASE, git, verify_tree
CAPSULE_SHA = '17ce2d9700ccb6227a7fb86a879a5f39c4e5ebec535980a7cdf446a2e961d9b4'
PLAN_SHA = '63a2596d48b75bf4d9d16d5dd95635b6b557990f3a62b804899e5581e1eb81de'
BRANCH = 'integration/post-dir-catchup-20260919'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def run_logged(command, root, log):
    with log.open('w') as stream:
        env = dict(os.environ)
        for key in ('GITHUB_OUTPUT','GITHUB_ENV','GITHUB_PATH','GITHUB_STEP_SUMMARY'):
            env.pop(key, None)
        result = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    print(log.read_text()[-10000:], flush=True)
    if result.returncode: raise RuntimeError('GATE_FAILED: ' + log.name)

def require_results(tests, preservation):
    s = tests['summary']
    if s.get('passed') is not True or s.get('tests_run') != 6485:
        raise ValueError('INCOMPLETE_REGRESSION')
    if any(s.get(k) != 0 for k in ('failed_files', 'failures', 'errors', 'skipped')):
        raise ValueError('REGRESSION_FAILURE_OR_SKIP')
    if preservation.get('passed') is not True or preservation.get('errors') != []:
        raise ValueError('PRESERVATION_FAILURE')
    expected = {'supplied_files_verified':386,'source_member_mappings_verified':6014,
                'unique_zip_archives_verified':435,'nested_member_occurrences_verified':83616}
    if any(preservation.get(k) != v for k,v in expected.items()):
        raise ValueError('INCOMPLETE_PRESERVATION')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--trigger',required=True)
    a=p.parse_args();root=a.root.resolve();work=a.work.resolve()
    if work.is_relative_to(root):raise ValueError('WORK_MUST_BE_OUTSIDE_CHECKOUT')
    control=Path(__file__).resolve().parent
    if git(root,'rev-parse','HEAD') != a.trigger:raise ValueError('TRIGGER_CHANGED')
    capsule=root/'.integration/post-dir-catchup/BIE_POST_DIR_CANONICAL_TRANSFER.tar.xz'
    if digest(capsule)!=CAPSULE_SHA:raise ValueError('CAPSULE_SHA256_MISMATCH')
    subprocess.run([sys.executable,str(control/'import_plan.py'),str(capsule),
                    '--sha256',CAPSULE_SHA,'--root',str(root),'--work',str(work)],check=True)
    if digest(work/'capsule/plan.json')!=PLAN_SHA:raise ValueError('PLAN_SHA256_MISMATCH')
    if digest(root/'requirements-comp-h3.txt')!=digest(control/'requirements-validation.txt'):
        raise ValueError('VALIDATION_PROFILE_MISMATCH')
    plan=json.loads((work/'capsule/plan.json').read_text());head=git(root,'rev-parse','HEAD')
    evidence=work/'evidence';evidence.mkdir();publish=work/'publish';publish.mkdir()
    from diagnose_worker import diagnose
    diagnose(root, evidence)
    # Existing tests only: catch runner misconfiguration before the long suite.
    # Their execution is additional evidence, not counted as new unique tests.
    run_logged([sys.executable,'-B','-m','unittest',
                'tests.compiler.test_comp_h7_004','tests.compiler.test_comp_h2_004',
                'tests.compiler.test_comp_h9_005'],root,evidence/'runner-preflight.log')
    run_logged([sys.executable,'-B','scripts/integrated_check.py','--output-dir',str(evidence)],root,evidence/'integrated-gate.log')
    run_logged([sys.executable,'-B','scripts/verify_post_dir.py','--output',str(evidence/'post-dir-preservation.json')],root,evidence/'post-dir-preservation.log')
    tests=json.loads((evidence/'integrated_tests.json').read_text())
    preservation=json.loads((evidence/'post-dir-preservation.json').read_text())
    require_results(tests,preservation)
    if git(root,'rev-parse','HEAD')!=head or git(root,'status','--porcelain'):
        raise ValueError('TESTS_CHANGED_REPOSITORY')
    count=verify_tree(root,head,plan)
    bundle=publish/'adoption.bundle'
    subprocess.run(['git','-C',str(root),'bundle','create',str(bundle),'HEAD','^'+a.trigger],check=True)
    shutil.copy2(work/'capsule/plan.json',publish/'plan.json')
    receipt={'schema_version':'bie.github-integration-verification.v1','trigger_commit':a.trigger,
        'candidate_commit':head,'candidate_tree':git(root,'rev-parse','HEAD^{tree}'),
        'base_commit':BASE,'capsule_sha256':CAPSULE_SHA,'plan_sha256':PLAN_SHA,
        'bundle_sha256':digest(bundle),'phases':json.loads((work/'APPLIED.json').read_text())['phases'],
        'final_mapped_blobs_verified':count,'tests':tests['summary'],'preservation':preservation,
        'run_id':os.environ.get('GITHUB_RUN_ID'),'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
        'historical_corpus_complete':False,'runtime_accepted':False,'product_accepted':False,
        'scope':'All supplied files and canonical source adoption; not complete historical artifact availability or actual Remotion acceptance.'}
    (publish/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    shutil.copy2(publish/'receipt.json',evidence/'receipt.json')
    subprocess.run(['git','-C',str(root),'archive','--format=zip','-o',str(evidence/'VERIFIED_CANDIDATE_REPOSITORY.zip'),head],check=True)
    outputs={'bundle_sha256':digest(bundle),'receipt_sha256':digest(publish/'receipt.json'),
             'candidate_commit':head,'candidate_tree':receipt['candidate_tree']}
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            for key,value in outputs.items():f.write(f'{key}={value}\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
