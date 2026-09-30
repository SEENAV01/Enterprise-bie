"""Actual capture-call configuration contracts; NOT rendering witnesses."""
from pathlib import Path
import json
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'bie/compiler/qa_support/remotion_raster_capture.cjs'


def options():
    text=SOURCE.read_text()
    matches=re.findall(r'const serveUrl=await bundle\((\{[^\n]+\})\);',text)
    if len(matches)!=1: raise AssertionError('EXACT_CAPTURE_BUNDLE_CALL_REQUIRED')
    script=("const path=require('node:path');const req={workspace:'/work'};const out='/work/capture-output';"
            "console.log(JSON.stringify(("+matches[0]+")));")
    p=subprocess.run(['node','-e',script],text=True,capture_output=True,timeout=15,check=False)
    if p.returncode: raise AssertionError(p.stderr)
    return json.loads(p.stdout)


class CaptureCacheConfigurationTests(unittest.TestCase):
    def test_cache_is_explicitly_disabled(self):
        self.assertIs(options().get('enableCaching'),False)

    def test_checked_entry_is_unchanged(self):
        self.assertEqual(options()['entryPoint'],'/work/qa-capture-entry.tsx')

    def test_bundle_output_remains_in_writable_capture_directory(self):
        self.assertEqual(options()['outDir'],'/work/capture-output/bundle')

    def test_public_assets_are_not_redirected(self):
        self.assertEqual(options()['publicDir'],'/work/public')

    def test_no_other_bundle_options_or_node_syntax_change(self):
        self.assertEqual(set(options())-{'enableCaching'},{'entryPoint','outDir','publicDir'})
        p=subprocess.run(['node','--check',str(SOURCE)],text=True,capture_output=True,timeout=15,check=False)
        self.assertEqual(p.returncode,0,p.stderr)


if __name__=='__main__': unittest.main(verbosity=2)
