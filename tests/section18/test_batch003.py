"""Batch003 checkpoint A: ART005/006. Native Linux acceptance remains open."""
from pathlib import Path
from dataclasses import replace,asdict
import json,hashlib,secrets,time,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch002 import ViewBase
from preview_fixtures import game,changed_game,render,WIRE
from apps.operator.previews import Previews,byte_range
from apps.operator.contracts import OperatorError,Principal,PERMISSIONS
from apps.operator.service import Service
from bie.qa.release_v2.contracts import ContractError
import apps.operator.previews as module

class PreviewBase(ViewBase):
    def setUp(self):
        super().setUp();self.preview=Previews(self.service);self.data,self.receipt,self.policy,self.decoded=render()
    def render_publish(self,**kwargs):
        opts=dict(source_hash=self.body['source_hash'],decoder=lambda *args:self.decoded);opts.update(kwargs)
        return self.preview.publish_render(self.p,self.run,self.data,self.receipt,self.policy,**opts)
    def game_publish(self,**kwargs):
        opts=dict(evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']);opts.update(kwargs)
        return self.preview.publish_game(self.p,self.run,*game(),**opts)
    def bind_http(self):self.client.app.state.previews=self.preview
    def ticket(self):return self.preview.grant(self.p,self.run,self.token)['preview_path']
    def first_file_id(self,kind):
        with self.art.context(self.p,self.run) as (db,body,native):
            r=db.execute('SELECT artifact FROM graphs WHERE run=? AND kind=?',(self.run,'artifact:preview:'+kind)).fetchone()
            raw=native.cas.get_bytes(__import__('bie.infrastructure.artifact_store',fromlist=['BlobRef']).BlobRef('sha256',
                native.persistence.load_artifact(r['artifact']).blob_digest,native.persistence.load_artifact(r['artifact']).blob_size))
            return next(iter(json.loads(raw)['artifact_ids'].values()))

class Art005(PreviewBase):
    def test_persisted_actual_mp4_bytes_and_verified_metadata(self):
        meta=self.render_publish();raw,status,_=self.preview.media(self.p,self.run)
        self.assertEqual(raw,self.data);self.assertEqual(status,200);self.assertEqual(meta['info']['duration_seconds'],2)
        self.assertTrue(meta['fixture_evidence']);self.assertEqual(meta['info']['qa_state'],'REVIEW_REQUIRED')
    def test_native_decoder_is_called_without_injection(self):
        self.receipt=replace(self.receipt,execution_kind='LOCAL_REMOTION_CLI')
        with patch.object(module,'inspect_bytes',return_value=self.decoded) as native:
            v=self.preview.publish_render(self.p,self.run,self.data,self.receipt,self.policy,source_hash=self.body['source_hash'])
        native.assert_called_once_with(self.data,self.policy,None);self.assertFalse(v['fixture_evidence'])
    def test_missing_render_explicit_not_run(self):self.assertEqual(self.preview.get(self.p,self.run,'render')['status'],'NOT_RUN')
    def test_scene_ir_does_not_fabricate_media(self):
        self.art.publish(self.p,self.run,'scene_ir',self.docs['scene_ir'],evidence_origin='SYNTHETIC_TEST')
        self.assertEqual(self.preview.get(self.p,self.run,'render')['status'],'NOT_RUN')
    def test_hash_mismatch_rejected(self):
        self.data+=b'x';self.error(self.render_publish,'render_receipt_invalid')
    def test_partial_render_receipt_rejected(self):
        self.receipt=replace(self.receipt,mode='smoke');self.error(self.render_publish,'render_receipt_invalid')
    def test_failed_render_receipt_rejected(self):
        self.receipt=replace(self.receipt,passed=False);self.error(self.render_publish,'render_receipt_invalid')
    def test_injected_decoder_cannot_claim_native(self):
        self.receipt=replace(self.receipt,execution_kind='LOCAL_REMOTION_CLI');self.error(self.render_publish,'render_execution_kind_invalid')
    def test_full_decode_inventory_mismatch_rejected(self):
        self.decoded=replace(self.decoded,frames=self.decoded.frames[:-1]);self.error(self.render_publish,'render_decode_mismatch')
    def test_required_audio_absence_rejected(self):
        self.policy=replace(self.policy,require_audio=True);self.error(self.render_publish,'render_decode_mismatch')
    def test_corrupt_media_fails_closed(self):
        self.error(lambda:self.render_publish(decoder=lambda *a:(_ for _ in ()).throw(ContractError('VIDEO_DECODE_FAILED'))),'media_validation_failed')
    def test_posix_worker_not_bypassed_on_windows(self):
        self.receipt=replace(self.receipt,execution_kind='LOCAL_REMOTION_CLI')
        with patch.object(module,'inspect_bytes',side_effect=ContractError('VIDEO_POSIX_WORKER_REQUIRED')):
            self.error(lambda:self.preview.publish_render(self.p,self.run,self.data,self.receipt,self.policy,source_hash=self.body['source_hash']),
                       'native_media_worker_unavailable')
    def test_source_identity_mismatch_rejected(self):self.error(lambda:self.render_publish(source_hash='0'*64),'preview_source_mismatch')
    def test_input_manifest_policy_mismatch_rejected(self):
        self.policy=replace(self.policy,expected_input_digest='0'*64);self.error(self.render_publish,'render_receipt_invalid')
    def test_repeat_restart_is_same_verified_preview(self):
        a=self.render_publish();self.assertEqual(a,self.render_publish())
        self.assertEqual(a,Previews(Service(self.root,self.creds)).get(self.p,self.run,'render'))
    def test_cas_tamper_blocks_media(self):
        self.render_publish();self.tamper_blob(self.first_file_id('render'))
        with self.assertRaises(ValueError):self.preview.media(self.p,self.run)
    def test_partial_publication_recovers_without_overwrite(self):
        with patch.object(self.service.catalog,'event',side_effect=RuntimeError('seeded_interruption')):
            with self.assertRaises(RuntimeError):self.render_publish()
        self.assertEqual(self.render_publish()['integrity'],'VERIFIED')
    def test_cross_tenant_cannot_open_preview(self):
        self.render_publish();self.error(lambda:self.preview.get(self.foreign(),self.run,'render'),'run_not_found')
    def test_revocation_blocks_further_media(self):
        self.render_publish();self.creds.revoke(self.token);self.error(lambda:self.preview.media(self.p,self.run),'unauthorized')
    def test_http_range_first_and_suffix_exact(self):
        self.render_publish()
        for value,expect in [('bytes=0-9',self.data[:10]),('bytes=-11',self.data[-11:]),('bytes=11-',self.data[11:])]:
            with self.subTest(value=value):
                r=self.client.get('/operator/v1/runs/'+self.run+'/render/media',headers=dict(self.headers,Range=value))
                self.assertEqual(r.status_code,206);self.assertEqual(r.content,expect);self.assertTrue(r.headers['content-range'].startswith('bytes '))
    def test_unsatisfiable_range_416_safe_length(self):
        self.render_publish();r=self.client.get('/operator/v1/runs/'+self.run+'/render/media',headers=dict(self.headers,Range='bytes=999999-'))
        self.assertEqual(r.status_code,416);self.assertEqual(r.headers['content-range'],'bytes */'+str(len(self.data)))
    def test_multipart_and_huge_ranges_bounded(self):
        for value in ('bytes=0-1,3-4','bytes='+'9'*1000+'-','bytes=-0','bytes=10-0'):
            with self.subTest(value=value):self.error(lambda:byte_range(value,100,'"x"'),'range_not_satisfiable')
    def test_if_range_mismatch_returns_full(self):
        self.render_publish();raw,status,_=self.preview.media(self.p,self.run,'bytes=0-1','"old"')
        self.assertEqual(raw,self.data);self.assertEqual(status,200)
    def test_http_mime_nosniff_head_and_no_paths(self):
        self.render_publish();r=self.get('runs/'+self.run+'/render/media');self.assertEqual(r.headers['content-type'],'video/mp4')
        self.assertEqual(r.headers['x-content-type-options'],'nosniff');self.assertEqual(r.headers['cache-control'],'no-store')
        head=self.client.head('/operator/v1/runs/'+self.run+'/render/media',headers=self.headers)
        self.assertEqual(head.content,b'');self.assertEqual(int(head.headers['content-length']),len(self.data))
        wire=self.get('runs/'+self.run+'/previews/render').text;self.assertNotIn('not-exposed',wire);self.assertNotIn(str(self.root),wire)
    def test_no_unauthenticated_media_or_public_cors(self):
        self.render_publish();r=self.client.get('/operator/v1/runs/'+self.run+'/render/media')
        self.assertEqual(r.status_code,401);self.assertNotIn('access-control-allow-origin',r.headers)
    def test_duration_clock_mismatch_rejected(self):
        self.decoded=replace(self.decoded,durations=(1,)*15+(100,));self.error(self.render_publish,'render_duration_mismatch')
    def test_native_receipt_probe_mismatch_rejected(self):
        self.receipt=replace(self.receipt,media=replace(self.receipt.media,width=999));self.error(self.render_publish,'render_probe_receipt_mismatch')
    def test_head_does_not_use_get_byte_range(self):
        self.render_publish();r=self.client.head('/operator/v1/runs/'+self.run+'/render/media',headers=dict(self.headers,Range='bytes=0-1'))
        self.assertEqual(r.status_code,200);self.assertEqual(int(r.headers['content-length']),len(self.data));self.assertNotIn('content-range',r.headers)

class Art006(PreviewBase):
    def test_native_compiler_package_and_module_graph_validation_invoked(self):
        with patch.object(module,'verify_package',wraps=module.verify_package) as p,patch.object(module,'verify_compiler_binding',wraps=module.verify_compiler_binding) as c,patch.object(module,'verify_module_graph',wraps=module.verify_module_graph) as g:
            value=self.game_publish()
        self.assertTrue(p.called and c.called and g.called);self.assertTrue(value['fixture_evidence'])
        self.assertTrue(value['info']['compiled_package']);self.assertFalse(value['info']['playable_acceptance_claimed'])
    def test_missing_game_not_run(self):self.assertEqual(self.preview.get(self.p,self.run,'game')['status'],'NOT_RUN')
    def test_game_ir_plan_is_not_playable_output(self):
        self.art.publish(self.p,self.run,'game_plan',self.docs['game_plan'],evidence_origin='SYNTHETIC_TEST')
        self.assertEqual(self.preview.get(self.p,self.run,'game')['status'],'NOT_RUN')
    def test_package_bytes_tampered_before_publication_rejected(self):
        ctx,b,m,f=game();f['runtime/bootstrap.js']+=b'// tamper'
        with self.assertRaises(OperatorError):self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash'])
    def test_manifest_self_hash_tamper_rejected(self):
        ctx,b,m,f=game();f['build-manifest.json']=b'{}'
        with self.assertRaises(OperatorError):self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash'])
    def test_package_fingerprint_tamper_rejected(self):
        ctx,b,m,f=game();m=replace(m,package_fingerprint='sha256:'+'0'*64)
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_package_fingerprint_invalid')
    def test_resealed_noncanonical_game_entry_rejected(self):
        ctx,b,m,f=changed_game('runtime/entry.js',b'import {bootstrap} from "./bootstrap.js"; globalThis.counter=1;')
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_entry_not_canonical')
    def test_resealed_inline_html_injection_rejected(self):
        ctx,b,m,f=changed_game('runtime/index.html',b'<html><script>parent.document.body.textContent="leak"</script></html>')
        with self.assertRaises(OperatorError):self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash'])
    def test_resealed_external_resource_html_rejected(self):
        ctx,b,m,f=changed_game('runtime/index.html',b'<html><img src="https://evil.invalid/secret"><script type="module" src="./entry.js"></script></html>')
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_html_external_resource')
    def test_resealed_dynamic_import_rejected(self):
        ctx,b,m,f=changed_game('runtime/bootstrap.js',b'import("./state-machine.js");')
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_package_invalid')
    def test_package_inventory_and_byte_caps(self):
        ctx,b,m,f=game();extra={str(n)+'.js':b'x' for n in range(129)}
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,extra,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_package_required')
        with patch.object(module,'MAX_GAME_BYTES',100):
            self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_package_limit')
    def test_compiler_receipt_cannot_be_substituted(self):
        ctx,b,m,f=game();b=replace(b,receipt=replace(b.receipt,bundle_fingerprint='sha256:'+'0'*64))
        with self.assertRaises(OperatorError):self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash'])
    def test_untracked_file_rejected(self):
        ctx,b,m,f=game();f['private.json']=b'{}'
        self.error(lambda:self.preview.publish_game(self.p,self.run,ctx,b,m,f,evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'game_inventory_invalid')
    def test_foreign_source_rejected(self):self.error(lambda:self.game_publish(source_hash='0'*64),'preview_source_mismatch')
    def test_game_replay_restart_preserves_identity(self):
        a=self.game_publish();self.assertEqual(a,self.game_publish());self.assertEqual(a,Previews(Service(self.root,self.creds)).get(self.p,self.run,'game'))
    def test_cross_tenant_grant_rejected(self):
        self.game_publish();self.error(lambda:self.preview.grant(self.foreign(),self.run,'x'*40),'unauthorized')
    def test_issued_grant_is_not_operator_bearer(self):
        self.game_publish();path=self.ticket();self.assertNotIn(self.token,path);ticket=path.split('/')[2]
        r=self.client.get('/operator/v1/runs/'+self.run,headers={'Authorization':'Bearer '+ticket});self.assertEqual(r.status_code,401)
    def test_scope_cannot_fetch_sources_or_other_game(self):
        self.game_publish();ticket=self.ticket().split('/')[2]
        self.error(lambda:self.preview.game_file(ticket,'operator.sqlite3'),'preview_not_found')
    def test_path_traversal_and_absolute_path_rejected(self):
        self.game_publish();ticket=self.ticket().split('/')[2]
        for path in ('../operator.sqlite3','/etc/passwd','runtime/../../x','runtime\\entry.js'):
            with self.subTest(path=path):self.error(lambda:self.preview.game_file(ticket,path),'preview_not_found')
    def test_expired_grant_fails_closed(self):
        self.game_publish();clock=[0];self.preview.clock=lambda:clock[0];path=self.ticket();clock[0]=121
        self.error(lambda:self.preview.game_file(path.split('/')[2],'runtime/entry.js'),'preview_expired_or_revoked')
    def test_revoked_bearer_immediately_revokes_game_grant(self):
        self.game_publish();path=self.ticket();self.creds.revoke(self.token)
        self.error(lambda:self.preview.game_file(path.split('/')[2],'runtime/entry.js'),'unauthorized')
    def test_distinct_same_principal_grant_cannot_preserve_revoked_token(self):
        self.game_publish();path=self.ticket();self.creds.grant('other-credential-'+'x'*32,self.p);self.creds.revoke(self.token)
        self.error(lambda:self.preview.game_file(path.split('/')[2],'runtime/entry.js'),'unauthorized')
    def test_explicit_stop_revokes_grant(self):
        self.game_publish();path=self.ticket();self.preview.revoke(self.p)
        self.error(lambda:self.preview.game_file(path.split('/')[2],'runtime/entry.js'),'preview_expired_or_revoked')
    def test_revocation_during_resource_read_rechecked_before_delivery(self):
        self.game_publish();ticket=self.ticket().split('/')[2];original=self.preview._read
        def read_then_revoke(*args):
            value=original(*args);self.preview.revoke(self.p);return value
        with patch.object(self.preview,'_read',read_then_revoke):
            self.error(lambda:self.preview.game_file(ticket,'runtime/entry.js'),'preview_expired_or_revoked')
    def test_grants_never_survive_process_restart(self):
        self.game_publish();path=self.ticket();new=Previews(Service(self.root,self.creds))
        self.error(lambda:new.game_file(path.split('/')[2],'runtime/entry.js'),'preview_expired_or_revoked')
    def test_grant_inventory_cap_and_ttl_bounds(self):
        self.game_publish()
        self.error(lambda:self.preview.grant(self.p,self.run,self.token,301),'preview_grant_ttl_invalid')
        with patch.object(module,'MAX_GRANTS',1):
            self.ticket();self.error(self.ticket,'preview_grant_limit')
    def test_corrupted_cas_blocks_game_resource(self):
        self.game_publish();ticket=self.ticket().split('/')[2];self.tamper_blob(self.first_file_id('game'))
        with self.assertRaises(ValueError):self.preview.game_file(ticket,'runtime/entry.js')
    def test_http_grant_and_opaque_sandbox_headers(self):
        self.game_publish();r=self.post('runs/'+self.run+'/game/preview-grant',{});self.assertEqual(r.status_code,200)
        html=self.client.get(r.json()['preview_path']);self.assertEqual(html.status_code,200)
        csp=html.headers['content-security-policy'];self.assertIn('sandbox allow-scripts;',csp);self.assertNotIn('allow-same-origin',csp)
        self.assertIn("connect-src 'none'",csp);self.assertIn("worker-src 'none'",csp);self.assertEqual(html.headers['access-control-allow-origin'],'null')
        self.assertNotIn('access-control-allow-credentials',html.headers);self.assertEqual(html.headers['referrer-policy'],'no-referrer')
    def test_parallel_module_reads_preserve_full_authorization_and_integrity(self):
        from concurrent.futures import ThreadPoolExecutor
        self.game_publish();grant=self.post('runs/'+self.run+'/game/preview-grant',{}).json()['preview_path']
        prefix=grant.rsplit('/',1)[0];paths=[prefix+'/'+name for name in ('entry.js','bootstrap.js','react-vendor.js','runtime-controller.js',
            'state-machine.js','rules.js','interactions.js','scoring.js','feedback.js','adaptation.js','telemetry.js','react-runtime.js')]
        with ThreadPoolExecutor(max_workers=12) as pool:responses=list(pool.map(self.client.get,paths))
        self.assertTrue(all(r.status_code==200 for r in responses),[r.status_code for r in responses])
        self.assertTrue(all(r.headers.get('access-control-allow-origin')=='null' for r in responses))
    def test_read_context_is_query_only_not_a_hidden_write(self):
        self.game_publish()
        with self.art.context(self.p,self.run) as (db,body,native):
            self.assertEqual(db.execute('PRAGMA query_only').fetchone()[0],1)
            with self.assertRaises(__import__('sqlite3').OperationalError):db.execute("UPDATE intents SET control='CANCELLED'")
    def test_operator_api_never_inherits_preview_cors(self):
        r=self.get('runs/'+self.run);self.assertNotIn('access-control-allow-origin',r.headers)
    def test_preview_cannot_be_created_by_cross_origin_write(self):
        self.game_publish();r=self.client.post('/operator/v1/runs/'+self.run+'/game/preview-grant',json={},headers=dict(self.headers,Origin='https://evil.invalid'))
        self.assertEqual(r.status_code,403)
    def test_no_http_producer_upload_endpoint(self):
        r=self.post('runs/'+self.run+'/previews/game',{});self.assertEqual(r.status_code,405)
    def test_safe_metadata_does_not_expose_game_code_or_titles(self):
        self.game_publish();wire=self.get('runs/'+self.run+'/previews/game').text
        self.assertNotIn('getState',wire);self.assertNotIn('Correct. The object',wire);self.assertNotIn(str(self.root),wire)
    def test_read_only_operator_cannot_publish(self):
        p=Principal('reader','tenant-a',frozenset({'read'}),time.time()+100);self.creds.grant('reader-'+('x'*40),p)
        self.error(lambda:self.preview.publish_game(p,self.run,*game(),evidence_origin='SYNTHETIC_TEST',source_hash=self.body['source_hash']),'forbidden')
    def test_invalid_preview_kind_no_fallback(self):self.error(lambda:self.preview.get(self.p,self.run,'game_ir'),'preview_kind_unavailable')

TASK_CLASSES={'BIE-APP-ART-005':Art005,'BIE-APP-ART-006':Art006}
def selected_suite(task=None):
    suite=unittest.TestSuite()
    for key,cls in TASK_CLASSES.items():
        if task is None or key==task:
            for name in sorted(cls.__dict__):
                if name.startswith('test_'):suite.addTest(cls(name))
    return suite
if __name__=='__main__':unittest.TextTestRunner(verbosity=2).run(selected_suite())
