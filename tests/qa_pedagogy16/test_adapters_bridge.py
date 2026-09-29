from ped_helpers import *
from bie.qa.pedagogy_v2.adapters import import_objective,inspect_load,inspect_blueprint,inspect_sequence
from bie.qa.pedagogy_v2.bridge import prepare_release_evidence
from bie.pedagogy.learning_objective_generator import generate_objective
from bie.pedagogy.assessment_blueprint import AssessmentCell,build_assessment_blueprint
from bie.pedagogy.multi_constraint_sequencer import CurriculumNode,SequenceConstraint,sequence_curriculum
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.evaluator import ReleaseEvaluator
ROOT=Path(__file__).resolve().parents[2]

class AdapterTests(FixtureCase):
 def native(self):return generate_objective('concept-1','equal groups',('cite-c1-objective',))
 def import_native(self,n=None,**kw):
  req=replace(self.policy.objectives[0],objective_id='obj:concept-1');args=dict(statement_claim_ids=('c1-objective',),citation_ids=('cite-c1-objective',),level='APPLY');args.update(kw)
  return import_objective(n or self.native(),req,self.request.source,**args)
 def test_actual_native_objective_adapter(self):self.assertEqual(self.import_native().objective_id,'obj:concept-1')
 def test_native_statement_must_match_output(self):
  with self.assertRaises(ContractError):self.import_native(replace(self.native(),statement='Unsupported teaching'))
 def test_native_identity_must_match(self):
  with self.assertRaises(ContractError):self.import_native(replace(self.native(),concept_id='other'))
 def test_native_evidence_must_match(self):
  with self.assertRaises(ContractError):self.import_native(replace(self.native(),evidence_ids=('other',)))
 def test_native_explicit_level(self):
  with self.assertRaises(ContractError):self.import_native(level='CREATE')
 def test_native_missing_binding(self):
  with self.assertRaises(ContractError):self.import_native(statement_claim_ids=())
 def test_native_unknown_citation(self):
  with self.assertRaises(ContractError):self.import_native(citation_ids=('missing',))
 def blueprint(self):
  req=(('obj','concept','APPLY',True),);cells=(AssessmentCell('obj','concept','APPLY',None,True,('item',),('evidence',)),)
  return build_assessment_blueprint(req,cells),req,cells
 def test_actual_blueprint_not_semantic_acceptance(self):
  b,r,c=self.blueprint();out=inspect_blueprint(b,r,c);self.assertTrue(out.native_checks_passed);self.assertEqual(out.disposition,'REVIEW_REQUIRED');self.assertFalse(out.product_accepted)
 def test_edited_blueprint_rejected(self):
  b,r,c=self.blueprint()
  with self.assertRaises(ContractError):inspect_blueprint(replace(b,passed=False),r,c)
 def test_actual_native_load_review_only(self):
  x=inspect_load((('s',0.5),),max_load=1.8,max_jump=0.7);self.assertTrue(x.native_checks_passed);self.assertEqual(x.disposition,'REVIEW_REQUIRED')
 def test_empty_native_load_cannot_pass(self):
  with self.assertRaises(ContractError):inspect_load((),max_load=1.8,max_jump=.7)
 def test_native_load_duplicate_id_rejected(self):
  with self.assertRaises(ContractError):inspect_load((('s',.5),('s',.5)),max_load=1.8,max_jump=.7)
 def test_native_load_nonfinite_and_boolean(self):
  for value in (True,float('nan'),float('inf')):
   with self.subTest(value=str(value)),self.assertRaises(ContractError):inspect_load((('s',value),),max_load=1.8,max_jump=.7)
 def test_native_load_failure_preserved(self):self.assertFalse(inspect_load((('s',3),),max_load=1.8,max_jump=.7).native_checks_passed)
 def seq(self):
  n=(CurriculumNode('a',0,.2,.8),CurriculumNode('b',1,.2,.7));c=(SequenceConstraint('a','b','prerequisite'),);return sequence_curriculum(n,c),n,c
 def test_native_sequencer_executed(self):
  s,n,c=self.seq();x=inspect_sequence(s,n,c,max_adjacent_load=1.8);self.assertTrue(x.native_checks_passed);self.assertFalse(x.product_accepted)
 def test_native_sequence_tampering(self):
  s,n,c=self.seq()
  with self.assertRaises(ContractError):inspect_sequence(replace(s,order=('b','a')),n,c,max_adjacent_load=1.8)
 def test_native_dependency_git_hashes(self):
  receipt=json.loads((ROOT/'evidence/qa_section16/native_dependencies_006.json').read_text())
  for row in receipt:
   data=(ROOT/row['path']).read_bytes()
   with self.subTest(path=row['path']):self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),row['git_blob_sha'])

class BridgeTests(FixtureCase):
 def prepare(self,r=None,c=None,**kw):
  r=r or self.request;return prepare_release_evidence(r,c or self.candidate,self.root,self.policy,as_of=NOW,**options(r,self.policy,**kw))
 def test_plan_never_passes_media_gate(self):self.assertEqual(self.prepare().envelope.status,'NOT_RUN')
 def test_unsigned_evidence(self):
  p=self.prepare();self.assertEqual(p.envelope.signature,'');self.assertEqual(p.envelope.signer_key_id,'UNSIGNED')
 def test_report_content_hash(self):
  p=self.prepare();self.assertEqual(hashlib.sha256(p.report_bytes).hexdigest(),p.envelope.report.sha256)
 def test_report_states_media_unobserved(self):self.assertFalse(json.loads(self.prepare().report_bytes)['actual_media_evaluated'])
 def test_bad_plan_exports_failure(self):self.assertEqual(self.prepare(self.event('e1-solution',wait_for_response=False)).envelope.status,'FAIL')
 def test_candidate_binding(self):
  with self.assertRaises(ContractError):self.prepare(c=replace(self.candidate,run_id='another'))
 def test_candidate_artifact_binding(self):
  a=replace(self.candidate.artifacts[0],sha256='0'*64);c=replace(self.candidate,artifacts=(a,)+self.candidate.artifacts[1:]);r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
  with self.assertRaises(ContractError):self.prepare(r,c)
 def test_candidate_source_inventory(self):
  a=artifact(self.root,'extra.txt',b'Extra','extra-source','source');c=replace(self.candidate,artifacts=self.candidate.artifacts+(a,));r=replace(self.request,source=replace(self.request.source,candidate_digest=c.content_digest))
  with self.assertRaises(ContractError):self.prepare(r,c)
 def test_actual_release_evaluator_blocks(self):
  p=self.prepare();dest=self.root/p.envelope.report.path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.report_bytes)
  x=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.candidate,(p.envelope,)),self.root,as_of=NOW)
  self.assertEqual(x.release_status,'BLOCKED');self.assertFalse(x.product_accepted)
