from dataclasses import replace,asdict
import hashlib
from bie.qa.reasoning_v2 import *
from bie.qa.reasoning_v2.calibration import inspect_calibration
from bie.qa.source_v2.models import Source
from re_helpers import *

class EvidenceTests(FixtureCase):
    def test_missing_premise_evidence(self):self.assertCode(self.run_check(replace(self.request,evidence=self.request.evidence[:1])),'evidence','PREMISE_EVIDENCE_INSUFFICIENT')
    def test_zero_evidence(self):self.assertCode(self.run_check(replace(self.request,evidence=())),'evidence','PREMISE_EVIDENCE_INSUFFICIENT')
    def test_derived_conclusion_cannot_be_own_root_evidence(self):
        r=replace(self.request,evidence=(replace(self.request.evidence[0],premise_id='s3'),)+self.request.evidence[1:]);self.assertCode(self.run_check(r),'evidence','EVIDENCE_PREMISE_REFERENCE_INVALID')
    def test_unknown_argument(self):
        r=replace(self.request,evidence=(replace(self.request.evidence[0],argument_id='other'),)+self.request.evidence[1:]);self.assertCode(self.run_check(r),'evidence','EVIDENCE_PREMISE_REFERENCE_INVALID')
    def test_missing_citation(self):
        r=replace(self.request,evidence=(replace(self.request.evidence[0],citation_ids=('missing',)),)+self.request.evidence[1:]);self.assertCode(self.run_check(r),'evidence','EVIDENCE_CITATION_UNRESOLVED')
    def test_citation_not_attached_to_premise(self):
        r=replace(self.request,evidence=(replace(self.request.evidence[0],citation_ids=('cite-3',)),)+self.request.evidence[1:]);self.assertCode(self.run_check(r),'evidence','PREMISE_CITATION_LINK_MISMATCH')
    def test_counterevidence_wins_over_support(self):
        e=EvidenceLink('counter','arg-1','s1',('cite-2',),'contradiction')
        result=self.run_check(replace(self.request,evidence=self.request.evidence+(e,)))
        self.assertCode(result,'evidence','UNRESOLVED_COUNTEREVIDENCE');self.assertEqual(result.decision_witnesses[0].required_action,'abstain')
    def test_missing_support_assessment(self):
        opts=options(self.request,self.policy);opts['reviews']=tuple(x for x in opts['reviews'] if x.purpose!='support')
        self.assertCode(self.run_check(**opts),'evidence','PREMISE_SUPPORT_UNVERIFIED')
    def test_assumption_not_empirical_support(self):
        a=replace(self.request.arguments[0],assumption_ids=('s1',),conclusion_mode='conditional')
        self.assertCode(self.run_check(replace(self.request,arguments=(a,))),'evidence','ASSUMPTION_MASQUERADING_AS_EVIDENCE')
    def test_operator_lineage_required(self):
        p=replace(self.policy,lineages=(SourceLineage('other','lineage-a'),));self.assertCode(self.run_check(policy=p),'evidence','SOURCE_LINEAGE_INVENTORY_MISMATCH')
    def copy_source(self,distinct_bytes,group='lineage-b'):
        r=self.request;block=r.source.blocks[0];body=block.text+('\nIndependent synthetic copy context.' if distinct_bytes else '')
        ref=artifact(self.root,'inputs/book-2.txt',body.encode(),'source-file-2','source')
        b=replace(block,block_id='block-2',source_id='book-2',source_sha256=ref.sha256,text=body)
        cites=[];claims=list(r.source.claims);links=[]
        for i in (1,2):
            old=r.source.citations[i-1];new=replace(old,citation_id=f'copy-{i}',block_id=b.block_id,block_digest=b.content_digest);cites.append(new)
            claims[i-1]=replace(claims[i-1],citation_ids=claims[i-1].citation_ids+(new.citation_id,))
            links.append(EvidenceLink(f'extra-{i}','arg-1',f's{i}',(new.citation_id,)))
        src=replace(r.source,sources=r.source.sources+(Source('book-2',ref,'utf8',1),),blocks=r.source.blocks+(b,),citations=r.source.citations+tuple(cites),claims=tuple(claims))
        return replace(r,source=src,evidence=r.evidence+tuple(links)),replace(self.policy,lineages=self.policy.lineages+(SourceLineage('book-2',group),),minimum_independent_sources=2)
    def test_identical_bytes_not_independent(self):
        r,p=self.copy_source(False);result=self.run_check(r,p);self.assertCode(result,'evidence','PREMISE_EVIDENCE_INSUFFICIENT')
        self.assertTrue(all(len(w.independent_groups)==1 for w in result.evidence_witnesses))
    def test_shared_lineage_not_independent(self):
        r,p=self.copy_source(True,'lineage-a');self.assertCode(self.run_check(r,p),'evidence','PREMISE_EVIDENCE_INSUFFICIENT')
    def test_distinct_governed_sources_count(self):
        r,p=self.copy_source(True);result=self.run_check(r,p);self.assertEqual(result.evidence.status,'CHECKS_PASSED');self.assertTrue(all(len(w.independent_groups)==2 for w in result.evidence_witnesses))
    def test_insufficient_sources_cannot_be_overridden_by_confidence(self):
        p=replace(self.policy,minimum_independent_sources=2);result=self.run_check(policy=p)
        self.assertCode(result,'uncertainty','UNSAFE_UNCERTAINTY_DISPOSITION');self.assertEqual(result.decision_witnesses[0].required_action,'abstain')

