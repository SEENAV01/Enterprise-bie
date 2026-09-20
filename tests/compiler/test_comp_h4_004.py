from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import json,tempfile,unittest
from bie.compiler.layout_repair import _run_candidates,repair_scene_layout,repair_and_publish
from bie.compiler.content_fit_qa import DECLARED_SCOPE
from bie.compiler.layout_repair_contracts import default_policy
from tests.compiler.h4_test_support import text_case,observation,TARGET_BIG,scene

class FakeProbe:
    """Explicit synthetic measurement double for state-machine tests only."""
    def __init__(self,fail_until=0,mode=None):self.calls=0;self.fail_until=fail_until;self.mode=mode
    def measure(self,compiled,target,output,**kwargs):
        self.calls+=1;output.mkdir(parents=True)
        if self.mode=='timeout':raise TimeoutError('LAYOUT_BRIDGE_FAILED: timeout')
        report=observation(compiled,target);report['scope']=DECLARED_SCOPE
        if self.calls<=self.fail_until:
            for row in report['records']:row['scroll_overflow']=True
        if self.mode=='missing-frame':report['records'].pop()
        if self.mode=='wrong-source':report['scene_identity']='b'*64
        (output/'MEASUREMENTS.json').write_text(json.dumps(report))
        return report

class RepairLoopTests(unittest.TestCase):
    def setUp(self):self.p,self.policy=text_case()
    def run_loop(self,probe,policy=None):
        with tempfile.TemporaryDirectory() as td:
            return _run_candidates(self.p,self.policy if policy is None else policy,TARGET_BIG,probe,Path(td))
    def test_selects_first_measured_pass(self):
        probe=FakeProbe(fail_until=1);r,e=self.run_loop(probe);self.assertEqual(probe.calls,2);self.assertEqual(r['selected_index'],1);self.assertIsNotNone(e)
    def test_original_is_not_mutated_by_search(self):
        old=deepcopy(self.p);self.run_loop(FakeProbe(1));self.assertEqual(self.p,old)
    def test_pass_is_local_only(self):
        r,e=self.run_loop(FakeProbe());self.assertFalse(r['real_remotion']);self.assertFalse(r['release_authorized']);self.assertFalse(r['accepted'])
    def test_budget_exhaustion_requests_upstream(self):
        self.policy['max_candidates']=2;r,e=self.run_loop(FakeProbe(100));self.assertEqual(r['status'],'UPSTREAM_REVISION_REQUIRED');self.assertIsNone(e);self.assertEqual(r['attempt_count'],2)
    def test_upstream_request_contains_bound_sources_and_no_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            r,e=_run_candidates(self.p,self.policy,TARGET_BIG,FakeProbe(100),Path(td));request=json.loads((Path(td)/'UPSTREAM_REVISION_REQUEST.json').read_text());self.assertEqual(request['source_refs'],self.p['source_refs']);self.assertFalse(request['automatic_text_deletion']);self.assertFalse(request['automatic_font_reduction'])
    def test_no_effective_scene_written_for_no_fit(self):
        with tempfile.TemporaryDirectory() as td:
            _run_candidates(self.p,self.policy,TARGET_BIG,FakeProbe(100),Path(td));self.assertFalse((Path(td)/'EFFECTIVE_SCENE.json').exists())
    def test_runtime_failure_is_not_upstream_pedagogical_failure(self):
        r,e=self.run_loop(FakeProbe(mode='timeout'));self.assertEqual(r['status'],'ENVIRONMENT_OR_VALIDATOR_BLOCKED');self.assertNotIn('upstream_revision_request_sha256',r)
    def test_runtime_failure_stops_further_attempts(self):
        probe=FakeProbe(mode='timeout');self.run_loop(probe);self.assertEqual(probe.calls,1)
    def test_missing_frames_do_not_become_fit(self):
        r,e=self.run_loop(FakeProbe(mode='missing-frame'));self.assertFalse(r['local_fit_passed']);self.assertIsNone(e)
    def test_wrong_source_report_does_not_become_fit(self):
        r,e=self.run_loop(FakeProbe(mode='wrong-source'));self.assertFalse(r['local_fit_passed'])
    def test_failed_source_does_not_reach_probe(self):
        p=scene();other=deepcopy(p['elements'][0]);other['element_id']='overlap';p['elements'].append(other);q=default_policy(p);probe=FakeProbe()
        with tempfile.TemporaryDirectory() as td:r,e=_run_candidates(p,q,TARGET_BIG,probe,Path(td))
        self.assertEqual(probe.calls,0);self.assertEqual(r['status'],'UPSTREAM_REVISION_REQUIRED')
    def test_reports_carry_candidate_manifest(self):
        r,e=self.run_loop(FakeProbe());self.assertEqual(len(r['attempts'][0]['source_manifest_sha256']),64);self.assertEqual(len(r['attempts'][0]['measurement_sha256']),64)
    def test_no_source_publish_from_internal_candidate_search(self):
        r,e=self.run_loop(FakeProbe());self.assertFalse(r['source_published'])
    def test_public_probe_missing_environment_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            r=repair_scene_layout(self.p,self.policy,Path(td)/'e',browser='/missing/chromium');self.assertEqual(r['status'],'ENVIRONMENT_OR_VALIDATOR_BLOCKED')
    def test_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):repair_scene_layout(self.p,self.policy,td)
    def test_empty_policy_is_not_silently_defaulted(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'POLICY_INVALID'):repair_scene_layout(self.p,{},Path(td)/'e')
    def test_publish_and_evidence_paths_must_not_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'PATHS_MUST_BE_SEPARATE'):repair_and_publish(self.p,self.policy,Path(td)/'x',Path(td)/'x/e')
    def test_existing_destination_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,'DESTINATION_EXISTS'):repair_and_publish(self.p,self.policy,td,Path(td).parent/'unused')
    def test_policy_grant_can_limit_no_move_no_resize(self):
        p,q=text_case(expand=False);self.p,self.policy=p,q;r,e=self.run_loop(FakeProbe(100));self.assertEqual(r['status'],'UPSTREAM_REVISION_REQUIRED');self.assertLessEqual(r['attempt_count'],2)
    def test_budget_limit_rejects_bool(self):
        self.policy['max_candidates']=False
        with self.assertRaises(ValueError):self.run_loop(FakeProbe())

if __name__=='__main__':unittest.main()
