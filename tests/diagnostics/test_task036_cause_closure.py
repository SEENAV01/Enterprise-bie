import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import task036_cause_closure as probe
from bie.compiler.qa_common import CompilerQAError
from bie.compiler.layout_browser import ChromiumLayoutProbe
from playwright.sync_api import Error, TimeoutError as PWTimeout

SECRET = 'private-token-private-path-private-media'


class CauseClosureControls(unittest.TestCase):
    def test_exact_native_code_only(self):
        self.assertEqual(probe.error_label(CompilerQAError('LAYOUT_BRIDGE_FAILED: ' + SECRET)),
            {'exception_class': 'COMPILER_QA', 'code': 'LAYOUT_BRIDGE_FAILED'})
        self.assertNotIn(SECRET, json.dumps(probe.error_label(CompilerQAError(SECRET))))

    def test_playwright_classifies_without_exporting_private_payload(self):
        value = probe.error_label(Error("BrowserType.launch: Target page, context or browser has been closed " + SECRET))
        self.assertEqual(value['code'], 'BROWSER_TARGET_CLOSED')
        self.assertNotIn(SECRET, json.dumps(value))

    def test_timeout_class_identity_retained(self):
        self.assertEqual(probe.error_label(PWTimeout('Timeout 30000ms exceeded '+SECRET))['exception_class'], 'PLAYWRIGHT_TIMEOUT')

    def test_foreign_exception_properties_and_formatting_unread(self):
        class Foreign(ValueError):
            @property
            def message(self): raise AssertionError('must not read')
            def __str__(self): raise AssertionError('must not format')
            def __repr__(self): raise AssertionError('must not format')
        self.assertEqual(probe.error_label(Foreign(SECRET)), {'exception_class': 'OTHER', 'code': 'UNCLASSIFIED'})

    def test_oversized_text_is_unclassified(self):
        self.assertEqual(probe.error_label(Error('x'*16385))['code'], 'UNCLASSIFIED')

    def test_real_constructor_failure_classification_and_trace_restoration(self):
        previous = sys.gettrace()
        with probe.layout_observation() as receipt:
            with self.assertRaises(CompilerQAError):
                ChromiumLayoutProbe('/missing-task036-synthetic-browser')
        self.assertIs(sys.gettrace(), previous)
        self.assertEqual(receipt['events'], [{'site':'BROWSER_CONSTRUCTOR', 'exception_class':'COMPILER_QA', 'code':'LAYOUT_BROWSER_UNAVAILABLE'}])
        self.assertFalse(receipt['product_accepted'])
        self.assertNotIn('/missing', json.dumps(receipt))

    def test_existing_trace_is_preserved_and_not_overwritten(self):
        previous = sys.gettrace()
        def existing(*_): return existing
        sys.settrace(existing)
        try:
            with probe.layout_observation() as receipt:
                self.assertIs(sys.gettrace(), existing)
                self.assertEqual(receipt['availability'], 'UNAVAILABLE')
                self.assertEqual(receipt['reason'], 'EXISTING_TRACE')
        finally:
            sys.settrace(previous)

    def test_foreign_frame_cannot_create_native_observation(self):
        with probe.layout_observation() as receipt:
            try: raise CompilerQAError('LAYOUT_BRIDGE_FAILED: '+SECRET)
            except CompilerQAError: pass
        self.assertEqual(receipt['events'], [])


if __name__ == '__main__': unittest.main()
