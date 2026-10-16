"""Synthetic observer controls plus a real Linux whole-thread-group pidfd check.

None of these fixtures are a produced scene, browser or render witness.
"""
from contextlib import ExitStack
from copy import deepcopy
import ctypes
import gc
import json
import os
from pathlib import PosixPath, PurePosixPath
import select
import signal
import sys
import threading
import time
import unittest
from unittest.mock import patch

from tests.compiler import m1_proc_link_observation as diag
TERMINAL_SAMPLE=diag.terminal_sample
PROC_PATH=PosixPath if sys.platform=='linux' else PurePosixPath

class ProjectionControls(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(diag,'PosixPath',PROC_PATH))
        self.open=self.stack.enter_context(patch.object(diag.os,'pidfd_open',return_value=77,create=True))
        self.close=self.stack.enter_context(patch.object(diag.os,'close'))
        self.sample=self.stack.enter_context(patch.object(diag,'terminal_sample',return_value=False))
        self.observer=diag.LinkObserver()
        self.observer.safe.update(availability='VALID',reason='NONE',binding_verified=True,event_limit_reached=False)

    def rejected(self, error=None, request=(123,'EXE')):
        error=error if error is not None else PermissionError(13,'FAKE_PRIVATE_TEXT','C:/FAKE_PRIVATE_PATH')
        calls=[]
        def original(*args,**kwargs):calls.append((args,kwargs));raise error
        args=(object(),);kwargs={'dir_fd':None}
        with self.assertRaises(type(error)) as caught:self.observer.invoke(original,args,kwargs,request)
        self.assertIs(caught.exception,error);self.assertEqual(calls,[(args,kwargs)])
        return self.observer.snapshot()

    def test_live_kernel_sample_preserves_exact_exception_and_once(self):
        value=self.rejected();self.assertTrue(diag.is_safe(value))
        self.assertIs(value['events'][0]['whole_process_terminal_when_sampled'],False)
        self.open.assert_called_once_with(123,0);self.close.assert_called_once_with(77)

    def test_terminal_kernel_sample_is_not_a_render_verdict(self):
        self.sample.return_value=True;value=self.rejected()
        self.assertIs(value['events'][0]['whole_process_terminal_when_sampled'],True)
        self.assertTrue(all(value[k] is False for k in ('render_passed','accepted','product_accepted')))

    def test_errno_only_closed_codes_never_messages(self):
        for code,label in ((1,'EPERM'),(13,'EACCES'),(99,'UNKNOWN')):
            self.observer.safe['events']=[]
            self.assertEqual(self.rejected(PermissionError(code,'FAKE_PRIVATE_TEXT'))['events'][0]['errno_code'],label)

    def test_unavailable_fd_is_unknown_not_live_or_success(self):
        self.open.side_effect=PermissionError(13,'FAKE_PRIVATE_KERNEL')
        row=self.rejected()['events'][0]
        self.assertIs(row['pidfd_acquired'],False)
        self.assertEqual(row['whole_process_terminal_when_sampled'],'UNKNOWN')
        self.assertEqual(row['pidfd_closed'],'UNKNOWN');self.close.assert_not_called()

    def test_kernel_sample_exception_cannot_mask_original(self):
        self.sample.side_effect=RuntimeError('FAKE_PRIVATE_OBSERVER')
        self.assertEqual(self.rejected()['events'][0]['whole_process_terminal_when_sampled'],'UNKNOWN')

    def test_close_exception_cannot_mask_original(self):
        self.close.side_effect=RuntimeError('FAKE_PRIVATE_CLOSE')
        self.assertEqual(self.rejected()['events'][0]['pidfd_closed'],'UNKNOWN')

    def test_private_result_returned_identically_and_not_retained(self):
        class Private:
            def __str__(self):raise AssertionError('PRIVATE_STR_CALLED')
            def __repr__(self):raise AssertionError('PRIVATE_REPR_CALLED')
        private=Private();calls=[]
        def original(*a,**k):calls.append((a,k));return private
        self.assertIs(self.observer.invoke(original,(),{},(123,'ROOT')),private)
        self.assertEqual(calls,[((),{})]);self.assertEqual(self.observer.snapshot()['events'],[])
        self.assertNotIn(private,gc.get_referents(self.observer.safe));self.close.assert_called_once_with(77)

    def test_non_permission_exception_identity_and_no_projection(self):
        self.assertEqual(self.rejected(RuntimeError('FAKE_PRIVATE_TEXT'))['events'],[])

    def test_malformed_requests_delegate_without_observation(self):
        for request in (None,[123,'EXE'],(True,'EXE'),(0,'ROOT'),(2**31,'ROOT'),(123,'FAKE_PRIVATE')):
            with self.subTest(kind=type(request).__name__):
                self.assertEqual(self.rejected(request=request)['events'],[])
        self.open.assert_not_called()

    def test_oversized_private_error_fields_never_inspected_or_retained(self):
        error=PermissionError(13,'FAKE_TOKEN_PRIVATE_BOOK_'+'x'*300000,'C:/FAKE_PRIVATE_LOCATION')
        error.stdout=b'FAKE_PRIVATE_STDOUT'*300000;error.stderr=b'FAKE_PRIVATE_STDERR'*300000
        error.command=['FAKE_PRIVATE_ARGV'];error.mappings={'FAKE_PRIVATE_MAP':'FAKE_PRIVATE_GRANT'}
        value=self.rejected(error);encoded=json.dumps(value)
        self.assertLess(len(encoded),4096)
        for marker in ('FAKE_TOKEN','PRIVATE_BOOK','STDOUT','STDERR','LOCATION','ARGV','GRANT','MAP'):
            self.assertNotIn(marker,encoded)
        self.assertNotIn(error,gc.get_referents(self.observer.safe))

    def test_arbitrary_sampler_objects_become_unknown_without_retention(self):
        class Private:
            def __str__(self):raise AssertionError('PRIVATE_STR')
            def __repr__(self):raise AssertionError('PRIVATE_REPR')
        private=Private();self.sample.return_value=private
        value=self.rejected();self.assertEqual(value['events'][0]['whole_process_terminal_when_sampled'],'UNKNOWN')
        self.assertNotIn(private,gc.get_referents(self.observer.safe['events'][0]))

    def test_closed_schema_unknown_keys_types_and_promotions_rejected(self):
        value=self.rejected()
        for key,item in (('stdout','FAKE_PRIVATE'),('accepted',True),('binding_restored',1),('availability',True)):
            changed=deepcopy(value);changed[key]=item;self.assertFalse(diag.is_safe(changed))
        for key,item in (('pidfd_acquired',1),('pidfd_closed',None),('whole_process_terminal_when_sampled',0),('link_kind','FOREIGN')):
            changed=deepcopy(value);changed['events'][0][key]=item;self.assertFalse(diag.is_safe(changed))

    def test_event_budget_bound_no_private_accumulation(self):
        for _ in range(diag.MAX_EVENTS+1):self.rejected()
        value=self.observer.snapshot();self.assertEqual(len(value['events']),diag.MAX_EVENTS)
        self.assertIs(value['event_limit_reached'],True);self.assertLess(len(json.dumps(value)),8192)

    def test_snapshot_corruption_is_invalid_not_serialized(self):
        self.observer.safe['events']=[{'stderr':'FAKE_PRIVATE'}]
        value=self.observer.snapshot();self.assertTrue(diag.is_safe(value));self.assertEqual(value['availability'],'UNAVAILABLE')
        self.assertNotIn('FAKE_PRIVATE',json.dumps(value))

    def test_request_parser_fixed_proc_links_only(self):
        self.assertEqual(diag.monitor_request((PROC_PATH('/proc/123/exe'),),{}),(123,'EXE'))
        self.assertEqual(diag.monitor_request((PROC_PATH('/proc/123/root'),),{}),(123,'ROOT'))
        for path in ('/proc/0/exe','/proc/001/root','/proc/2147483648/exe','/proc/123/maps','/tmp/123/exe','/proc/１２３/exe'):
            self.assertIsNone(diag.monitor_request((PROC_PATH(path),),{}))
        self.assertIsNone(diag.monitor_request(('/proc/123/exe',),{}))
        self.assertIsNone(diag.monitor_request((PROC_PATH('/proc/123/exe'),),{'dir_fd':1}))

    def test_poll_projection_valid_live_and_terminal_states(self):
        with patch.object(diag.select,'poll',create=True) as factory,patch.object(diag.select,'POLLIN',1,create=True),patch.object(diag.select,'POLLHUP',16,create=True):
            poller=factory.return_value
            for rows,expected in (([],False),([(77,1)],True),([(77,16)],True),([(77,17)],True)):
                poller.poll.return_value=rows;self.assertIs(TERMINAL_SAMPLE(77),expected)
            poller.poll.assert_called_with(0)

    def test_poll_bad_fd_types_masks_and_multiple_rows_unknown(self):
        with patch.object(diag.select,'poll',create=True) as factory,patch.object(diag.select,'POLLIN',1,create=True),patch.object(diag.select,'POLLHUP',16,create=True):
            for rows in (None,[(78,1)],[(True,1)],[(77,True)],[(77,8)],[(77,0)],[(77,-1)],[(77,1),(77,1)],['FAKE_PRIVATE']):
                factory.return_value.poll.return_value=rows
                self.assertEqual(TERMINAL_SAMPLE(77),'UNKNOWN')

    def test_no_whole_private_serialization_in_source(self):
        import ast
        tree=ast.parse(PathSource.read_text())
        bad={'asdict','repr','str','vars'}
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in bad for n in ast.walk(tree)))

    def test_invalid_fd_boolean_negative_and_overflow_never_closed(self):
        for fd in (True,-1,2**31,'FAKE_PRIVATE',None):
            self.observer.safe['events']=[];self.open.return_value=fd
            row=self.rejected()['events'][0]
            self.assertIs(row['pidfd_acquired'],False)
            self.assertEqual(row['whole_process_terminal_when_sampled'],'UNKNOWN')
        self.close.assert_not_called()

    def test_source_pathlike_hook_is_never_invoked(self):
        class Private:
            def __fspath__(self):raise AssertionError('PRIVATE_HOOK')
            def __str__(self):raise AssertionError('PRIVATE_STR')
        self.assertIsNone(diag.monitor_request((Private(),),{}))

    def test_hostile_schema_values_do_not_execute_hooks(self):
        class Private:
            def __eq__(self,other):raise AssertionError('PRIVATE_EQ')
            def __str__(self):raise AssertionError('PRIVATE_STR')
        for field in ('availability','reason','binding_restored'):
            value=diag.empty();value[field]=Private();self.assertFalse(diag.is_safe(value))

    def test_absence_does_not_claim_zero_events_or_kernel_termination(self):
        value=diag.empty('KERNEL_API_UNAVAILABLE')
        self.assertTrue(diag.is_safe(value));self.assertFalse(value['binding_verified'])
        self.assertEqual(value['availability'],'UNAVAILABLE');self.assertEqual(value['events'],[])
        self.assertEqual(value['binding_restored'],'UNKNOWN')
        self.assertEqual(value['event_limit_reached'],'UNKNOWN')

    def test_sample_point_is_after_error_not_original_error_time(self):
        value=self.rejected()
        self.assertEqual(value['capture_point'],'AFTER_READLINK_PERMISSION_ERROR_BEFORE_ORIGINAL_RERAISE')
        self.assertIn('NOT_CGROUP_ANCESTRY_OR_FINAL_PROCESS_VERDICT',value['scope'])

    def test_unknown_kernel_mask_does_not_become_false_or_true(self):
        with patch.object(diag.select,'poll',create=True) as factory,patch.object(diag.select,'POLLIN',1,create=True),patch.object(diag.select,'POLLHUP',16,create=True):
            factory.return_value.poll.return_value=[(77,32)]
            self.assertEqual(TERMINAL_SAMPLE(77),'UNKNOWN')

