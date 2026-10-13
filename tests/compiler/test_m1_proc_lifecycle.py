"""Portable privacy/parser controls; actual kernel control remains a hosted gate."""
import ast
import errno
import inspect
import json
import stat
from pathlib import Path
from contextlib import ExitStack
import unittest
from unittest.mock import Mock, patch

from tests.compiler import run_m1_proc_lifecycle as probe

class ProcLifecyclePortableControls(unittest.TestCase):
    def test_fixed_denial_and_disappearance_codes_only(self):
        for code, expected in ((1, 'EPERM'), (2, 'ENOENT'), (3, 'ESRCH'), (13, 'EACCES')):
            self.assertEqual(probe.classification(OSError(code, 'PRIVATE_TOKEN_PATH')), expected)

    def test_unknown_errno_remains_unknown(self):
        self.assertEqual(probe.classification(OSError(99999, 'PRIVATE')), 'UNKNOWN')

    def test_bool_errno_is_not_integer_permission(self):
        error = OSError('PRIVATE'); error.errno = True
        self.assertEqual(probe.classification(error), 'UNKNOWN')

    def test_foreign_exception_subclass_is_not_inspected(self):
        class Foreign(PermissionError):
            @property
            def errno(self): raise AssertionError('PRIVATE_PROPERTY_READ')
        self.assertEqual(probe.classification(Foreign()), 'UNKNOWN')

    def test_raw_link_target_cannot_escape_safe_result(self):
        private = 'FAKE_TOKEN_PRIVATE_BOOK_C:/private/argv/browser_pid'
        with patch.object(probe.worker.os, 'readlink', return_value=private) as call:
            result = probe.link('/proc/123/exe')
        call.assert_called_once_with('/proc/123/exe')
        self.assertEqual(result, 'READABLE')
        self.assertNotIn(private, json.dumps(result))

    def test_raw_exception_message_cannot_escape_safe_result(self):
        private = 'FAKE_TOKEN_PRIVATE_BOOK /private/browser-argv'
        error = PermissionError(errno.EACCES, private)
        with patch.object(probe.worker.os, 'readlink', side_effect=error) as call:
            result = probe.link('exe', directory=9)
        call.assert_called_once_with('exe', dir_fd=9)
        self.assertEqual(result, 'EACCES')
        self.assertNotIn(private, json.dumps(result))

    def stat_bytes(self, pid=123, start=456, comm=b'name with ) parentheses'):
        fields = [b'S'] + [b'0'] * 18 + [str(start).encode()] + [b'0'] * 30
        return str(pid).encode() + b' (' + comm + b') ' + b' '.join(fields)

    def identity(self, data, pid=123):
        # Explicit synthetic POSIX constants; never a Windows kernel claim or
        # a production fallback for unavailable flags.
        with patch.object(probe.os, 'O_NOFOLLOW', 131072, create=True), patch.object(probe.os, 'O_CLOEXEC', 524288, create=True), patch.object(probe.os, 'open', return_value=9), patch.object(probe.os, 'read', return_value=data), patch.object(probe.os, 'close') as close:
            result = probe.fresh_identity(8, pid)
        close.assert_called_once_with(9)
        return result

    def test_fresh_stat_parses_parenthesized_private_comm_without_export(self):
        self.assertEqual(self.identity(self.stat_bytes()), ((123, 456), b'S'))

    def test_mismatched_pid_rejected(self):
        with self.assertRaises(ValueError): self.identity(self.stat_bytes(pid=124))

    def test_truncated_or_oversize_stat_rejected(self):
        for value in (b'', b'123 (PRIVATE) S', b'X' * 4097):
            with self.subTest(bound=len(value)), self.assertRaises(ValueError): self.identity(value)

    def test_boolean_pid_or_descriptor_rejected(self):
        for fd, pid in ((True, 123), (8, True), (-1, 123), (8, 0)):
            with self.subTest(fd=fd, pid=pid), self.assertRaises(ValueError):
                probe.fresh_identity(fd, pid)

    def test_no_poll_event_is_live_not_unknown_or_terminal(self):
        poll = Mock(); poll.poll.return_value = []
        with patch.object(probe.select, 'poll', return_value=poll, create=True), patch.object(probe.select, 'POLLIN', 1, create=True), patch.object(probe.select, 'POLLHUP', 16, create=True):
            self.assertIs(probe.terminal(9), False)
        poll.poll.assert_called_once_with(0)

    def test_foreign_fd_or_unknown_poll_mask_rejected(self):
        for row in ([(8, 1)], [(9, 16)], [(9, 1), (9, 1)]):
            poll = Mock(); poll.poll.return_value = row
            with patch.object(probe.select, 'poll', return_value=poll, create=True), patch.object(probe.select, 'POLLIN', 1, create=True), patch.object(probe.select, 'POLLHUP', 16, create=True), self.assertRaises(ValueError):
                probe.terminal(9)

    def test_reaped_pidfd_in_and_hup_is_terminal(self):
        poll = Mock(); poll.poll.return_value = [(9, 17)]
        with patch.object(probe.select, 'poll', return_value=poll, create=True), patch.object(probe.select, 'POLLIN', 1, create=True), patch.object(probe.select, 'POLLHUP', 16, create=True):
            self.assertIs(probe.terminal(9), True)

    def test_second_pipe_failure_closes_first_pair(self):
        group = Mock(); error = OSError(24, 'PRIVATE_DESCRIPTOR_PATH')
        with patch.object(probe.worker, 'OwnedMemoryGroup', return_value=group), patch.object(probe.os, 'pipe', side_effect=[(8, 9), error]), patch.object(probe.os, 'close') as close:
            with self.assertRaises(OSError) as result:
                probe.run_case('LIVE_DUMPABLE', {})
        self.assertIs(result.exception, error)
        group.close.assert_called_once_with()
        self.assertEqual([c.args for c in close.call_args_list], [(8,), (9,)])

    def early_failure(self, location):
        group = Mock(); error = ValueError('PRIVATE_CONTROL_TEXT')
        if location == 'JOIN': group.join.side_effect = error
        with ExitStack() as stack:
            stack.enter_context(patch.object(probe.worker, 'OwnedMemoryGroup', return_value=group))
            stack.enter_context(patch.object(probe.os, 'pipe', side_effect=[(8, 9), (10, 11)]))
            stack.enter_context(patch.object(probe.signal, 'SIGCHLD', 17, create=True))
            stack.enter_context(patch.object(probe.signal, 'SIGKILL', 9, create=True))
            stack.enter_context(patch.object(probe.signal, 'getsignal', return_value=probe.signal.SIG_DFL))
            stack.enter_context(patch.object(probe.os, 'fork', return_value=123, create=True))
            stack.enter_context(patch.object(probe, 'wait_for', side_effect=error if location == 'STOPPED_WAIT' else None))
            stack.enter_context(patch.object(probe.os, 'close'))
            killed = stack.enter_context(patch.object(probe.os, 'kill'))
            stack.enter_context(patch.object(probe.os, 'WNOHANG', 1, create=True))
            reaped = stack.enter_context(patch.object(probe.os, 'waitpid', return_value=(123, 0)))
            with self.assertRaises(ValueError) as result:
                probe.run_case('LIVE_DUMPABLE', {})
            self.assertIs(result.exception, error)
            killed.assert_called_once_with(123, probe.signal.SIGKILL)
            reaped.assert_called_once_with(123, 1)
        group.close.assert_called_once_with()

    def test_stopped_wait_failure_cannot_leave_child_outside_group(self):
        self.early_failure('STOPPED_WAIT')

    def test_join_failure_cannot_treat_empty_group_close_as_child_exit(self):
        self.early_failure('JOIN')

    def test_cleanup_uses_owned_pidfd_when_available(self):
        with patch.object(probe.signal, 'SIGKILL', 9, create=True), patch.object(probe.signal, 'pidfd_send_signal', create=True) as kill, patch.object(probe.os, 'waitpid', return_value=(123, 0)), patch.object(probe.os, 'WNOHANG', 1, create=True):
            probe.reap_owned_child(123, 9)
        kill.assert_called_once_with(9, 9)

    def test_reap_is_bounded_and_not_blocking_wait(self):
        with patch.object(probe.signal, 'SIGKILL', 9, create=True), patch.object(probe.os, 'kill'), patch.object(probe.os, 'waitpid', return_value=(0, 0)) as reap, patch.object(probe.os, 'WNOHANG', 1, create=True), patch.object(probe.time, 'monotonic', side_effect=[0, 4]), self.assertRaises(ValueError):
            probe.reap_owned_child(123, None)
        reap.assert_called_once_with(123, 1)

    def test_cleanup_reaps_before_removing_group(self):
        events = []
        group = Mock(); group.close.side_effect = lambda: events.append('GROUP')
        with patch.object(probe, 'reap_owned_child', side_effect=lambda *a: events.append('REAP')), patch.object(probe, 'close_owned', side_effect=lambda *a: events.append('FDS')):
            state = {}
            probe.cleanup_probe(group, 123, 9, (8, 9), state)
        self.assertEqual(events, ['REAP', 'GROUP', 'FDS'])
        self.assertTrue(state['cleanup_completed'])

    def test_cleanup_first_rejection_not_replaced_by_later_phase(self):
        first = ValueError('PRIVATE_FIRST'); second = OSError(13, 'PRIVATE_SECOND')
        group = Mock(); group.close.side_effect = second
        with patch.object(probe, 'reap_owned_child', side_effect=first), patch.object(probe, 'close_owned') as close:
            state = {}
            with self.assertRaises(ValueError) as result:
                probe.cleanup_probe(group, 123, 9, (8, 9), state)
        self.assertIs(result.exception, first)
        self.assertEqual(state['phase'], 'OWN_CHILD_REAP')
        self.assertFalse(state['cleanup_completed'])
        close.assert_called_once_with((8, 9))

    def test_native_cleanup_code_exact_allowlist_no_private_message(self):
        trusted = probe.worker.CompilerQAError('CHROMIUM_RESOURCE_CLEANUP_DEADLINE')
        self.assertEqual(probe.classification(trusted), 'CHROMIUM_RESOURCE_CLEANUP_DEADLINE')
        self.assertEqual(probe.classification(probe.worker.CompilerQAError('CHROMIUM_RESOURCE_PRIVATE_TOKEN')), 'UNKNOWN')

    def test_parent_capabilities_are_projected_as_two_booleans_only(self):
        raw = b'Name:\tPRIVATE_PROCESS\nCapEff:\t0000004000080000\nPid:\t123\n'
        with patch.object(probe.worker, 'bounded_read', return_value=raw):
            value = probe.supervisor_capabilities()
        self.assertEqual(value, dict(sys_ptrace=True, perfmon=True))
        self.assertNotIn('PRIVATE', json.dumps(value))

    def test_capability_status_duplicate_or_invalid_is_rejected(self):
        for raw in (b'CapEff:\tprivate\n', b'Name:\tPRIVATE\n', b'CapEff:\t0000000000000000\nCapEff:\t0000000000000000\n'):
            with patch.object(probe.worker, 'bounded_read', return_value=raw), self.assertRaises(ValueError):
                probe.supervisor_capabilities()

    def test_zero_capabilities_are_false_not_unknown(self):
        with patch.object(probe.worker, 'bounded_read', return_value=b'CapEff:\t0000000000000000\n'):
            self.assertEqual(probe.supervisor_capabilities(), dict(sys_ptrace=False, perfmon=False))

    def test_all_owned_fds_attempted_even_on_close_failure(self):
        error = OSError(9, 'PRIVATE_PATH')
        with patch.object(probe.os, 'close', side_effect=[error, None, None]) as close:
            with self.assertRaises(OSError) as result: probe.close_owned((7, None, 8, 9))
        self.assertIs(result.exception, error)
        self.assertEqual([c.args for c in close.call_args_list], [(7,), (8,), (9,)])

    def test_fixed_link_pinning_uses_only_owned_directory_and_no_target_read(self):
        with patch.object(probe.os, 'O_PATH', 0x200000, create=True), patch.object(probe.os, 'O_NOFOLLOW', 0x20000, create=True), patch.object(probe.os, 'O_CLOEXEC', 0x80000, create=True), patch.object(probe.os, 'open', return_value=7) as opened, patch.object(probe.os, 'fstat', return_value=Mock(st_mode=stat.S_IFLNK)), patch.object(probe.os, 'get_inheritable', return_value=False):
            self.assertEqual(probe.pin_executable_link(8), 7)
        opened.assert_called_once_with('exe', 0x2a0000, dir_fd=8)

    def test_fixed_link_rejection_closes_descriptor(self):
        with patch.object(probe.os, 'O_PATH', 0x200000, create=True), patch.object(probe.os, 'O_NOFOLLOW', 0x20000, create=True), patch.object(probe.os, 'O_CLOEXEC', 0x80000, create=True), patch.object(probe.os, 'open', return_value=7), patch.object(probe.os, 'fstat', return_value=Mock(st_mode=stat.S_IFREG)), patch.object(probe.os, 'close') as close, self.assertRaises(ValueError):
            probe.pin_executable_link(8)
        close.assert_called_once_with(7)

    def test_fixed_link_read_uses_same_native_api_and_returns_no_target(self):
        with patch.object(probe.worker.os, 'readlink', return_value='PRIVATE_EXECUTABLE') as read:
            self.assertEqual(probe.link('', directory=7), 'READABLE')
        read.assert_called_once_with('', dir_fd=7)

    def test_sixth_control_is_explicit_not_pid_reuse_or_render_proof(self):
        self.assertEqual(probe.CASES[-1], 'PINNED_LINK_AFTER_REAP')
        self.assertEqual(len(probe.CASES), 6)
        self.assertEqual(probe.SCHEMA, 'bie.task036.m1.proc-lifecycle-reproduction/3')

    def test_probe_does_not_invoke_renderer_or_change_worker_admission(self):
        source = inspect.getsource(probe)
        ast.parse(source)
        self.assertNotIn('produce_actual_paint(', source)
        self.assertNotIn('run_chromium_isolated(', source)
        self.assertNotIn('asdict(', source)
        self.assertNotIn('str(error)', source)
        self.assertNotIn('repr(error)', source)

    def test_probe_tests_have_one_owner_and_retain_native_inventory(self):
        from tests.compiler.run_m1_tests import inventory
        lanes, inherited = inventory()
        own = 'tests/compiler/test_m1_proc_lifecycle.py'
        self.assertEqual(lanes['new'].count(own), 1)
        self.assertNotIn(own, set(lanes['native-extra']) | set(lanes['safety']) | inherited)
        self.assertEqual(len(lanes['native-extra']), 214)
