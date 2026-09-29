from h3_support import *
from copy import deepcopy
import os

class DocumentChecks(TempCase):
    def setUp(self):
        super().setUp();self.p,self.b,self.ref,self.s,self.source,self.blocks=doc_fixture(self.root)
    def verify(self):return verify_document(self.s,self.ref,self.root,self.b,self.p)
    def reseal(self):self.s['content_digest']=digest({k:v for k,v in self.s.items() if k!='content_digest'})
    def test_actual_native_ingestion(self):
        self.assertEqual(self.s['native_inventory'],{'page_count':1,'text_pages':1,'encrypted':False});self.assertEqual(self.blocks[0].text,SENTENCE)
    def test_healthy_requires_reading_order_review(self):self.assertEqual(self.verify().status,'REVIEW_REQUIRED')
    def test_raw_qualifier_preserved(self):self.assertIn('when acceleration is constant',self.blocks[0].text)
    def test_exact_normalization_map(self):
        self.assertEqual(self.s['regions'][0]['normalization'],[dict(raw_start=0,raw_end=len(SENTENCE),out_start=0,out_end=len(SENTENCE),operation='IDENTITY')])
    def test_rehash_does_not_conceal_erased_qualifier(self):
        self.s['regions'][0]['text']='Force is proportional to mass.';self.reseal()
        with self.assertRaisesRegex(ContractError,'TEXT_REGION_CHANGED'):self.verify()
    def test_reordered_regions(self):
        self.ref=save(self.root,'source.pdf',text_pdf(('First source statement.','Second source statement.')),'source','source-pdf');self.s=inspect_pdf(self.ref,self.root,self.b,self.p)
        self.s['pages'][0]['region_ids'].reverse();self.reseal()
        with self.assertRaisesRegex(ContractError,'TEXT_REGION_CHANGED'):self.verify()
    def test_wrong_page_raster(self):
        self.s['pages'][0]['raster_sha256']='f'*64;self.reseal()
        with self.assertRaisesRegex(ContractError,'PAGE_OBSERVATION_CHANGED'):self.verify()
    def test_changed_region_raster(self):
        self.s['regions'][0]['raster_sha256']='f'*64;self.reseal()
        with self.assertRaisesRegex(ContractError,'TEXT_REGION_CHANGED'):self.verify()
    def test_changed_region_bounds(self):
        self.s['regions'][0]['box_ppm'][0]+=1;self.reseal()
        with self.assertRaisesRegex(ContractError,'TEXT_REGION_CHANGED'):self.verify()
    def test_forged_semantic_verified(self):
        self.s['semantic_correctness_verified']=True;self.reseal()
        with self.assertRaisesRegex(ContractError,'EXTRACTOR_IDENTITY_CHANGED'):self.verify()
    def test_wrong_native_page_inventory(self):
        self.s['native_inventory']['page_count']=2;self.reseal()
        with self.assertRaisesRegex(ContractError,'NATIVE_INVENTORY_CHANGED'):self.verify()
    def test_duplicate_region(self):
        self.s['regions'].append(deepcopy(self.s['regions'][0]));self.reseal()
        with self.assertRaisesRegex(ContractError,'DUPLICATE_REGION'):self.verify()
    def test_missing_region(self):
        self.s['regions']=[];self.reseal()
        with self.assertRaisesRegex(ContractError,'TEXT_REGION_CHANGED'):self.verify()
    def test_extra_unknown_region_field(self):
        self.s['regions'][0]['approved']=True;self.reseal()
        with self.assertRaisesRegex(ContractError,'REGION_FIELDS'):self.verify()
    def test_unknown_schema(self):
        self.s['schema_version']='other/1';self.reseal()
        with self.assertRaisesRegex(ContractError,'DOCUMENT_SCHEMA'):self.verify()
    def test_binding_foreign_run(self):
        self.s['binding']['run_id']='other';self.reseal()
        with self.assertRaisesRegex(ContractError,'NATIVE_BINDING_MISMATCH'):self.verify()
    def test_output_export_requires_correct_binding(self):
        r=replace(self.verify(),binding=replace(self.b,run_id='foreign'))
        with self.assertRaisesRegex(ContractError,'UNVERIFIED_DOCUMENT_EXPORT'):to_source_records(self.s,self.ref,verified_report=r)
    def test_required_missing_fragment_blocks(self):
        self.blocked(verify_document(self.s,self.ref,self.root,self.b,self.p,required_fragments=((1,'temperature must remain constant'),)),'REQUIRED_SOURCE_FRAGMENT_MISSING')
    def test_required_present_fragment_retained(self):
        self.assertNotIn('REQUIRED_SOURCE_FRAGMENT_MISSING',codes(verify_document(self.s,self.ref,self.root,self.b,self.p,required_fragments=((1,SENTENCE),))))
    def test_figure_requires_meaning_review(self):
        ref=save(self.root,'drawn.pdf',text_pdf(draw=True),'source','drawn');s=inspect_pdf(ref,self.root,self.b,self.p)
        self.assertIn('FIGURE_TABLE_MEANING_REQUIRES_REVIEW',codes(verify_document(s,ref,self.root,self.b,self.p)))
    def test_altered_figure_cannot_reuse_snapshot(self):
        self.ref=save(self.root,'source.pdf',text_pdf(draw=True),'source','source-pdf')
        with self.assertRaisesRegex(ContractError,'DOCUMENT_SOURCE_OR_POLICY_BINDING'):self.verify()
    def test_actual_source_tamper(self):
        (self.root/self.ref.path).write_bytes(PDF_BYTES+b'changed')
        with self.assertRaises(ContractError):self.verify()
    def test_symlink_source_rejected(self):
        (self.root/'alias.pdf').symlink_to(self.root/'source.pdf');ref=replace(self.ref,path='alias.pdf')
        with self.assertRaises(ContractError):inspect_pdf(ref,self.root,self.b,self.p)
    def test_text_budget_not_truncated(self):
        p=replace(self.p,max_text=2)
        with self.assertRaisesRegex(ContractError,'DOCUMENT_TEXT_LIMIT'):inspect_pdf(self.ref,self.root,bound(p),p)
    def test_pixel_budget_checked_before_render(self):
        p=replace(self.p,max_pixels_per_page=1)
        with self.assertRaisesRegex(ContractError,'DOCUMENT_PIXEL_LIMIT'):inspect_pdf(self.ref,self.root,bound(p),p)
    def test_byte_budget(self):
        p=replace(self.p,max_bytes=1)
        with self.assertRaisesRegex(ContractError,'DOCUMENT_BYTE_LIMIT'):inspect_pdf(self.ref,self.root,bound(p),p)
    def test_bad_pdf_rejected(self):
        ref=save(self.root,'bad.pdf',b'%PDF corrupt','source')
        with self.assertRaises(ContractError):inspect_pdf(ref,self.root,self.b,self.p)
    def test_rotated_pdf_explicitly_unsupported(self):
        import pymupdf
        with pymupdf.open(stream=PDF_BYTES,filetype='pdf') as d:d[0].set_rotation(90);data=d.tobytes()
        ref=save(self.root,'rotated.pdf',data,'source')
        with self.assertRaisesRegex(ContractError,'PAGE_ROTATION'):inspect_pdf(ref,self.root,self.b,self.p)
    def test_empty_text_page_requires_review_not_fake_ocr(self):
        import pymupdf
        d=pymupdf.open();d.new_page();ref=save(self.root,'blank.pdf',d.tobytes(),'source');d.close();s=inspect_pdf(ref,self.root,self.b,self.p)
        self.assertEqual(s['regions'],[]);self.assertEqual(s['pages'][0]['basis'],'IMAGE_ONLY_UNREAD');self.assertEqual(verify_document(s,ref,self.root,self.b,self.p).status,'REVIEW_REQUIRED')
        with self.assertRaisesRegex(ContractError,'NO_EXTRACTED_TEXT'):to_source_records(s,ref,verified_report=verify_document(s,ref,self.root,self.b,self.p))