class CalibrationTests(FixtureCase):
    def test_exact_metrics(self):
        cal=self.request.calibrations[0];metrics=inspect_calibration((self.root/cal.artifact.path).read_bytes(),cal,())
        self.assertEqual(metrics.samples,100);self.assertEqual(metrics.ece_ppm,0);self.assertEqual(metrics.brier_ppm,47500)
        self.assertEqual(metrics.canonical_brier_ppm,47500)
    def test_duplicate_samples_rejected(self):
        r=self.change_calibration(lambda d:d['samples'].append(d['samples'][0]));self.assertCode(self.run_check(r),'uncertainty','DUPLICATE_CALIBRATION_SAMPLE_OR_GROUP')
    def test_duplicate_groups_rejected(self):
        r=self.change_calibration(lambda d:d['samples'][1].update(group_id='group-0'));self.assertCode(self.run_check(r),'uncertainty','DUPLICATE_CALIBRATION_SAMPLE_OR_GROUP')
    def test_label_integer_not_boolean(self):
        r=self.change_calibration(lambda d:d['samples'][0].update(correct=1));self.assertCode(self.run_check(r),'uncertainty','NONBOOLEAN_CALIBRATION_LABEL')
    def test_boolean_confidence_not_integer(self):
        r=self.change_calibration(lambda d:d['samples'][0].update(confidence_ppm=True));self.assertCode(self.run_check(r),'uncertainty','INVALID_INTEGER')
    def test_not_heldout(self):
        r=self.change_calibration(lambda d:d.update(split='training'));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_NOT_HELDOUT')
    def test_candidate_leakage(self):
        r=self.change_calibration(lambda d:d.update(source_hashes=[self.request.source.sources[0].artifact.sha256]));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_CANDIDATE_LEAKAGE')
    def test_duplicate_source_hashes(self):
        r=self.change_calibration(lambda d:d['source_hashes'].append(d['source_hashes'][0]));self.assertCode(self.run_check(r),'uncertainty','DUPLICATE_CALIBRATION_SOURCE')
    def test_too_few_samples(self):
        r=self.change_calibration(lambda d:d.update(samples=d['samples'][:10]));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_SAMPLE_FLOOR')
    def test_bad_calibration_error_floor(self):
        r=self.change_calibration(lambda d:[x.update(correct=False) for x in d['samples']]);self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_ERROR_FLOOR')
    def test_bad_calibration_binding(self):
        r=self.change_calibration(lambda d:d.update(model_id='another'));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_BINDING_MISMATCH')
    def test_bad_calibration_field(self):
        r=self.change_calibration(lambda d:d.update(trusted=True));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_FIELDS_MISMATCH')
    def test_calibration_empty(self):
        r=self.change_calibration(lambda d:d.update(samples=[]));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_SAMPLE_LIMIT')
    def test_future_calibration(self):
        r=replace(self.request,calibrations=(replace(self.request.calibrations[0],issued_at=NOW+1),));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_STALE')
    def test_stale_calibration(self):
        r=replace(self.request,calibrations=(replace(self.request.calibrations[0],issued_at=NOW-604801),));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_STALE')
    def test_domain_mismatch(self):
        r=replace(self.request,calibrations=(replace(self.request.calibrations[0],domain='another'),));self.assertCode(self.run_check(r),'uncertainty','CALIBRATION_DOMAIN_MISMATCH')
    def test_missing_calibration_review(self):
        opts=options(self.request,self.policy);opts['reviews']=tuple(x for x in opts['reviews'] if x.purpose!='calibration')
        self.assertCode(self.run_check(**opts),'uncertainty','CALIBRATION_AUTHORITY_MISSING')
    def test_error_rounding_conservative(self):
        r=self.change_calibration(lambda d:d.update(samples=[dict(sample_id=f'i-{i}',group_id=f'g-{i}',confidence_ppm=1,correct=False) for i in range(3)]))
        cal=r.calibrations[0];m=inspect_calibration((self.root/cal.artifact.path).read_bytes(),cal,());self.assertEqual(m.brier_ppm,1)
    def test_all_true_all_confident_last_bin(self):
        r=self.change_calibration(lambda d:[x.update(confidence_ppm=1000000,correct=True) for x in d['samples']]);cal=r.calibrations[0]
        m=inspect_calibration((self.root/cal.artifact.path).read_bytes(),cal,());self.assertEqual(m.bins,((9,100,100000000,100),));self.assertEqual(m.ece_ppm,0)

