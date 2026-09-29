from h4_support import *
class VisualChecks(TempCase):
    def setUp(self):super().setUp();self.p,self.b,self.native,self.html,self.refs,self.obs,self.png=visual_fixture(self.root)
    def run_it(self):return evaluate_visual(self.native,self.html,self.refs,self.root,self.b,self.p,capture=(self.obs,self.png))[0]
    def test_healthy_supplied_not_execution(self):self.assertEqual(self.run_it().status,'REVIEW_REQUIRED');self.assertIn('SUPPLIED_CAPTURE_REQUIRES_ATTESTATION',codes(self.run_it()))
    def test_missing_node(self):self.obs['nodes'].pop();self.blocked(self.run_it(),'RENDERED_CONTENT_INVENTORY_MISMATCH')
    def test_extra_node(self):r=copy.deepcopy(self.obs['nodes'][0]);r['id']='extra';self.obs['nodes'].append(r);self.blocked(self.run_it(),'RENDERED_CONTENT_INVENTORY_MISMATCH')
    def test_changed_text(self):self.obs['nodes'][0]['text']='Not the cause';self.blocked(self.run_it(),'RENDERED_TEXT_CHANGED')
    def test_cropped_label(self):self.obs['nodes'][0]['clipped']=True;self.blocked(self.run_it(),'RENDERED_CONTENT_CROPPED')
    def test_hidden_label(self):self.obs['nodes'][0]['visible']=False;self.blocked(self.run_it(),'RENDERED_CONTENT_HIDDEN')
    def test_small_occlusion(self):self.obs['nodes'][0]['hit_samples'][3]=False;self.blocked(self.run_it(),'RENDERED_CONTENT_OCCLUDED')
    def test_zero_area(self):self.obs['nodes'][0]['rect'][2]=0;self.blocked(self.run_it(),'RENDERED_CONTENT_HIDDEN')
    def test_changed_position(self):self.obs['nodes'][0]['rect'][0]=100;self.blocked(self.run_it(),'NATIVE_RENDER_LAYOUT_MISMATCH')
    def test_changed_relationship(self):self.obs['nodes'][0]['rect'][0]=250;self.blocked(self.run_it(),'RENDERED_SCIENTIFIC_RELATION_CHANGED')
    def test_complex_paint_not_certified(self):self.obs['nodes'][0]['unsupported']=True;self.assertIn('COMPLEX_PAINT_REVIEW_REQUIRED',codes(self.run_it()))
    def test_untracked_markup(self):self.obs['unsupported_markup']=1;self.assertIn('UNSUPPORTED_OR_EXTERNAL_CONTENT',codes(self.run_it()))
    def test_bad_png_bytes(self):
        self.png=b'bad'
        with self.assertRaises(ContractError):self.run_it()
    def test_different_png_dimensions(self):
        im=Image.new('RGB',(100,100));buf=BytesIO();im.save(buf,format='PNG');self.png=buf.getvalue();self.obs['png_sha256']=hashlib.sha256(self.png).hexdigest()
        with self.assertRaises(ContractError):self.run_it()
    def test_changed_source_html(self):
        (self.root/'scene.html').write_text('changed')
        with self.assertRaises(ContractError):self.run_it()
    def test_foreign_html_binding(self):
        self.obs['html_sha256']=digest('wrong')
        with self.assertRaises(ContractError):self.run_it()
    def test_fabricated_native_scope(self):
        self.obs['native_runtime_verified']=True
        with self.assertRaises(ContractError):self.run_it()
    def test_nonfinite_geometry(self):
        self.obs['nodes'][0]['rect'][0]=float('nan')
        with self.assertRaises(ContractError):self.run_it()
    def test_bool_geometry(self):
        self.obs['nodes'][0]['rect'][0]=True
        with self.assertRaises(ContractError):self.run_it()
    def test_missing_hit_samples(self):
        self.obs['nodes'][0]['hit_samples'].pop()
        with self.assertRaises(ContractError):self.run_it()
    def test_duplicate_node_identity(self):
        self.obs['nodes'][1]['id']='a'
        with self.assertRaises(ContractError):self.run_it()
    def test_native_plan_changed(self):
        self.native=replace(self.native,fingerprint='changed')
        with self.assertRaises(ContractError):self.run_it()
    def test_contradictory_policy_binding(self):
        self.p=replace(self.p,tolerance_millipixels=3000)
        with self.assertRaises(ContractError):self.run_it()
