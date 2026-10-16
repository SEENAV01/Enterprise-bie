"""Capture/parsing conservation controls, not real-kernel/render witnesses."""
from contextlib import contextmanager
from unittest.mock import patch,Mock
import inspect
import unittest
from bie.compiler import chromium_resource_worker as worker

SMALL=b'00000000-00000100 rw-p 0 00:00 0\n'
LARGE=b'00000000-40000000 ---p 0 00:00 0 /PRIVATE_SOURCE\n'

class CaptureParseControls(unittest.TestCase):
    @contextmanager
    def cycle(self,rows=(7,8),thaw_error=None):
        state={'frozen':False,'events':[]}
        @contextmanager
        def scope(group):
            state['frozen']=True;state['events'].append('FREEZE')
            try:yield rows
            finally:
                state['frozen']=False;state['events'].append('THAW')
                if thaw_error is not None:raise thaw_error
        def capture(group,pid,browser,grants):
            self.assertTrue(state['frozen']);state['events'].append(('CAPTURE',pid))
            return (pid,pid+1,LARGE)
        with patch.object(worker,'frozen_monitor_members',scope),patch.object(worker,'capture_frozen_member',capture):
            yield state

    def test_canonical_capture_finishes_and_thaws_before_pure_processing(self):
        with self.cycle() as state:
            captured=worker.capture_monitor_cycle(None,None,[])
            self.assertFalse(state['frozen'])
            self.assertEqual([r[0] for r in captured],[7,8])
            for row in captured:self.assertEqual(worker.parse_captured_member(row),[{'bytes':1024**3,'permissions':'---p'}])
        self.assertEqual(state['events'],['FREEZE',('CAPTURE',7),('CAPTURE',8),'THAW'])

    def test_capture_phase_does_not_call_parser(self):
        with self.cycle(),patch.object(worker,'parse_captured_member',side_effect=AssertionError('PARSER_WHILE_FROZEN')):
            self.assertEqual(len(worker.capture_monitor_cycle(None,None,[])),2)

    def test_real_capture_reads_raw_maps_without_decoding(self):
        source=inspect.getsource(worker.capture_frozen_member)
        self.assertIn("_monitor_read(directory,'maps',2*1024**2)",source)
        self.assertNotIn('.decode()',source)
        self.assertNotIn('.splitlines()',source)
        self.assertIn('_monitor_identity(directory,pid)==before',source)
        self.assertIn("resource.prlimit(pid,resource.RLIMIT_AS)",source)

    def test_parser_has_no_kernel_io_grant_or_resource_mutation(self):
        with patch.object(worker.os,'open',side_effect=AssertionError('KERNEL_IO')),patch.object(worker,'_monitor_read',side_effect=AssertionError('KERNEL_IO')),patch.object(worker,'_grant',side_effect=AssertionError('GRANT')):
            self.assertEqual(worker.parse_captured_member((7,1,LARGE))[0]['bytes'],1024**3)
        source=inspect.getsource(worker.parse_captured_member)
        self.assertNotIn('resource.prlimit',source)
        self.assertNotIn('group.members',source)

    def test_compatibility_helper_returns_original_list_or_none(self):
        for capture,expected in ((None,None),((7,1,LARGE),[{'bytes':1024**3,'permissions':'---p'}])):
            with patch.object(worker,'capture_frozen_member',return_value=capture) as delegated:
                self.assertEqual(worker.observe_frozen_member('group',7,'browser','grants'),expected)
                delegated.assert_called_once_with('group',7,'browser','grants')

    def test_compatibility_helper_preserves_original_capture_exception(self):
        original=PermissionError('PRIVATE_CAPTURE')
        with patch.object(worker,'capture_frozen_member',side_effect=original),self.assertRaises(PermissionError) as caught:
            worker.observe_frozen_member(None,7,None,[])
        self.assertIs(caught.exception,original)

    def test_permission_error_preserved_and_all_pending_discarded(self):
        original=PermissionError('PRIVATE_SECOND_ACTOR')
        with self.cycle() as state,patch.object(worker,'capture_frozen_member',side_effect=[(7,1,LARGE),original]),self.assertRaises(PermissionError) as caught:
            worker.capture_monitor_cycle(None,None,[])
        self.assertIs(caught.exception,original);self.assertFalse(state['frozen'])

    def test_failed_thaw_prevents_successful_snapshot_use(self):
        original=worker.CompilerQAError('CHROMIUM_RESOURCE_FREEZE_DEADLINE')
        with self.cycle(thaw_error=original),self.assertRaises(worker.CompilerQAError) as caught:
            worker.capture_monitor_cycle(None,None,[])
        self.assertIs(caught.exception,original)

    def test_existing_gone_actor_conditions_not_permission_denials_are_retained(self):
        for gone in (FileNotFoundError('PRIVATE'),ProcessLookupError('PRIVATE')):
            with self.cycle(),patch.object(worker,'capture_frozen_member',side_effect=[gone,(8,1,LARGE)]):
                self.assertEqual([r[0] for r in worker.capture_monitor_cycle(None,None,[])],[8])

    def test_later_permission_failure_precedes_earlier_deferred_parse_rejection(self):
        original=PermissionError('PRIVATE')
        with self.cycle(),patch.object(worker,'capture_frozen_member',side_effect=[(7,1,b'not maps'),original]),self.assertRaises(PermissionError) as caught:
            worker.capture_monitor_cycle(None,None,[])
        self.assertIs(caught.exception,original)

    def test_parse_rejection_after_thaw_still_rejects(self):
        with self.cycle(rows=(7,)) as state,patch.object(worker,'capture_frozen_member',return_value=(7,1,b'not maps')):
            captured=worker.capture_monitor_cycle(None,None,[])
            self.assertFalse(state['frozen'])
            with self.assertRaises(ValueError):worker.parse_captured_member(captured[0])

    def test_complete_bytes_utf8_range_permissions_and_threshold_conserved(self):
        raw=SMALL+LARGE+b'40000000-c0000000 r--p 0 00:00 0\n'
        self.assertEqual(worker.parse_captured_member((7,1,raw)),[{'bytes':1024**3,'permissions':'---p'},{'bytes':2*1024**3,'permissions':'r--p'}])
        self.assertEqual(worker.parse_captured_member((7,1,SMALL)),[])

    def test_invalid_utf8_is_not_replaced_or_ignored(self):
        with self.assertRaises(UnicodeDecodeError):worker.parse_captured_member((7,1,b'\xff'))

    def test_invalid_ranges_columns_and_hex_fail_closed(self):
        for raw in (b'100-000 rw-p\n',b'0-10000000000000000 rw-p\n',b'GG-HH rw-p\n',b'0-40000000\n'):
            with self.assertRaises((ValueError,IndexError,worker.CompilerQAError)):worker.parse_captured_member((7,1,raw))

    def test_capture_shape_boolean_coercion_and_byte_bounds_rejected(self):
        for row in ([7,1,LARGE],(True,1,LARGE),(7,True,LARGE),(0,1,LARGE),(7,0,LARGE),(7,1,'PRIVATE'),(7,1,b' '* (2*1024**2+1))):
            with self.assertRaises(worker.CompilerQAError):worker.parse_captured_member(row)

    def test_all_128_members_preserved_without_sampling(self):
        with self.cycle(rows=tuple(range(1,129))):
            result=worker.capture_monitor_cycle(None,None,[])
        self.assertEqual([r[0] for r in result],list(range(1,129)))

    def test_extra_pending_member_rejected_not_silently_truncated(self):
        with self.cycle(rows=tuple(range(1,130))),self.assertRaises(worker.CompilerQAError):
            worker.capture_monitor_cycle(None,None,[])

    def test_private_mapping_paths_not_present_in_parsed_span_fields(self):
        import json
        result=worker.parse_captured_member((7,1,LARGE))
        self.assertNotIn('PRIVATE',json.dumps(result));self.assertEqual(set(result[0]),{'bytes','permissions'})

    def test_foreign_actor_capture_cannot_be_joined_to_queried_actor(self):
        with self.cycle(rows=(7,)),patch.object(worker,'capture_frozen_member',return_value=(8,1,LARGE)),self.assertRaises(worker.CompilerQAError):
            worker.capture_monitor_cycle(None,None,[])

    def test_overlarge_single_capture_rejected_before_pending_allocation(self):
        with self.cycle(rows=(7,)),patch.object(worker,'capture_frozen_member',return_value=(7,1,b' '* (2*1024**2+1))),self.assertRaises(worker.CompilerQAError):
            worker.capture_monitor_cycle(None,None,[])

    def test_bounded_capture_bytes_conserved_exactly(self):
        with self.cycle(rows=(7,)),patch.object(worker,'capture_frozen_member',return_value=(7,1,LARGE)):
            captured=worker.capture_monitor_cycle(None,None,[])
        self.assertIs(captured[0][2],LARGE)

    def test_ungranted_context_retains_no_maps_or_fabricated_spans(self):
        with self.cycle(rows=(7,)),patch.object(worker,'capture_frozen_member',return_value=None):
            self.assertEqual(worker.capture_monitor_cycle(None,None,[]),[])

    def test_pending_bound_checked_before_return(self):
        import ast
        tree=ast.parse(inspect.getsource(worker.capture_monitor_cycle))
        self.assertIn('128*2*1024**2',inspect.getsource(worker.capture_monitor_cycle))
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='clear' for n in ast.walk(tree)))

    def test_native_runtime_consumes_capture_only_after_thaw(self):
        source=inspect.getsource(worker.run_chromium_isolated)
        self.assertLess(source.index('granted=_grant('),source.index('captured=capture_monitor_cycle('))
        self.assertLess(source.index('captured=capture_monitor_cycle('),source.index('spans=parse_captured_member(row)'))
        self.assertIn("sum(r['bytes'] for r in spans)>sum(r['bytes'] for r in old)",source)
        self.assertIn('captured.clear();row=None',source)

