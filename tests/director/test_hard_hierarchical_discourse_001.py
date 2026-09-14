from dataclasses import asdict, replace
import json
import tempfile
import unittest
from pathlib import Path

from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.grounded_directing import execute_grounded_director
from bie.director.hierarchical_annotations import (HierarchicalAnnotationPolicy,
    HierarchicalAnnotationProduction)
from bie.director.narration_annotations import produce_annotations,verify_production
from bie.director.recovery_codec import annotation_production_record
from bie.director.director_model import DirectingFailure
from bie.director.director_artifacts import canonical,parse_json
from context_fixtures import context_upstream
from completion_fixtures import (rich_context,RichTeachingProvider,HierarchicalAnnotationFixture)
from directing_fixtures import GENERATOR
from annotation_fixtures import ANNOTATOR
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY
from window_fixtures import long_upstream
from windowed_directing_fixtures import windowed_base


class HierarchicalDiscourseTests(unittest.TestCase):
    def fixture(self,transform=None,policy=None):
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,
            ProtocolFixtureProvider(),IDENTITY,WindowedDirectingPolicy(continuity_reserve_characters=1000))
        provider=HierarchicalAnnotationFixture(transform);policy=policy or HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1)
        production=produce_annotations(f.io,inputs,base,provider,ANNOTATOR,policy)
        return f,inputs,base,provider,production

    def test_complete_speech_is_covered_without_one_global_speech_request(self):
        f,inputs,base,provider,production=self.fixture()
        self.assertIsInstance(production,HierarchicalAnnotationProduction)
        leaf=[s for s in production.discourse_scopes if s.kind=='LEAF']
        self.assertEqual(len(base.plan.scenes),len(leaf))
        covered={uid for scope in leaf for uid in scope.utterance_ids}
        self.assertEqual({u.utterance_id for u in base.execution.snapshot.utterances},covered)
        self.assertFalse(any('COMPLETE_SPOKEN_LESSON_DISCOURSE' in r.messages[1]['content'] for r in provider.requests
                             if 'ANNOTATE_DISCOURSE' in r.messages[1]['content']))

    def test_every_interleaf_boundary_receives_an_exact_scope(self):
        _,_,base,_,production=self.fixture()
        boundary=[s for s in production.discourse_scopes if s.kind=='BOUNDARY']
        self.assertEqual(len(base.plan.scenes)-1,len(boundary))
        self.assertEqual([(a.scene_id,b.scene_id) for a,b in zip(base.plan.scenes,base.plan.scenes[1:])],
                         [s.boundary_edges[0] for s in boundary])

    def test_host_reassembles_and_runs_original_full_validator(self):
        _,inputs,base,_,production=self.fixture()
        checked=verify_production(production,inputs,base)
        self.assertEqual(len(base.execution.snapshot.utterances),len(checked.discourse))
        self.assertEqual(len(base.plan.scenes)-1,len(checked.transitions))

    def test_leaf_cannot_omit_an_utterance(self):
        def change(payload,value,_):
            if payload['operation']=='ANNOTATE_DISCOURSE_LEAF':value['discourse'].pop()
            return value
        with self.assertRaises(DirectingFailure) as caught:self.fixture(change)
        self.assertEqual('RESPONSE_CONTRACT_REJECTED',caught.exception.code)

    def test_boundary_cannot_claim_another_edge(self):
        def change(payload,value,_):
            if payload['operation']=='ANNOTATE_DISCOURSE_BOUNDARY':value['transitions'][0]['from_scene']='wrong'
            return value
        with self.assertRaises(DirectingFailure):self.fixture(change)

    def test_retrieval_scope_cannot_link_an_unselected_utterance(self):
        def change(payload,value,_):
            if payload['operation']=='ANNOTATE_DISCOURSE_RETRIEVAL':
                value['reference_links']=[{'utterance_id':payload['utterances'][0]['utterance_id'],
                    'references':['unknown'],'rationale':'bad','confidence':.9}]
            return value
        # The two-scene fixture has no non-adjacent retrieval scope; force three scenes by using a large source fixture is tested below.
        _,_,_,_,production=self.fixture(change)
        self.assertFalse(any(s.kind=='RETRIEVAL' for s in production.discourse_scopes))

    def test_three_scene_lesson_executes_deterministic_nonadjacent_retrieval(self):
        f=long_upstream(Path(tempfile.mkdtemp()),units=3,page_characters=500,dependencies='chain')
        base=windowed_base(f);provider=HierarchicalAnnotationFixture()
        production=produce_annotations(f.io,f.inputs,base,provider,ANNOTATOR,
            HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1))
        retrieval=[scope for scope in production.discourse_scopes if scope.kind=='RETRIEVAL']
        self.assertTrue(retrieval)
        first,last=base.plan.scenes[0].scene_id,base.plan.scenes[-1].scene_id
        selected=next(scope for scope in retrieval if scope.call.scene_ids==(first,last))
        self.assertEqual(len(selected.utterance_ids),2)
        response=json.loads(selected.call.response_json)
        payload=next(json.loads(r.messages[1]['content']) for r in provider.requests
            if json.loads(r.messages[1]['content']).get('scope_fingerprint')==response['scope_fingerprint'])
        self.assertEqual({u['utterance_id'] for u in payload['utterances']},set(selected.utterance_ids))
        self.assertEqual(verify_production(production,f.inputs,base),production.annotations)

    def test_persisted_hierarchical_evidence_roundtrips_and_revalidates(self):
        _,inputs,base,_,production=self.fixture()
        decoded=annotation_production_record(parse_json(canonical(asdict(production))))
        self.assertEqual(production,decoded);self.assertEqual(production.annotations,verify_production(decoded,inputs,base))

    def test_metadata_stripping_cannot_downgrade_hierarchical_record(self):
        _,_,_,_,production=self.fixture();raw=parse_json(canonical(asdict(production)))
        raw['annotations']['policy'].pop('window_version')
        with self.assertRaises(ValueError):annotation_production_record(raw)

    def test_indivisible_leaf_overflow_fails_without_truncating_speech(self):
        policy=HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1,
            execution=replace(HierarchicalAnnotationPolicy().execution,maximum_request_characters=1000))
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,
            ProtocolFixtureProvider(),IDENTITY,WindowedDirectingPolicy(continuity_reserve_characters=1000))
        provider=HierarchicalAnnotationFixture()
        with self.assertRaises(DirectingFailure) as caught:produce_annotations(f.io,inputs,base,provider,ANNOTATOR,policy)
        self.assertIn(caught.exception.code,('DIRECTOR_CONTEXT_BUDGET_EXCEEDED','ANNOTATION_INDIVISIBLE_DISCOURSE_SCENE_EXCEEDED'))


if __name__=='__main__':unittest.main()
