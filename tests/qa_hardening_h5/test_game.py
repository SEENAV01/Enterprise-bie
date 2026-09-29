from h5_helpers import *
from bie.qa.media_runtime_v2.game import *
sys.path.insert(0,str(ROOT/'tests/qa_game16'))
import game_helpers as gh
class NativeGame(Case):
    def seed(self,change=None):
        req,gp,c=gh.fixture(self.root);rr=load_runtime((self.root/req.runtime_receipt.path).read_bytes())
        # Two JavaScript modules and one HTML entry, all explicitly synthetic bytes.
        extra=ref(self.root,'dist/extra.js',b'// SYNTHETIC native module','game-extra')
        req=replace(req,outputs=req.outputs+(extra,));rr=replace(rr,outputs_digest=inventory(req.outputs),loaded=rr.loaded+(gh.LoadedAsset(extra.path,extra.sha256,extra.size),),traces=tuple(replace(t,loaded_paths=t.loaded_paths+(extra.path,)) for t in rr.traces))
        req=replace(req,runtime_receipt=save(self.root,req.runtime_receipt.path,asdict(rr),'runtime-receipt'))
        p=NativeGamePolicy(req.game_id,gp.entrypoint,'dist/game.js',('dist/extra.js','dist/game.js'),'sha256:'+'b'*64,gh.REV)
        b=Binding(req.run_id,gh.REV,req.candidate_digest,digest(asdict(p)))
        d=dict(static_origin_verified=True,native_esm_loader_verified=True,exact_module_count=2,module_graph_fingerprint=p.module_graph_fingerprint,entry_source_sha256=req.outputs[1].sha256,browser_origin_navigation_verified=True,origin_block_reason=None,sandbox_evidence={'synthetic':True},product_accepted=False)
        if change:change(d)
        dr=save(self.root,'deployment.json',d,'deployment');return req,gp,rr,p,b,dr
    def run_case(self,change=None,rt=None):
        req,gp,rr,p,b,dr=self.seed(change)
        if rt:rr=replace(rr,**rt);req=replace(req,runtime_receipt=save(self.root,req.runtime_receipt.path,asdict(rr),'runtime-receipt'))
        return inspect_native_game(self.root,dr,req.runtime_receipt,req.outputs,b,p,now=gh.NOW)
    def test_synthetic_origin_report_not_accepted(self):
        r=self.run_case();self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.unchanged(r)
    def test_data_esm_is_not_origin_navigation(self):self.has(self.run_case(lambda d:d.update(browser_origin_navigation_verified=False)),'H5_NATIVE_BROWSER_ORIGIN_NAVIGATION_VERIFIED')
    def test_managed_browser_block_cannot_be_ignored(self):self.has(self.run_case(lambda d:d.update(origin_block_reason='ERR_BLOCKED_BY_ADMINISTRATOR')),'H5_NATIVE_ORIGIN_BLOCKED')
    def test_about_blank_rejected(self):self.has(self.run_case(rt={'method':'injected_bundle','origin':'about:blank'}),'H5_GAME_NATIVE_ORIGIN_REQUIRED')
    def test_wrong_module_hash(self):self.has(self.run_case(lambda d:d.update(entry_source_sha256='0'*64)),'H5_NATIVE_MODULE_CHANGED')
    def test_wrong_module_count(self):self.has(self.run_case(lambda d:d.update(exact_module_count=3)),'H5_NATIVE_MODULE_GRAPH')
    def test_wrong_graph(self):self.has(self.run_case(lambda d:d.update(module_graph_fingerprint='sha256:'+'c'*64)),'H5_NATIVE_MODULE_GRAPH')
    def test_future_runtime(self):self.has(self.run_case(rt={'issued_at':gh.NOW+1}),'H5_NATIVE_GAME_FRESHNESS')
    def test_missing_loaded_module(self):self.has(self.run_case(rt={'loaded':()}),'H5_NATIVE_GAME_LOAD_COVERAGE')
    def test_runtime_page_error(self):self.has(self.run_case(rt={'page_errors':('broken',)}),'H5_NATIVE_GAME_BROWSER_ERROR')
    def test_unknown_deployment_field(self):
        with self.assertRaisesRegex(ContractError,'H5_DEPLOYMENT_FIELDS'):self.run_case(lambda d:d.update(passed=True))
    def test_self_declared_acceptance(self):
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_GAME_ACCEPTANCE_CLAIM'):self.run_case(lambda d:d.update(product_accepted=True))
    def test_capture_requires_trust_opt_in(self):
        req,gp,*_=self.seed()
        with self.assertRaisesRegex(ContractError,'H5_GAME_CAPTURE_OPT_IN'):collect_native_game(req.outputs,req.build_receipt,gp,self.root,run_id=req.run_id,code_revision=req.revision,issued_at=gh.NOW,output_prefix='capture')
