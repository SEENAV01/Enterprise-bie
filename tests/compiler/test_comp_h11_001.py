import json,os,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from bie.compiler.visual_assets import *
from bie.compiler.asset_bundler import bundle_assets
from bie.compiler.compiler_asset_common import CompilerAssetRecord
from tests.compiler.h11_test_support import scene,asset,path,copy_assets,ASSET_ROOT

class VisualAssetContracts(unittest.TestCase):
    def bad(self,change,code):
        p=scene();change(p);self.assertRaisesRegex(ValueError,code,plan_visual_assets,p)
    def test_input_is_not_mutated(self):
        p=scene();q=deepcopy(p);self.assertTrue(plan_visual_assets(p));self.assertEqual(p,q)
    def test_missing_manifest_cannot_pass(self):self.bad(lambda p:p['metadata'].pop(KEY),'MANIFEST_REQUIRED')
    def test_empty_manifest_cannot_pass(self):self.bad(lambda p:p['metadata'][KEY].update(assets=[]),'ASSET_COUNT')
    def test_unknown_fields_cannot_hide(self):self.bad(lambda p:p['metadata'][KEY].update(unknown=1),'VERSION_OR_FIELDS')
    def test_wrong_schema_cannot_pass(self):self.bad(lambda p:p['metadata'][KEY].update(schema_version='v99'),'VERSION_OR_FIELDS')
    def test_duplicate_asset_cannot_pass(self):self.bad(lambda p:p['metadata'][KEY]['assets'].append(deepcopy(asset(p))),'DUPLICATE')
    def test_forged_path_cannot_pass(self):self.bad(lambda p:asset(p).update(public_path='../escape.png'),'CONTENT_PATH')
    def test_unresolved_element_cannot_pass(self):self.bad(lambda p:p['elements'][0]['props'].update(asset_ref='missing'),'UNRESOLVED')
    def test_source_reference_is_bound(self):self.bad(lambda p:asset(p).update(source_refs=['forged']),'PROVENANCE_UNBOUND')
    def test_reasoning_reference_is_bound(self):self.bad(lambda p:asset(p).update(reasoning_refs=['forged']),'PROVENANCE_UNBOUND')
    def test_rights_reference_is_bound(self):self.bad(lambda p:asset(p).update(rights_ref='forged'),'RIGHTS_REFERENCE')
    def test_mime_is_not_arbitrary(self):self.bad(lambda p:asset(p).update(media_type='image/svg+xml'),'TYPE_UNSUPPORTED')
    def test_unknown_descriptor_field_rejected(self):self.bad(lambda p:asset(p).update(extra=True),'DESCRIPTOR_FIELDS')
    def test_false_byte_length_rejected(self):self.bad(lambda p:asset(p).update(byte_length=True),'BYTE_BUDGET')
    def test_pixel_budget(self):self.bad(lambda p:asset(p)['media'].update(width=10000,height=10000),'PIXEL_BUDGET')
    def test_unused_assets_rejected(self):self.bad(lambda p:p.update(elements=[]),'UNUSED_ASSET')
    def test_digest_changes_with_source_identity(self):
        p=scene();a=plan_visual_assets(p)['plan_sha256'];asset(p)['rights_ref']='rights:new';p['elements'][0]['props']['rights_ref']='rights:new';self.assertNotEqual(a,plan_visual_assets(p)['plan_sha256'])
    def test_path_must_match_descriptor(self):self.bad(lambda p:p['elements'][0]['props'].update(resolved_asset_path='other.png'),'RESOLVED_PATH')
    def test_no_media_scene_requires_no_assets(self):
        p=scene();p['metadata'].pop(KEY);p['elements']=[];self.assertIsNone(plan_visual_assets(p));self.assertEqual(verified_visual_bytes(p,None)[0],{})

