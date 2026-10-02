"""OS-enforced local PDF process budgets; NOT a code/network sandbox.

Linux uses hard resource limits. Windows uses an unnamed Job Object, retained
until process exit. Unsupported/enforcement-denied environments fail closed.
Source: Python resource docs and Microsoft's Job Object limit contracts.
"""
from dataclasses import dataclass
import os
import sys

_JOB_HANDLES = []


@dataclass(frozen=True)
class PdfProcessBudget:
    memory_bytes: int = 1024 * 1024 * 1024
    cpu_seconds: int = 30
    wall_seconds: int = 45

    def __post_init__(self):
        ceilings = dict(memory_bytes=1024 * 1024 * 1024, cpu_seconds=30, wall_seconds=45)
        for name, maximum in ceilings.items():
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= maximum:
                raise ValueError('pdf_process_budget_invalid')


def enforce_current_process(budget):
    if type(budget) is not PdfProcessBudget:
        raise ValueError('pdf_process_budget_invalid')
    if sys.platform == 'linux':
        import resource
        for kind, maximum in ((resource.RLIMIT_AS, budget.memory_bytes),
                              (resource.RLIMIT_CPU, budget.cpu_seconds),
                              (resource.RLIMIT_CORE, 0),
                              (resource.RLIMIT_FSIZE, 64 * 1024 * 1024)):
            _, inherited = resource.getrlimit(kind)
            cap = maximum if inherited == resource.RLIM_INFINITY else min(maximum, inherited)
            resource.setrlimit(kind, (cap, cap))
        return 'LINUX_RLIMIT'
    if os.name != 'nt':
        raise RuntimeError('pdf_process_enforcement_unavailable')
    import ctypes
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                    ('flags', wintypes.DWORD), ('working_min', ctypes.c_size_t),
                    ('working_max', ctypes.c_size_t), ('active_processes', wintypes.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                    ('scheduling', wintypes.DWORD)]

    class Counters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in
                    ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]

    class Extended(ctypes.Structure):
        _fields_ = [('basic', Basic), ('io', Counters), ('process_memory', ctypes.c_size_t),
                    ('job_memory', ctypes.c_size_t), ('peak_process', ctypes.c_size_t),
                    ('peak_job', ctypes.c_size_t)]

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise RuntimeError('pdf_process_enforcement_unavailable')
    limits = Extended()
    limits.basic.flags = 0x00000002 | 0x00000008 | 0x00000100 | 0x00000200 | 0x00002000
    limits.basic.process_time = budget.cpu_seconds * 10_000_000
    limits.basic.active_processes = 1
    limits.process_memory = limits.job_memory = budget.memory_bytes
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(handle)
        raise RuntimeError('pdf_process_enforcement_unavailable')
    if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        kernel.CloseHandle(handle)
        raise RuntimeError('pdf_process_enforcement_unavailable')
    # Closing KILL_ON_JOB_CLOSE before interpreter exit would kill this process.
    # No inheritable job handle, name, breakaway flag or ambient exemption.
    _JOB_HANDLES.append(handle)
    return 'WINDOWS_JOB_OBJECT'
