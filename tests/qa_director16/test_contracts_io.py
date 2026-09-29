from dir_helpers import *
import json, subprocess, sys, os
from bie.qa.director_v2.codec import load_request, load_policy, load_reviews
from bie.qa.director_v2.__main__ import main as cli
from bie.qa.director_v2.models import *

class Contracts(FixtureCase):
    def test_request_roundtrip(self):self.assertEqual(load_request(canonical_bytes(asdict(self.request))),self.request)
    def test_policy_roundtrip(self):self.assertEqual(load_policy(canonical_bytes(asdict(self.policy))),self.policy)
    def test_review_roundtrip(self):
        rr=signed_reviews(self.request,self.policy);self.assertEqual(load_reviews(canonical_bytes([asdict(a) for a in rr])),rr)
    def test_unknown_field_rejected(self):
        d=asdict(self.request);d['quality_pass']=True
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_missing_field_rejected(self):
        d=asdict(self.request);del d['beats']
        with self.assertRaises(ContractError):load_request(canonical_bytes(d))
    def test_duplicate_json_keys(self):
        with self.assertRaises(ContractError):load_request(b'{"schema_version":"1.0.0","schema_version":"1.0.0"}')
    def test_nan_json(self):
        with self.assertRaises(ContractError):load_request(b'{"x":NaN}')
    def test_cross_collection_identity_collision(self):
        with self.assertRaisesRegex(ContractError,'DIR_CROSS_COLLECTION_ID_COLLISION'):
            self.beat('b-hook',beat_id='s1')
    def test_reserved_identity_collision(self):
        with self.assertRaises(ContractError):self.beat('b-hook',beat_id='director-scope')
    def test_duplicate_fidelity_claim(self):
        with self.assertRaisesRegex(ContractError,'DIR_DUPLICATE_FIDELITY_CLAIM'):
            replace(self.request,fidelity=self.request.fidelity+(replace(self.request.fidelity[0],mapping_id='another-map'),))
    def test_duplicate_term_intro(self):
        with self.assertRaisesRegex(ContractError,'DIR_DUPLICATE_TERM_INTRODUCTION'):
            replace(self.request,term_introductions=self.request.term_introductions+(replace(self.request.term_introductions[0],introduction_id='other-intro'),))
    def test_boolean_duration_not_integer(self):
        with self.assertRaises(ContractError):self.beat('b-hook',start_ms=True)
    def test_pause_cannot_hide_text(self):
        with self.assertRaises(ContractError):self.beat('b-hook',channel='pause',role='pause')
    def test_policy_cannot_drop_scene_from_all_routes(self):
        with self.assertRaises(ContractError):replace(self.policy,routes=(replace(self.policy.routes[0],scene_ids=('s1',)),))
    def test_policy_cannot_drop_facet_from_all_routes(self):
        with self.assertRaises(ContractError):replace(self.policy,routes=(replace(self.policy.routes[0],facet_ids=('facet-definition',)),))
    def test_json_schema_request_policy_reviews(self):
        import jsonschema
        root=Path(__file__).resolve().parents[2]
        for name,value in [('request',self.request),('policy',self.policy),('review',signed_reviews(self.request,self.policy)[0])]:
            with self.subTest(name=name):
                schema=json.loads((root/f'docs/qa_section16/batch007/{name}.schema.json').read_text())
                jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(json.loads(canonical_bytes(asdict(value))),schema)
    def test_cli_unsigned_review_exit(self):
        request=self.root/'request.json';policy=self.root/'policy.json';output=self.root/'result.json'
        request.write_bytes(canonical_bytes(asdict(self.request)));policy.write_bytes(canonical_bytes(asdict(self.policy)))
        code=cli(['--request',str(request),'--policy',str(policy),'--artifact-root',str(self.root),'--as-of',str(NOW),'--output',str(output)])
        self.assertEqual(code,3);self.assertEqual(json.loads(output.read_text())['status'],'REVIEW_REQUIRED')
    def test_cli_never_overwrites_evidence(self):
        request=self.root/'request.json';policy=self.root/'policy.json';output=self.root/'result.json'
        request.write_bytes(canonical_bytes(asdict(self.request)));policy.write_bytes(canonical_bytes(asdict(self.policy)));output.write_text('prior evidence')
        self.assertEqual(cli(['--request',str(request),'--policy',str(policy),'--artifact-root',str(self.root),'--as-of',str(NOW),'--output',str(output)]),4)
        self.assertEqual(output.read_text(),'prior evidence')
    def test_cli_rejects_invalid_json(self):
        request=self.root/'request.json';policy=self.root/'policy.json';request.write_text('{"x":NaN}');policy.write_bytes(canonical_bytes(asdict(self.policy)))
        self.assertEqual(cli(['--request',str(request),'--policy',str(policy),'--artifact-root',str(self.root),'--as-of',str(NOW)]),4)

