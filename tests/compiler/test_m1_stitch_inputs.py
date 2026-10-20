"""Pinned final-stitch input policy controls; not native paint evidence."""
from copy import deepcopy
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.compiler.test_m1_media_threads import run_node, STITCH
from scripts import compiler_stitch_input_amendment as audit
ROOT=Path(__file__).resolve().parents[2]
from tests.source_baseline_fixture import overlay_baseline

PAIR = ['-i', 'synthetic-video.mp4', '-i', 'synthetic-normalized-audio.aac',
        '-c:a', 'copy', '-c:v', 'copy', '-map_metadata', '-1',
        '-metadata', 'comment=Made with Remotion 4.0.506', '-y', 'synthetic-final.mp4']


def invoke(args, kind='stitcher'):
    return run_node('const a=' + json.dumps(args) + ';let out;try{out={passed:true,args:api.lowerArguments(' +
                    json.dumps(kind) + ',a)}}catch(e){out={passed:false,guard:e.m1_media_guard}}console.log(JSON.stringify(out));')


def cleaned(args):
    result = []; i = 0
    while i < len(args):
        if args[i] in ('-threads', '-filter_threads', '-filter_complex_threads'): i += 2
        else: result.append(args[i]); i += 1
    return result


class StitchInputPolicy(unittest.TestCase):
    def test_pinned_preencoded_normalized_audio_pair_admitted(self):
        self.assertTrue(invoke(PAIR)['passed'])

    def test_pinned_image_sequence_normalized_audio_pair_admitted(self):
        args = ['-r', '24', '-f', 'image2', '-s', '960x640', '-start_number', '0'] + deepcopy(PAIR)
        args[args.index('-c:v') + 1] = 'libx264'
        self.assertTrue(invoke(args)['passed'])

    def test_every_original_token_in_order_and_input_unchanged(self):
        original = deepcopy(PAIR); value = invoke(PAIR)
        self.assertTrue(value['passed']); self.assertEqual(cleaned(value['args']), PAIR)
        self.assertEqual(PAIR, original)

    def test_each_input_has_decoder_bound_and_output_encoder_bound(self):
        value = invoke(PAIR); self.assertTrue(value['passed']); args = value['args']
        for i, token in enumerate(args):
            if token == '-i': self.assertEqual(args[i-2:i], ['-threads', '1'])
        self.assertEqual(args[-4:], ['-threads', '1', '-y', PAIR[-1]])

    def test_filter_bounds_remain_one(self):
        value = invoke(PAIR); self.assertTrue(value['passed'])
        self.assertEqual(value['args'][:4], ['-filter_threads', '1', '-filter_complex_threads', '1'])

    def test_single_input_legacy_governed_shape_unchanged(self):
        value = invoke(STITCH); self.assertTrue(value['passed'])
        self.assertEqual(cleaned(value['args']), STITCH)
        self.assertEqual(value['args'].count('-threads'), 2)

    def test_single_input_before_after_lowering_byte_identical(self):
        old=ROOT/audit.DIRECTORY/'bounded_media_threads.cjs.before'
        value=run_node('const old=require('+json.dumps(str(old))+');console.log(JSON.stringify(["pre-stitcher","stitcher"].every(k=>{const a=k==="stitcher"?stitch:pre;return JSON.stringify(old.lowerArguments(k,a))===JSON.stringify(api.lowerArguments(k,a))})));')
        self.assertTrue(value)

    def test_prestitcher_still_rejects_multiple_inputs(self):
        self.assertEqual(invoke(PAIR, 'pre-stitcher'), {'passed': False, 'guard': 'ARGUMENT_INPUT'})

    def test_third_input_not_generic_multi_input_support(self):
        self.assertFalse(invoke(PAIR[:4] + ['-i', 'foreign-third.aac'] + PAIR[4:])['passed'])

    def test_missing_or_extra_audio_copy_clause_rejected(self):
        for args in (PAIR[:4] + PAIR[6:], PAIR[:6] + ['-c:a', 'copy'] + PAIR[6:]):
            with self.subTest(args_count=len(args)): self.assertFalse(invoke(args)['passed'])

    def test_wrong_audio_codec_not_silently_reencoded(self):
        args = deepcopy(PAIR); args[5] = 'aac'; self.assertFalse(invoke(args)['passed'])

    def test_audio_disabled_conflicts_with_audio_input(self):
        self.assertFalse(invoke(PAIR[:6] + ['-an'] + PAIR[6:])['passed'])

    def test_empty_same_optionlike_or_pipe_operands_rejected(self):
        for position, value in ((1, ''), (3, ''), (3, PAIR[1]), (1, '-'), (3, '-'), (3, '-unapproved')):
            args = deepcopy(PAIR); args[position] = value
            with self.subTest(position=position, operand_kind='synthetic'): self.assertFalse(invoke(args)['passed'])

    def test_audio_copy_must_immediately_bind_second_input(self):
        args = PAIR[:4] + ['-metadata', 'synthetic=fixture'] + PAIR[4:]
        self.assertFalse(invoke(args)['passed'])

    def test_second_input_cannot_be_after_output_codec(self):
        args = PAIR[:2] + PAIR[6:8] + PAIR[2:6] + PAIR[8:]
        self.assertFalse(invoke(args)['passed'])

    def test_unknown_video_codec_still_rejected(self):
        args = deepcopy(PAIR); args[7] = 'vp9'; self.assertFalse(invoke(args)['passed'])

    def test_existing_decoder_encoder_filter_thread_options_rejected(self):
        for option in ('-threads', '-threads:a', '-filter_threads', '-filter_complex_threads'):
            with self.subTest(option=option): self.assertFalse(invoke([option, '2'] + PAIR)['passed'])

    def test_nonfinite_boolean_and_nonstring_not_coerced(self):
        for value in (None, True, 2):
            args = deepcopy(PAIR); args[3] = value
            with self.subTest(value=value): self.assertFalse(invoke(args)['passed'])

    def test_completion_has_no_private_operands(self):
        value = run_node('const a='+json.dumps(PAIR)+';const b=api.createOverride(p);b.override({type:"stitcher",args:a});console.log(JSON.stringify(b.completed()));')
        self.assertNotIn('synthetic-', json.dumps(value)); self.assertEqual(value['stitcher_calls'], 1)

    def test_callback_duplication_remains_fail_closed(self):
        value = run_node('const a='+json.dumps(PAIR)+';const b=api.createOverride(p);let rejected=false;try{b.override({type:"stitcher",args:a});b.override({type:"stitcher",args:a})}catch(e){rejected=true}console.log(JSON.stringify(rejected));')
        self.assertTrue(value)

    def test_new_inventory_once_no_native_safety_inherited_overlap(self):
        from tests.compiler import run_m1_tests as runner
        lanes, inherited = runner.inventory(); name = 'tests/compiler/test_m1_stitch_inputs.py'
        self.assertEqual(lanes['new'].count(name), 1); self.assertEqual(len(lanes['native-extra']), 214)
        self.assertNotIn(name, lanes['native-extra']); self.assertNotIn(name, lanes['safety']); self.assertNotIn(name, inherited)


class StitchInputAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=audit.validate(ROOT)
        tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(tmp.cleanup);cls.root=Path(tmp.name)
        for folder in ('docs/productization','scripts','bie/compiler'):
            shutil.copytree(ROOT/folder,cls.root/folder,ignore=shutil.ignore_patterns('__pycache__','*.zip'))
        (cls.root/'manifests').mkdir()
        shutil.copyfile(ROOT/'manifests/post_dir_integration_004.json',cls.root/'manifests/post_dir_integration_004.json')
        from scripts import compiler_cache_source_amendment as cache
        selected={cache.NATIVE_DOCUMENT,cache.DOCUMENT,cache.BEFORE,cache.PAINT_DOCUMENT,cache.PAINT_BEFORE,cache.RENDER_BEFORE}
        selected.update(r['path'] for r in cache.NATIVE_EXPECTED['previous_active_sources'])
        for relative in selected:
            target=cls.root/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)
        overlay_baseline(ROOT,cls.root)  # Task 037C: authenticated baseline bytes
        path=cls.root/'manifests'/cache.MANIFEST
        document=json.loads(path.read_text())
        # Prove real canonical entrypoints pass with the complete intact fixture,
        # not merely reject missing historical files during later negative tests.
        cache.resolve(cls.root,path,document)
        cache.resolve_source_members(cls.root,path,document)

    def native_cache_entrypoint(self, root):
        from scripts import compiler_cache_source_amendment as cache
        path=root/'manifests'/cache.MANIFEST
        document=json.loads(path.read_text())
        return cache.resolve(root,path,document)

    def test_complete_previous_chain_and_original_manifest_meaning(self):
        from scripts import compiler_media_source_pin_amendment as previous
        from scripts import compiler_media_policy_observation_amendment as policy
        from scripts import compiler_media_thread_amendment as threads
        from scripts import compiler_motion_source_amendment as motion
        self.assertEqual(audit.validate(self.root),self.doc)
        previous.validate(self.root);policy.validate(self.root);threads.validate(self.root);motion.validate(self.root)
        self.assertEqual(sha256((self.root/audit.M1_DOCUMENT).read_bytes()).hexdigest(),audit.M1_SHA256)

    def test_all_exact_17da_git_preimages(self):
        for row in self.doc['replacements']:
            raw=subprocess.check_output(['git','show','17da2a5a24d8dec3065bc8a292fb848e423a9bb5:'+row['path']],cwd=ROOT)
            self.assertEqual(raw,(self.root/row['preimage']).read_bytes())
            self.assertEqual(sha256(raw).hexdigest(),row['original_sha256'])

    def test_every_active_and_preimage_tamper_rejected(self):
        for row in self.doc['replacements']:
            for key in ('path','preimage'):
                path=self.root/row[key];old=path.read_bytes()
                try:
                    path.write_bytes(old+b'UNAUTHORIZED')
                    with self.assertRaises(ValueError):audit.validate(self.root)
                finally:path.write_bytes(old)

    def test_duplicate_extra_and_recomputed_self_blessing_manifest_rejected(self):
        path=self.root/audit.DOCUMENT;old=path.read_bytes()
        try:
            for kind in ('duplicate','extra','bless'):
                doc=deepcopy(self.doc)
                if kind=='bless':doc['replacements'][0]['active_sha256']='f'*64
                else:
                    row=deepcopy(doc['replacements'][0])
                    if kind=='extra':row['path']='bie/compiler/unapproved.py'
                    doc['replacements'].append(row)
                path.write_text(json.dumps(doc))
                with self.assertRaises(ValueError):audit.validate(self.root)
        finally:path.write_bytes(old)

    def test_original_and_adjacent_documents_remain_immutable(self):
        for relative in (audit.M1_DOCUMENT,audit.PREVIOUS_DOCUMENT,
                'docs/productization/task036-media-policy-observation-amendment/AMENDMENT.json'):
            path=self.root/relative;old=path.read_bytes()
            try:
                path.write_bytes(old+b' ')
                with self.assertRaises(ValueError):audit.validate(self.root)
            finally:path.write_bytes(old)

    def test_unlisted_native_controller_and_prior_preimage_rejected(self):
        prior=json.loads((self.root/audit.PREVIOUS_DOCUMENT).read_text())
        for relative in ('bie/compiler/qa_support/remotion_raster_capture.cjs',prior['replacements'][0]['preimage']):
            path=self.root/relative;old=path.read_bytes()
            try:
                path.write_bytes(old+b'UNAUTHORIZED')
                with self.assertRaises(ValueError):audit.validate(self.root)
            finally:path.write_bytes(old)

    def test_foreign_parent_or_path_cannot_unwrap(self):
        for path in ('bie/compiler/unapproved.py',audit.HELPER):
            with self.assertRaises(ValueError):audit.authenticated_previous_bytes(self.root,path,'a'*64)

    def test_coordinated_historical_rollback_rejected_by_native_audit_entrypoints(self):
        from scripts import compiler_media_source_pin_amendment as pin
        from scripts import compiler_media_policy_observation_amendment as policy
        from scripts import compiler_media_thread_amendment as threads
        from scripts import compiler_motion_source_amendment as motion
        saved={}
        try:
            for row in self.doc['replacements']:
                path=self.root/row['path'];saved[path]=path.read_bytes()
                path.write_bytes((self.root/row['preimage']).read_bytes())
            for check in (pin.validate,policy.validate,threads.validate,motion.validate,self.native_cache_entrypoint):
                with self.subTest(entrypoint=check.__module__),self.assertRaises(ValueError):check(self.root)
        finally:
            for path,raw in saved.items():path.write_bytes(raw)

    def test_missing_or_tampered_latest_cannot_hide_behind_historical_rollback(self):
        from scripts import compiler_media_source_pin_amendment as pin
        saved={};manifest=self.root/audit.DOCUMENT;original=manifest.read_bytes()
        try:
            for row in self.doc['replacements']:
                path=self.root/row['path'];saved[path]=path.read_bytes()
                path.write_bytes((self.root/row['preimage']).read_bytes())
            for kind in ('missing','tampered'):
                if kind=='missing':manifest.unlink()
                else:manifest.write_bytes(original+b'UNAUTHORIZED')
                for check in (pin.validate,self.native_cache_entrypoint):
                    with self.subTest(kind=kind,entrypoint=check.__module__),self.assertRaises((ValueError,FileNotFoundError)):
                        check(self.root)
        finally:
            manifest.write_bytes(original)
            for path,raw in saved.items():path.write_bytes(raw)

    def test_active_painter_fixed_pin_matches_and_rejects_changed_helper(self):
        from tests.compiler.test_m1_media_source_pin import execute_guard
        from bie.compiler.qa_common import CompilerQAError
        source=(self.root/'bie/compiler/real_paint.py').read_text()
        self.assertEqual(execute_guard(source,audit.HELPER_SHA256),audit.HELPER_SHA256)
        with self.assertRaisesRegex(CompilerQAError,'^M1_MEDIA_THREAD_SOURCE_IDENTITY$'):execute_guard(source,'a'*64)
        old=(self.root/audit.DIRECTORY/'real_paint.py.before').read_text()
        self.assertEqual(old.replace('af0eae48357c10fbdfbda113b945c9f443684dac593b56d2049f57502f5b6ad5',audit.HELPER_SHA256),source)

    def test_resource_security_validation_call_asts_unchanged(self):
        before=ast.parse((self.root/audit.DIRECTORY/'real_paint.py.before').read_text())
        after=ast.parse((self.root/'bie/compiler/real_paint.py').read_text())
        for name in ('run_chromium_isolated','isolated_typecheck','WorkerPolicy','inspect_owner_fit','inspect_paint_quality','inspect_counterfactual_capture'):
            def calls(tree):return [ast.dump(n,include_attributes=False) for n in ast.walk(tree)
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name]
            self.assertEqual(calls(before),calls(after),name)

    def test_policy_shape_and_completion_do_not_expand_diagnostic_surface(self):
        from tests.compiler.test_m1_media_threads import POLICY
        self.assertEqual(self.doc['runtime_policy'],{k:v for k,v in POLICY.items() if k!='admission_id'})
        source=(self.root/audit.HELPER).read_text()
        for forbidden in ('child_process','readFile','writeFile','stdout','stderr','console.','process.env'):
            self.assertNotIn(forbidden,source)


if __name__ == '__main__': unittest.main()
