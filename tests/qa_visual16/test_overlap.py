from vis_helpers import *

class OverlapTests(FixtureCase):
    def group_fixture(self,limit=1000000):
        # Authored structural group: text inside a container. Not measured paint order.
        r=self.request;p=self.policy;box=Rect(30000,30000,720000,270000)
        e=VisualElement('container-main','scene-main','container',(),'meaning-container',('shape',))
        m=Measurement(e.object_id,box,Rect(0,0,800000,450000),'',0,RGBA(0,0,0),RGBA(255,255,255))
        r=replace(r,elements=r.elements+(e,),states=(replace(r.states[0],measurements=r.states[0].measurements+(m,)),))
        allowances=tuple(OverlapAllowance('allow-'+str(i),'state-desktop',e.object_id,'object-'+str(i),limit,'Reviewed text containment, not unrestricted overlap.') for i in range(1,4))
        p=replace(p,elements=p.elements+(e,),states=(replace(p.states[0],object_ids=p.states[0].object_ids+(e.object_id,)),),overlaps=allowances)
        return r,p
    def test_explicit_reviewed_container_overlap(self):
        r,p=self.group_fixture();self.assertNotIn('VIS_LAYOUT_COLLISION',codes(self.run_check(r,p).layout))
    def test_common_group_no_automatic_exemption(self):
        r,p=self.group_fixture();p=replace(p,overlaps=());self.assertCode(self.run_check(r,p),'layout','VIS_LAYOUT_COLLISION')
    def test_allowance_requires_authenticated_context(self):
        r,p=self.group_fixture();rr=tuple(x for x in signed_reviews(r,p) if x.purpose!='support')
        self.assertCode(self.run_check(r,p,reviews=rr),'layout','VIS_LAYOUT_COLLISION')
    def test_allowance_cannot_exceed_fraction(self):
        r,p=self.group_fixture(limit=500000);self.assertCode(self.run_check(r,p),'layout','VIS_LAYOUT_COLLISION')
    def test_text_text_overlap_never_exempt(self):
        a=OverlapAllowance('forbidden','state-desktop','object-1','object-2',1000000,'Attempt to waive two distinct labels.')
        with self.assertRaises(ContractError):replace(self.policy,overlaps=(a,))
    def test_duplicate_allowance_rejected(self):
        r,p=self.group_fixture()
        with self.assertRaises(ContractError):replace(p,overlaps=p.overlaps+(replace(p.overlaps[0],allowance_id='duplicate'),))
    def test_unknown_allowance_state_rejected(self):
        r,p=self.group_fixture()
        with self.assertRaises(ContractError):replace(p,overlaps=(replace(p.overlaps[0],state_id='unknown'),))
    def test_containment_does_not_inflate_occupied_foreground(self):
        original=dict(self.run_check().clutter.measurements)['max_area'];r,p=self.group_fixture()
        self.assertEqual(dict(self.run_check(r,p).clutter.measurements)['max_area'],original)
