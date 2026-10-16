"""Portable security/restoration controls, not browser or real-kernel witnesses."""
from contextlib import ExitStack
import inspect
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import Mock, MagicMock, patch

from bie.compiler import chromium_resource_worker as worker


class SnapshotControls(unittest.TestCase):
    def test_kernel_baseline_binding_restored_after_original_rejection(self):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        original=kernel.probe.worker;error=PermissionError('PRIVATE_CONTROL_REJECTION')
        with patch.object(kernel.probe,'run',side_effect=error),self.assertRaises(PermissionError) as caught:
            kernel.baseline_controls()
        self.assertIs(caught.exception,error)
        self.assertIs(kernel.probe.worker,original)
        self.assertNotIn(kernel.BASELINE_NAME,sys.modules)

    def test_kernel_baseline_runs_once_on_authenticated_original_module(self):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        original=kernel.probe.worker;calls=[]
        expected=dict(passed=True,controls_completed=True,pinned_task_removal_denial_observed=True,observations=[{}]*6)
        def declared():
            calls.append(kernel.probe.worker)
            self.assertIsNot(kernel.probe.worker,original)
            self.assertEqual(kernel.probe.worker.__package__,'bie.compiler')
            self.assertEqual(Path(kernel.probe.worker.__file__).read_bytes(),
                (kernel.ROOT/kernel.DIRECTORY/'chromium_resource_worker.py.before').read_bytes())
            return expected
        with patch.object(kernel.probe,'run',declared):self.assertIs(kernel.baseline_controls(),expected)
        self.assertEqual(len(calls),1)
        self.assertIs(kernel.probe.worker,original)
        self.assertNotIn(kernel.BASELINE_NAME,sys.modules)

    def test_kernel_foreign_baseline_alias_is_not_overwritten_or_removed(self):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        foreign=ModuleType(kernel.BASELINE_NAME)
        with patch.dict(sys.modules,{kernel.BASELINE_NAME:foreign}),self.assertRaises(ValueError):
            kernel.baseline_controls()
            self.fail('foreign baseline accepted')
        self.assertNotIn(kernel.BASELINE_NAME,sys.modules)

    def test_parent_trace_does_not_label_copied_code_in_foreign_namespace(self):
        from types import FunctionType
        from tests.compiler import m1_parent_exception_observation as parent
        original=worker.bounded_read
        foreign=FunctionType(original.__code__,{'__name__':worker.__name__},original.__name__)
        # Missing source-bound helper raises PermissionError in this genuine code
        # object, but its foreign globals must prevent an attributed native event.
        def denied(*args,**kwargs):raise PermissionError('PRIVATE_FOREIGN_NAMESPACE')
        foreign.__globals__['Path']=denied
        with parent.observe_parent_exception_sites() as observation,self.assertRaises(PermissionError):
            foreign(Path('/synthetic'),1)
        self.assertEqual(observation.snapshot()['selected_exception_events'],0)

    def test_kernel_error_classification_uses_identity_not_foreign_equality(self):
        from tests.compiler.run_m1_monitor_snapshot_kernel import safe_exception_class
        class Counterfeit(type):
            def __eq__(self,other):raise AssertionError('PRIVATE_EQUALITY_MUST_NOT_RUN')
        foreign=Counterfeit('PRIVATE_TOKEN_EXCEPTION',(Exception,),{})
        self.assertEqual(safe_exception_class(foreign('PRIVATE_BOOK')),'OTHER')
        for expected in (ValueError,PermissionError,FileNotFoundError,ProcessLookupError,TimeoutError,worker.CompilerQAError):
            self.assertEqual(safe_exception_class(expected('PRIVATE')),expected.__name__)

    def test_actual_current_import_rejection_is_not_a_legacy_cleanup_site(self):
        import builtins
        from tests.compiler import m1_parent_exception_observation as parent
        real_import=builtins.__import__;original=PermissionError('PRIVATE_IMPORT_VALUE')
        def guarded(name,*args,**kwargs):
            if name=='linux_worker':raise original
            return real_import(name,*args,**kwargs)
        with patch.dict(sys.modules,{'resource':ModuleType('resource')}):
            with parent.observe_parent_exception_sites() as observation:
                with patch.object(builtins,'__import__',guarded),self.assertRaises(PermissionError) as caught:
                    worker.run_chromium_isolated((),workspace=None,engine=None,browser=None,kind=None)
        self.assertIs(caught.exception,original)
        safe=observation.snapshot()
        self.assertEqual(safe['availability'],'VALID')
        self.assertEqual(safe['selected_exception_events'],1)
        self.assertEqual(safe['first_site'],'RUN_OTHER')
        self.assertNotIn('PRIVATE',__import__('json').dumps(safe))

    def test_every_current_parent_location_matches_its_exact_operation(self):
        from tests.compiler import m1_parent_exception_observation as parent
        source=Path(worker.__file__).read_text().splitlines()
        fragments={'MONITOR_COMMAND_READ':"argv=bounded_read(proc/'cmdline')",'DRIVER_COMMUNICATE':'outer.communicate',
            'DRIVER_RESULT_READ':'v=json.loads','POST_RUN_ENGINE_HASH':'ENGINE_CHANGED_AFTER_RUN',
            'POST_RUN_BROWSER_HASH':"receipt['browser_bytes_unchanged']",'CLEANUP_GROUP':'group.close()',
            'CLEANUP_DRIVER':'outer.communicate','CLEANUP_TEMPORARY':'temporary.cleanup()',
            'RESOURCE_RECEIPT_PUBLICATION':".open('xb')"}
        for line,site in parent.LOCATIONS['run_chromium_isolated'].items():
            self.assertIn(fragments[site],source[line-1])
        self.assertNotIn(405,parent.LOCATIONS['run_chromium_isolated'])
        self.assertNotIn(407,parent.LOCATIONS['run_chromium_isolated'])

    def test_anchor_observer_resolves_only_fixed_owned_proc_fd(self):
        from tests.compiler.m1_proc_link_observation import anchored_monitor_request
        calls=[]
        def original(path):calls.append(path);return '/proc/7'
        self.assertEqual(anchored_monitor_request(('exe',),{'dir_fd':8},original),(7,'EXE'))
        self.assertEqual(calls,['/proc/self/fd/8'])

    def test_anchor_observer_rejects_foreign_deleted_or_ambiguous_targets(self):
        from tests.compiler.m1_proc_link_observation import anchored_monitor_request
        for target in ('/private/secret','/proc/7 (deleted)','/proc/07','/proc/7/extra','/proc/0','/proc/2147483648','/proc/７'):
            self.assertIsNone(anchored_monitor_request(('root',),{'dir_fd':8},lambda p:target))

    def test_anchor_observer_rejects_unbounded_or_coerced_fd_before_lookup(self):
        from tests.compiler.m1_proc_link_observation import anchored_monitor_request
        for fd in (True,-1,2**31,8.0,'8'):
            original=Mock()
            self.assertIsNone(anchored_monitor_request(('exe',),{'dir_fd':fd},original))
            original.assert_not_called()

    def test_anchor_observer_unknown_fields_never_read_arbitrary_control(self):
        from tests.compiler.m1_proc_link_observation import anchored_monitor_request
        original=Mock()
        for args,kwargs in ((('environ',),{'dir_fd':8}),(('exe',),{'dir_fd':8,'stderr':'PRIVATE'}),(('/private/source',),{})):
            self.assertIsNone(anchored_monitor_request(args,kwargs,original))
        original.assert_not_called()

    def test_versioned_observers_bind_current_and_keep_original_pin(self):
        from tests.compiler import m1_parent_exception_observation as parent,m1_proc_link_observation as link
        from hashlib import sha256
        actual=sha256(Path(worker.__file__).read_bytes()).hexdigest()
        for module in (parent,link):
            self.assertEqual(module.SOURCE_SHA256,actual)
            self.assertEqual(module.LEGACY_SOURCE_SHA256,'aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963')
            self.assertTrue(module.SCHEMA.endswith('/2'))

    def group(self):
        group=Mock(spec=worker.OwnedMemoryGroup)
        group.path=Path('/sys/fs/cgroup/bie-chromium-owned-synthetic')
        group.inode=123
        group.members.side_effect=[{7},{8,7}]
        return group

    def context(self,group):
        stack=ExitStack()
        stack.enter_context(patch.object(worker,'OwnedMemoryGroup',type(group)))
        stack.enter_context(patch.object(worker.Path,'is_symlink',return_value=False))
        stack.enter_context(patch.object(worker.Path,'stat',return_value=SimpleNamespace(st_ino=123)))
        stack.enter_context(patch.object(worker.os,'getpid',return_value=100))
        stack.enter_context(patch.object(worker,'counters',return_value={'frozen':0}))
        return stack

    def test_membership_is_sampled_after_actual_freeze_not_old_enumeration(self):
        group=self.group(); events=[]
        group.freeze.side_effect=lambda state:events.append(('FREEZE',state))
        group.members.side_effect=lambda:events.append(('MEMBERS',None)) or {7}
        with self.context(group),worker.frozen_monitor_members(group) as members:
            self.assertEqual(members,(7,)); events.append(('BODY',None))
        self.assertEqual(events,[('MEMBERS',None),('FREEZE',True),('MEMBERS',None),('BODY',None),('FREEZE',False)])

    def test_body_permission_error_is_not_swallowed(self):
        group=self.group(); original=PermissionError(13,'PRIVATE_CONTENT')
        with self.context(group),self.assertRaises(PermissionError) as caught:
            with worker.frozen_monitor_members(group):raise original
        self.assertIs(caught.exception,original)
        self.assertEqual([c.args for c in group.freeze.call_args_list],[(True,),(False,)])

    def test_partially_failed_freeze_attempts_restore(self):
        group=self.group(); original=worker.CompilerQAError('CHROMIUM_RESOURCE_FREEZE_DEADLINE')
        group.freeze.side_effect=[original,None]
        with self.context(group),self.assertRaises(worker.CompilerQAError) as caught:
            with worker.frozen_monitor_members(group):self.fail('BODY_RAN')
        self.assertIs(caught.exception,original)
        self.assertEqual([c.args for c in group.freeze.call_args_list],[(True,),(False,)])

    def test_restore_failure_cannot_convert_success_to_pass(self):
        group=self.group(); original=worker.CompilerQAError('CHROMIUM_RESOURCE_FREEZE_DEADLINE')
        group.freeze.side_effect=[None,original]
        with self.context(group),self.assertRaises(worker.CompilerQAError) as caught:
            with worker.frozen_monitor_members(group):pass
        self.assertIs(caught.exception,original)

    def test_body_rejection_identity_survives_restore_rejection(self):
        group=self.group(); original=PermissionError(13,'PRIVATE_CONTENT')
        group.freeze.side_effect=[None,worker.CompilerQAError('CHROMIUM_RESOURCE_FREEZE_DEADLINE')]
        with self.context(group),self.assertRaises(PermissionError) as caught:
            with worker.frozen_monitor_members(group):raise original
        self.assertIs(caught.exception,original)

    def test_foreign_group_inode_never_freezes(self):
        group=self.group()
        with self.context(group),patch.object(worker.Path,'stat',return_value=SimpleNamespace(st_ino=999)),self.assertRaises(worker.CompilerQAError):
            with worker.frozen_monitor_members(group):self.fail('BODY_RAN')
        group.freeze.assert_not_called()

    def test_nested_or_foreign_existing_freeze_is_not_thawed(self):
        group=self.group()
        with self.context(group),patch.object(worker,'counters',return_value={'frozen':1}),self.assertRaises(worker.CompilerQAError):
            with worker.frozen_monitor_members(group):self.fail('BODY_RAN')
        group.freeze.assert_not_called()

    def test_supervisor_inside_group_is_rejected(self):
        group=self.group();group.members.side_effect=None;group.members.return_value={100}
        with self.context(group),self.assertRaises(worker.CompilerQAError):
            with worker.frozen_monitor_members(group):self.fail('BODY_RAN')
        group.freeze.assert_not_called()

    def test_member_bounds_and_boolean_ids_reject(self):
        for value in ({True},{0},{2**31},set(range(1,130))):
            group=self.group();group.members.side_effect=[{7},value]
            with self.context(group),self.assertRaises(worker.CompilerQAError):
                with worker.frozen_monitor_members(group):self.fail('BODY_RAN')
            self.assertEqual(group.freeze.call_args.args,(False,))

    def test_unknown_field_cannot_expand_proc_reads(self):
        with patch.object(worker.os,'open') as opened,self.assertRaises(worker.CompilerQAError):
            worker._monitor_read(7,'environ',4096)
        opened.assert_not_called()

    def test_invalid_proc_descriptor_or_read_limit_rejected_before_open(self):
        for directory,maximum in ((True,4096),(-1,4096),(2**31,4096),(7,True),(7,0),(7,2*1024**2+1)):
            with patch.object(worker.os,'open') as opened,self.assertRaises(worker.CompilerQAError):
                worker._monitor_read(directory,'stat',maximum)
            opened.assert_not_called()

    def test_bounded_read_closes_fd_even_when_oversize(self):
        reader=MagicMock();reader.__enter__.return_value=reader;reader.read.return_value=b'x'*4097
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',return_value=reader),self.assertRaises(worker.CompilerQAError):
            worker._monitor_read(8,'stat',4096)
        reader.close.assert_called_once();reader.read.assert_called_once_with(4097)

    def test_permission_rejection_from_read_is_preserved(self):
        original=PermissionError(13,'PRIVATE_CONTENT')
        reader=MagicMock();reader.__enter__.return_value=reader;reader.read.side_effect=original
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',return_value=reader),self.assertRaises(PermissionError) as caught:
            worker._monitor_read(8,'stat',4096)
        self.assertIs(caught.exception,original);reader.close.assert_called_once()

    def test_nested_proc_read_permission_error_survives_close_failure(self):
        original=PermissionError(13,'PRIVATE_CONTENT')
        reader=Mock();reader.read.side_effect=original;reader.close.side_effect=OSError(9,'PRIVATE_FD')
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',return_value=reader),self.assertRaises(PermissionError) as caught:
            worker._monitor_read(8,'stat',4096)
        self.assertIs(caught.exception,original);reader.close.assert_called_once()

    def test_nested_proc_close_failure_rejects_success(self):
        original=OSError(9,'PRIVATE_FD')
        reader=Mock();reader.read.return_value=b'complete';reader.close.side_effect=original
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',return_value=reader),self.assertRaises(OSError) as caught:
            worker._monitor_read(8,'stat',4096)
        self.assertIs(caught.exception,original)

    def test_fdopen_failure_closes_untransferred_descriptor(self):
        original=OSError(9,'PRIVATE_FD')
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',side_effect=original),patch.object(worker.os,'close') as closed,self.assertRaises(OSError) as caught:
            worker._monitor_read(8,'stat',4096)
        self.assertIs(caught.exception,original);closed.assert_called_once_with(7)

    def test_proc_reader_consumes_complete_bounded_stream_not_single_raw_read(self):
        reader=MagicMock();reader.__enter__.return_value=reader;reader.read.return_value=b'complete-map'
        with patch.object(worker.os,'O_NOFOLLOW',0x20000,create=True),patch.object(worker.os,'O_CLOEXEC',0x80000,create=True),patch.object(worker.os,'open',return_value=7),patch.object(worker.os,'fdopen',return_value=reader) as opened:
            self.assertEqual(worker._monitor_read(8,'maps',2*1024**2),b'complete-map')
        opened.assert_called_once_with(7,'rb');reader.read.assert_called_once_with(2*1024**2+1)

    def test_stat_parser_does_not_split_comm_into_identity(self):
        raw=b'7 (PRIVATE (name) with spaces) S '+b'0 '*18+b'123 0\n'
        with patch.object(worker,'_monitor_read',return_value=raw):
            self.assertEqual(worker._monitor_identity(8,7),(7,123))

    def test_stat_unknown_state_and_wrong_pid_reject(self):
        for raw in (b'8 (x) S '+b'0 '*18+b'123',b'7 (x) Q '+b'0 '*18+b'123',b'7 x S',b'7 (x) S '+b'0 '*19):
            with patch.object(worker,'_monitor_read',return_value=raw),self.assertRaises(worker.CompilerQAError):
                worker._monitor_identity(8,7)

    def setup_member(self):
        stack=ExitStack();group=Mock(spec=worker.OwnedMemoryGroup)
        if sys.platform!='linux':
            # Explicit portable fixture only; actual Linux/render gates use the
            # native resource module and are independently mandatory.
            synthetic=ModuleType('resource');synthetic.RLIMIT_AS=0
            synthetic.prlimit=Mock(return_value=(worker.CHROME_AS,worker.CHROME_AS))
            stack.enter_context(patch.dict(sys.modules,{'resource':synthetic}))
        group.path=Path('/sys/fs/cgroup/bie-chromium-owned-synthetic');group.members.return_value={7}
        stack.enter_context(patch.object(worker,'OwnedMemoryGroup',type(group)))
        stack.enter_context(patch.object(worker,'counters',return_value={'frozen':1}))
        for key,value in (('O_DIRECTORY',0x10000),('O_NOFOLLOW',0x20000),('O_CLOEXEC',0x80000)):
            stack.enter_context(patch.object(worker.os,key,value,create=True))
        stack.enter_context(patch.object(worker.os,'open',return_value=8))
        stack.enter_context(patch.object(worker.os,'fstat',return_value=SimpleNamespace(st_mode=stat.S_IFDIR)))
        stack.enter_context(patch.object(worker.os,'get_inheritable',return_value=False))
        stack.enter_context(patch.object(worker.os,'pidfd_open',return_value=9,create=True))
        stack.enter_context(patch.object(worker,'_monitor_identity',return_value=(7,123)))
        stack.enter_context(patch.object(worker,'_monitor_read',return_value=b'0::/bie-chromium-owned-synthetic\n'))
        stack.enter_context(patch.object(worker.os,'readlink',return_value='PRIVATE_TARGET'))
        stack.enter_context(patch.object(worker,'admitted_browser_grant',return_value=None))
        closed=stack.enter_context(patch.object(worker.os,'close'))
        return stack,group,closed

    def test_unfrozen_observation_rejected_before_open(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker,'counters',return_value={'frozen':0}),patch.object(worker.os,'open') as opened,self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        opened.assert_not_called()

    def test_coerced_or_out_of_bounds_pid_rejected_before_open(self):
        for pid in (True,0,-1,2**31,7.0,'7'):
            stack,group,closed=self.setup_member()
            with stack,patch.object(worker.os,'open') as opened,self.assertRaises(worker.CompilerQAError):
                worker.observe_frozen_member(group,pid,Path('/synthetic/browser'),[])
            opened.assert_not_called()

    def test_nonbrowser_yields_no_grant_or_reservation(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker.os,'readlink',return_value='PRIVATE_TARGET') as link:
            self.assertIsNone(worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[]))
        self.assertEqual([c.args for c in link.call_args_list],[('exe',),('root',)])
        self.assertTrue(all(c.kwargs=={'dir_fd':8} for c in link.call_args_list))
        self.assertEqual([c.args for c in closed.call_args_list],[(9,),(8,)])

    def test_live_permission_denial_preserved_without_terminal_probe(self):
        stack,group,closed=self.setup_member(); original=PermissionError(13,'PRIVATE_TARGET')
        with stack,patch.object(worker.os,'readlink',side_effect=original),self.assertRaises(PermissionError) as caught:
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertIs(caught.exception,original)
        self.assertEqual([c.args for c in closed.call_args_list],[(9,),(8,)])

    def test_foreign_cgroup_rejected_before_link(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker,'_monitor_read',return_value=b'0::/foreign\n'),patch.object(worker.os,'readlink') as link,self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        link.assert_not_called()

    def test_rebound_pid_identity_rejected_before_link(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker,'_monitor_identity',side_effect=[(7,123),(7,124)]),patch.object(worker.os,'readlink') as link,self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        link.assert_not_called()

    def test_exit_or_rebinding_after_links_cannot_mint_observation(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker,'_monitor_identity',side_effect=[(7,123),(7,123),(7,124)]),self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])

    def test_inheritable_anchor_rejected_and_closed(self):
        stack,group,closed=self.setup_member()
        with stack,patch.object(worker.os,'get_inheritable',return_value=True),self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        closed.assert_called_once_with(8)

    def test_body_error_survives_close_failure_and_all_closes_attempted(self):
        stack,group,closed=self.setup_member();original=PermissionError(13,'PRIVATE_TARGET')
        closed.side_effect=OSError(9,'PRIVATE_FD')
        with stack,patch.object(worker.os,'readlink',side_effect=original),self.assertRaises(PermissionError) as caught:
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertIs(caught.exception,original);self.assertEqual(closed.call_count,2)

    def test_close_failure_cannot_mint_success(self):
        stack,group,closed=self.setup_member();original=OSError(9,'PRIVATE_FD')
        closed.side_effect=[original,None]
        with stack,self.assertRaises(OSError) as caught:
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertIs(caught.exception,original);self.assertEqual(closed.call_count,2)

    def test_unrelated_caller_exception_cannot_hide_successful_body_close_failure(self):
        stack,group,closed=self.setup_member();original=OSError(9,'PRIVATE_FD')
        closed.side_effect=[original,None]
        with stack:
            try:raise ValueError('UNRELATED_PRIVATE_CALLER')
            except ValueError:
                with self.assertRaises(OSError) as caught:
                    worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertIs(caught.exception,original);self.assertEqual(closed.call_count,2)

    def test_browser_observation_requires_actual_limit_and_bound_mapping(self):
        stack,group,closed=self.setup_member()
        with stack:
            import resource
            def fields(directory,name,maximum):
                return b'0::/bie-chromium-owned-synthetic\n' if name=='cgroup' else b'1000-10000002000 ---p 0 00:00 0\n'
            with patch.object(worker,'admitted_browser_grant',return_value={'owned_sandbox_root':'PRIVATE_ROOT'}),patch.object(worker,'_monitor_read',side_effect=fields),patch.object(resource,'prlimit',return_value=(worker.CHROME_AS,worker.CHROME_AS)) as limit:
                spans=worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
            self.assertEqual(spans,[{'bytes':int('10000002000',16)-int('1000',16),'permissions':'---p'}])
            limit.assert_called_once_with(7,resource.RLIMIT_AS)
        self.assertEqual(closed.call_count,2)

    def test_wrong_browser_limit_blocks_before_mapping_read(self):
        stack,group,closed=self.setup_member()
        with stack:
            import resource
            with patch.object(worker,'admitted_browser_grant',return_value={'owned_sandbox_root':'PRIVATE_ROOT'}),patch.object(resource,'prlimit',return_value=(worker.NODE_AS,worker.NODE_AS)),self.assertRaises(worker.CompilerQAError):
                worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertEqual(closed.call_count,2)

    def test_reversed_mapping_cannot_contribute_reservation(self):
        stack,group,closed=self.setup_member()
        with stack:
            import resource
            def fields(directory,name,maximum):
                return b'0::/bie-chromium-owned-synthetic\n' if name=='cgroup' else b'2000-1000 ---p 0 00:00 0\n'
            with patch.object(worker,'admitted_browser_grant',return_value={'owned_sandbox_root':'PRIVATE_ROOT'}),patch.object(worker,'_monitor_read',side_effect=fields),patch.object(resource,'prlimit',return_value=(worker.CHROME_AS,worker.CHROME_AS)),self.assertRaises(worker.CompilerQAError):
                worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])

    def test_foreign_final_membership_rejects_completed_link_read(self):
        stack,group,closed=self.setup_member()
        group.members.side_effect=[{7},set()]
        with stack,self.assertRaises(worker.CompilerQAError):
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])

    def test_pidfd_failure_closes_existing_anchor_and_preserves_error(self):
        stack,group,closed=self.setup_member(); original=PermissionError(13,'PRIVATE_FD')
        with stack,patch.object(worker.os,'pidfd_open',side_effect=original),self.assertRaises(PermissionError) as caught:
            worker.observe_frozen_member(group,7,Path('/synthetic/browser'),[])
        self.assertIs(caught.exception,original);closed.assert_called_once_with(8)

    def test_monitor_has_no_terminal_after_error_omission(self):
        source=inspect.getsource(worker.observe_frozen_member)
        self.assertNotIn('except PermissionError',source)
        self.assertNotIn('poll(',source)
        self.assertNotIn('SIGCONT',source)
        self.assertNotIn('setrlimit',source)

    def test_grant_is_not_nested_under_observation_freeze(self):
        source=inspect.getsource(worker.run_chromium_isolated)
        self.assertLess(source.index('granted=_grant('),source.index('captured=capture_monitor_cycle('))
        self.assertNotIn('_grant(',source[source.index('captured=capture_monitor_cycle('):])
        self.assertIn('with frozen_monitor_members(',inspect.getsource(worker.capture_monitor_cycle))