class ParseAmendmentControls(unittest.TestCase):
    def setUp(self):
        from pathlib import Path
        from scripts import compiler_monitor_parse_source_amendment as audit
        self.root=Path(__file__).resolve().parents[2];self.audit=audit

    def reject(self,path,change):
        regular,_=self.audit.reader()
        def read(root,relative,maximum):
            value=regular(root,relative,maximum)
            return change(value) if relative==path else value
        with self.assertRaises(ValueError):self.audit.validate(self.root,read=read)

    def test_exact_new_and_historical_seals_and_preimages_authenticate(self):
        doc=self.audit.validate(self.root)
        self.assertEqual(len(doc['replacements']),3)
        self.assertFalse(doc['resource_limits_changed']);self.assertFalse(doc['security_policy_weakened'])
        self.assertEqual(self.audit.historical_bytes(self.root,'bie/compiler/chromium_resource_worker.py'),
            (self.root/self.audit.D/'chromium_resource_worker.py.before').read_bytes())

    def test_changed_native_byte_rejected_not_current_hash_self_blessed(self):
        self.reject('bie/compiler/chromium_resource_worker.py',lambda value:value+b'\n')

    def test_audit_resolver_and_attributes_tamper_rejected(self):
        for path in ('scripts/compiler_monitor_snapshot_amendment.py','.gitattributes'):
            self.reject(path,lambda value:value+b'\n')

    def test_new_manifest_and_both_original_seals_tamper_rejected(self):
        for path in (self.audit.DOCUMENT,self.audit.PREVIOUS,self.audit.M1):
            self.reject(path,lambda value:value+b'\n')

    def test_preimages_raw_bytes_and_partial_rollback_rejected(self):
        for path in ('chromium_resource_worker.py.before','compiler_monitor_snapshot_amendment.py.before','.gitattributes.before'):
            self.reject(self.audit.D+path,lambda value:value.replace(b'\n',b'\r\n'))
        prior=(self.root/self.audit.D/'chromium_resource_worker.py.before').read_bytes()
        self.reject('bie/compiler/chromium_resource_worker.py',lambda value:prior)

    def test_unknown_source_cannot_request_historical_byte_substitution(self):
        with self.assertRaises(ValueError):self.audit.historical_bytes(self.root,'bie/compiler/real_paint.py')

    def test_original_native_source_proves_parsing_was_inside_frozen_observer(self):
        import hashlib
        raw=(self.root/self.audit.D/'chromium_resource_worker.py.before').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb')
        import ast
        tree=ast.parse(raw)
        original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='observe_frozen_member')
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='decode' for n in ast.walk(original)))
        current=ast.parse(inspect.getsource(worker.capture_frozen_member))
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='decode' for n in ast.walk(current)))

    def test_new_inventory_once_and_original_native_extra_file_count(self):
        from tests.compiler.run_m1_tests import inventory
        lanes,inherited=inventory();own='tests/compiler/test_m1_monitor_parse.py'
        self.assertEqual(lanes['new'].count(own),1)
        self.assertNotIn(own,set(lanes['native-extra'])|set(lanes['safety'])|inherited)
        self.assertEqual(len(lanes['native-extra']),214)

if __name__=='__main__':unittest.main()