class Extended(Case):
    def seed(self):
        r,gp,c=gh.fixture(self.root)
        p=ExtendedGamePolicy(gp.content_digest,tuple(s.scenario_id for s in gp.scenarios),(('increase','manipulation'),('key-increase','keyboard'),('reload','reload')),(StateConstraint('x','1','3'),StateConstraint('score','0','10')))
        b=Binding(r.run_id,r.revision,r.candidate_digest,digest(asdict(p)));return r,gp,p,b
    def evaluate(self,r,gp,p,b):return inspect_extended_game(self.root,r,gp,b,p,as_of=gh.NOW)
    def change_values(self,r,fn):
        rr=load_runtime((self.root/r.runtime_receipt.path).read_bytes());t=rr.traces[0];s=t.steps[1];s=replace(s,values=tuple(fn(v) for v in s.values));t=replace(t,steps=(t.steps[0],s)+t.steps[2:]);rr=replace(rr,traces=(t,)+rr.traces[1:]);return replace(r,runtime_receipt=save(self.root,r.runtime_receipt.path,asdict(rr),'runtime-receipt'))
    def test_existing_full_qa_executed(self):
        r,gp,p,b=self.seed();out=self.evaluate(r,gp,p,b);self.assertGreater(out['details']['checked_checkpoints'],0);self.assertIn('inherited_report',out['details']);self.unchanged(out)
    def test_intermediate_impossible_state(self):
        r,gp,p,b=self.seed();r=self.change_values(r,lambda v:replace(v,text='99') if v.key=='x' else v);self.has(self.evaluate(r,gp,p,b),'H5_GAME_IMPOSSIBLE_STATE')
    def test_invalid_numerical_state(self):
        r,gp,p,b=self.seed();r=self.change_values(r,lambda v:replace(v,text='NaN') if v.key=='x' else v);self.has(self.evaluate(r,gp,p,b),'H5_GAME_STATE_NOT_QUANTITATIVE')
    def test_missing_nondefault_route(self):
        r,gp,p,b=self.seed();p=replace(p,required_scenarios=p.required_scenarios[:-1]);b=replace(b,policy_digest=digest(asdict(p)))
        with self.assertRaisesRegex(ContractError,'H5_GAME_BRANCH_INVENTORY'):self.evaluate(r,gp,p,b)
    def test_wrong_game_policy(self):
        r,gp,p,b=self.seed();p=replace(p,game_policy_digest='d'*64);b=replace(b,policy_digest=digest(asdict(p)))
        with self.assertRaisesRegex(ContractError,'H5_GAME_POLICY_DIGEST'):self.evaluate(r,gp,p,b)
    def test_keyboard_not_click_label(self):
        r,gp,p,b=self.seed();p=replace(p,required_mechanics=(('increase','keyboard'),));b=replace(b,policy_digest=digest(asdict(p)));self.has(self.evaluate(r,gp,p,b),'H5_KEYBOARD_MECHANIC_UNTESTED')
    def test_reload_not_click_label(self):
        r,gp,p,b=self.seed();p=replace(p,required_mechanics=(('increase','reload'),));b=replace(b,policy_digest=digest(asdict(p)));self.has(self.evaluate(r,gp,p,b),'H5_RELOAD_MECHANIC_UNTESTED')
    def test_device_touch_not_inferred_from_mobile(self):
        r,gp,p,b=self.seed();p=replace(p,actual_touch_required=True);b=replace(b,policy_digest=digest(asdict(p)));self.assertIn('H5_ACTUAL_DEVICE_TOUCH_EVIDENCE_REQUIRED',codes(self.evaluate(r,gp,p,b)))
    def test_conservation_every_checkpoint(self):
        r,gp,p,b=self.seed();p=replace(p,conserved_groups=((('x','score'),'1'),));b=replace(b,policy_digest=digest(asdict(p)));self.has(self.evaluate(r,gp,p,b),'H5_GAME_CONSERVATION_BROKEN')
    def test_missing_mechanic_from_policy(self):
        r,gp,p,b=self.seed();p=replace(p,required_mechanics=(('unknown','simulation'),));b=replace(b,policy_digest=digest(asdict(p)))
        with self.assertRaisesRegex(ContractError,'H5_REQUIRED_MECHANIC_ACTION'):self.evaluate(r,gp,p,b)

class AdditionalGuards(Case):
    def test_html_cannot_be_counted_as_javascript_module(self):
        with self.assertRaisesRegex(ContractError,'H5_NATIVE_MODULE_EXTENSION'):NativeGamePolicy('g','index.html','x.js',('index.html','x.js'),'sha256:'+'a'*64,gh.REV)
