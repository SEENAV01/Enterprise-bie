import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.verify_section17_adoption import matches


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


if __name__ == '__main__':
    unittest.main()
