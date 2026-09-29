from h3_support import *
from copy import deepcopy

class CalibrationChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.c,self.d,self.cr,self.pr=calibration_fixture(self.root)
    def refresh(self):
        self.cr=save(self.root,'corpus.json',self.c,identifier='corpus');self.d['corpus_sha256']=self.cr.sha256;self.pr=save(self.root,'predictions.json',self.d,identifier='predictions')
    def run_check(self,**kwargs):return evaluate_calibration(self.cr,self.pr,self.root,self.b,self.p,now=NOW,**kwargs)[0]
    def approve(self,**kwargs):
        req=digest(dict(binding=asdict(self.b),corpus=asdict(self.cr),predictions=asdict(self.pr)))
        return signed('corpus1','calibration',req,self.p.content_digest,('corpus','predictions'),**kwargs)
    def test_exact_metrics_computed(self):
        r,d=evaluate_calibration(self.cr,self.pr,self.root,self.b,self.p,now=NOW)
        self.assertEqual(d['metrics']['academic']['accuracy'],'1');self.assertEqual(d['metrics']['academic']['total'],8)
    def test_unsigned_requires_review(self):self.assertEqual(self.run_check().status,'REVIEW_REQUIRED')
    def test_synthetic_approved_still_not_empirical(self):
        r=self.run_check(review=self.approve(),verifier=ReviewVerifier((SYNTHETIC_KEY,)));self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertIn('DIAGNOSTIC_CALIBRATION_NOT_EMPIRICAL',codes(r))
    def test_positive_authorized_independent_contract(self):
        self.c['provenance_mode']='independent';self.refresh()
        r=self.run_check(review=self.approve(),verifier=ReviewVerifier((SYNTHETIC_KEY,)))
        self.assertEqual(r.status,'LOCAL_CHECKS_CLEAR');self.assertFalse(r.to_dict()['product_accepted'])
    def test_bad_signature_rejected(self):
        self.blocked(self.run_check(review=replace(self.approve(),signature='f'*64),verifier=ReviewVerifier((SYNTHETIC_KEY,))),'CALIBRATION_AUTHORITY_REQUIRED')
    def test_revoked_key_rejected(self):self.blocked(self.run_check(review=self.approve(),verifier=ReviewVerifier((replace(SYNTHETIC_KEY,enabled=False),))),'CALIBRATION_AUTHORITY_REQUIRED')
    def test_test_only_authority_cannot_pass(self):
        self.c['provenance_mode']='independent';self.refresh();r=self.run_check(review=self.approve(),verifier=ReviewVerifier((replace(SYNTHETIC_KEY,assurance='test_only'),)))
        self.assertEqual(r.status,'REVIEW_REQUIRED')
    def test_critical_false_clear_blocks(self):
        self.d['predictions'][4]['scores']['academic']=900000;self.refresh();self.blocked(self.run_check(),'CRITICAL_DEFECT_FALSE_CLEAR')
    def test_disagreement_not_averaged(self):
        self.d['predictions'][1]['scores']['teaching']=100000;self.refresh();self.blocked(self.run_check(),'CALIBRATION_RATER_DISAGREEMENT')
    def test_all_bad_predictions_fail_floor(self):
        for row in self.d['predictions']:row['scores']={k:1000000-v for k,v in row['scores'].items()}
        self.refresh();self.blocked(self.run_check(),'CALIBRATION_ACCURACY_FLOOR')
    def test_training_source_overlap(self):
        self.c['training_source_hashes']=[self.c['cases'][0]['source_sha256']];self.refresh();self.blocked(self.run_check(),'CALIBRATION_HOLDOUT_LEAKAGE')
    def test_training_input_overlap_different_source(self):
        c=deepcopy(self.c['cases'][0]);c.update(case_id='traincase',blind_id='trainblind',source_sha256=digest('different source'),split='train');self.c['cases'].append(c)
        self.refresh();self.blocked(self.run_check(),'CALIBRATION_HOLDOUT_LEAKAGE')
    def test_duplicate_holdout_input(self):
        self.c['cases'][1]['input_sha256']=self.c['cases'][0]['input_sha256'];self.refresh();self.blocked(self.run_check(),'CALIBRATION_HOLDOUT_LEAKAGE')
    def test_missing_negative_examples(self):
        for c in self.c['cases']:c['labels']={'academic':True,'teaching':True}
        self.refresh();self.blocked(self.run_check(),'CALIBRATION_CLASS_COVERAGE')
    def test_blind_identifier_duplicates(self):
        self.c['cases'][1]['blind_id']=self.c['cases'][0]['blind_id'];self.refresh()
        with self.assertRaisesRegex(ContractError,'BLIND_ID_DUPLICATE'):self.run_check()
    def test_duplicate_case(self):
        self.c['cases'].append(self.c['cases'][0]);self.refresh()
        with self.assertRaisesRegex(ContractError,'CALIBRATION_CASE_DUPLICATE'):self.run_check()
    def test_future_corpus(self):self.c['created_at']=NOW+10;self.refresh();self.blocked(self.run_check(),'CALIBRATION_STALE')
    def test_stale_corpus(self):self.c['created_at']=NOW-999999;self.refresh();self.blocked(self.run_check(),'CALIBRATION_STALE')
    def test_wrong_language(self):self.c['language']='hi';self.refresh();self.blocked(self.run_check(),'CALIBRATION_SCOPE_MISMATCH')
    def test_wrong_domain(self):self.c['domain']='biology';self.refresh();self.blocked(self.run_check(),'CALIBRATION_SCOPE_MISMATCH')
    def test_wrong_prediction_corpus_hash(self):
        self.d['corpus_sha256']='f'*64;self.pr=save(self.root,'predictions.json',self.d,identifier='predictions')
        with self.assertRaisesRegex(ContractError,'PREDICTION_BINDING'):self.run_check()
    def test_changed_rater_version(self):
        self.d['raters'][0]['model_version']='v2';self.refresh()
        with self.assertRaisesRegex(ContractError,'RATER_IDENTITY_MISMATCH'):self.run_check()
    def test_missing_rater_case(self):
        self.d['predictions'].pop();self.refresh()
        with self.assertRaisesRegex(ContractError,'PREDICTION_CASE_COVERAGE'):self.run_check()
    def test_duplicate_prediction(self):
        self.d['predictions'].append(self.d['predictions'][0]);self.refresh()
        with self.assertRaisesRegex(ContractError,'PREDICTION_DUPLICATE'):self.run_check()
    def test_numeric_label_not_boolean(self):
        self.c['cases'][0]['labels']['academic']=1;self.refresh()
        with self.assertRaisesRegex(ContractError,'CALIBRATION_LABELS'):self.run_check()
    def test_same_principal_cannot_be_independent(self):
        with self.assertRaisesRegex(ContractError,'RATERS_NOT_INDEPENDENT'):replace(self.p,raters=(self.p.raters[0],replace(self.p.raters[1],principal='principal1')))
    def test_same_group_cannot_be_independent(self):
        with self.assertRaisesRegex(ContractError,'RATERS_NOT_INDEPENDENT'):replace(self.p,raters=(self.p.raters[0],replace(self.p.raters[1],independence_group='group1')))
    def test_quality_style_cannot_hide_wrong_academics(self):
        q=evaluate_quality({'rater1':{'academic':200000,'teaching':1000000},'rater2':{'academic':1000000,'teaching':1000000}},self.p,self.run_check())
        self.assertEqual(q['status'],'BLOCKED');self.assertEqual(q['failed_criteria'],['academic'])
    def test_quality_requires_calibrated_review(self):
        q=evaluate_quality({r.rater_id:{'academic':900000,'teaching':900000} for r in self.p.raters},self.p,self.run_check());self.assertEqual(q['status'],'REVIEW_REQUIRED')
    def test_quality_missing_criterion(self):
        with self.assertRaisesRegex(ContractError,'QUALITY_CRITERION_COVERAGE'):evaluate_quality({r.rater_id:{'academic':900000} for r in self.p.raters},self.p,self.run_check())
