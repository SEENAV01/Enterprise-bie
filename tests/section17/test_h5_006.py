"""Actual AX API tests on an in-memory authored document, NOT HTTP boot proof."""
import unittest
from playwright.sync_api import sync_playwright
from h5_support import BROWSER
from bie.evaluation.benchmarks.browser.served.accessibility import inspect_ax
class H5006(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path=BROWSER,headless=True,chromium_sandbox=False)
  cls.page=cls.browser.new_page();cls.page.set_content('<button id="b">Submit answer</button><label for="i">Explanation</label><input id="i"><div id="hidden" hidden>Hidden</div><img id="image" alt="Fraction diagram"><button id="aria" aria-label="Next step">Go</button>')
 @classmethod
 def tearDownClass(cls):cls.browser.close();cls.pw.stop()
 def test_button_native_role(self):self.assertEqual(inspect_ax(self.page,'#b')['role'],'button')
 def test_button_native_name(self):self.assertEqual(inspect_ax(self.page,'#b')['name'],'Submit answer')
 def test_label_association(self):self.assertEqual(inspect_ax(self.page,'#i')['name'],'Explanation')
 def test_textbox_native_role(self):self.assertEqual(inspect_ax(self.page,'#i')['role'],'textbox')
 def test_hidden_is_ignored(self):self.assertTrue(inspect_ax(self.page,'#hidden')['ignored'])
 def test_missing_element(self):self.assertFalse(inspect_ax(self.page,'#missing')['present'])
 def test_image_alt_name(self):self.assertEqual(inspect_ax(self.page,'#image')['name'],'Fraction diagram')
 def test_aria_name_overrides_visible_label(self):self.assertEqual(inspect_ax(self.page,'#aria')['name'],'Next step')
