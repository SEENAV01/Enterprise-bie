from domain_helpers import *
class SourceTests(Base):
 def test_exact_block_restoration(self):
  c=self.context();a,w=source.repair(c.bad,c.root,c.dp);self.assertEqual(a,c.good);self.assertFalse(w['claims_changed'])
 def test_source_unchanged(self):
  c=self.context();c.generate();self.assertEqual(c.original_bytes,{a.path:(c.root/a.path).read_bytes() for a in c.snapshot.artifacts})
 def test_unique_reanchor(self):
  c=self.context();r=replace(c.good,citations=(replace(c.good.citations[0],start=1,end=len(c.good.citations[0].quote)+1),));a,w=source.repair(r,c.root,c.dp);self.assertEqual(a.citations[0].start,0)
 def test_missing_quote(self):
  c=self.context();r=replace(c.bad,citations=(replace(c.bad.citations[0],quote='NEVER APPEARS IN SOURCE'),));self.assertError('DOMAIN_REPAIR_QUOTE_NOT_FOUND',source.repair,r,c.root,c.dp)
 def test_ambiguous_reanchor(self):
  c=self.context();s=c.good.sources[0];quote='echo';data=b'echo echo';ref=c.write(s.artifact.path,data,s.artifact.artifact_id,'source');b=replace(c.bad.blocks[0],source_sha256=ref.sha256)
  r=replace(c.bad,sources=(replace(s,artifact=ref),),blocks=(b,),citations=(replace(c.bad.citations[0],quote=quote,start=1,end=5),));self.assertError('DOMAIN_REPAIR_AMBIGUOUS_QUOTE',source.repair,r,c.root,c.dp)
 def test_correct_anchor_disambiguates(self):
  c=self.context();s=c.good.sources[0];ref=c.write(s.artifact.path,b'echo echo',s.artifact.artifact_id,'source');b=replace(c.bad.blocks[0],source_sha256=ref.sha256)
  r=replace(c.bad,sources=(replace(s,artifact=ref),),blocks=(b,),citations=(replace(c.bad.citations[0],quote='echo',start=5,end=9),));a,w=source.repair(r,c.root,c.dp);self.assertEqual(a.citations[0].start,5)
 def test_partial_block_not_guessed(self):
  c=self.context();r=replace(c.bad,blocks=(replace(c.bad.blocks[0],box_ppm=(0,0,500000,1000000)),));self.assertError('DOMAIN_REPAIR_PARTIAL_BLOCK_UNSUPPORTED',source.repair,r,c.root,c.dp)
 def test_pdf_requires_real_extractor(self):
  c=self.context();r=replace(c.bad,sources=(replace(c.bad.sources[0],media_type='pdf'),));self.assertError('DOMAIN_REPAIR_EXTRACTOR_REQUIRED',source.repair,r,c.root,c.dp)
 def test_confidence_not_increased(self):
  c=self.context();r=replace(c.bad,blocks=(replace(c.bad.blocks[0],confidence_ppm=900000),));a,w=source.repair(r,c.root,c.dp);self.assertEqual(a.blocks[0].confidence_ppm,900000)
 def test_claim_not_rewritten(self):
  c=self.context();r=replace(c.bad,claims=(replace(c.bad.claims[0],text='Incorrect fabricated output'),));self.assertError('DOMAIN_REPAIR_CLAIM_TEXT_CHANGED',source.repair,r,c.root,c.dp)
 def test_no_normalization(self):
  c=self.context();s=c.bad.sources[0];raw=(c.root/s.artifact.path).read_bytes()+'\ne\u0301  हिन्दी\n'.encode();ref=c.write(s.artifact.path,raw,s.artifact.artifact_id,'source');r=replace(c.bad,sources=(replace(s,artifact=ref),));a,w=source.repair(r,c.root,c.dp);self.assertEqual(a.blocks[0].text.encode(),raw)
 def test_noop(self):
  c=self.context();self.assertError('DOMAIN_REPAIR_NO_CHANGE',source.repair,c.good,c.root,c.dp)
 def test_byte_tamper(self):
  c=self.context();(c.root/c.bad.sources[0].artifact.path).write_bytes(b'bad');self.assertError('ARTIFACT_SIZE_MISMATCH',source.repair,c.bad,c.root,c.dp)
 def test_hidden_output(self):
  c=self.context();p=replace(c.dp,expected_output_ids=('different',));self.assertError('DOMAIN_REPAIR_SOURCE_SCOPE',source.repair,c.bad,c.root,p)
 def test_small_output_budget(self):
  c=self.context();self.assertError('DOMAIN_REPAIR_OUTPUT_LIMIT',source.repair,c.bad,c.root,c.dp,Limits(max_generated_bytes=1))
 def test_provenance_checker_executed(self):
  c=self.context();a,w=source.repair(c.bad,c.root,c.dp);out=evaluate_candidate(c.task,a,c.root,c.dp,as_of=c.now);self.assertEqual(out.provenance.status,'CHECKS_PASSED');self.assertEqual(status_of(out),'REVIEW_REQUIRED')
