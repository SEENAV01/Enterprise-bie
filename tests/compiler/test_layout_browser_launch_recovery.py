import sys
import unittest
from unittest.mock import patch

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from bie.compiler.layout_browser import ChromiumLayoutProbe


class FakeBrowser:
    version = 'fake-chromium'

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def launch(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class FakePlaywright:
    def __init__(self, outcome):
        self.chromium = FakeChromium(outcome)
        self.stopped = False

    def stop(self):
        self.stopped = True


class Starter:
    def __init__(self, playwright):
        self.playwright = playwright

    def start(self):
        return self.playwright


class ChromiumLaunchRecoveryTests(unittest.TestCase):
    def probe(self):
        return ChromiumLayoutProbe(sys.executable, timeout_ms=1000)

    def test_single_timeout_retries_with_fresh_playwright(self):
        first = FakePlaywright(PlaywrightTimeoutError('cold start timeout'))
        browser = FakeBrowser()
        second = FakePlaywright(browser)
        with patch('playwright.sync_api.sync_playwright',
                   side_effect=[Starter(first), Starter(second)]) as factory, \
             patch('bie.compiler.layout_browser.time.sleep') as sleep:
            probe = self.probe()
            self.assertIs(probe.__enter__(), probe)
            self.assertIs(probe.browser, browser)
            self.assertEqual(factory.call_count, 2)
            self.assertTrue(first.stopped)
            self.assertFalse(second.stopped)
            sleep.assert_called_once()
            probe.__exit__()
            self.assertTrue(browser.closed)
            self.assertTrue(second.stopped)

    def test_second_timeout_fails_closed(self):
        first = FakePlaywright(PlaywrightTimeoutError('cold start timeout'))
        second = FakePlaywright(PlaywrightTimeoutError('second timeout'))
        with patch('playwright.sync_api.sync_playwright',
                   side_effect=[Starter(first), Starter(second)]) as factory, \
             patch('bie.compiler.layout_browser.time.sleep'):
            probe = self.probe()
            with self.assertRaises(PlaywrightTimeoutError):
                probe.__enter__()
            self.assertEqual(factory.call_count, 2)
            self.assertTrue(first.stopped)
            self.assertTrue(second.stopped)
            self.assertIsNone(probe.playwright)
            self.assertIsNone(probe.browser)

    def test_non_timeout_error_is_not_retried(self):
        first = FakePlaywright(RuntimeError('invalid browser'))
        with patch('playwright.sync_api.sync_playwright',
                   return_value=Starter(first)) as factory, \
             patch('bie.compiler.layout_browser.time.sleep') as sleep:
            probe = self.probe()
            with self.assertRaisesRegex(RuntimeError, 'invalid browser'):
                probe.__enter__()
            self.assertEqual(factory.call_count, 1)
            sleep.assert_not_called()
            self.assertTrue(first.stopped)
            self.assertIsNone(probe.playwright)
            self.assertIsNone(probe.browser)


if __name__ == '__main__':
    unittest.main()
