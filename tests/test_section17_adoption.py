import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.verify_section17_adoption import matches, verify_h1_preimages


class Section17AdoptionTests(unittest.TestCase):
    def test_exact_bytes_match(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.py'
            path.write_bytes(b'a\nb\n')
            expected = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(matches(path, expected))

    def test_windows_crlf_materialization_matches_pinned_lf(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.py'
            path.write_bytes(b'a\r\nb\r\n')
            expected = hashlib.sha256(b'a\nb\n').hexdigest()
            self.assertTrue(matches(path, expected))

    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.py'
            path.write_bytes(b'changed\r\nb\r\n')
            expected = hashlib.sha256(b'a\nb\n').hexdigest()
            self.assertFalse(matches(path, expected))

    def test_binary_line_ending_rewrite_is_not_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.mkv'
            path.write_bytes(b'a\r\nb\r\n')
            expected = hashlib.sha256(b'a\nb\n').hexdigest()
            self.assertFalse(matches(path, expected))


class H1PreimageRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.paths = {}
        self.delta = {'changed_original_files': []}
        self.recovery = {
            'source_master_sha256': '03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e',
            'status': 'RECOVERED_EXACT_BYTES', 'bytes_reconstructed': False, 'files': [],
        }
        for index in range(14):
            relative = f'evidence/section17/h1/preimages/fixture{index}.py'
            path = Path(self.directory.name) / f'fixture{index}.py'
            path.write_bytes(f'original{index}\n'.encode())
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            self.paths[relative] = path
            self.delta['changed_original_files'].append({
                'path': f'original{index}.py', 'preimage': relative, 'before_sha256': sha,
            })
            self.recovery['files'].append({
                'path': relative, 'original_path': f'original{index}.py', 'sha256': sha,
            })

    def verify(self):
        with patch('scripts.verify_section17_adoption.checked_path', side_effect=self.paths.__getitem__):
            return verify_h1_preimages(self.delta, self.recovery)

    def test_all_original_preimage_bytes_pass(self):
        self.assertEqual(self.verify(), [])

    def test_missing_preimage_does_not_pass_on_metadata(self):
        next(iter(self.paths.values())).unlink()
        self.assertTrue(self.verify())

    def test_changed_preimage_is_rejected(self):
        next(iter(self.paths.values())).write_bytes(b'changed\n')
        self.assertTrue(self.verify())

    def test_wrong_preimage_binding_is_rejected(self):
        self.recovery['files'][0]['sha256'] = '0' * 64
        self.assertTrue(self.verify())

    def test_duplicate_or_missing_manifest_row_is_rejected(self):
        self.recovery['files'][-1] = self.recovery['files'][0]
        self.assertTrue(self.verify())


if __name__ == '__main__':
    unittest.main()
