"""Exact historical bytes, narrow replacement and unlisted-change controls."""
import copy
from pathlib import Path
import tempfile
import unittest
from scripts import director_span_source_amendment as amendment

ROOT = Path(__file__).resolve().parents[2]


class DirectorSpanAmendmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.document = amendment.validate(ROOT)

    def fixture(self):
        tmp = tempfile.TemporaryDirectory(prefix='bie-span-amendment-')
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        paths = {r['path'] for r in self.document['original_director_inventory']}
        paths |= {r['preimage'] for r in self.document['files']}
        paths |= {amendment.DOCUMENT, amendment.PREVIOUS_DOCUMENT, 'manifests/'+amendment.MANIFEST}
        paths |= {self.document['audit_wiring']['path'], self.document['audit_wiring']['preimage']}
        for relative in paths:
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT/relative).read_bytes())
        return root

    def reject_edit(self, relative, transform):
        root = self.fixture(); path = root/relative
        path.write_bytes(transform(path.read_bytes()))
        with self.assertRaises(ValueError): amendment.validate(root)

    def test_exact_original_and_active_identities_pass(self):
        original, document = amendment.validate(ROOT)
        self.assertEqual(original, self.original)
        self.assertEqual(document['independent_review'], 'PENDING_NOT_SELF_APPROVED')
        self.assertIs(document['product_accepted'], False)

    def test_all_seven_members_and_six_contributors_are_reconciled(self):
        result, count = amendment.resolve(ROOT, Path(amendment.MANIFEST), copy.deepcopy(self.original))
        self.assertEqual(count, 7)
        for row in self.document['files']:
            actual = [r for r in result['members'] if r['canonical_path']==row['preimage']]
            self.assertEqual(len(actual), amendment.TARGETS[row['path']])
            self.assertEqual([r['original_sha256'] for r in actual], [r['original_sha256'] for r in row['member_rows']])
            self.assertTrue(all(r['canonical_sha256']==row['before']['sha256'] for r in actual))
        collision = next(r for r in result['collisions'] if r['canonical_path'].endswith('narration_annotations.py.before'))
        self.assertEqual(len(collision['contributors']), 6)
        self.assertEqual(collision['contributors'], self.document['files'][1]['collision_rows'][0]['contributors'])

    def test_resolver_does_not_mutate_manifest_or_unrelated_rows(self):
        original = copy.deepcopy(self.original)
        result, _ = amendment.resolve(ROOT, Path(amendment.MANIFEST), original)
        self.assertEqual(original, self.original)
        for before, after in zip(original['members'], result['members']):
            if before['canonical_path'] not in amendment.TARGETS: self.assertEqual(before, after)
        self.assertEqual(original['archives'], result['archives'])

    def test_wrong_manifest_is_not_a_wildcard_exception(self):
        original = copy.deepcopy(self.original)
        result, count = amendment.resolve(ROOT, Path('other.json'), original)
        self.assertIs(result, original); self.assertEqual(count, 0)

    def test_each_active_source_tamper_rejected(self):
        for row in self.document['files']:
            with self.subTest(path=row['path']): self.reject_edit(row['path'], lambda b:b+b'\n')

    def test_each_preimage_tamper_rejected(self):
        for row in self.document['files']:
            with self.subTest(path=row['path']): self.reject_edit(row['preimage'], lambda b:b+b'\n')

    def test_rollback_to_original_source_rejected(self):
        root = self.fixture()
        for row in self.document['files']:
            (root/row['path']).write_bytes((root/row['preimage']).read_bytes())
        with self.assertRaises(ValueError): amendment.validate(root)

    def test_crlf_authority_conversion_rejected(self):
        for path in (amendment.DOCUMENT, 'manifests/'+amendment.MANIFEST, self.document['files'][0]['preimage']):
            with self.subTest(path=path): self.reject_edit(path, lambda b:b.replace(b'\n',b'\r\n'))

    def test_changed_expected_hash_cannot_bless_current_bytes(self):
        self.reject_edit(amendment.DOCUMENT, lambda b:b.replace(b'PENDING_NOT_SELF_APPROVED', b'APPROVED'))

    def test_duplicate_or_extra_document_fields_rejected(self):
        self.reject_edit(amendment.DOCUMENT, lambda b:b.replace(b'{',b'{"schema":"forged",',1))
        self.reject_edit(amendment.DOCUMENT, lambda b:b.replace(b'{',b'{"wildcard":true,',1))

    def test_original_manifest_tamper_rejected(self):
        self.reject_edit('manifests/'+amendment.MANIFEST, lambda b:b+b' ')

    def test_previous_step4_draft_is_immutable_and_authenticated(self):
        self.reject_edit(amendment.PREVIOUS_DOCUMENT, lambda b:b+b' ')

    def test_forged_duplicate_extra_or_missing_caller_member_rejected(self):
        for mode in ('duplicate','extra','missing'):
            manifest = copy.deepcopy(self.original)
            if mode=='duplicate': manifest['members'].append(copy.deepcopy(self.document['files'][0]['member_rows'][0]))
            elif mode=='extra': manifest['members'].append({'canonical_path':'bie/director/unlisted.py'})
            else: manifest['members'].remove(self.document['files'][0]['member_rows'][0])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                amendment.resolve(ROOT, Path(amendment.MANIFEST), manifest)

    def test_changed_collision_contributor_rejected(self):
        manifest = copy.deepcopy(self.original)
        next(c for c in manifest['collisions'] if c['canonical_path'] in amendment.TARGETS)['contributors'].pop()
        with self.assertRaises(ValueError): amendment.resolve(ROOT, Path(amendment.MANIFEST), manifest)

    def test_unrelated_director_change_rejected(self):
        row = next(r for r in self.document['original_director_inventory'] if r['path'] not in amendment.TARGETS)
        self.reject_edit(row['path'], lambda b:b+b'\n')

    def test_unlisted_native_source_rejected(self):
        root = self.fixture(); (root/'bie/director/unlisted.py').write_bytes(b'pass\n')
        with self.assertRaises(ValueError): amendment.validate(root)

    def test_missing_native_source_rejected(self):
        root = self.fixture()
        (root/self.document['original_director_inventory'][0]['path']).unlink()
        with self.assertRaises(ValueError): amendment.validate(root)

    def test_audit_wiring_and_its_preimage_tamper_rejected(self):
        for key in ('path', 'preimage'):
            self.reject_edit(self.document['audit_wiring'][key], lambda b:b+b'\n')


if __name__ == '__main__': unittest.main()
