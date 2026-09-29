import os
from unittest.mock import patch
from dataclasses import replace
from source_helpers import *
from bie.qa.source_v2.io import SnapshotStore
from bie.qa.source_v2.adapters import block_from_bi, claim_from_ki
from bie.document_intelligence.source_anchors import Anchor
from bie.document_intelligence.text_blocks import build as build_text
from bie.knowledge_intelligence.claim_extraction import extract
from bie.knowledge_intelligence.claim_evidence import bind

class StoreTests(FixtureCase):
    def test_exact_bytes_returned(self):
        with SnapshotStore(self.root) as s:self.assertEqual(s.read(self.request.sources[0].artifact),TEXT.encode())
    def test_closed_store_rejected(self):
        with self.assertRaises(ContractError):SnapshotStore(self.root).read(self.request.sources[0].artifact)
    def test_double_open_rejected(self):
        with SnapshotStore(self.root) as s:
            with self.assertRaises(ContractError):s.__enter__()
    def test_leaf_symlink_rejected(self):
        src=self.root/'inputs/source.txt';src.unlink();src.symlink_to(self.root/'surfaces/narration.txt')
        self.blocked(self.request,'ARTIFACT_OPEN_OR_READ_FAILED')
    def test_directory_symlink_rejected(self):
        (self.root/'inputs/source.txt').unlink();(self.root/'inputs').rmdir();(self.root/'inputs').symlink_to(self.root/'surfaces',target_is_directory=True)
        self.blocked(self.request,'ARTIFACT_OPEN_OR_READ_FAILED')
    def test_root_symlink_rejected(self):
        alias=self.root/'alias';alias.symlink_to(self.root,target_is_directory=True)
        result=evaluate(self.request,alias,self.policy,as_of=NOW)
        self.assertIn('ARTIFACT_ROOT_UNAVAILABLE',codes(result.provenance))
    def test_hardlink_rejected(self):
        os.link(self.root/'inputs/source.txt',self.root/'another-link')
        self.blocked(self.request,'HARD_LINK_REJECTED')
    def test_fifo_does_not_hang(self):
        path=self.root/'inputs/source.txt';path.unlink();os.mkfifo(path)
        self.blocked(self.request,'NOT_REGULAR_FILE')
    def test_directory_as_leaf_rejected(self):
        path=self.root/'inputs/source.txt';path.unlink();path.mkdir()
        self.blocked(self.request,'NOT_REGULAR_FILE')
    def test_size_mismatch_rejected(self):
        (self.root/'inputs/source.txt').write_bytes(b'short')
        self.blocked(self.request,'ARTIFACT_SIZE_MISMATCH')
    def test_traversal_and_absolute_path_rejected(self):
        for path in ('../outside','/etc/passwd','inputs/../source.txt','inputs//source.txt'):
            with self.subTest(path=path),self.assertRaises(ContractError):replace(self.request.sources[0].artifact,path=path)
    def test_mutation_during_descriptor_read_rejected(self):
        original=os.read;changed=False;target=self.root/'inputs/source.txt'
        def changing(fd,n):
            nonlocal changed
            out=original(fd,n)
            if not changed:
                changed=True;target.write_bytes(TEXT.replace('5','9').encode())
            return out
        with SnapshotStore(self.root) as s,patch('bie.qa.source_v2.io.os.read',side_effect=changing):
            with self.assertRaises(ContractError) as cm:s.read(self.request.sources[0].artifact)
        self.assertEqual(cm.exception.code,'ARTIFACT_CHANGED_DURING_READ')
    def test_snapshot_is_not_reopened_after_hash_check(self):
        with SnapshotStore(self.root) as s:payload=s.read(self.request.sources[0].artifact)
        (self.root/'inputs/source.txt').write_bytes(b'changed')
        self.assertEqual(payload,TEXT.encode())
    def test_descriptor_budget_failure_is_closed(self):
        with SnapshotStore(self.root) as s:
            s.total=64*1024*1024
            with self.assertRaises(ContractError):s.read(self.request.sources[0].artifact)

