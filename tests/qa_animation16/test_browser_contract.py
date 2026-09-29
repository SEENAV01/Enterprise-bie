"""Collector preflight only. Actual Chromium runs have separate execution receipts."""
from ani_helpers import *
from bie.qa.animation_v2.browser import collect
class CollectorBoundaryTests(FixtureCase):
    def html(self):return artifact(self.root,'demo.html',b'<p>trusted authored fixture</p>','html')
    def test_input_type(self):
        with self.assertRaises(ContractError):collect({},self.p,self.root,self.html(),'standard')
    def test_no_unapproved_mode(self):
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,self.html(),'missing')
    def test_no_unapproved_role(self):
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,self.r.source.sources[0].artifact,'standard')
    def test_capture_id_not_path(self):
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,self.html(),'standard',capture_id='../escape')
    def test_nonportable_output_id(self):
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,self.html(),'standard',capture_id='a:b')
    def test_html_hash_rechecked(self):
        h=self.html();(self.root/h.path).write_bytes(b'bad')
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,h,'standard')
    def test_non_utf8_rejected(self):
        h=artifact(self.root,'nonutf8.html',b'\xff','nonutf8')
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,h,'standard')
    def test_output_symlink_refused(self):
        (self.root/'other').mkdir();(self.root/'animation_captures').symlink_to(self.root/'other',target_is_directory=True)
        with self.assertRaises(ContractError):collect(self.r,self.p,self.root,self.html(),'standard')
    def test_pixel_budget(self):
        m=replace(self.p.modes[0],width_px=8192,height_px=8192);p=replace(self.p,modes=(m,))
        with self.assertRaises(ContractError):collect(self.r,p,self.root,self.html(),'standard')
    def test_previous_capture_not_overwritten(self):
        (self.root/'animation_captures/browser-animation').mkdir(parents=True)
        with self.assertRaises(FileExistsError):collect(self.r,self.p,self.root,self.html(),'standard')