class ActualVisualBytes(unittest.TestCase):
    def test_actual_png_decodes_in_kernel_worker(self):
        p=scene();info,proof=inspect_visual_bytes(path(p).read_bytes(),'image/png');self.assertEqual(info,asset(p)['media']);self.assertTrue(proof['kernel_isolated']);self.assertFalse(proof['accepted'])
    def test_actual_video_timestamps_checked(self):
        p=scene('trim-video');info,proof=inspect_visual_bytes(path(p).read_bytes(),'video/mp4');self.assertEqual(info,asset(p)['media']);self.assertTrue(proof['kernel_isolated'])
    def test_real_verification_preserves_bytes(self):
        p=scene();data,r=verified_visual_bytes(p,ASSET_ROOT);self.assertEqual(data[asset(p)['public_path']],path(p).read_bytes());self.assertFalse(r['accepted'])
    def test_missing_root_rejected(self):self.assertRaisesRegex(ValueError,'ROOT_REQUIRED',verified_visual_bytes,scene(),None)
    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as td:self.assertRaisesRegex(ValueError,'UNAVAILABLE',verified_visual_bytes,scene(),Path(td))
    def test_changed_bytes_rejected(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            f=copy_assets(Path(td),p);f.write_bytes(f.read_bytes()[:-1]+b'x');self.assertRaisesRegex(ValueError,'HASH_MISMATCH',verified_visual_bytes,p,Path(td))
    def test_forged_dimensions_rejected_by_decoder(self):
        p=scene();asset(p)['media']['width']+=1;self.assertRaisesRegex(ValueError,'METADATA_MISMATCH',verified_visual_bytes,p,ASSET_ROOT)
    def test_symlink_file_rejected(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/asset(p)['public_path'];f.parent.mkdir();f.symlink_to(path(p));self.assertRaisesRegex(ValueError,'UNAVAILABLE',verified_visual_bytes,p,Path(td))
    def test_symlink_asset_directory_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'assets').symlink_to(ASSET_ROOT/'assets',target_is_directory=True);self.assertRaisesRegex(ValueError,'UNAVAILABLE',verified_visual_bytes,scene(),Path(td))
    def test_nonregular_file_rejected_without_hanging(self):
        p=scene()
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/asset(p)['public_path'];f.parent.mkdir();os.mkfifo(f);self.assertRaisesRegex(ValueError,'TYPE_OR_SIZE',verified_visual_bytes,p,Path(td))
    def test_mime_does_not_override_image_bytes(self):self.assertRaisesRegex(ValueError,'MIME_BYTES_MISMATCH',inspect_visual_bytes,path(scene()).read_bytes(),'image/jpeg')
    def test_corrupt_image_rejected(self):self.assertRaisesRegex(ValueError,'DECODE_BLOCKED',inspect_visual_bytes,b'not an image','image/png')
    def test_bad_movie_rejected(self):self.assertRaisesRegex(ValueError,'DECODE_BLOCKED',inspect_visual_bytes,b'not a movie','video/mp4')
    def test_original_asset_bundler_adopted_with_real_bytes(self):
        p=scene();p['metadata'].pop(KEY);p['elements'][0]['props'].pop('resolved_asset_path');a=asset(scene())
        with tempfile.TemporaryDirectory() as td:
            receipt=bundle_assets([CompilerAssetRecord('image',str(path(scene())),a['sha256'],'image/png',a['rights_ref'])],td)
            bound,proof=bind_visual_bundle(p,receipt,Path(td)/'public');self.assertEqual(p['metadata'].get(KEY),None)
            data,_=verified_visual_bytes(bound,Path(td)/'public');self.assertEqual(next(iter(data.values())),path(scene()).read_bytes());self.assertFalse(proof['accepted'])
    def test_bundle_pass_flag_does_not_override_actual_bytes(self):
        p=scene();p['metadata'].pop(KEY);p['elements'][0]['props'].pop('resolved_asset_path');a=asset(scene())
        with tempfile.TemporaryDirectory() as td:
            receipt=bundle_assets([CompilerAssetRecord('image',str(path(scene())),a['sha256'],'image/png',a['rights_ref'])],td)
            f=Path(td)/'public'/receipt.bundled[0].public_path;f.write_bytes(b'forged');self.assertRaisesRegex(ValueError,'HASH_MISMATCH',bind_visual_bundle,p,receipt,Path(td)/'public')

class AdditionalActualRasterFormats(unittest.TestCase):
    def raster(self, fmt, **kwargs):
        import io
        from PIL import Image
        b=io.BytesIO();Image.new('RGB',(12,8),(64,128,192)).save(b,format=fmt,**kwargs);return b.getvalue()
    def test_actual_jpeg_decoder(self):
        info,_=inspect_visual_bytes(self.raster('JPEG'),'image/jpeg');self.assertEqual(info,{'kind':'image','width':12,'height':8,'frame_count':1,'format':'jpeg'})
    def test_actual_webp_decoder(self):
        info,_=inspect_visual_bytes(self.raster('WEBP'),'image/webp');self.assertEqual(info,{'kind':'image','width':12,'height':8,'frame_count':1,'format':'webp'})
    def test_exif_rotation_is_not_silently_reinterpreted(self):
        from PIL import Image
        exif=Image.Exif();exif[274]=6
        self.assertRaisesRegex(ValueError,'DECODE_BLOCKED',inspect_visual_bytes,self.raster('JPEG',exif=exif),'image/jpeg')
    def test_animated_webp_is_not_silently_frozen(self):
        import io
        from PIL import Image
        b=io.BytesIO();Image.new('RGB',(12,8),'red').save(b,format='WEBP',save_all=True,append_images=[Image.new('RGB',(12,8),'blue')],duration=100,loop=0)
        self.assertRaisesRegex(ValueError,'DECODE_BLOCKED',inspect_visual_bytes,b.getvalue(),'image/webp')
