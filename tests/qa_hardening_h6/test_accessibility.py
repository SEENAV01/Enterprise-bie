from h6_helpers import *
class Accessibility(Temp):
 def setup_doc(self):self.p,self.b,self.d=access_fixture(self.root)
 def run_doc(self):return evaluate_accessibility(self.root,save(self.root,'observation.json',self.d),self.b,self.p,now=NOW)
 def test_healthy_requires_review(self):
  self.setup_doc();r=self.run_doc();self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.assertFalse(r['production_authorized'])
 def test_complete_axes_required(self):
  self.setup_doc();self.d['views'][0]['measured_axes']=['keyboard'];r=self.run_doc();self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.assertIn('ACCESS_AXIS_NOT_MEASURED',{f['code'] for f in r['report']['findings']})
 def test_foreign_binding(self):
  self.setup_doc();self.d['binding']['run_id']='foreign';self.error('NATIVE_BINDING_MISMATCH',self.run_doc)
 def test_capture_bytes_changed(self):
  self.setup_doc();(self.root/'captured.bin').write_bytes(b'changed')
  with self.assertRaises(ContractError):self.run_doc()
 def test_bool_not_numeric_contrast(self):
  self.setup_doc();self.d['views'][0]['controls'][0]['contrast']=True
  with self.assertRaises(ContractError):self.run_doc()
 def test_unknown_axis(self):
  self.setup_doc();self.d['views'][0]['measured_axes'].append('certified');self.error('H6_ACCESS_UNKNOWN_AXIS',self.run_doc)
 def test_duplicate_control(self):
  self.setup_doc();self.d['views'][0]['controls'].append(self.d['views'][0]['controls'][0]);self.error('H6_CONTROL_DUPLICATE',self.run_doc)
 def test_unknown_visibility(self):
  self.setup_doc();self.d['views'][0]['controls'][0]['focus_indicator']=None
  r=self.run_doc();self.assertIn('ACCESS_MEASUREMENT_UNKNOWN',{f['code'] for f in r['report']['findings']})
 def test_unknown_flash_is_not_clear(self):
  self.setup_doc();self.d['views'][0]['flash']['screening']='UNKNOWN';r=self.run_doc()
  self.assertIn('ACCESS_FLASH_COVERAGE_UNVERIFIED',{f['code'] for f in r['report']['findings']})
 def test_no_conformance_certificate(self):
  self.setup_doc();self.d['mode']='NATIVE_OUTPUT';r=self.run_doc();self.assertFalse(r['details']['conformance_certified']);self.assertFalse(r['product_accepted'])

def negative(name,mutate,code):
 def test(self):self.setup_doc();mutate(self.d);self.blocked(self.run_doc(),code)
 test.__name__='test_'+name;setattr(Accessibility,test.__name__,test)
for name,mutate,code in [
 ('missing_viewport',lambda d:d['views'][0].update(viewport_id='mobile'),'ACCESS_VIEWPORT_CENSUS'),
 ('missing_control',lambda d:d['views'][0]['controls'].pop(),'ACCESS_CONTROL_CENSUS'),
 ('unnamed_control',lambda d:d['views'][0]['controls'][0].update(name=''),'ACCESS_UNNAMED_CONTROL'),
 ('dead_keyboard',lambda d:d['views'][0]['controls'][0].update(keyboard_reached=False),'ACCESS_KEYBOARD_UNREACHABLE'),
 ('invisible_focus',lambda d:d['views'][0]['controls'][0].update(focus_indicator=False),'ACCESS_FOCUS_MISSING'),
 ('hidden_control',lambda d:d['views'][0]['controls'][0].update(visible=False),'ACCESS_CONTROL_HIDDEN'),
 ('low_contrast',lambda d:d['views'][0]['controls'][0].update(contrast='2'),'ACCESS_CONTROL_CONTRAST'),
 ('color_only',lambda d:d['views'][0]['meanings'][0].update(non_color_label=''),'ACCESS_COLOR_ONLY_MEANING'),
 ('meaning_missing',lambda d:d['views'][0]['meanings'].clear(),'ACCESS_MEANING_CENSUS'),
 ('caption_missing',lambda d:d['views'][0]['captions'].clear(),'ACCESS_CAPTION_CENSUS'),
 ('caption_hidden',lambda d:d['views'][0]['captions'][0].update(visible=False),'ACCESS_CAPTION_HIDDEN'),
 ('caption_fast',lambda d:d['views'][0]['captions'][0].update(end_ms=50),'ACCESS_CAPTION_TOO_FAST'),
 ('caption_contrast',lambda d:d['views'][0]['captions'][0].update(contrast='1'),'ACCESS_CAPTION_CONTRAST'),
 ('reduced_meaning_lost',lambda d:d['views'][0]['motion'].update(meaning_ids=[]),'ACCESS_REDUCED_MEANING_LOSS'),
 ('flash_failure',lambda d:d['views'][0]['flash'].update(screening='FAIL'),'ACCESS_FLASH_SCREENING_FAILED'),
 ('future_capture',lambda d:d.update(created_at=NOW+1),'ACCESS_CAPTURE_EXPIRED_OR_FUTURE'),
 ('stale_capture',lambda d:d.update(created_at=NOW-4000),'ACCESS_CAPTURE_EXPIRED_OR_FUTURE'),
]:negative(name,mutate,code)
