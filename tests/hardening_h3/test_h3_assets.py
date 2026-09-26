import unittest,tempfile,hashlib
from pathlib import Path
from dataclasses import replace
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.compiler_engine.contracts import AssetDescriptor
from bie.game_engine.build_runtime_engine.workspace import build_workspace
class H3Assets(unittest.TestCase):
 def test_sanitized_collision_gets_distinct_content_addressed_paths(self):
  ctx,base_blobs=build_inputs();base_assets=dict(ctx.assets);a=b'one';b=b'two';d1=AssetDescriptor('asset:a/b','audio/wav',hashlib.sha256(a).hexdigest(),'a').validate();d2=AssetDescriptor('asset:a:b','audio/wav',hashlib.sha256(b).hexdigest(),'b').validate();base_assets.update({d1.asset_ref:d1,d2.asset_ref:d2});ctx=replace(ctx,assets=base_assets);blobs=dict(base_blobs);blobs.update({d1.asset_ref:a,d2.asset_ref:b})
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(ctx,blobs,Path(td));paths=[x[1] for x in w.manifest.asset_bindings if x[0] in {d1.asset_ref,d2.asset_ref}];self.assertEqual(len(paths),2);self.assertEqual(len(set(paths)),2);self.assertTrue(all('--' in x for x in paths))
 def test_asset_binding_hashes_match(self):
  ctx,assets=build_inputs()
  with tempfile.TemporaryDirectory() as td:
   w=build_workspace(ctx,assets,Path(td));
   for ref,path,sha in w.manifest.asset_bindings:self.assertEqual(hashlib.sha256((Path(td)/'dist'/path).read_bytes()).hexdigest(),sha)