PathSource=__import__('pathlib').Path(diag.__file__)

class ContextControls(unittest.TestCase):
    def context_fixture(self, original):
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(diag,'PosixPath',PROC_PATH))
        namespace={'os':os}
        exec(compile('\n'*374+'def monitor(value):\n    return os.readlink(value)\n',
            'EXPLICIT_SYNTHETIC_MONITOR_NOT_NATIVE','exec'),namespace)
        original.__module__='posix';original.__name__='readlink'
        stack.enter_context(patch.object(diag.sys,'platform','linux'))
        stack.enter_context(patch.object(diag,'BuiltinFunctionType',type(original)))
        stack.enter_context(patch.object(diag,'canonical_monitor',return_value=(namespace['monitor'].__code__,namespace)))
        stack.enter_context(patch.object(diag,'native_frame_reader',return_value=sys._getframe))
        stack.enter_context(patch.object(diag.os,'readlink',original))
        opened=stack.enter_context(patch.object(diag.os,'pidfd_open',return_value=77,create=True))
        closed=stack.enter_context(patch.object(diag.os,'close'))
        stack.enter_context(patch.object(diag.select,'poll',create=True))
        sampled=stack.enter_context(patch.object(diag,'terminal_sample',return_value=False))
        stack.enter_context(patch.object(diag,'native_kernel_bindings',return_value=
            (opened,closed,diag.select.poll,1,16,sampled)))
        return namespace['monitor'],opened,closed

    def test_actual_context_delegates_once_return_identity_and_restores(self):
        private=object();calls=[]
        def original(*a,**k):calls.append((a,k));return private
        monitor,opened,closed=self.context_fixture(original);path=PROC_PATH('/proc/123/exe')
        with diag.observe_proc_links() as observer:self.assertIs(monitor(path),private)
        self.assertEqual(calls,[((path,),{})]);opened.assert_called_once_with(123,0);closed.assert_called_once_with(77)
        self.assertIs(os.readlink,original);self.assertIs(observer.snapshot()['binding_restored'],True)
        self.assertEqual(observer.snapshot()['events'],[])

    def test_actual_context_preserves_exception_identity_and_restores(self):
        private=PermissionError(13,'FAKE_PRIVATE_BODY');calls=[]
        def original(*a,**k):calls.append((a,k));raise private
        monitor,opened,closed=self.context_fixture(original);path=PROC_PATH('/proc/123/root')
        with self.assertRaises(PermissionError) as caught:
            with diag.observe_proc_links() as observer:monitor(path)
        self.assertIs(caught.exception,private);self.assertEqual(calls,[((path,),{})])
        self.assertIs(os.readlink,original);self.assertIs(observer.snapshot()['binding_restored'],True)
        self.assertEqual(observer.snapshot()['events'][0]['link_kind'],'ROOT')

    def test_foreign_caller_does_not_open_pidfd_or_claim_observation(self):
        token=object()
        def original(*a,**k):return token
        _,opened,closed=self.context_fixture(original)
        with diag.observe_proc_links() as observer:self.assertIs(os.readlink(PROC_PATH('/proc/123/exe')),token)
        opened.assert_not_called();closed.assert_not_called();self.assertEqual(observer.snapshot()['events'],[])

    def test_same_code_foreign_namespace_cannot_claim_monitor_provenance(self):
        from types import FunctionType
        token=object()
        def original(*a,**k):return token
        monitor,opened,closed=self.context_fixture(original)
        foreign=FunctionType(monitor.__code__,{'os':os},monitor.__name__)
        with diag.observe_proc_links() as observer:
            self.assertIs(foreign(PROC_PATH('/proc/123/exe')),token)
        opened.assert_not_called();closed.assert_not_called()
        self.assertEqual(observer.snapshot()['events'],[])

    def test_captured_apis_not_replaced_by_late_mutation(self):
        private=PermissionError(13,'FAKE_PRIVATE')
        def original(*a,**k):raise private
        monitor,opened,closed=self.context_fixture(original)
        with self.assertRaises(PermissionError) as caught:
            with diag.observe_proc_links() as observer:
                with (patch.object(diag.os,'pidfd_open',side_effect=AssertionError('LATE_OPEN')),
                        patch.object(diag.os,'close',side_effect=AssertionError('LATE_CLOSE')),
                        patch.object(diag.select,'poll',side_effect=AssertionError('LATE_POLL'))):
                    monitor(PROC_PATH('/proc/123/exe'))
        self.assertIs(caught.exception,private)
        opened.assert_called_once_with(123,0);closed.assert_called_once_with(77)
        self.assertIs(observer.snapshot()['events'][0]['whole_process_terminal_when_sampled'],False)

    def test_replaced_native_api_declines_observation_without_altering_body(self):
        def original(*a,**k):return object()
        self.context_fixture(original)
        with patch.object(diag,'native_kernel_bindings',side_effect=ValueError('KERNEL_API')):
            with diag.observe_proc_links() as observer:self.assertIs(os.readlink,original)
        value=observer.snapshot()
        self.assertEqual(value['reason'],'KERNEL_API_UNAVAILABLE')
        self.assertFalse(value['binding_verified']);self.assertEqual(value['events'],[])

    def test_nonatomic_association_is_not_denied_process_identity_proof(self):
        value=diag.empty()
        self.assertIn('NONATOMIC_PIDFD_PATH_ASSOCIATION',value['scope'])
        self.assertIn('NOT_CGROUP_ANCESTRY_OR_FINAL_PROCESS_VERDICT',value['scope'])

    def test_captured_frame_reader_survives_late_rebinding(self):
        token=object()
        def original(*a,**k):return token
        monitor,opened,closed=self.context_fixture(original)
        with diag.observe_proc_links() as observer:
            with patch.object(diag.sys,'_getframe',side_effect=AssertionError('LATE_FRAME')):
                self.assertIs(monitor(PROC_PATH('/proc/123/exe')),token)
        opened.assert_called_once_with(123,0);closed.assert_called_once_with(77)
        self.assertIs(observer.snapshot()['binding_restored'],True)

    def test_counterfeit_frame_like_object_is_not_callsite_authority(self):
        token=object()
        def original(*a,**k):return token
        monitor,opened,closed=self.context_fixture(original)
        class Counterfeit:
            @property
            def f_code(self):raise AssertionError('FAKE_FRAME_CONTENT_READ')
        with patch.object(diag,'native_frame_reader',return_value=lambda depth:Counterfeit()):
            with diag.observe_proc_links() as observer:
                self.assertIs(monitor(PROC_PATH('/proc/123/exe')),token)
        opened.assert_not_called();closed.assert_not_called()
        self.assertEqual(observer.snapshot()['events'],[])

    def test_third_party_binding_is_not_clobbered_at_exit(self):
        def original(*a,**k):return object()
        self.context_fixture(original)
        def foreign(*a,**k):return object()
        with diag.observe_proc_links() as observer:os.readlink=foreign
        self.assertIs(os.readlink,foreign)
        self.assertEqual(observer.snapshot()['reason'],'RESTORATION_CHANGED')

    def test_observer_fd_error_does_not_change_original_return(self):
        token=object()
        def original(*a,**k):return token
        monitor,opened,closed=self.context_fixture(original);opened.side_effect=RuntimeError('FAKE_PRIVATE')
        with diag.observe_proc_links():self.assertIs(monitor(PROC_PATH('/proc/123/exe')),token)
        self.assertIs(os.readlink,original);closed.assert_not_called()

    def test_unavailable_platform_restores_original_binding(self):
        original=os.readlink
        with patch.object(diag.sys,'platform','win32'):
            with diag.observe_proc_links() as observer:self.assertIs(os.readlink,original)
        self.assertIs(os.readlink,original);self.assertEqual(observer.snapshot()['reason'],'KERNEL_API_UNAVAILABLE')

    def test_constructor_fault_cannot_prevent_context_body(self):
        original=os.readlink
        with patch.object(diag,'LinkObserver',side_effect=RuntimeError('FAKE_PRIVATE')):
            with diag.observe_proc_links() as observer:self.assertIsNone(observer)
        self.assertIs(os.readlink,original)

    def test_source_setup_failure_never_changes_binding(self):
        original=os.readlink
        with patch.object(diag.sys,'platform','linux'),patch.object(diag.os,'pidfd_open',create=True),patch.object(diag.select,'poll',create=True),patch.object(diag,'canonical_monitor',side_effect=ValueError('FAKE_PRIVATE')):
            with diag.observe_proc_links() as observer:pass
        self.assertIs(os.readlink,original);self.assertEqual(observer.snapshot()['availability'],'UNAVAILABLE')

    def test_registered_once_and_native_extra_retained(self):
        from tests.compiler import run_m1_tests as runner
        lanes,inherited=runner.inventory();path='tests/compiler/test_m1_proc_link_observation.py'
        self.assertEqual(lanes['new'].count(path),1);self.assertEqual(len(lanes['native-extra']),214)
        self.assertNotIn(path,set(lanes['native-extra'])|set(lanes['safety'])|inherited)

