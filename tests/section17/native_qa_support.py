"""Authored component fixtures; never a native book/game generation claim."""
from pathlib import Path
from dataclasses import replace
from functools import lru_cache
import tempfile,hashlib,shutil,atexit
from copy import deepcopy
from h3_support import fixture,TD,LIMITS
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.adoption.contracts import ExecutionContext
from bie.evaluation.benchmarks.native_qa.bridge import execute,PIN
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate
from bie.qa.release_v2.policy import enterprise_policy
NOW=1790701200

def inputs(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    checks=[]
    for n in (12,13,15):
        r,c=fixture(n)
        for k in ('media','captions'):
            if c[k] is not None:shutil.copyfile(TD/c[k]['path'],root/c[k]['path'])
        checks.append({'metric_id':r['metric_id'],'reference':r,'candidate':c,
                       'expected_reference_sha256':digest(r),'expected_candidate_sha256':digest(c)})
    (root/'source.txt').write_text('Authored diagnostic only: inverse square force example. Not a real book.\n')
    (root/'game.html').write_text('<!doctype html><title>Unexecuted authored game placeholder</title>')
    refs=[]
    for name,role in [('source.txt','source'),('game.html','game'),('lesson.mkv','video'),('lesson.srt','support')]:
        b=(root/name).read_bytes();refs.append(ArtifactRef(role,name,hashlib.sha256(b).hexdigest(),len(b),role))
    candidate=ReleaseCandidate('2.0.0','native-qa-authored-candidate','native-qa-authored-run',PIN['commit'],tuple(refs))
    return candidate,checks

def run(root,candidate=None,checks=None,**changes):
    if candidate is None:candidate,checks=inputs(root)
    kw={'execution_context':ExecutionContext(root,LIMITS),'as_of':NOW,
        'expected_candidate_digest':candidate.content_digest,'expected_policy_digest':enterprise_policy().content_digest,
        'expected_checks_digest':digest(checks)}
    kw.update(changes)
    return execute(candidate,checks,**kw)

_TEMP=tempfile.TemporaryDirectory(prefix='bie-native-qa-test-');atexit.register(_TEMP.cleanup)
@lru_cache(None)
def _positive():return run(Path(_TEMP.name)/'positive')
def positive():return deepcopy(_positive())