class AdapterTests(FixtureCase):
    def native(self):
        source=self.request.sources[0]
        b=build_text('block-1',TEXT,('region-1',),1,1.0)
        a=Anchor(source.artifact.sha256,1,'region-1',(0.0,0.0,1.0,1.0))
        return b,a,source
    def test_actual_canonical_bi_producer_consumed(self):
        b,a,s=self.native()
        result=block_from_bi(b,a,s,extractor_id='utf8',extractor_version='1')
        self.assertEqual(result,self.request.blocks[0])
    def test_actual_canonical_ki_producers_consumed(self):
        row=extract([{'id':'narration','claims':[TEXT],'anchor_id':'bi-anchor'}])[0]
        binding=bind(row['claim_id'],('bi-anchor',),1.0)
        c=claim_from_ki(row,binding,self.request.outputs[0],start=0,end=len(TEXT),citation_map={'bi-anchor':'cite-1'})
        r=replace(self.request,claims=(c,));result=self.check(r)
        self.assertEqual(result.provenance.status,'CHECKS_PASSED')
        self.assertTrue(binding['grounded']);self.assertEqual(result.grounding.status,'REVIEW_REQUIRED')
    def test_bi_anchor_source_mismatch(self):
        b,a,s=self.native()
        with self.assertRaises(ContractError):block_from_bi(b,replace(a,source_hash='0'*64),s,extractor_id='a',extractor_version='1')
    def test_bi_region_mismatch(self):
        b,a,s=self.native()
        with self.assertRaises(ContractError):block_from_bi(replace(b,region_ids=('other',)),a,s,extractor_id='a',extractor_version='1')
    def test_bi_float_nan_bool_and_precision_rejected(self):
        b,a,s=self.native()
        for val in (float('nan'),True,0.123456789):
            with self.subTest(val=val),self.assertRaises(ContractError):block_from_bi(replace(b,confidence=val),a,s,extractor_id='a',extractor_version='1')
    def test_bi_geometry_not_silently_rounded(self):
        b,a,s=self.native()
        with self.assertRaises(ContractError):block_from_bi(b,replace(a,box=(0.0000001,0,1,1)),s,extractor_id='a',extractor_version='1')
    def test_ki_missing_anchor_mapping_rejected(self):
        row=extract([{'id':'o','claims':[TEXT],'anchor_id':'a'}])[0];binding=bind(row['claim_id'],('a',),1)
        with self.assertRaises(ContractError):claim_from_ki(row,binding,self.request.outputs[0],start=0,end=len(TEXT),citation_map={})
    def test_ki_unexpected_authority_field_rejected(self):
        row=extract([{'id':'o','claims':[TEXT],'anchor_id':'a'}])[0];binding=bind(row['claim_id'],('a',),1);row['accepted']=True
        with self.assertRaises(ContractError):claim_from_ki(row,binding,self.request.outputs[0],start=0,end=len(TEXT),citation_map={'a':'cite-1'})
    def test_ki_claim_identity_mismatch_rejected(self):
        row=extract([{'id':'o','claims':[TEXT],'anchor_id':'a'}])[0];binding=bind('other',('a',),1)
        with self.assertRaises(ContractError):claim_from_ki(row,binding,self.request.outputs[0],start=0,end=len(TEXT),citation_map={'a':'cite-1'})

    def test_bi_mutable_geometry_rejected(self):
        b,a,s=self.native()
        with self.assertRaises(ContractError):block_from_bi(b,replace(a,box=[0,0,1,1]),s,extractor_id='a',extractor_version='1')
    def test_ki_malformed_anchor_types_fail_as_contract_errors(self):
        row=extract([{'id':'o','claims':[TEXT],'anchor_id':'a'}])[0]
        binding=bind(row['claim_id'],('a',),1)
        for anchors in (({},),('a',None),['a']):
            with self.subTest(anchors=anchors),self.assertRaises(ContractError):
                claim_from_ki(row,{**binding,'anchor_ids':anchors},self.request.outputs[0],start=0,end=len(TEXT),citation_map={'a':'cite-1'})
    def test_ki_mapping_cannot_contain_malformed_ids(self):
        row=extract([{'id':'o','claims':[TEXT],'anchor_id':'a'}])[0];binding=bind(row['claim_id'],('a',),1)
        with self.assertRaises(ContractError):claim_from_ki(row,binding,self.request.outputs[0],start=0,end=len(TEXT),citation_map={'a':None})
