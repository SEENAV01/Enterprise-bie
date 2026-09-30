"""Checkout line endings may differ; the pinned Git blob must not."""
import unittest

from bie.evaluation.benchmarks.native_api.service import (
    _checkout_blob_bytes,
    verify_native_api,
)


class CheckoutPinTests(unittest.TestCase):
    def test_exact_lf_is_unchanged(self):
        self.assertEqual(_checkout_blob_bytes(b'a\nb\n'), b'a\nb\n')

    def test_exact_crlf_conversion(self):
        self.assertEqual(_checkout_blob_bytes(b'a\r\nb\r\n'), b'a\nb\n')

    def test_stray_carriage_return_not_normalized(self):
        self.assertEqual(_checkout_blob_bytes(b'a\r\nb\r'), b'a\r\nb\r')

    def test_altered_content_is_not_repaired(self):
        self.assertNotEqual(_checkout_blob_bytes(b'a!\r\nb\r\n'), b'a\nb\n')

    def test_actual_canonical_api_pin(self):
        from bie.infrastructure.benchmark_api import BenchmarkAPI

        self.assertIs(verify_native_api(), BenchmarkAPI)


if __name__ == '__main__':
    unittest.main()