class UncertaintyTests(FixtureCase):
    def test_missing_confidence_decision(self):self.assertCode(self.run_check(replace(self.request,decisions=())),'uncertainty','CONFIDENCE_DECISION_INVENTORY_MISMATCH')
    def test_unknown_argument(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],argument_id='missing'),))),'uncertainty','CONFIDENCE_ARGUMENT_MISSING')
    def test_unknown_calibration(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],calibration_id='missing'),))),'uncertainty','CALIBRATION_INVENTORY_MISMATCH')
    def test_model_version_mismatch(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],model_version='2'),))),'uncertainty','CALIBRATION_MODEL_BINDING_MISMATCH')
    def test_decision_language_mismatch(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],language='hi'),))),'uncertainty','DECISION_DOMAIN_MISMATCH')
    def test_confidence_above_observed_bin(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],confidence_ppm=990000),))),'uncertainty','CONFIDENCE_EXCEEDS_OBSERVED_BIN_ACCURACY')
    def test_confidence_in_unseen_range(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],confidence_ppm=700000),))),'uncertainty','CALIBRATION_CONFIDENCE_BIN_UNSUPPORTED')
    def test_absolute_empirical_certainty_not_accepted(self):self.assertCode(self.run_check(replace(self.request,decisions=(replace(self.request.decisions[0],confidence_ppm=1000000),))),'uncertainty','ABSOLUTE_CERTAINTY_UNJUSTIFIED')
    def test_low_confidence_requires_abstain(self):
        r=replace(self.request,decisions=(replace(self.request.decisions[0],confidence_ppm=200000),));result=self.run_check(r);self.assertEqual(result.decision_witnesses[0].required_action,'abstain')
    def test_unverified_calibration_cannot_publish(self):
        r=replace(self.request,calibrations=(),decisions=(replace(self.request.decisions[0],calibration_id=''),));result=self.run_check(r)
        self.assertCode(result,'uncertainty','UNSAFE_UNCERTAINTY_DISPOSITION');self.assertEqual(result.decision_witnesses[0].required_action,'review')
    def test_abstention_metadata_without_output_disclosure(self):
        r=replace(self.request,decisions=(replace(self.request.decisions[0],disposition='abstain'),));self.assertCode(self.run_check(r),'uncertainty','UNCERTAINTY_DISCLOSURE_UNVERIFIED')
    def test_unknown_disclosure_claim(self):
        r=replace(self.request,decisions=(replace(self.request.decisions[0],disposition='review',disclosure_claim_ids=('missing',)),));self.assertCode(self.run_check(r),'uncertainty','UNCERTAINTY_DISCLOSURE_UNVERIFIED')
    def test_authorized_abstention_still_not_product_release(self):
        r=replace(self.request,decisions=(replace(self.request.decisions[0],disposition='abstain',disclosure_claim_ids=('claim-3',)),));result=self.run_check(r)
        self.assertNotIn('UNSAFE_UNCERTAINTY_DISPOSITION',codes(result.uncertainty));self.assertEqual(result.uncertainty.status,'REVIEW_REQUIRED');self.assertFalse(result.product_accepted)