# Every generated test names a distinct contract boundary, not repeat runs.
def invalid_test(factory):
    def test(self):
        with self.assertRaises((ContractError,ValueError)):factory(self)
    return test

INVALID = {
 'bad_schema':lambda s:replace(s.request,schema_version='2'),
 'bad_scene_role':lambda s:replace(s.request.scenes[0],role='decorative'),
 'negative_scene_duration':lambda s:replace(s.request.scenes[0],duration_ms=-1),
 'scene_empty_purpose':lambda s:replace(s.request.scenes[0],purpose=' '),
 'scene_list_not_tuple':lambda s:replace(s.request,scenes=list(s.request.scenes)),
 'beat_zero_duration':lambda s:s.beat('b-hook',end_ms=0),
 'beat_negative_start':lambda s:s.beat('b-hook',start_ms=-1),
 'beat_unknown_channel':lambda s:s.beat('b-hook',channel='video'),
 'beat_duplicate_claim':lambda s:s.beat('b-hook',claim_ids=('c-hook','c-hook')),
 'beat_null_speaker':lambda s:s.beat('b-hook',speaker_id=''),
 'route_cycle_ids':lambda s:Route('loop',('s1','s2','s1')),
 'route_empty':lambda s:Route('empty',()),
 'self_transition':lambda s:Transition('t','s1','s1',('c-hook',)),
 'empty_transition_claim':lambda s:Transition('t','s1','s2',()),
 'empty_promise_payoff':lambda s:Promise('p','b-hook',()),
 'empty_spoken_form':lambda s:SpokenForm('b-hook',' '),
 'huge_spoken_form':lambda s:SpokenForm('b-hook','a'*100001),
 'unknown_fidelity_mode':lambda s:replace(s.request.fidelity[0],mode='trusted'),
 'facet_empty_citations':lambda s:FacetRequirement('f',()),
 'facet_unknown_mode':lambda s:FacetRequirement('f',('c',),allowed_modes=('trusted',)),
 'term_empty_forms':lambda s:TermRequirement('t',()),
 'term_duplicate_forms':lambda s:TermRequirement('t',('abc','abc')),
 'term_nonbool_assumed':lambda s:TermRequirement('t',('abc',),assumed_known=1),
 'timing_self':lambda s:TimingConstraint('x','b','b',0,1),
 'timing_bad_range':lambda s:TimingConstraint('x','a','b',10,9),
 'speech_zero_rate':lambda s:PacingLimits(speech_codepoints_per_minute=0),
 'screen_negative_rate':lambda s:PacingLimits(screen_codepoints_per_minute=-1),
 'excessive_speech_concurrency':lambda s:PacingLimits(max_concurrent_speech=5),
 'negative_pause':lambda s:PacingLimits(max_pause_ms=-1),
 'too_large_window':lambda s:PacingLimits(qualification_window_ms=600001),
 'weak_review_floor':lambda s:replace(s.policy,minimum_review_confidence_ppm=899999),
 'zero_assessors':lambda s:replace(s.policy,minimum_independent_assessors=0),
 'zero_age':lambda s:replace(s.policy,max_receipt_age_seconds=0),
 'unknown_policy_parent':lambda s:replace(s.policy,scenes=(replace(s.policy.scenes[0],parent_scene_ids=('absent',)),s.policy.scenes[1])),
 'policy_self_parent':lambda s:replace(s.policy,scenes=(replace(s.policy.scenes[0],parent_scene_ids=('s1',)),s.policy.scenes[1])),
 'wrong_source_type':lambda s:replace(s.request,source={}),
 'wrong_policy_source':lambda s:replace(s.policy,source={}),
 'wrong_pacing_type':lambda s:replace(s.policy,pacing={}),
}
for name,factory in INVALID.items():setattr(Contracts,'test_contract_'+name,invalid_test(factory))
