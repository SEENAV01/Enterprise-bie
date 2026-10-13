"""Controlled Linux proc-access/lifecycle reproduction, never monitor admission.

Trusted synthetic actors only. Uses canonical OwnedMemoryGroup and the unchanged
worker's actual readlink/bounded_read APIs. No browser, rendered witness, source
payload, skip, resource grant or production scene is created by this probe.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import stat
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bie.compiler import chromium_resource_worker as worker

SCHEMA = 'bie.task036.m1.proc-lifecycle-reproduction/1'
WORKER_SHA = 'aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963'
CASES = ('LIVE_DUMPABLE', 'LIVE_NONDUMPABLE', 'WHOLE_PROCESS_EXITED',
         'DEAD_LEADER_LIVE_THREAD', 'ANCHORED_AFTER_REAP')
OUTCOMES = frozenset(('READABLE', 'EACCES', 'EPERM', 'ENOENT', 'ESRCH', 'UNKNOWN'))

def require(value):
    if not value:
        raise ValueError('M1_PROC_LIFECYCLE_CONTROL_REJECTED')

def classification(error):
    if type(error) not in (PermissionError, FileNotFoundError, ProcessLookupError, OSError):
        return 'UNKNOWN'
    code = error.errno
    if type(code) is not int:
        return 'UNKNOWN'
    return {1: 'EPERM', 2: 'ENOENT', 3: 'ESRCH', 13: 'EACCES'}.get(code, 'UNKNOWN')

def link(path, *, directory=None):
    try:
        # Same native API as the exact worker monitor. Raw link targets remain
        # local; never returned, formatted or serialized into the safe receipt.
        worker.os.readlink(path) if directory is None else worker.os.readlink(path, dir_fd=directory)
        return 'READABLE'
    except OSError as error:
        return classification(error)

def fresh_identity(directory, pid):
    require(type(directory) is int and directory >= 0 and type(pid) is int and 0 < pid < 2**31)
    fd = os.open('stat', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
    try:
        raw = os.read(fd, 4097)
    finally:
        os.close(fd)
    require(0 < len(raw) <= 4096)
    first, separator, rest = raw.partition(b' (')
    end = rest.rfind(b') ')
    require(separator == b' (' and first.isdigit() and int(first) == pid and end >= 0)
    fields = rest[end + 2:].split()
    require(len(fields) >= 20 and fields[0] in (b'R', b'S', b'D', b'Z', b'T', b't', b'X', b'x', b'I'))
    require(fields[19].isdigit() and int(fields[19]) > 0)
    return (pid, int(fields[19])), fields[0]

def terminal(fd):
    require(type(fd) is int and fd >= 0)
    poll = select.poll()
    poll.register(fd, select.POLLIN)
    rows = poll.poll(0)
    require(not rows or (len(rows) == 1 and rows[0][0] == fd and
        rows[0][1] in (select.POLLIN, select.POLLIN | select.POLLHUP)))
    return bool(rows)

def close_owned(fds):
    first = None
    for fd in fds:
        if fd is not None:
            try:
                os.close(fd)
            except OSError as error:
                if first is None:
                    first = error
    if first is not None:
        raise first

def reap_owned_child(pid, pidfd):
    """Unreaped fork child only: group removal is not child-exit evidence."""
    try:
        if pidfd is not None:
            signal.pidfd_send_signal(pidfd, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # Own child already exited; still require actual bounded waitpid.
    end = time.monotonic() + 3
    while True:
        found, _ = os.waitpid(pid, os.WNOHANG)
        require(found in (0, pid))
        if found == pid:
            return
        require(time.monotonic() < end)
        time.sleep(.005)

def wait_for(predicate):
    end = time.monotonic() + 3
    while not predicate():
        require(time.monotonic() < end)
        time.sleep(.005)

def child(mode, ready, release):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    os.kill(os.getpid(), signal.SIGSTOP)
    if libc.prctl(4, 0 if mode == 'LIVE_NONDUMPABLE' else 1, 0, 0, 0) != 0:
        os._exit(92)
    def hold():
        os.write(ready, b'R')
        os.read(release, 1)
        os._exit(0)
    if mode == 'DEAD_LEADER_LIVE_THREAD':
        threading.Thread(target=hold, daemon=True).start()
        libc.pthread_exit.argtypes = [ctypes.c_void_p]
        libc.pthread_exit.restype = None
        libc.pthread_exit(None)
        os._exit(93)
    hold()

def sample(mode, pid, directory, pidfd, bound, group):
    before, state = fresh_identity(directory, pid)
    require(before == bound)
    # Cgroup read can change legitimately after whole-process exit; retain its
    # exact observed classification, not inferred ownership or a skip grant.
    def membership():
        try:
            cfd = os.open('cgroup', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
            try:
                raw = os.read(cfd, 4097)
            finally:
                os.close(cfd)
            require(len(raw) <= 4096)
            return dict(state='READABLE', owned=raw == ('0::/' + group.path.name + '\n').encode(),
                listed=pid in group.members())
        except OSError as error:
            return dict(state=classification(error), owned=None, listed=None)
    cgroup_before = membership()
    numeric = {name: link(Path('/proc', str(pid), name)) for name in ('exe', 'root')}
    anchored = {name: link(name, directory=directory) for name in ('exe', 'root')}
    after, after_state = fresh_identity(directory, pid)
    same = before == after == bound
    cgroup_after = membership()
    result = dict(case=mode, numeric_links=numeric, anchored_links=anchored,
        anchored_identity_consistent=same, leader_zombie=state == after_state == b'Z',
        whole_process_terminal_when_sampled=terminal(pidfd),
        cgroup_before_links=cgroup_before, cgroup_after_links=cgroup_after)
    require(same)
    return result

def run_case(mode, progress):
    ready_r = ready_w = release_r = release_w = None
    pid = pidfd = directory = None
    group = None
    try:
        progress['phase'] = 'CREATE_GROUP'
        group = worker.OwnedMemoryGroup()
        progress['phase'] = 'PIPES'
        ready_r, ready_w = os.pipe()
        release_r, release_w = os.pipe()
        # Own unreaped fork PID cannot be recycled before our actual waitpid.
        require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL)
        progress['phase'] = 'FORK'
        pid = os.fork()
        if pid == 0:
            try:
                os.close(ready_r)
                os.close(release_w)
                child(mode, ready_w, release_r)
            finally:
                # Child must never unwind into parent's group/receipt cleanup.
                os._exit(94)
        os.close(ready_w); ready_w = None
        os.close(release_r); release_r = None
        wait_for(lambda: worker.stopped(pid))
        progress['phase'] = 'JOIN'
        group.join(pid)
        progress['phase'] = 'ANCHOR'
        directory = os.open('/proc/' + str(pid), os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        require(stat.S_ISDIR(os.fstat(directory).st_mode) and not os.get_inheritable(directory))
        before, _ = fresh_identity(directory, pid)
        pidfd = os.pidfd_open(pid, 0)
        after, _ = fresh_identity(directory, pid)
        require(before == after and not os.get_inheritable(pidfd))
        progress['phase'] = 'READY'
        os.kill(pid, signal.SIGCONT)
        require(bool(select.select([ready_r], [], [], 3)[0]) and os.read(ready_r, 1) == b'R')
        if mode == 'DEAD_LEADER_LIVE_THREAD':
            wait_for(lambda: fresh_identity(directory, pid)[1] == b'Z')
        progress['phase'] = 'INITIAL_SAMPLE'
        initial = sample(mode, pid, directory, pidfd, before, group)
        require(initial['whole_process_terminal_when_sampled'] is False)
        if mode == 'DEAD_LEADER_LIVE_THREAD':
            require(initial['leader_zombie'] is True)
        else:
            require(initial['cgroup_before_links']['owned'] is True and
                    initial['cgroup_after_links']['owned'] is True)
        if mode in ('WHOLE_PROCESS_EXITED', 'ANCHORED_AFTER_REAP'):
            os.write(release_w, b'X')
            wait_for(lambda: terminal(pidfd))
            if mode == 'WHOLE_PROCESS_EXITED':
                progress['phase'] = 'EXIT_SAMPLE'
                observed = sample(mode, pid, directory, pidfd, before, group)
                require(observed['whole_process_terminal_when_sampled'] is True)
            else:
                progress['phase'] = 'REAP_SAMPLE'
                os.waitpid(pid, 0); pid = None
                try:
                    fresh_identity(directory, before[0])
                    raise ValueError('M1_PROC_REAP_ANCHOR_REBOUND')
                except OSError as error:
                    outcome = classification(error)
                    require(outcome in ('ENOENT', 'ESRCH'))
                observed = dict(case=mode, anchored_after_reap=outcome,
                    anchored_links={name: link(name, directory=directory) for name in ('exe', 'root')},
                    whole_process_terminal_when_sampled=terminal(pidfd),
                    anchored_identity_consistent=None, numeric_pid_reuse_tested=False)
        else:
            observed = initial
        progress['observed'] = observed
        return observed
    finally:
        # Only the freshly owned canonical group; cleanup must actually succeed.
        cleanup_ok = False
        try:
            if group is not None:
                group.close()
            cleanup_ok = True
        finally:
            try:
                if pid is not None:
                    reap_owned_child(pid, pidfd)
            finally:
                close_owned((directory, pidfd, ready_r, ready_w, release_r, release_w))
        progress['cleanup_completed'] = cleanup_ok

def run():
    require(sys.platform == 'linux' and os.getuid() == 0)
    require(hashlib.sha256(Path(worker.__file__).read_bytes()).hexdigest() == WORKER_SHA)
    observations = []
    for mode in CASES:
        progress = dict(case=mode, phase='CREATE_GROUP', observed=None, cleanup_completed=False)
        try:
            observations.append(run_case(mode, progress))
        except BaseException as error:
            return dict(schema=SCHEMA, question='PROC_LINK_ACCESS_VERSUS_SAME_ACTOR_LIFECYCLE',
                evidence_kind='CONTROLLED_LINUX_KERNEL_NOT_NATIVE_RENDER', worker_sha256=WORKER_SHA,
                observations=observations, passed=False, render_passed=False, accepted=False,
                product_accepted=False, failed_case=mode, failed_phase=progress['phase'],
                last_observed=progress['observed'], cleanup_completed=progress['cleanup_completed'],
                error_code=classification(error))
    # Kernel facts, not monitor policy. No terminal row grants successful
    # browser admission, maps/reservation evidence or actual-paint acceptance.
    require(len(observations) == 5)
    by_case = {row['case']: row for row in observations}
    live = by_case['LIVE_DUMPABLE']
    non = by_case['LIVE_NONDUMPABLE']
    contrast = (all(value == 'READABLE' for value in live['anchored_links'].values()) and
        any(value in ('EACCES', 'EPERM') for value in non['anchored_links'].values()) and
        all(value != 'UNKNOWN' for value in non['anchored_links'].values()))
    return dict(schema=SCHEMA, question='PROC_LINK_ACCESS_VERSUS_SAME_ACTOR_LIFECYCLE',
        evidence_kind='CONTROLLED_LINUX_KERNEL_NOT_NATIVE_RENDER', worker_sha256=WORKER_SHA,
        observations=observations, controls_completed=True, access_contrast_observed=contrast,
        passed=contrast, render_passed=False, accepted=False,
        access_denial_cases=[r['case'] for r in observations if any(
            v in ('EACCES', 'EPERM') for v in r.get('anchored_links', {}).values())],
        product_accepted=False, source_semantics_changed=False,
        ownership_cleanup='CANONICAL_FRESH_OWNED_CGROUP_CLOSED_ON_EVERY_CASE')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = run()
    except BaseException:
        # Never exception-stringify a kernel error or expose proc paths/IDs.
        receipt = dict(schema=SCHEMA, question='PROC_LINK_ACCESS_VERSUS_SAME_ACTOR_LIFECYCLE',
            passed=False, safe_code='M1_PROC_LIFECYCLE_CONTROL_REJECTED',
            observations=[], render_passed=False, accepted=False, product_accepted=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(schema=SCHEMA, passed=receipt['passed'], cases=len(receipt['observations']))))
    return 0 if receipt['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