class AuditControls(unittest.TestCase):
    root=Path(__file__).resolve().parents[2]

    def test_actual_exact_followon_manifest_and_original_authenticate(self):
        from scripts import compiler_monitor_snapshot_amendment as audit
        document=audit.validate(self.root)
        self.assertEqual(len(document['replacements']),3)
        self.assertEqual(len(audit.authenticated_original_worker(self.root)),28552)
        self.assertEqual(document['independent_review_status'],'REQUIRES_REASSESSMENT_AND_ACTUAL_LINUX_RENDER_PROOF')

    def reject_changed(self,target,transform):
        from scripts import compiler_monitor_snapshot_amendment as audit
        regular,unique=audit.reader()
        def read(root,relative,maximum):
            value=regular(root,relative,maximum)
            return transform(value) if relative==target else value
        with patch.object(audit,'reader',return_value=(read,unique)),self.assertRaises(ValueError):
            audit.validate(self.root)

    def test_active_worker_tamper_rejected(self):
        self.reject_changed('bie/compiler/chromium_resource_worker.py',lambda value:value+b'\n')

    def test_active_entrypoint_tamper_rejected(self):
        self.reject_changed('scripts/verify_post_dir.py',lambda value:value+b'\n')

    def test_active_attributes_tamper_rejected(self):
        self.reject_changed('.gitattributes',lambda value:value+b'\n')

    def test_original_worker_tamper_rejected(self):
        self.reject_changed('docs/productization/task036-monitor-snapshot-amendment/chromium_resource_worker.py.before',lambda value:value+b'\n')

    def test_original_preimage_crlf_conversion_is_not_admitted(self):
        self.reject_changed('docs/productization/task036-monitor-snapshot-amendment/chromium_resource_worker.py.before',lambda value:value.replace(b'\n',b'\r\n'))

    def test_original_attribute_preimage_tamper_rejected(self):
        self.reject_changed('docs/productization/task036-monitor-snapshot-amendment/.gitattributes.before',lambda value:value+b'\n')

    def test_original_entrypoint_preimage_tamper_rejected(self):
        self.reject_changed('docs/productization/task036-monitor-snapshot-amendment/verify_post_dir.py.before',lambda value:value+b'\n')

    def test_original_m1_seal_unchanged_and_tamper_rejected(self):
        self.reject_changed('docs/productization/task036-motion-amendment/AMENDMENT.json',lambda value:value+b'\n')

    def test_original_reviewed_chain_index_tamper_rejected(self):
        self.reject_changed('docs/productization/m1-review/SOURCE_CHAIN_A24EF1CD.json',lambda value:value+b'\n')

    def test_manifest_mutation_cannot_self_bless(self):
        self.reject_changed('docs/productization/task036-monitor-snapshot-amendment/AMENDMENT.json',lambda value:value+b'\n')

    def test_unlisted_amendment_path_rejected(self):
        from scripts import compiler_monitor_snapshot_amendment as audit
        original=Path.rglob
        def paths(folder,pattern):
            yield from original(folder,pattern)
            if folder==self.root/audit.DIRECTORY:yield self.root/'tests/compiler/run_m1_tests.py'
        with patch.object(Path,'rglob',paths),self.assertRaises(ValueError):audit.validate(self.root)

    def test_partial_rollback_cannot_admit_original_active_worker(self):
        original=(self.root/'docs/productization/task036-monitor-snapshot-amendment/chromium_resource_worker.py.before').read_bytes()
        self.reject_changed('bie/compiler/chromium_resource_worker.py',lambda value:original)

    def test_portable_active_source_conversion_does_not_rewrite_preimages(self):
        from scripts import compiler_monitor_snapshot_amendment as audit
        regular,unique=audit.reader()
        def read(root,relative,maximum):
            value=regular(root,relative,maximum)
            return value.replace(b'\n',b'\r\n') if relative=='bie/compiler/chromium_resource_worker.py' else value
        with patch.object(audit,'reader',return_value=(read,unique)):
            self.assertEqual(audit.validate(self.root)['monitor_policy'],audit.POLICY)

    def test_new_inventory_owner_is_unique_and_native_extra_retained(self):
        from tests.compiler.run_m1_tests import inventory
        lanes,inherited=inventory();own='tests/compiler/test_m1_monitor_snapshot.py'
        self.assertEqual(lanes['new'].count(own),1)
        self.assertNotIn(own,set(lanes['native-extra'])|set(lanes['safety'])|inherited)
        self.assertEqual(len(lanes['native-extra']),214)

    def test_canonical_audit_actually_invokes_new_gate(self):
        from scripts import verify_post_dir
        self.assertIn('validate_monitor_snapshot(root)',inspect.getsource(verify_post_dir.resolve_source_members))

    def test_original_four_motion_seams_and_three_modules_match_immutable_seal(self):
        import hashlib,json
        document=json.loads((self.root/'docs/productization/task036-motion-amendment/AMENDMENT.json').read_bytes())
        for row in document['replacements']:
            actual=(self.root/row['path']).read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(hashlib.sha256(actual).hexdigest(),row['active_sha256'])
        for path,expected in document['additions'].items():
            actual=(self.root/path).read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(hashlib.sha256(actual).hexdigest(),expected)


