"""Recheck recorded actual OCR output without making another OCR call."""
from h3_support import *
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[2]

class ScanChecks(TempCase):
    def setUp(self):
        super().setUp();base=ROOT/'hardening/section16_h3/evidence/diagnostics'
        self.s=json.loads((base/'scan_snapshot.json').read_text());self.ref=ArtifactRef(**self.s['source']);self.b=Binding(**self.s['binding']);self.p=DocumentPolicy()
        (self.root/self.ref.path).write_bytes((base/'documents'/self.ref.path).read_bytes())
    def reseal(self):self.s['content_digest']=digest({k:v for k,v in self.s.items() if k!='content_digest'})
    def run_check(self):return verify_document(self.s,self.ref,self.root,self.b,self.p)
    def test_scan_crop_is_stable_across_renderer_cache_states(self):self.assertEqual(self.run_check().status,'REVIEW_REQUIRED')
    def test_scan_raster_tamper_rejected(self):
        self.s['regions'][0]['raster_sha256']='f'*64;self.reseal()
        with self.assertRaisesRegex(ContractError,'OCR_CROP_CHANGED'):self.run_check()
    def test_scan_coordinate_mismatch(self):
        self.s['regions'][0]['box_ppm'][0]+=10;self.reseal()
        with self.assertRaisesRegex(ContractError,'OCR_COORDINATE_MISMATCH'):self.run_check()
    def test_scan_normalization_not_silently_replaced(self):
        self.s['regions'][0]['normalized_text']='other';self.reseal()
        with self.assertRaisesRegex(ContractError,'OCR_NORMALIZATION_REVIEW'):self.run_check()
    def test_scan_cannot_borrow_other_page_measurement(self):
        self.s['pages'][0]['ocr_receipt']['source_png_sha256']='f'*64;self.reseal()
        with self.assertRaisesRegex(ContractError,'OCR_PAGE_BINDING'):self.run_check()
    def test_reported_ocr_words_not_semantically_certified(self):
        r=self.s['regions'][0];r['text']='Wrong';r['normalized_text']='Wrong';r['text_sha256']=hashlib.sha256(b'Wrong').hexdigest();r['normalization']=[dict(raw_start=0,raw_end=5,out_start=0,out_end=5,operation='IDENTITY')];self.reseal()
        self.assertEqual(self.run_check().status,'REVIEW_REQUIRED');self.assertIn('OCR_OR_IMAGE_CONTENT_REQUIRES_REVIEW',codes(self.run_check()))