class ActualKernelControl(unittest.TestCase):
    def test_actual_native_api_authentication_rejects_replaced_bindings(self):
        if sys.platform!='linux' or not hasattr(os,'pidfd_open') or not hasattr(select,'poll'):
            raise RuntimeError('LINUX_PIDFD_REQUIRED_NOT_SKIPPED')
        captured=diag.native_kernel_bindings()
        self.assertIs(captured[0],os.pidfd_open);self.assertIs(captured[1],os.close)
        self.assertIs(captured[2],select.poll);self.assertEqual(captured[3:5],(1,16))
        for module,name in ((os,'pidfd_open'),(os,'close'),(select,'poll'),(select,'POLLIN'),(select,'POLLHUP')):
            with self.subTest(api=name),patch.object(module,name,object()):
                with self.assertRaises(ValueError):diag.native_kernel_bindings()
        self.assertEqual(diag.native_kernel_bindings(),captured)
        native_frame=diag.native_frame_reader()
        self.assertIs(native_frame,sys._getframe)
        with patch.object(sys,'_getframe',lambda depth:object()):
            with self.assertRaises(ValueError):diag.native_frame_reader()
        original=os.readlink
        with diag.observe_proc_links() as observer:
            self.assertEqual(observer.snapshot()['availability'],'VALID')
            self.assertTrue(observer.snapshot()['binding_verified'])
        self.assertIs(os.readlink,original)
        self.assertIs(observer.snapshot()['binding_restored'],True)

    def test_live_nondumpable_process_pidfd_is_not_terminal(self):
        if sys.platform!='linux' or not hasattr(os,'pidfd_open') or not hasattr(select,'poll'):
            raise RuntimeError('LINUX_PIDFD_REQUIRED_NOT_SKIPPED')
        ready_r,ready_w=os.pipe();release_r,release_w=os.pipe();pid=None;fd=None
        try:
            pid=os.fork()
            if pid==0:
                os.close(ready_r);os.close(release_w)
                libc=ctypes.CDLL(None);libc.prctl.argtypes=[ctypes.c_int,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong]
                libc.prctl.restype=ctypes.c_int
                if libc.prctl(4,0,0,0,0)!=0:os._exit(92)
                os.write(ready_w,b'R');os.read(release_r,1);os._exit(0)
            os.close(ready_w);ready_w=None;os.close(release_r);release_r=None;fd=os.pidfd_open(pid,0)
            self.assertTrue(select.select([ready_r],[],[],3)[0],'KERNEL_ACTOR_READY_BOUND')
            self.assertEqual(os.read(ready_r,1),b'R')
            try:os.readlink('/proc/'+str(pid)+'/exe')
            except PermissionError as error:self.assertIn(error.errno,(1,13),'KERNEL_PERMISSION_CODE')
            # Root/capability profiles may permit this read. That is not a
            # fabricated before failure; the independent live pidfd invariant
            # still must hold. Actual M1 denials remain separately observed.
            self.assertIs(diag.terminal_sample(fd),False)
            os.write(release_w,b'X');deadline=time.monotonic()+3
            while time.monotonic()<deadline and diag.terminal_sample(fd) is not True:time.sleep(.01)
            self.assertIs(diag.terminal_sample(fd),True);os.waitpid(pid,0);pid=None
        finally:
            if pid is not None:
                try:
                    if fd is not None:signal.pidfd_send_signal(fd,signal.SIGKILL)
                    else:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass
                os.waitpid(pid,0)
            for owned in (fd,ready_r,ready_w,release_r,release_w):
                if owned is not None:os.close(owned)

    def test_real_process_pidfd_waits_for_last_thread_not_zombie_leader(self):
        if sys.platform!='linux' or not hasattr(os,'pidfd_open') or not hasattr(select,'poll'):
            raise RuntimeError('LINUX_PIDFD_REQUIRED_NOT_SKIPPED')
        ready_r,ready_w=os.pipe();release_r,release_w=os.pipe();pid=None;fd=None
        try:
            pid=os.fork()
            if pid==0:
                os.close(ready_r);os.close(release_w)
                def wait():
                    os.write(ready_w,b'R');os.read(release_r,1);os._exit(0)
                threading.Thread(target=wait,daemon=True).start()
                libc=ctypes.CDLL(None);libc.pthread_exit.argtypes=[ctypes.c_void_p];libc.pthread_exit.restype=None
                libc.pthread_exit(None);os._exit(91)
            os.close(ready_w);ready_w=None;os.close(release_r);release_r=None
            fd=os.pidfd_open(pid,0)
            self.assertTrue(select.select([ready_r],[],[],3)[0],'KERNEL_ACTOR_READY_BOUND')
            self.assertEqual(os.read(ready_r,1),b'R')
            # Bounded synthetic kernel status read. No PID/name/status bytes leave
            # this test; a leader Z is deliberately NOT terminal evidence.
            deadline=time.monotonic()+3
            state=None
            while time.monotonic()<deadline:
                with open('/proc/'+str(pid)+'/stat','rb') as stream:raw=stream.read(4097)
                self.assertLessEqual(len(raw),4096,'KERNEL_STAT_BOUND')
                state=raw.rsplit(b') ',1)[1].split(b' ',1)[0]
                if state==b'Z':break
                time.sleep(.01)
            self.assertEqual(state,b'Z','KERNEL_DEAD_LEADER_REQUIRED')
            self.assertIs(diag.terminal_sample(fd),False)
            os.write(release_w,b'X')
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and diag.terminal_sample(fd) is not True:time.sleep(.01)
            self.assertIs(diag.terminal_sample(fd),True)
            os.waitpid(pid,0);pid=None
        finally:
            if pid is not None:
                try:
                    if fd is not None:signal.pidfd_send_signal(fd,signal.SIGKILL)
                    else:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass
                os.waitpid(pid,0)
            for owned in (fd,ready_r,ready_w,release_r,release_w):
                if owned is not None:os.close(owned)

def selected_suite():
    return unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
        for cls in (ProjectionControls,ContextControls,ActualKernelControl))
