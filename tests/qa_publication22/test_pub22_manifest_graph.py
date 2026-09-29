import json,os
from dataclasses import replace
from pub22_support import *
from bie.qa.publication_v2.codec import loads,dumps

class ManifestGraph(Case):
    def test_complete_diagnostic_ready_not_accepted(self):
        a=self.f.assess();self.assertEqual(a.status,'READY_FOR_AUTHORIZATION');self.assertFalse(a.product_accepted);self.assertFalse(a.manifest['product_accepted'])
    def test_manifest_rereads_subject_bytes(self):
        (self.root/'subjects/video.fixture').write_bytes(b'changed');self.blocked('CANDIDATE_ARTIFACT_INVALID')
    def test_report_bytes_reread(self):
        (self.root/self.f.ev().report.path).write_bytes(b'changed');self.blocked('ARTIFACT_SIZE_MISMATCH')
    def test_native_report_bytes_reread(self):
        (self.root/self.f.native['video_render'].path).write_bytes(b'changed');self.blocked('ARTIFACT_SIZE_MISMATCH')
    def test_missing_artifact(self):
        (self.root/'subjects/game.fixture').unlink();self.blocked('CANDIDATE_ARTIFACT_INVALID')
    def test_hardlink_refused(self):
        p=self.root/'subjects/game.fixture';p.unlink();os.link(self.root/'subjects/source.txt',p);self.blocked('CANDIDATE_ARTIFACT_INVALID')
    def test_symlink_refused(self):
        p=self.root/'subjects/game.fixture';p.unlink();p.symlink_to(self.root/'subjects/source.txt');self.blocked('CANDIDATE_ARTIFACT_INVALID')
    def test_root_symlink(self):
        p=self.root/'rootlink';p.symlink_to(self.root,target_is_directory=True)
        self.assertFalse(assess(self.f.request,p,self.f.policy,as_of=NOW,verifier=self.f.verifier).ready_for_signing)
    def test_inventory_contains_native_reports(self):
        ids={r['artifact_id'] for r in self.f.assess().manifest['artifacts']};self.assertIn('native-video_render',ids);self.assertIn('exit-native-reaudit',ids)
    def test_graph_has_gate_proof_report_edges(self):
        edges=self.f.assess().graph['edges'];self.assertIn(dict(source='gate:video_render',target='evidence:ev-video_render',relation='evaluated_by'),edges)
    def test_graph_topological_valid(self):
        g=self.f.assess().graph;p={x:i for i,x in enumerate(g['topological_order'])}
        self.assertEqual(len(p),len(g['nodes']));self.assertTrue(all(p[x['source']]<p[x['target']] for x in g['edges']))
    def test_deterministic_repeat(self):self.assertEqual(self.f.assess().to_bytes(),self.f.assess().to_bytes())
    def test_evidence_permutation(self):
        before=self.f.assess();self.f.request=replace(self.f.request,bundle=replace(self.f.request.bundle,evidence=self.f.request.bundle.evidence[::-1]))
        self.assertEqual(before.to_bytes(),self.f.assess().to_bytes())
    def test_lineage_order_deterministic(self):
        before=self.f.assess();self.f.request=replace(self.f.request,lineage=self.f.request.lineage[::-1]);self.assertEqual(before.to_bytes(),self.f.assess().to_bytes())
    def test_missing_lineage(self):
        self.f.request=replace(self.f.request,lineage=());self.blocked('MISSING_ARTIFACT_LINEAGE')
    def test_lineage_cycle(self):
        self.f.request=replace(self.f.request,lineage=(Lineage('video',('game',)),Lineage('game',('video',))));self.blocked('EVIDENCE_GRAPH_CYCLE')
    def test_lineage_self_cycle(self):
        self.f.request=replace(self.f.request,lineage=(Lineage('video',('video','source')),Lineage('game',('source',))));self.blocked('EVIDENCE_GRAPH_CYCLE')
    def test_unknown_parent(self):
        self.f.request=replace(self.f.request,lineage=(Lineage('video',('missing',)),Lineage('game',('source',))));self.blocked('LINEAGE_UNKNOWN_ARTIFACT')
    def test_source_cannot_be_derived(self):
        self.f.request=replace(self.f.request,lineage=self.f.request.lineage+(Lineage('source',('video',)),));self.blocked('SOURCE_CANNOT_BE_DERIVED')
    def test_open_item_preserved(self):
        self.f.request=replace(self.f.request,open_items=(OpenItem('gap','GAME','NATIVE_GAME_PENDING',('game',)),));self.blocked('NATIVE_GAME_PENDING')
    def test_open_item_unknown_artifact(self):
        self.f.request=replace(self.f.request,open_items=(OpenItem('gap','QA','PENDING',('unknown',)),));self.blocked('OPEN_ITEM_UNKNOWN_ARTIFACT')
    def test_codec_roundtrip(self):self.assertEqual(self.f.request.content_digest,loads(dumps(self.f.request)).content_digest)
    def test_codec_reject_authority_injection(self):
        d=self.f.request.to_dict();d['trusted_keys']=[];self.raises('PUBLICATION_FIELDS',loads,canonical_bytes(d))
    def test_codec_duplicate_keys(self):self.raises('DUPLICATE_JSON_KEY',loads,b'{"a":1,"a":2}')
    def test_codec_float(self):self.raises('NON_INTEGER_JSON_NUMBER',loads,b'{"a":1.0}')
    def test_codec_empty(self):self.raises('PUBLICATION_JSON_SIZE',loads,b'')
    def test_codec_nonobject(self):self.raises('PUBLICATION_JSON_OBJECT',loads,b'[]')
    def test_codec_unsafe_path(self):
        d=self.f.request.to_dict();d['bundle']['candidate']['artifacts'][0]['path']='../escape';self.raises('UNSAFE_PATH',loads,canonical_bytes(d))
    def test_schema_version(self):self.raises('PUBLICATION_SCHEMA',replace,self.f.request,schema_version='unknown')
    def test_policy_default_diagnostic(self):self.assertEqual(PublicationPolicy('env').mode,'diagnostic')
    def test_no_policy_gate_waiver(self):self.raises('WEAKENED_REQUIRED_GATE',replace,self.f.policy.release_policy,gates=self.f.policy.release_policy.gates[:-1])
    def test_production_diagnostic_scope_blocked(self):
        self.f.policy=replace(self.f.policy,mode='production');self.blocked('NON_NATIVE_PROOF')
    def test_production_detects_synthetic_source_report(self):
        self.f.policy=replace(self.f.policy,mode='production');self.blocked('SYNTHETIC_SOURCE_REPORT')
