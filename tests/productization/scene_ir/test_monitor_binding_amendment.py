"""Exact admission-metadata chain controls; not native render or approval proof."""
from pathlib import Path
import json
import unittest
import tempfile
from contextlib import contextmanager
from hashlib import sha1,sha256
from types import SimpleNamespace
from unittest.mock import patch
from scripts import compiler_monitor_binding_source_amendment as audit
from bie.productization import scene_ir_monitor_review as admission
from bie.productization.contracts import ProducerError

ROOT=Path(__file__).resolve().parents[3]

class MonitorBindingAmendmentControls(unittest.TestCase):
    @contextmanager
    def synthetic_admission_namespace(self):
        """Document mocks exercise admission only; they never constitute approval."""
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);rows=[]
            for path in sorted(admission.PATHS):
                raw=(ROOT/path).read_bytes();target=root/path
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                mode='RAW_IMMUTABLE' if path.startswith('docs/') else 'CRLF_TO_LF_ONLY'
                data=raw if mode=='RAW_IMMUTABLE' else raw.replace(b'\r\n',b'\n')
                rows.append(dict(path=path,git_blob=sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),
                    raw_git_bytes=len(raw),raw_git_sha256=sha256(raw).hexdigest(),mode=mode,bytes=len(data),
                    sha256=sha256(data).hexdigest(),origin=('EXACT_REVIEWED_PROSPECTIVE_ADMISSION_OVERLAY'
                        if path in admission.OVERLAY_PATHS else 'REVIEWED_PARENT_GIT')))
            for path in set(admission.AMENDMENTS)-admission.PATHS:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/path).read_bytes())
            source=dict(source_bindings=rows,
                original_review_sha256='33458799eaf58951aa474a08d412b6b56361ec2f08aebdc23f150976a92410a5',
                original_final_review_sha256='9eb3ff17a7e128d5dd9ac6da6210c9461dfbecf6002c33bb499c8215a492612a',
                original_binding_sha256='dbed506a90958c88263dad9280eb2575ec285e79a960952c5c62b4c9f8da53ad',
                original_chain_sha256=admission.ORIGINAL_CHAIN_SHA,
                native_scope=dict(commit=admission.CANDIDATE,tree=admission.TREE,worker_sha256=admission.ACTIVE_SHA),
                admission_overlay_scope='EXACT_READ_ONLY_ADMISSION_AND_RAW_RECORD_EOL_ONLY')
            review={key:None for key in admission.REVIEW_FIELDS}
            review.update(schema='bie.task036.m1.monitor-closure-review/1',candidate=admission.CANDIDATE,
                tree=admission.TREE,base=admission.BASE,base_tree=admission.BASE_TREE,decision=admission.DECISION,
                blocking_findings_remaining=0,amendments=admission.AMENDMENTS,source_review=source,
                product_accepted=False,reviewer=dict(execution_identity=admission.REVIEWER,
                    implementation_execution='/root',type='GENUINELY_SEPARATE_READ_ONLY_AI_ASSISTED_EXECUTION',
                    role='M1-EXTERNAL-TECHNICAL-REVIEWER-001',human_signature=False,PR_review_submission=False))
            binding=dict(schema='bie.task036.reviewed-monitor-source-bindings/1',
                role='REVIEWED_NATIVE_PARENT_AND_EXACT_ADMISSION_OVERLAY_NOT_AN_APPROVAL',
                candidate=admission.CANDIDATE,tree=admission.TREE,review_sha256=admission.REVIEW_SHA,
                original_source_chain_sha256=admission.ORIGINAL_CHAIN_SHA,amendments=admission.AMENDMENTS,
                files=rows,product_accepted=False)
            def documents(_,path,*args):return review if path==admission.REVIEW else binding
            with patch.object(admission,'document',side_effect=documents):yield root

    @staticmethod
    def admission_read(root,path,*args):return (root/path).read_bytes()

    def test_admission_path_accepts_only_complete_authenticated_flat_namespaces(self):
        with self.synthetic_admission_namespace() as root:
            row=admission.verified_review(root,read=self.admission_read)
            self.assertEqual(row['sha256'],admission.ACTIVE_SHA)

    def test_admission_path_rejects_unlisted_files_and_directories_in_every_namespace(self):
        for directory in admission.AMENDMENT_DIRECTORIES:
            for extra_directory in (False,True):
                with self.subTest(directory=directory,extra_directory=extra_directory),self.synthetic_admission_namespace() as root:
                    extra=root/directory/'unlisted'
                    if extra_directory:extra.mkdir()
                    else:extra.write_bytes(b'test-only unlisted member')
                    with self.assertRaises(ProducerError):admission.verified_review(root,read=self.admission_read)

    def test_admission_path_rejects_missing_required_members_in_every_namespace(self):
        for directory,names in admission.AMENDMENT_DIRECTORIES.items():
            with self.subTest(directory=directory),self.synthetic_admission_namespace() as root:
                (root/directory/sorted(names)[0]).unlink()
                with self.assertRaises(ProducerError):admission.verified_review(root,read=self.admission_read)

    def test_admission_path_rejects_link_and_nonregular_entries_before_payload_reads(self):
        original=admission.os.scandir
        for linked in (False,True):
            with self.subTest(linked=linked),self.synthetic_admission_namespace() as root:
                @contextmanager
                def scan(directory):
                    with original(directory) as entries:
                        rows=list(entries);first=rows[0]
                        rows[0]=SimpleNamespace(name=first.name,is_symlink=lambda:linked,
                            is_file=lambda **kwargs:False,stat=first.stat)
                        yield iter(rows)
                with patch.object(admission.os,'scandir',scan),self.assertRaises(ProducerError):
                    admission.verified_review(root,read=self.admission_read)

    def reject(self,target,transform):
        from scripts.compiler_cache_source_amendment import regular
        def read(root,path,maximum):
            raw=regular(root,path,maximum)
            return transform(raw) if path==target else raw
        with self.assertRaises(ValueError):audit.validate(ROOT,read=read)

    def test_actual_exact_metadata_amendment_and_preimages_authenticate(self):
        doc=audit.validate(ROOT)
        self.assertEqual(len(doc['replacements']),2)
        self.assertFalse(doc['native_compiler_sources_changed'])
        self.assertEqual(audit.historical_attribute_bytes(ROOT),
            (ROOT/audit.D/'.gitattributes.before').read_bytes())

    def test_current_attribute_and_resolver_tamper_each_rejected(self):
        for path in audit.TARGETS:self.reject(path,lambda raw:raw+b'\n')

    def test_each_exact_preimage_tamper_and_crlf_conversion_rejected(self):
        for name in ('.gitattributes.before','compiler_monitor_parse_source_amendment.py.before'):
            self.reject(audit.D+name,lambda raw:raw+b'\n')
            self.reject(audit.D+name,lambda raw:raw.replace(b'\n',b'\r\n'))

    def test_immutable_previous_and_current_seals_cannot_self_bless(self):
        for path in (audit.DOCUMENT,audit.PREVIOUS):self.reject(path,lambda raw:raw+b'\n')

    def test_partial_old_attribute_rollback_rejected(self):
        before=(ROOT/audit.D/'.gitattributes.before').read_bytes()
        self.reject('.gitattributes',lambda raw:before)

    def test_unlisted_amendment_path_is_not_wildcard_exempt(self):
        original=Path.rglob
        def paths(root,pattern):
            yield from original(root,pattern)
            if root==ROOT/audit.D:yield ROOT/'tools/run_task036_tests.py'
        with patch.object(Path,'rglob',paths),self.assertRaises(ValueError):audit.validate(ROOT)

    def test_complete_original_two_monitor_gates_remain_active(self):
        from scripts.compiler_monitor_snapshot_amendment import validate as snapshot
        from scripts.compiler_monitor_parse_source_amendment import validate as capture
        self.assertEqual(len(snapshot(ROOT)['replacements']),3)
        self.assertEqual(len(capture(ROOT)['replacements']),3)

    def test_pending_actual_approval_cannot_grant_admission_or_read_arbitrary_files(self):
        read=unittest.mock.Mock()
        with patch.object(admission,'DOCUMENT_BYTES',{admission.REVIEW:0,admission.BINDINGS:0}),self.assertRaises(ProducerError):
            admission.verified_review(ROOT,read=read)
        read.assert_not_called()

    def test_new_guard_cannot_expand_exact_source_paths_or_normalize_sealed_metadata(self):
        self.assertEqual(len(admission.PATHS),17)
        self.assertEqual(len(admission.OVERLAY_PATHS),6)
        self.assertLessEqual(admission.OVERLAY_PATHS,admission.PATHS)
        self.assertNotIn('bie/compiler/real_paint.py',admission.PATHS)
        self.assertEqual(admission.AMENDMENTS['docs/productization/task036-motion-amendment/AMENDMENT.json'],
            'b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c')

if __name__=='__main__':unittest.main()
