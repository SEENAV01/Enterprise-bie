from dataclasses import asdict,replace
import tempfile
import unittest
from pathlib import Path

from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_artifacts import canonical,parse_json
from bie.director.grounded_directing import execute_grounded_director
from bie.director.hierarchical_annotations import HierarchicalAnnotationPolicy
from bie.director.narration_annotations import produce_annotations,verify_production
from bie.director.recovery_codec import annotation_production_record
from bie.director.scene_correction import correct_scenes
from bie.director.semantic_execution import SemanticExecutionPolicy
from context_fixtures import context_upstream
from completion_fixtures import (rich_context,RichTeachingProvider,HierarchicalAnnotationFixture,SceneCorrectionFixture)
from directing_fixtures import GENERATOR
from annotation_fixtures import ANNOTATOR
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY


class SelectiveAnnotationReuseTests(unittest.TestCase):
    def fixture(self):
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            WindowedDirectingPolicy(continuity_reserve_characters=1000))
        policy=HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1)
        prior=produce_annotations(f.io,inputs,base,HierarchicalAnnotationFixture(),ANNOTATOR,policy)
        target=base.plan.scenes[-1].scene_id
        corrected=correct_scenes(f.io,inputs,base,SceneCorrectionFixture(),GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            SemanticExecutionPolicy(),(target,),{target:('ANNOTATION_REVIEW_ISSUE',)})
        return f,inputs,base,corrected,policy,prior

    def reuse(self,policy_change=None):
        f,inputs,base,corrected,policy,prior=self.fixture();provider=HierarchicalAnnotationFixture()
        current=produce_annotations(f.io,inputs,corrected,provider,ANNOTATOR,policy_change or policy,reuse=(prior,base))
        return f,inputs,base,corrected,policy,prior,provider,current

    def test_unchanged_scene_local_annotation_reuses_exact_prior_call(self):
        _,_,base,corrected,_,prior,provider,current=self.reuse()
        self.assertEqual(1,len(current.source_reuses));self.assertEqual(base.plan.scenes[0].scene_id,current.source_reuses[0].scene_id)
        self.assertEqual(prior.fingerprint(),current.source_reuses[0].prior_production_fingerprint)

    def test_changed_scene_and_all_discourse_scopes_execute_fresh(self):
        _,_,_,corrected,_,_,provider,current=self.reuse()
        self.assertEqual({corrected.plan.scenes[-1].scene_id},{call.scene_ids[0] for call in current.source_calls})
        operations=[parse_json(request.messages[1]['content'])['operation'] for request in provider.requests]
        self.assertEqual(1,operations.count('ANNOTATE_SCENE'))
        self.assertTrue(all('ANNOTATE_DISCOURSE' in op for op in operations[1:]))

    def test_reused_local_data_and_fresh_global_data_pass_full_validator(self):
        _,inputs,_,corrected,_,_,_,current=self.reuse()
        checked=verify_production(current,inputs,corrected)
        self.assertEqual(len(corrected.execution.snapshot.utterances),len(checked.discourse))

    def test_policy_or_identity_change_disables_reuse_by_failing_closed(self):
        f,inputs,base,corrected,policy,prior=self.fixture();changed=replace(policy,minimum_confidence=.91);provider=HierarchicalAnnotationFixture()
        with self.assertRaises(ValueError):produce_annotations(f.io,inputs,corrected,provider,ANNOTATOR,changed,reuse=(prior,base))
        self.assertEqual([],provider.requests)

    def test_persisted_reuse_receipt_roundtrips_and_revalidates(self):
        _,inputs,_,corrected,_,_,_,current=self.reuse();decoded=annotation_production_record(parse_json(canonical(asdict(current))))
        self.assertEqual(current,decoded);verify_production(decoded,inputs,corrected)

    def test_tampered_prior_payload_or_response_is_rejected(self):
        _,inputs,_,corrected,_,_,_,current=self.reuse();raw=parse_json(canonical(asdict(current)))
        raw['source_reuses'][0]['prior_payload_json']='{}';changed=annotation_production_record(raw)
        with self.assertRaises((ValueError,KeyError)):verify_production(changed,inputs,corrected)

    def test_reuse_attempts_are_not_falsely_counted_as_new_model_calls(self):
        _,_,_,_,_,_,provider,current=self.reuse()
        actual=sum(len(scope.attempts) for scope in current.source_calls)+sum(len(scope.call.attempts) for scope in current.discourse_scopes)
        self.assertEqual(actual,len(current.attempts));self.assertEqual(len(provider.requests),len(current.attempts))


if __name__=='__main__':unittest.main()
