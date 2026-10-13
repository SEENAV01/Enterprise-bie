"""Read-only test observation of the exact pinned monitor readlink boundary.

Never an admission verdict. A process-level pidfd is sampled only when the
original readlink raises PermissionError. No PID, path, result or exception is
retained/exported. The extra syscalls have nonzero scheduling overhead.
The pidfd referent and the numeric proc path are associated non-atomically:
termination of the former does not prove the denied path's process terminated.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path, PosixPath
import os
import select
import sys
from types import BuiltinFunctionType, CodeType, FrameType, FunctionType, ModuleType

LEGACY_SCHEMA = 'bie.task036.m1.proc-link-identity-observation/1'
LEGACY_SOURCE_SHA256 = 'aeedfc527fb47df33c448ad2bf1a2553574015e3124a14e35fae1e94f75c2963'
SCHEMA = 'bie.task036.m1.proc-link-identity-observation/2'
SOURCE_SHA256 = 'dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb'
MAX_EVENTS = 32
UNKNOWN = 'UNKNOWN'
REASONS = frozenset({'NONE', 'SOURCE_UNAVAILABLE', 'KERNEL_API_UNAVAILABLE',
    'SETUP_FAILED', 'OBSERVER_FAILED', 'RESTORATION_CHANGED'})
KINDS = frozenset({'EXE', 'ROOT'})
PROVENANCE = 'PIDFD_OPEN_IMMEDIATELY_BEFORE_PINNED_MONITOR_READLINK'

def empty(reason='SOURCE_UNAVAILABLE'):
    return dict(schema=SCHEMA, provenance=PROVENANCE, source_sha256=SOURCE_SHA256,
        capture_point='AFTER_READLINK_PERMISSION_ERROR_BEFORE_ORIGINAL_RERAISE',
        scope='NONATOMIC_PIDFD_PATH_ASSOCIATION_NOT_CGROUP_ANCESTRY_OR_FINAL_PROCESS_VERDICT',
        availability='UNAVAILABLE', reason=reason if reason in REASONS else 'OBSERVER_FAILED',
        binding_verified=False, binding_restored=UNKNOWN, events=[],
        event_limit_reached=UNKNOWN, render_passed=False, accepted=False, product_accepted=False)

def is_safe(value):
    try:
        if type(value) is not dict or len(value) != len(empty()) or not all(type(k) is str for k in value) or set(value) != set(empty()): return False
        for key in ('schema', 'provenance', 'source_sha256', 'scope', 'capture_point'):
            if type(value[key]) is not str or value[key] != empty()[key]: return False
        if type(value['availability']) is not str or value['availability'] not in ('UNAVAILABLE', 'VALID', 'INVALID'): return False
        if type(value['reason']) is not str or value['reason'] not in REASONS: return False
        if type(value['binding_verified']) is not bool: return False
        if type(value['event_limit_reached']) is not bool and not (type(value['event_limit_reached']) is str and value['event_limit_reached']==UNKNOWN): return False
        if type(value['binding_restored']) is not bool and not (type(value['binding_restored']) is str and value['binding_restored'] == UNKNOWN): return False
        if any(value[k] is not False for k in ('render_passed', 'accepted', 'product_accepted')): return False
        if type(value['events']) is not list or len(value['events']) > MAX_EVENTS: return False
        if value['availability'] == 'VALID' and (not value['binding_verified'] or value['reason'] != 'NONE' or type(value['event_limit_reached']) is not bool): return False
        if value['availability'] != 'VALID' and value['reason'] == 'NONE': return False
        if value['availability'] != 'VALID' and value['events']: return False
        if value['event_limit_reached'] is True and len(value['events']) != MAX_EVENTS: return False
        for row in value['events']:
            if type(row) is not dict or len(row)!=5 or not all(type(k) is str for k in row) or set(row) != {'link_kind', 'errno_code', 'pidfd_acquired',
                    'whole_process_terminal_when_sampled', 'pidfd_closed'}: return False
            if type(row['link_kind']) is not str or row['link_kind'] not in KINDS: return False
            if type(row['errno_code']) is not str or row['errno_code'] not in ('EACCES', 'EPERM', UNKNOWN): return False
            for key in ('pidfd_acquired', 'whole_process_terminal_when_sampled', 'pidfd_closed'):
                if type(row[key]) is not bool and not (type(row[key]) is str and row[key] == UNKNOWN): return False
            if row['pidfd_acquired'] is not True and row['whole_process_terminal_when_sampled'] != UNKNOWN: return False
        return True
    except BaseException:
        return False

def monitor_request(args, kwargs):
    # Only the native expression's builtin Path value, never arbitrary PathLike,
    # strings, parent directories, frame locals or user-selected filesystem data.
    if type(args) is not tuple or type(kwargs) is not dict or len(args) != 1 or kwargs or type(args[0]) is not PosixPath: return None
    parts = args[0].parts
    if len(parts) != 4 or parts[:2] != ('/', 'proc') or parts[3] not in ('exe', 'root'): return None
    number = parts[2]
    if not 1 <= len(number) <= 10 or number[0] == '0' or any(c not in '0123456789' for c in number): return None
    pid = int(number)
    if not 0 < pid < 2**31: return None
    return pid, parts[3].upper()

def terminal_sample(fd, *, poll_factory=None, poll_in=None, poll_hup=None):
    # flags=0 pidfd denotes the entire thread group, NOT PIDFD_THREAD. No stat
    # Z/X inference, migration inference, wait/retry, signal or process mutation.
    poll_factory = select.poll if poll_factory is None else poll_factory
    poll_in = select.POLLIN if poll_in is None else poll_in
    poll_hup = select.POLLHUP if poll_hup is None else poll_hup
    poller = poll_factory()
    poller.register(fd, poll_in | poll_hup)
    rows = poller.poll(0)
    if type(rows) is not list: return UNKNOWN
    if not rows: return False
    if len(rows) != 1 or type(rows[0]) is not tuple or len(rows[0]) != 2: return UNKNOWN
    identity, flags = rows[0]
    if type(identity) is not int or identity != fd or type(flags) is not int: return UNKNOWN
    allowed = poll_in | poll_hup
    if flags <= 0 or flags & ~allowed: return UNKNOWN
    return bool(flags & allowed)

def anchored_monitor_request(args,kwargs,original):
    """Only a fixed native monitor's owned proc-directory FD, no path export.

    The extra fd-link lookup does NOT create atomic identity/ownership evidence.
    Its temporary target is parsed strictly and discarded, never retained.
    """
    if type(args) is not tuple or len(args)!=1 or type(args[0]) is not str or args[0] not in ('exe','root'):
        return None
    if type(kwargs) is not dict or set(kwargs)!={'dir_fd'} or type(kwargs['dir_fd']) is not int or not 0<=kwargs['dir_fd']<2**31:
        return None
    target=original(f'/proc/self/fd/{kwargs["dir_fd"]}')
    if type(target) is not str or not target.startswith('/proc/'):
        return None
    number=target[6:]
    if not 1<=len(number)<=10 or number[0]=='0' or not number.isascii() or not number.isdigit():
        return None
    pid=int(number)
    return (pid,args[0].upper()) if 0<pid<2**31 else None

_PINNED_SAMPLE = terminal_sample

def native_kernel_bindings():
    """Authenticate and capture native APIs once, not mutable late lookups."""
    import posix
    if sys.platform != 'linux' or type(posix) is not ModuleType or type(select) is not ModuleType:
        raise ValueError('KERNEL_API')
    opened, closed, factory = os.pidfd_open, os.close, select.poll
    for function, module, name in ((opened, 'posix', 'pidfd_open'),
            (closed, 'posix', 'close'), (factory, 'select', 'poll')):
        if (type(function) is not BuiltinFunctionType or function.__module__ != module
                or function.__name__ != name): raise ValueError('KERNEL_API')
    if opened is not posix.pidfd_open or closed is not posix.close: raise ValueError('KERNEL_API')
    if (type(select.POLLIN) is not int or select.POLLIN != 1
            or type(select.POLLHUP) is not int or select.POLLHUP != 16): raise ValueError('KERNEL_API')
    return opened, closed, factory, select.POLLIN, select.POLLHUP, _PINNED_SAMPLE

def native_frame_reader():
    function = sys._getframe
    if (type(sys) is not ModuleType or type(function) is not BuiltinFunctionType
            or function.__module__ != 'sys' or function.__name__ != '_getframe'):
        raise ValueError('FRAME_API')
    return function

class LinkObserver:
    def __init__(self, backend=None):
        self.safe = empty()
        # None is for explicit synthetic unit fixtures. The actual context always
        # supplies authenticated captured APIs; no private result is held here.
        self.backend = backend

    def failed(self):
        self.safe['availability'] = 'INVALID'
        self.safe['reason'] = 'OBSERVER_FAILED'

    def invoke(self, original, args, kwargs, request):
        if (type(request) is not tuple or len(request) != 2 or type(request[0]) is not int
                or not 0 < request[0] < 2**31 or type(request[1]) is not str or request[1] not in KINDS):
            return original(*args, **kwargs)
        fd = None
        row = None
        try:
            if self.backend is None:
                opened, close_api, sampled = os.pidfd_open, os.close, terminal_sample
            else:
                opened, close_api, factory, poll_in, poll_hup, sample = self.backend
                def sampled(value):
                    return sample(value, poll_factory=factory, poll_in=poll_in, poll_hup=poll_hup)
        except BaseException:
            return original(*args, **kwargs)
        try:
            try:
                fd = opened(request[0], 0)
                if type(fd) is not int or not 0 <= fd < 2**31: fd = None
            except BaseException:
                fd = None
            try:
                return original(*args, **kwargs)
            except BaseException as error:
                # Inspect only the builtin errno scalar, not args/message/path.
                try:
                    if type(error) is PermissionError:
                        row = dict(link_kind=request[1], errno_code=UNKNOWN,
                            pidfd_acquired=fd is not None,
                            whole_process_terminal_when_sampled=UNKNOWN, pidfd_closed=UNKNOWN)
                        if type(error.errno) is int:
                            row['errno_code'] = {13:'EACCES', 1:'EPERM'}.get(error.errno, UNKNOWN)
                        if fd is not None:
                            terminal = sampled(fd)
                            row['whole_process_terminal_when_sampled'] = terminal if type(terminal) is bool else UNKNOWN
                except BaseException: pass
                raise
        finally:
            if fd is not None:
                closed = UNKNOWN
                try: close_api(fd); closed = True
                except BaseException: pass
                if row is not None: row['pidfd_closed'] = closed
            if row is not None:
                try:
                    if len(self.safe['events']) < MAX_EVENTS: self.safe['events'].append(row)
                    else: self.safe['event_limit_reached'] = True
                except BaseException:
                    try: self.failed()
                    except BaseException: pass

    def snapshot(self):
        try:
            if not is_safe(self.safe): return empty('OBSERVER_FAILED')
            value = {key: self.safe[key] for key in empty() if key != 'events'}
            value['events'] = [{key:row[key] for key in ('link_kind', 'errno_code', 'pidfd_acquired',
                'whole_process_terminal_when_sampled', 'pidfd_closed')} for row in self.safe['events']]
            return value if is_safe(value) else empty('OBSERVER_FAILED')
        except BaseException: return empty('OBSERVER_FAILED')

def canonical_monitor():
    from bie.compiler import chromium_resource_worker as worker
    path = Path(__file__).resolve().parents[2]/'bie/compiler/chromium_resource_worker.py'
    if type(worker) is not ModuleType or Path(worker.__file__).resolve() != path.resolve(): raise ValueError('SOURCE')
    if worker.Path is not Path or worker.os is not os: raise ValueError('SOURCE')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536: raise ValueError('SOURCE')
    with path.open('rb') as stream: raw = stream.read(65537)
    if len(raw) > 65536 or sha256(raw).hexdigest() != SOURCE_SHA256: raise ValueError('SOURCE')
    code, = [c for c in compile(raw, path.resolve().as_posix(), 'exec', dont_inherit=True).co_consts
        if type(c) is CodeType and c.co_name == 'observe_frozen_member']
    function = worker.observe_frozen_member
    if (type(function) is not FunctionType or function.__module__!=worker.__name__ or
            function.__name__!='observe_frozen_member' or function.__code__ != code or
            function.__globals__ is not worker.__dict__): raise ValueError('SOURCE')
    return function.__code__, function.__globals__

@contextmanager
def observe_proc_links():
    observer = None
    original = None
    wrapper = None
    try:
        observer = LinkObserver()
        original = os.readlink
        if sys.platform != 'linux' or not hasattr(os, 'pidfd_open') or not hasattr(select, 'poll'):
            observer.safe = empty('KERNEL_API_UNAVAILABLE')
        else:
            if type(original) is not BuiltinFunctionType or original.__module__ != 'posix' or original.__name__ != 'readlink':
                raise ValueError('SOURCE')
            target, namespace = canonical_monitor()
            frame_reader = native_frame_reader()
            try:
                observer.backend = native_kernel_bindings()
            except BaseException:
                observer.safe = empty('KERNEL_API_UNAVAILABLE')
                raise ValueError('KERNEL_API')
            def readlink(*args, **kwargs):
                request = None
                try:
                    caller = frame_reader(1)
                    if (type(caller) is FrameType and caller.f_code is target
                            and caller.f_globals is namespace and caller.f_lineno in (376,377)):
                        request = monitor_request(args, kwargs)
                        if request is None:
                            request = anchored_monitor_request(args,kwargs,original)
                    del caller
                except BaseException: pass
                if request is None: return original(*args, **kwargs)
                return observer.invoke(original, args, kwargs, request)
            wrapper = readlink
            os.readlink = wrapper
            observer.safe.update(availability='VALID', reason='NONE', binding_verified=True, event_limit_reached=False)
    except BaseException:
        try:
            if observer is not None and observer.safe['reason'] != 'KERNEL_API_UNAVAILABLE':
                observer.safe = empty('SOURCE_UNAVAILABLE')
        except BaseException: pass
    try:
        yield observer
    finally:
        if wrapper is not None:
            try:
                if os.readlink is wrapper:
                    os.readlink = original
                    observer.safe['binding_restored'] = True
                else:
                    observer.safe.update(availability='INVALID', reason='RESTORATION_CHANGED', binding_restored=False)
            except BaseException:
                try: observer.failed()
                except BaseException: pass
