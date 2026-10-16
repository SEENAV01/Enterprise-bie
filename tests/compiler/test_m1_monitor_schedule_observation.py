"""Synthetic timing/privacy contracts; not Linux/renderer performance evidence."""
from contextlib import contextmanager
import gc
import json
from pathlib import Path
import sys
from types import FunctionType
import unittest
from unittest.mock import patch
import weakref
from tests.compiler import m1_monitor_schedule_observation as d

class SchedulingContracts(unittest.TestCase):
    def active(self):
        result=d.Observer();result.activate();return result
    def fixture(self,callback):
        namespace={'callback':callback}
        exec('class Group:\n    def freeze(self,value): return callback(self,value)\n'
            'def monitor(group,value): return group.freeze(value)\n',namespace)
        cls=namespace['Group'];fn=namespace['monitor']
        return cls,fn,(sys.modules[__name__],cls,cls.freeze,((fn.__code__,namespace,'MONITOR'),))
    @contextmanager
    def scope(self,callback):
        cls,fn,binding=self.fixture(callback)
        with patch.object(d,'binding',return_value=binding),patch.object(d,'cpu_scalars',return_value={'usage_usec':0,'user_usec':0,'system_usec':0}):
            with d.observe_monitor_schedule() as observer:yield cls,fn,observer
    def test_exactly_once_arguments_return_identity_and_binding_restore(self):
        token=object();calls=[]
        def native(*args,**kwargs):calls.append((args,kwargs));return token
        with self.scope(native) as (cls,fn,observer):
            group=cls();self.assertIs(fn(group,True),token);self.assertIs(fn(group,False),token)
        self.assertEqual(calls,[((group,True),{}),((group,False),{})])
        self.assertTrue(observer.snapshot()['binding_restored'])
        self.assertTrue(d.is_safe(observer.snapshot()))
    def test_exact_original_error_and_native_finally_preserved(self):
        error=PermissionError('PRIVATE_TOKEN');steps=[]
        def native(*args):
            try:steps.append('call');raise error
            finally:steps.append('cleanup')
        with self.assertRaises(PermissionError) as caught:
            with self.scope(native) as (cls,fn,observer):fn(cls(),True)
        self.assertIs(caught.exception,error);self.assertEqual(steps,['call','cleanup'])
        self.assertTrue(observer.snapshot()['binding_restored'])
        self.assertNotIn('PRIVATE_TOKEN',json.dumps(observer.snapshot()))
    def test_foreign_namespace_same_code_does_not_gain_origin(self):
        calls=[]
        with self.scope(lambda *a:calls.append(1)) as (cls,fn,observer):
            foreign=FunctionType(fn.__code__,{},fn.__name__)
            foreign(cls(),True)
        self.assertEqual(calls,[1]);self.assertEqual(observer.snapshot()['scopes']['MONITOR']['acquisitions'],0)
    def test_sanitizer_failure_does_not_mask_native_return(self):
        token=object()
        with self.scope(lambda *a:token) as (cls,fn,observer),patch.object(observer,'start',side_effect=RuntimeError('PRIVATE')):
            self.assertIs(fn(cls(),True),token)
        self.assertEqual(observer.snapshot()['availability'],'INVALID')
    def test_sanitizer_failure_does_not_mask_original_exception(self):
        error=ValueError('PRIVATE')
        def native(*args):raise error
        with self.assertRaises(ValueError) as caught:
            with self.scope(native) as (cls,fn,observer),patch.object(observer,'finish',side_effect=KeyboardInterrupt()):fn(cls(),True)
        self.assertIs(caught.exception,error)
    def test_cleanup_bookkeeping_fault_cannot_mask_body_error(self):
        original=PermissionError('PRIVATE')
        with self.assertRaises(PermissionError) as caught:
            with self.scope(lambda *a:None) as (cls,fn,observer):
                observer.pending=None;raise original
        self.assertIs(caught.exception,original)
    def test_foreign_binding_replacement_is_not_overwritten(self):
        foreign=lambda *a:None
        with self.scope(lambda *a:None) as (cls,fn,observer):cls.freeze=foreign
        self.assertIs(cls.freeze,foreign);self.assertEqual(observer.snapshot()['reason'],'RESTORATION_CHANGED')
    def test_source_setup_rejection_leaves_binding_and_execution_alone(self):
        error=PermissionError('PRIVATE')
        with patch.object(d,'binding',side_effect=error):
            with d.observe_monitor_schedule() as observer:self.assertEqual(7,7)
        self.assertEqual(observer.snapshot()['availability'],'UNAVAILABLE')
    def test_no_private_group_argument_or_result_retained(self):
        class Private:
            def __str__(self):raise AssertionError('PRIVATE')
            def __repr__(self):raise AssertionError('PRIVATE')
        token=Private();ref=weakref.ref(token)
        with self.scope(lambda *a:token) as (cls,fn,observer):
            group=cls();group.private=token;refgroup=weakref.ref(group);fn(group,True);fn(group,False)
        del token,group;gc.collect()
        self.assertIsNone(refgroup());self.assertIsNone(ref())
        self.assertEqual(observer.pending,{})
    def test_held_lower_bound_and_scope_upper_are_measured_separately(self):
        o=self.active();o.start(1,'MONITOR',True,100,10);o.finish(1,'MONITOR',True,100,120,10,15,True)
        o.start(1,'MONITOR',False,200,35);o.finish(1,'MONITOR',False,200,220,35,40,True)
        row=o.snapshot()['scopes']['MONITOR']
        self.assertEqual(row['held_lower_bound_ns'],80);self.assertEqual(row['scope_upper_bound_ns'],120)
        self.assertEqual(row['scope_parent_cpu_ns'],30);self.assertEqual(row['freeze_calls_parent_cpu_ns'],10)
    def test_partial_acquisition_does_not_invent_confirmed_hold(self):
        o=self.active();o.start(1,'MONITOR',True,100,10);o.finish(1,'MONITOR',True,100,120,10,15,False)
        o.start(1,'MONITOR',False,200,35);o.finish(1,'MONITOR',False,200,220,35,40,True)
        row=o.snapshot()['scopes']['MONITOR'];self.assertEqual(row['held_lower_bound_ns'],0)
        self.assertEqual(row['partial_acquisition_failures'],1)
    def test_thawed_gap_uses_thaw_completion_not_request(self):
        o=self.active();o.start(1,'MONITOR',True,100,10);o.finish(1,'MONITOR',True,100,120,10,15,True)
        o.start(1,'MONITOR',False,200,35);o.finish(1,'MONITOR',False,200,220,35,40,True)
        o.start(1,'MONITOR',True,260,50)
        self.assertEqual(o.snapshot()['scopes']['MONITOR']['thawed_gap_ns'],40)
    def test_intervening_entry_grant_is_not_counted_as_thawed_monitor_gap(self):
        o=self.active()
        for kind,start,acquired,request,end in (('MONITOR',0,1,9,10),('ENTRY_GRANT',20,30,90,100),('MONITOR',110,111,119,120)):
            o.start(1,kind,True,start,start);o.finish(1,kind,True,start,acquired,start,acquired,True)
            o.start(1,kind,False,request,request);o.finish(1,kind,False,request,end,request,end,True)
        rows=o.snapshot()['scopes']
        self.assertEqual(rows['ENTRY_GRANT']['held_lower_bound_ns'],60)
        self.assertEqual(rows['MONITOR']['thawed_gap_ns'],10)
        self.assertEqual(rows['ENTRY_GRANT']['thawed_gap_ns'],10)
    def test_counterfeit_clock_cannot_install_valid_observer(self):
        from bie.compiler import chromium_resource_worker as worker
        original=worker.OwnedMemoryGroup.freeze
        with patch.object(d.time,'monotonic_ns',lambda:7),d.observe_monitor_schedule() as observer:
            self.assertIs(worker.OwnedMemoryGroup.freeze,original)
        self.assertEqual(observer.snapshot()['availability'],'UNAVAILABLE')
    def test_other_thread_delegate_remains_unchanged_without_mixed_thread_cpu(self):
        import threading
        calls=[]
        with self.scope(lambda *a:calls.append(1)) as (cls,fn,observer):
            thread=threading.Thread(target=lambda:fn(cls(),True));thread.start();thread.join()
        self.assertEqual(calls,[1]);self.assertEqual(observer.snapshot()['scopes']['MONITOR']['acquisitions'],0)
    def test_counterfeit_thread_identity_cannot_install_observer(self):
        from bie.compiler import chromium_resource_worker as worker
        original=worker.OwnedMemoryGroup.freeze
        with patch.object(d.threading,'get_ident',lambda:1),d.observe_monitor_schedule() as observer:
            self.assertIs(worker.OwnedMemoryGroup.freeze,original)
        self.assertEqual(observer.snapshot()['availability'],'UNAVAILABLE')
    def test_unbalanced_scope_is_unknown_not_zero_hold_at_context_end(self):
        with self.scope(lambda *a:None) as (cls,fn,observer):fn(cls(),True)
        safe=observer.snapshot();self.assertEqual(safe['availability'],'INVALID')
        self.assertEqual(safe['scopes']['MONITOR']['held_lower_bound_ns'],'UNKNOWN')
    def test_failed_thaw_cannot_mint_completed_scope_or_upper_bound(self):
        o=self.active();o.start(1,'MONITOR',True,100,10);o.finish(1,'MONITOR',True,100,120,10,15,True)
        o.start(1,'MONITOR',False,200,35);o.finish(1,'MONITOR',False,200,220,35,40,False)
        safe=o.snapshot();self.assertEqual(safe['availability'],'INVALID')
        self.assertEqual(safe['reason'],'UNCONFIRMED_THAW')
        self.assertEqual(safe['scopes']['MONITOR']['scope_upper_bound_ns'],'UNKNOWN')
    def test_native_thaw_error_identity_survives_observer_invalidation(self):
        original=PermissionError('PRIVATE_THAW')
        def native(group,value):
            if value is False:raise original
        with self.assertRaises(PermissionError) as caught:
            with self.scope(native) as (cls,fn,observer):
                group=cls();fn(group,True);fn(group,False)
        self.assertIs(caught.exception,original)
        self.assertEqual(observer.snapshot()['reason'],'UNCONFIRMED_THAW')
    def test_new_inventory_owned_once_with_no_native_extra_or_safety_overlap(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();own='tests/compiler/test_m1_monitor_schedule_observation.py'
        self.assertEqual(lanes['new'].count(own),1)
        self.assertNotIn(own,set(lanes['native-extra'])|set(lanes['safety'])|inherited)
        self.assertEqual(len(lanes['native-extra']),214)
    def test_captured_native_clocks_survive_later_module_rebinding(self):
        wall,cpu=d.native_clocks()
        with patch.object(d.time,'monotonic_ns',lambda:True),patch.object(d.time,'thread_time_ns',lambda:True):
            self.assertIs(type(wall()),int);self.assertIs(type(cpu()),int)
    def test_cpu_unknown_is_not_zero_or_workload_success(self):
        o=self.active();safe=o.snapshot();self.assertEqual(safe['cpu_delta']['usage_usec'],'UNKNOWN')
        self.assertFalse(safe['render_passed']);safe['cpu_delta']['usage_usec']=0;self.assertFalse(d.is_safe(safe))
    def test_missing_optional_cpu_counters_remain_unknown(self):
        o=self.active();native=object();group=object()
        with patch.object(d,'cpu_scalars',side_effect=[{'usage_usec':10,'user_usec':8,'system_usec':2},{'usage_usec':15,'user_usec':12,'system_usec':3}]):
            o.sample_cpu(native,group,1);o.sample_cpu(native,group,1,True)
        self.assertEqual(o.snapshot()['cpu_delta']['usage_usec'],5)
        self.assertEqual(o.snapshot()['cpu_delta']['nr_throttled'],'UNKNOWN')
    def test_negative_cpu_delta_invalidates_cpu_only(self):
        o=self.active()
        with patch.object(d,'cpu_scalars',side_effect=[{'usage_usec':10},{'usage_usec':2}]):
            o.sample_cpu(None,None,1);o.sample_cpu(None,None,1,True)
        safe=o.snapshot();self.assertEqual(safe['cpu_availability'],'INVALID');self.assertEqual(safe['availability'],'VALID')
    def test_cpu_reader_rejection_never_exports_private_exception(self):
        o=self.active()
        with patch.object(d,'cpu_scalars',side_effect=PermissionError('PRIVATE_TOKEN /secret')):o.sample_cpu(None,None,1)
        self.assertNotIn('PRIVATE_TOKEN',json.dumps(o.snapshot()))
        self.assertEqual(o.snapshot()['cpu_availability'],'INVALID')
    def test_closed_schema_rejects_extra_private_surfaces(self):
        for field in ('stderr','argv','pid','path','maps','grants','exception'):
            row=self.active().snapshot();row[field]='PRIVATE';self.assertFalse(d.is_safe(row))
    def test_boolean_negative_nonfinite_and_overflow_counters_reject(self):
        for value in (True,-1,10**15,1.0,float('nan')):
            row=self.active().snapshot();row['scopes']['MONITOR']['acquisitions']=value;self.assertFalse(d.is_safe(row))
    def test_incomplete_and_unknown_scope_shapes_reject(self):
        row=self.active().snapshot();del row['scopes']['ENTRY_GRANT'];self.assertFalse(d.is_safe(row))
        row=self.active().snapshot();row['scopes']['FOREIGN']={};self.assertFalse(d.is_safe(row))
    def test_fabricated_privacy_reason_cannot_escape_closed_projection(self):
        self.assertNotIn('PRIVATE',json.dumps(d.empty('PRIVATE')))
    def test_unsupported_clock_range_does_not_become_valid_timing(self):
        o=self.active()
        for wall,cpu in ((True,1),(-1,0),(0,-1),(1.0,1)):
            with self.assertRaises(ValueError):o.start(1,'MONITOR',True,wall,cpu)
    def test_source_pin_and_actual_canonical_callers(self):
        worker,cls,freeze,targets=d.binding()
        self.assertIs(cls.freeze,freeze);self.assertEqual({row[2] for row in targets},set(d.SCOPES))
    def test_replaced_native_freeze_binding_cannot_gain_observer_admission(self):
        from bie.compiler import chromium_resource_worker as worker
        with patch.object(worker.OwnedMemoryGroup,'freeze',lambda *a:None),self.assertRaises(ValueError):d.binding()
    def test_source_hash_tamper_does_not_install_wrapper(self):
        from bie.compiler import chromium_resource_worker as worker
        original=worker.OwnedMemoryGroup.freeze
        with patch.object(d,'SOURCE_SHA','0'*64),d.observe_monitor_schedule() as observer:self.assertIs(worker.OwnedMemoryGroup.freeze,original)
        self.assertEqual(observer.snapshot()['availability'],'UNAVAILABLE')

class CpuReaderContracts(unittest.TestCase):
    @contextmanager
    def reader(self,raw=b'usage_usec 10\nuser_usec 8\nsystem_usec 2\n',inode=7):
        from contextlib import ExitStack
        from types import SimpleNamespace
        import stat
        from unittest.mock import Mock
        group=SimpleNamespace(path=Path('/sys/fs/cgroup/bie-chromium-owned-synthetic'),inode=inode)
        worker=SimpleNamespace(CGROOT=Path('/sys/fs/cgroup'))
        stream=Mock();stream.read.return_value=raw
        with ExitStack() as stack:
            stack.enter_context(patch.object(Path,'is_symlink',return_value=False))
            for name in ('O_DIRECTORY','O_NOFOLLOW','O_CLOEXEC'):stack.enter_context(patch.object(d.os,name,0,create=True))
            opened=stack.enter_context(patch.object(d.os,'open',side_effect=[8,9]))
            stack.enter_context(patch.object(d.os,'fstat',side_effect=[SimpleNamespace(st_ino=7),SimpleNamespace(st_mode=stat.S_IFREG)]))
            converted=stack.enter_context(patch.object(d.os,'fdopen',return_value=stream))
            closed=stack.enter_context(patch.object(d.os,'close'))
            yield worker,group,stream,opened,converted,closed
    def test_exact_cpu_stat_and_bounded_read_with_transfer_close(self):
        with self.reader() as (worker,group,stream,opened,converted,closed):
            self.assertEqual(d.cpu_scalars(worker,group),dict(usage_usec=10,user_usec=8,system_usec=2))
            self.assertEqual(opened.call_args_list[1].args[0],'cpu.stat')
            stream.read.assert_called_once_with(4097);stream.close.assert_called_once();closed.assert_called_once_with(8)
    def test_fdopen_failure_attempts_all_closes_even_when_first_close_fails(self):
        from unittest.mock import call
        original=PermissionError('PRIVATE_FDOPEN')
        with self.reader() as (worker,group,stream,opened,converted,closed):
            converted.side_effect=original;closed.side_effect=[OSError('PRIVATE_CLOSE'),None]
            with self.assertRaises(PermissionError) as caught:d.cpu_scalars(worker,group)
            self.assertIs(caught.exception,original);self.assertEqual(closed.call_args_list,[call(9),call(8)])
    def test_read_rejection_survives_stream_and_directory_close_failures(self):
        original=PermissionError('PRIVATE_READ')
        with self.reader() as (worker,group,stream,opened,converted,closed):
            stream.read.side_effect=original;stream.close.side_effect=OSError('PRIVATE_CLOSE');closed.side_effect=OSError('PRIVATE_DIRECTORY')
            with self.assertRaises(PermissionError) as caught:d.cpu_scalars(worker,group)
            self.assertIs(caught.exception,original);stream.close.assert_called_once();closed.assert_called_once_with(8)
    def test_close_failure_cannot_mint_successful_cpu_sample(self):
        with self.reader() as (worker,group,stream,opened,converted,closed):
            stream.close.side_effect=OSError('PRIVATE_CLOSE')
            with self.assertRaises(OSError):d.cpu_scalars(worker,group)
            closed.assert_called_once_with(8)
    def test_foreign_leaf_inode_rejected_before_cpu_file_open(self):
        with self.reader(inode=8) as (worker,group,stream,opened,converted,closed):
            with self.assertRaises(ValueError):d.cpu_scalars(worker,group)
            self.assertEqual(opened.call_count,1);closed.assert_called_once_with(8)
    def test_boolean_inode_and_foreign_paths_reject_before_open(self):
        for bad in (True,0):
            with self.reader(inode=bad) as (worker,group,stream,opened,converted,closed):
                with self.assertRaises(ValueError):d.cpu_scalars(worker,group)
                opened.assert_not_called()
        with self.reader() as (worker,group,stream,opened,converted,closed):
            group.path=Path('/private/user-data')
            with self.assertRaises(ValueError):d.cpu_scalars(worker,group)
            opened.assert_not_called()
    def test_duplicate_coerced_negative_overflow_nonfinite_counters_reject(self):
        for raw in (b'usage_usec 1\nusage_usec 2\n',b'usage_usec True\n',b'usage_usec -1\n',b'usage_usec 1000000000001\n',b'usage_usec nan\n',b'usage_usec 1 extra\n'):
            with self.reader(raw) as (worker,group,stream,opened,converted,closed):
                with self.assertRaises(ValueError):d.cpu_scalars(worker,group)
                stream.close.assert_called_once();closed.assert_called_once_with(8)
    def test_oversized_or_missing_kernel_counters_cannot_report_zero(self):
        for raw in (b' '*4097,b'',b'nr_throttled 0\n'):
            with self.reader(raw) as (worker,group,stream,opened,converted,closed):
                with self.assertRaises(ValueError):d.cpu_scalars(worker,group)
    def test_unknown_private_text_has_no_exported_counter_surface(self):
        raw=b'usage_usec 10\nuser_usec 8\nsystem_usec 2\nFAKE_TOKEN PRIVATE_BOOK /private/argv\n'
        with self.reader(raw) as (worker,group,stream,opened,converted,closed):
            self.assertNotIn('PRIVATE',json.dumps(d.cpu_scalars(worker,group)))

if __name__=='__main__':unittest.main()
