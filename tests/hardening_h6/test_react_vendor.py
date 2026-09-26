from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.react_runtime_engine.vendor import verify_vendor, materialize_vendor
from bie.game_engine.react_runtime_engine import vendor as module
from bie.game_engine.build_runtime_engine.entrypoint import ENTRY_JS

class VendorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'vendor'
        shutil.copytree(Path(module.__file__).parent / 'vendor', self.root)

    def test_pinned_real_dependencies_and_license_inventory(self):
        result = verify_vendor(self.root)
        self.assertEqual(result['versions']['react'], '19.3.0')
        self.assertEqual(result['versions']['react-dom'], '19.3.0')
        self.assertTrue(any('react-dom-client.production.js' in x['path'] for x in result['sources']))
        self.assertTrue({'react-LICENSE.txt','react-dom-LICENSE.txt','scheduler-LICENSE.txt'}.issubset({x['path'] for x in result['files']}))

    def test_modified_vendor_bytes_rejected(self):
        (self.root / 'react-vendor.js').write_text('fake runtime')
        with self.assertRaisesRegex(GameContractError, 'FILE_TAMPER'):
            verify_vendor(self.root)

    def test_missing_license_rejected(self):
        (self.root / 'react-LICENSE.txt').unlink()
        with self.assertRaisesRegex(GameContractError, 'FILE_MISSING'):
            verify_vendor(self.root)

    def test_forged_manifest_rejected_even_with_new_hashes(self):
        p = self.root / 'vendor-manifest.json'
        manifest = json.loads(p.read_text()); manifest['versions']['react'] = '0.0.0'
        p.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(GameContractError, 'MANIFEST_TAMPER'):
            verify_vendor(self.root)

    def test_untracked_vendor_payload_rejected(self):
        (self.root / 'injected.js').write_text('injected')
        with self.assertRaisesRegex(GameContractError, 'UNTRACKED_FILE'):
            verify_vendor(self.root)

    def test_materialized_bytes_match_pinned_source(self):
        target = Path(self.temp.name) / 'runtime'; target.mkdir()
        manifest = materialize_vendor(target)
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((target / row['path']).read_bytes()).hexdigest(), row['sha256'])

    def test_materialization_cannot_overwrite_existing_file(self):
        target = Path(self.temp.name) / 'runtime'; target.mkdir()
        existing = target / 'react-vendor.js'; existing.write_text('preserve')
        with self.assertRaisesRegex(GameContractError, 'DESTINATION_EXISTS'):
            materialize_vendor(target)
        self.assertEqual(existing.read_text(), 'preserve')
        self.assertEqual(len(list(target.iterdir())), 1)

    def test_entrypoint_requires_real_vendor(self):
        self.assertIn('from "./react-vendor.js"', ENTRY_JS)
        self.assertIn('createRoot(container', ENTRY_JS)
        self.assertIn('flushSync(() => reactRoot.render', ENTRY_JS)
        self.assertNotIn('const React = {', ENTRY_JS)
