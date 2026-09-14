from dataclasses import asdict,replace
import tempfile
import unittest
from pathlib import Path

from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_artifacts import canonical,parse_json,fingerprint
from bie.director.director_model import DirectingFailure
from bie.director.grounded_directing import execute_grounded_director
from bie.director.narration_annotations import verify_base
from bie.director.recovery_codec import grounded_record
from bie.director.scene_correction import (SceneCorrectionPolicy,SceneCorrectedDirectorResult,
    correct_scenes,verify_scene_correction)
from context_fixtures import context_upstream
from completion_fixtures import rich_context,RichTeachingProvider,SceneCorrectionFixture
from directing_fixtures import GENERATOR
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY


class SceneCorrectionTests(unittest.TestCase):
    def fixture(self):
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            WindowedDirectingPolicy(continuity_reserve_characters=1000))
        return f,inputs,base

    def correct(self,provider=None,scene_ids=None,policy=None):
        f,inputs,base=self.fixture();scene_ids=scene_ids or (base.plan.scenes[-1].scene_id,)
        reasons={scene:('ANNOTATION_REVIEW_ISSUE',) for scene in scene_ids}
        result=correct_scenes(f.io,inputs,base,provider or SceneCorrectionFixture(),GENERATOR,
            ProtocolFixtureProvider(),IDENTITY,__import__('bie.director.semantic_execution',fromlist=['SemanticExecutionPolicy']).SemanticExecutionPolicy(),
            scene_ids,reasons,policy or SceneCorrectionPolicy())
        return f,inputs,base,result

    def test_only_named_scene_is_regenerated_and_all_other_bytes_are_reused(self):
        _,_,base,result=self.correct();target=result.correction_calls[0].scene_ids[0]
        for before,after in zip(base.narrated_scenes,result.narrated_scenes):
            if before.scene_id==target:self.assertNotEqual(fingerprint(asdict(before)),fingerprint(asdict(after)))
            else:self.assertEqual(before,after)
        self.assertEqual(tuple(s.scene_id for s in base.plan.scenes if s.scene_id!=target),result.reused_scene_ids)

    def test_plan_is_immutable_and_whole_lesson_is_recompiled(self):
        _,_,base,result=self.correct();self.assertEqual(base.plan,result.plan)
        self.assertNotEqual(base.execution.snapshot.fingerprint(),result.execution.snapshot.fingerprint())
        self.assertEqual({u.utterance_id for u in result.execution.snapshot.utterances},
                         {u.utterance_id for u in base.execution.snapshot.utterances})

    def test_noop_correction_is_rejected(self):
        with self.assertRaises(DirectingFailure) as caught:self.correct(SceneCorrectionFixture(no_change=True))
        self.assertEqual('DIRECTOR_SCENE_CORRECTION_NO_CHANGE',caught.exception.code)

    def test_wrong_evidence_or_scene_identity_exhausts_bounded_retries(self):
        def change(payload,value,_):value['scene_id']='wrong';return value
        with self.assertRaises(DirectingFailure) as caught:self.correct(SceneCorrectionFixture(change))
        self.assertEqual('RESPONSE_CONTRACT_REJECTED',caught.exception.code)

    def test_correction_count_budget_fails_before_provider_calls(self):
        f,inputs,base=self.fixture();provider=SceneCorrectionFixture();scene_ids=tuple(s.scene_id for s in base.plan.scenes)
        with self.assertRaises(DirectingFailure):correct_scenes(f.io,inputs,base,provider,GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            __import__('bie.director.semantic_execution',fromlist=['SemanticExecutionPolicy']).SemanticExecutionPolicy(),scene_ids,
            {s:('issue',) for s in scene_ids},SceneCorrectionPolicy(maximum_corrected_scenes=1))
        self.assertEqual([],provider.requests)

    def test_persisted_correction_roundtrips_and_revalidates_actual_requests(self):
        f,inputs,_,result=self.correct();decoded=grounded_record(parse_json(canonical(asdict(result))))
        self.assertEqual(result,decoded);verify_base(f.io,inputs,decoded);self.assertEqual(decoded,verify_scene_correction(inputs,decoded))

    def test_tampered_reason_changes_request_fingerprint_and_is_rejected(self):
        _,inputs,_,result=self.correct();raw=parse_json(canonical(asdict(result)))
        raw['correction_calls'][0]['correction_reasons']=['DIFFERENT_REASON'];changed=grounded_record(raw)
        with self.assertRaises(ValueError):verify_scene_correction(inputs,changed)

    def test_correction_retains_review_and_never_claims_acceptance(self):
        _,_,_,result=self.correct();self.assertIsInstance(result,SceneCorrectedDirectorResult)
        self.assertFalse(result.accepted);self.assertIn(result.status,('REVIEW_REQUIRED','BLOCKED'))


if __name__=='__main__':unittest.main()