class KernelSourceLabelControls(unittest.TestCase):
    """Portable receipt-label controls; mocks are NOT actual Linux kernel proof."""
    def bindings(self):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        return kernel.authenticated_worker_bindings()

    def execute(self, baseline=None, bindings=None):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        declared=self.bindings()
        baseline=baseline if baseline is not None else dict(worker_sha256=declared['baseline_worker_sha256'])
        with ExitStack() as stack:
            stack.enter_context(patch.object(kernel.sys,'platform','linux'))
            stack.enter_context(patch.object(kernel.os,'getuid',return_value=0,create=True))
            stack.enter_context(patch.object(kernel,'baseline_controls',return_value=baseline))
            stack.enter_context(patch.object(kernel,'fresh_actor_control',return_value=dict(passed=True)))
            stack.enter_context(patch.object(kernel,'owned_reaper_control',return_value=dict(passed=True)))
            if bindings is not None:
                stack.enter_context(patch.object(kernel,'authenticated_worker_bindings',side_effect=bindings))
            return kernel.run()

    def test_fixed_authentic_active_previous_baseline_hashes_are_distinct(self):
        value=self.bindings()
        self.assertEqual(value['active_worker_sha256'],'be4ac9863c6b5153568dec53d052e3d95973b4562e04d1efa2a0d8d5180e0aea')
        self.assertEqual(value['previous_worker_sha256'],'dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb')
        self.assertEqual(value['baseline_worker_sha256'],'aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963')
        self.assertEqual(len(set(value[k] for k in ('active_worker_sha256','previous_worker_sha256','baseline_worker_sha256'))),3)
        self.assertEqual(value['parse_amendment_sha256'],'a60c6bd3c343fcca66b44260040849c93e248fc8dd62a08ee6dbbb5640395df9')

    def test_version_two_receipt_labels_actual_active_not_prior_target_table(self):
        from tests.compiler import run_m1_monitor_snapshot_kernel as kernel
        value=self.execute()
        self.assertEqual(value['schema'],'bie.task036.m1.monitor-snapshot-kernel-proof/2')
        self.assertEqual(value['worker_sha256'],self.bindings()['active_worker_sha256'])
        self.assertNotEqual(value['worker_sha256'],value['baseline']['worker_sha256'])
        self.assertEqual(value['source_bindings'],self.bindings())
        self.assertFalse(value['render_passed']);self.assertFalse(value['accepted']);self.assertFalse(value['product_accepted'])

    def test_counterfeit_baseline_label_cannot_publish_success(self):
        with self.assertRaises(ValueError):
            self.execute(baseline=dict(worker_sha256=self.bindings()['active_worker_sha256']))

    def test_changed_authenticated_source_between_controls_rejects(self):
        before=self.bindings();after=dict(before,active_worker_sha256=before['previous_worker_sha256'])
        with self.assertRaises(ValueError):self.execute(bindings=[before,after])
