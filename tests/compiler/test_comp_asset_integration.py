import unittest,tempfile,hashlib
from pathlib import Path
from bie.scene_ir.unified_scene_ir_contract import UnifiedElement,UnifiedSceneIRDocument
from bie.compiler.compiler_asset_common import CompilerAssetRecord
from bie.compiler.asset_bundler import bundle_assets
from bie.compiler.asset_path_resolver import CompilerAssetPathRegistry
from bie.compiler.asset_hash_verifier import verify_bundle_hashes,require_all_hashes
from bie.compiler.missing_asset_failure import detect_missing_assets

class T(unittest.TestCase):
 def test_bundle_resolve_hash_and_missing_asset_gate(self):
  with tempfile.TemporaryDirectory() as src,tempfile.TemporaryDirectory() as out:
   p=Path(src)/"cell.png";p.write_bytes(b"image-bytes")
   digest=hashlib.sha256(b"image-bytes").hexdigest()
   rec=CompilerAssetRecord("cell",str(p),digest,"image/png","user_supplied",True)

   bundle=bundle_assets([rec],out)
   self.assertTrue(bundle.passed)
   self.assertTrue(require_all_hashes(verify_bundle_hashes(bundle)))

   registry=CompilerAssetPathRegistry()
   for item in bundle.bundled:
    registry.register(item)
   resolved=registry.require("asset://cell")
   self.assertTrue(resolved.passed)
   self.assertTrue(resolved.resolved_public_path.startswith("assets/"))

   element=UnifiedElement("img","image",{"asset_ref":"asset://cell"},("src",),("r",),{"alt":"cell"})
   doc=UnifiedSceneIRDocument("scene","1.0.0","T",10,(element,),(),("src",),("r",))
   report=detect_missing_assets(doc,registry)
   self.assertTrue(report.passed)
   self.assertFalse(report.accepted)

 def test_missing_asset_fails_closed(self):
  registry=CompilerAssetPathRegistry()
  element=UnifiedElement("img","image",{"asset_ref":"asset://missing"},("src",),("r",),{"alt":"x"})
  doc=UnifiedSceneIRDocument("scene","1.0.0","T",10,(element,),(),("src",),("r",))
  self.assertFalse(detect_missing_assets(doc,registry).passed)
