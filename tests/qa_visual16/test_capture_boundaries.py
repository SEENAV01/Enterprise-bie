from vis_helpers import *
from bie.qa.visual_v2.capture import capture_static_html,measurement_from_browser

class CollectorBoundaries(FixtureCase):
    def input(self):return artifact(self.root,'trusted.html',b'<!doctype html><html><body>Trusted</body></html>','trusted-html')
    def call(self,ref=None,**changes):
        kwargs=dict(capture_id='capture-test',state_id='state-desktop',scene_id='scene-main',start_ms=0,end_ms=20000,output_dir='out')
        kwargs.update(changes);return capture_static_html(self.root,ref or self.input(),self.policy.views[0],**kwargs)
    def test_output_escape_rejected_before_browser(self):
        with self.assertRaisesRegex(ContractError,'VIS_BROWSER_OUTPUT_ESCAPE'):self.call(output_dir='../escape')
    def test_existing_output_rejected(self):
        (self.root/'out').mkdir()
        with self.assertRaisesRegex(ContractError,'VIS_BROWSER_OUTPUT_EXISTS'):self.call()
    def test_input_hash_rechecked_before_browser(self):
        ref=self.input();(self.root/ref.path).write_bytes(b'CHANGED')
        with self.assertRaises(ContractError):self.call(ref)
    def test_html_invalid_utf8(self):
        ref=artifact(self.root,'invalid.html',b'\xff','invalid-html')
        with self.assertRaisesRegex(ContractError,'VIS_BROWSER_HTML_UTF8'):self.call(ref)
    def test_oversized_html(self):
        ref=artifact(self.root,'large.html',b'x'*(2*1024*1024+1),'large-html')
        with self.assertRaisesRegex(ContractError,'VIS_BROWSER_HTML_LIMIT'):self.call(ref)
    def test_bad_timeout_rejected(self):
        with self.assertRaises(ContractError):self.call(timeout_ms=True)
    def test_capture_identity_budget_checked_before_output(self):
        with self.assertRaises(ContractError):self.call(capture_id='a'*128)
        self.assertFalse((self.root/'out').exists())
    def test_symlink_input_rejected(self):
        ref=self.input();p=self.root/ref.path;raw=p.read_bytes();p.unlink();other=self.root/'real.html';other.write_bytes(raw);p.symlink_to(other)
        with self.assertRaises(ContractError):self.call(ref)
    def test_output_parent_symlink_rejected(self):
        real=self.root/'actual';real.mkdir();(self.root/'sym').symlink_to(real,target_is_directory=True)
        with self.assertRaisesRegex(ContractError,'VIS_BROWSER_OUTPUT_SYMLINK'):self.call(output_dir='sym/out')
    def test_zero_browser_extent_is_explicitly_hidden(self):
        d=dict(object_id='object-1',box=dict(x=0,y=0,width=0,height=0),clip=dict(x=0,y=0,width=100,height=100),text='',font_px=0,
            foreground=[0,0,0,1],background=[255,255,255,1],opacity=1,displayed=False,background_known=True,fonts_loaded=True,line_boxes=[],unsupported=[])
        m=measurement_from_browser(d);self.assertFalse(m.displayed);self.assertEqual(m.box.width,1)
