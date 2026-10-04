"""Private Windows test-job ownership, not a product sandbox or global cleanup.

The Node harness waits on stdin before launching Edge. Assignment to the private
job therefore precedes browser creation; no child can escape in a startup race.
Only our job is terminated. User browsers and profiles are never enumerated.
"""
import ctypes
from ctypes import wintypes
import os
import time


class WindowsBrowserJob:
    def __init__(self):
        if os.name!='nt':raise RuntimeError('WINDOWS_TEST_JOB_REQUIRED')
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel=kernel;self.handle=None
        kernel.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype=wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        kernel.SetInformationJobObject.restype=wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype=wintypes.BOOL
        kernel.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
        kernel.TerminateJobObject.restype=wintypes.BOOL
        kernel.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p]
        kernel.QueryInformationJobObject.restype=wintypes.BOOL
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle.restype=wintypes.BOOL
        class Basic(ctypes.Structure):
            _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),
                      ('flags',wintypes.DWORD),('min_work',ctypes.c_size_t),('max_work',ctypes.c_size_t),
                      ('active_limit',wintypes.DWORD),('affinity',ctypes.c_size_t),
                      ('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
        class IO(ctypes.Structure):
            _fields_=[(n,ctypes.c_ulonglong) for n in ('reads','writes','other','read_bytes','write_bytes','other_bytes')]
        class Extended(ctypes.Structure):
            _fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),
                      ('job_memory',ctypes.c_size_t),('peak_process_memory',ctypes.c_size_t),
                      ('peak_job_memory',ctypes.c_size_t)]
        class Accounting(ctypes.Structure):
            _fields_=[(n,ctypes.c_longlong) for n in ('user','kernel','period_user','period_kernel')]+[
                      (n,wintypes.DWORD) for n in ('faults','total','active','terminated')]
        self.Accounting=Accounting
        self.handle=kernel.CreateJobObjectW(None,None)
        if not self.handle:raise RuntimeError('WINDOWS_TEST_JOB_CREATE_FAILED')
        limits=Extended();limits.basic.flags=0x2000 # KILL_ON_JOB_CLOSE, no breakaway/handle inheritance.
        if not kernel.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            kernel.CloseHandle(self.handle);self.handle=None
            raise RuntimeError('WINDOWS_TEST_JOB_POLICY_FAILED')

    def attach(self,process):
        if not self.kernel.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(process._handle))):
            raise RuntimeError('WINDOWS_TEST_JOB_ASSIGN_FAILED')

    def close(self):
        if self.handle is None:return
        handle=self.handle;self.handle=None
        try:
            if not self.kernel.TerminateJobObject(handle,1):raise RuntimeError('WINDOWS_TEST_JOB_TERMINATE_FAILED')
            deadline=time.monotonic()+10
            while True:
                counters=self.Accounting()
                if not self.kernel.QueryInformationJobObject(handle,1,ctypes.byref(counters),ctypes.sizeof(counters),None):
                    raise RuntimeError('WINDOWS_TEST_JOB_QUERY_FAILED')
                if counters.active==0:return
                if time.monotonic()>=deadline:raise RuntimeError('WINDOWS_TEST_JOB_NOT_EMPTY')
                time.sleep(.1)
        finally:self.kernel.CloseHandle(handle)
