"""Source-bound aggregate monitor timing; not a verdict or private receipt reader.

Native freeze calls delegate once with identical arguments/results/exceptions.
No actor identifiers, group objects, paths, commands, mappings, or errors are
retained by the observer. Timing has nonzero instrumentation overhead.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import os
import stat
import sys
import time
import threading
from types import BuiltinFunctionType, CodeType, FunctionType, FrameType, ModuleType

SCHEMA='bie.task036.m1.monitor-scheduling-observation/1'
SOURCE_SHA='dea211dec77bbda9470c9f37331d236425c5dbf7dbf73d1769e8ba83e7c6f5eb'
UNKNOWN='UNKNOWN'
SCOPES=('MONITOR','ENTRY_GRANT','CLEANUP')
FIELDS=('acquisitions','acquired','partial_acquisition_failures','thaw_requests','thaws',
    'thaw_failures','completed_scopes','acquisition_ns','held_lower_bound_ns','thaw_ns',
    'scope_upper_bound_ns','freeze_calls_parent_cpu_ns','scope_parent_cpu_ns','max_held_ns','thawed_gap_ns','thawed_gaps')
CPU=('usage_usec','user_usec','system_usec','nr_periods','nr_throttled','throttled_usec')
MAX_TIME_NS=3600*10**9
REASONS=('NONE','SOURCE_UNAVAILABLE','OBSERVER_FAILED','RESTORATION_CHANGED','RESTORATION_FAILED','UNCONFIRMED_THAW')
_WALL=time.monotonic_ns
_CPU=time.thread_time_ns
_THREAD=threading.get_ident

def native_clocks():
    for clock,name in ((_WALL,'monotonic_ns'),(_CPU,'thread_time_ns')):
        if type(clock) is not BuiltinFunctionType or clock.__module__!='time' or clock.__name__!=name or getattr(time,name) is not clock:
            raise ValueError('CLOCK_BINDING')
    return _WALL,_CPU

def native_thread_identity():
    if type(_THREAD) is not BuiltinFunctionType or _THREAD.__module__!='_thread' or _THREAD.__name__!='get_ident' or threading.get_ident is not _THREAD:
        raise ValueError('THREAD_BINDING')
    return _THREAD

def empty(reason='SOURCE_UNAVAILABLE'):
    return dict(schema=SCHEMA,source_sha256=SOURCE_SHA,
        provenance='EXACT_NATIVE_FREEZE_CALLER_CODE_AND_NAMESPACE',
        availability='UNAVAILABLE',reason=reason if type(reason) is str and reason in REASONS else 'OBSERVER_FAILED',binding_verified=False,binding_restored=UNKNOWN,
        phase='REAL_GENERATED_CONSUMER',scopes={k:{f:UNKNOWN for f in FIELDS} for k in SCOPES},
        cpu_availability='UNAVAILABLE',cpu_delta={k:UNKNOWN for k in CPU},
        cpu_scope='FIRST_OBSERVED_FREEZE_TO_CLEANUP_THAW_NOT_FINAL_GROUP_TOTAL',
        thread_scope='CURRENT_SETUP_THREAD_ONLY',
        capture_progress='NOT_OBSERVED',timing_overhead='NONZERO_NOT_QUANTIFIED',
        render_passed=False,accepted=False,product_accepted=False)

def is_safe(value):
    try:
        template=empty()
        if type(value) is not dict or any(type(k) is not str for k in value) or set(value)!=set(template):return False
        for key in ('schema','source_sha256','provenance','phase','capture_progress','timing_overhead','cpu_scope','thread_scope'):
            if type(value[key]) is not str or value[key]!=template[key]:return False
        if type(value['binding_verified']) is not bool:return False
        if not(type(value['binding_restored']) is bool or type(value['binding_restored']) is str and value['binding_restored']==UNKNOWN):return False
        if type(value['reason']) is not str or value['reason'] not in REASONS:return False
        if type(value['availability']) is not str or value['availability'] not in ('VALID','UNAVAILABLE','INVALID'):return False
        if type(value['cpu_availability']) is not str or value['cpu_availability'] not in ('VALID','UNAVAILABLE','INVALID'):return False
        if any(value[k] is not False for k in ('render_passed','accepted','product_accepted')):return False
        if type(value['scopes']) is not dict or any(type(k) is not str for k in value['scopes']) or set(value['scopes'])!=set(SCOPES):return False
        for row in value['scopes'].values():
            if type(row) is not dict or any(type(k) is not str for k in row) or set(row)!=set(FIELDS):return False
            for field,n in row.items():
                if value['availability']=='VALID':
                    if type(n) is not int or not 0<=n<=(MAX_TIME_NS if field.endswith('_ns') else 1000000):return False
                elif type(n) is not str or n!=UNKNOWN:return False
            if value['availability']=='VALID' and not(row['acquired']<=row['acquisitions'] and row['thaws']<=row['thaw_requests']):return False
        if type(value['cpu_delta']) is not dict or any(type(k) is not str for k in value['cpu_delta']) or set(value['cpu_delta'])!=set(CPU):return False
        for n in value['cpu_delta'].values():
            if not(type(n) is int and 0<=n<=10**12 or type(n) is str and n==UNKNOWN):return False
            if value['cpu_availability']!='VALID' and not(type(n) is str and n==UNKNOWN):return False
        if value['availability']=='VALID' and not(value['binding_verified'] and value['reason']=='NONE' and value['binding_restored'] is not False):return False
        if value['availability']!='VALID' and value['reason']=='NONE':return False
        return True
    except BaseException:return False

def binding():
    from bie.compiler import chromium_resource_worker as worker
    path=Path(__file__).resolve().parents[2]/'bie/compiler/chromium_resource_worker.py'
    if type(worker) is not ModuleType or Path(worker.__file__).resolve()!=path.resolve() or path.is_symlink():raise ValueError('SOURCE')
    with path.open('rb') as stream:raw=stream.read(65537)
    if sha256(raw).hexdigest()!=SOURCE_SHA or len(raw)>65536:raise ValueError('SOURCE')
    codes={c.co_name:c for c in compile(raw,str(path.resolve()),'exec',dont_inherit=True).co_consts if type(c) is CodeType}
    cls=worker.OwnedMemoryGroup
    methods={c.co_name:c for c in codes['OwnedMemoryGroup'].co_consts if type(c) is CodeType}
    if type(cls) is not type or worker.CGROOT!=Path('/sys/fs/cgroup'):raise ValueError('SOURCE')
    for name in ('__init__','members'):
        method=getattr(cls,name)
        if type(method) is not FunctionType or method.__code__!=methods[name] or method.__globals__ is not worker.__dict__:raise ValueError('SOURCE')
    functions=((worker.frozen_monitor_members.__wrapped__,codes['frozen_monitor_members'],'MONITOR'),
        (worker._grant,codes['_grant'],'ENTRY_GRANT'),(cls.close,methods['close'],'CLEANUP'))
    targets=[]
    for fn,code,kind in functions:
        if type(fn) is not FunctionType or fn.__code__!=code or fn.__globals__ is not worker.__dict__:raise ValueError('SOURCE')
        targets.append((fn.__code__,worker.__dict__,kind))
    freeze=cls.freeze
    if type(freeze) is not FunctionType or freeze.__code__!=methods['freeze'] or freeze.__globals__ is not worker.__dict__:raise ValueError('SOURCE')
    return worker,cls,freeze,tuple(targets)

def cpu_scalars(worker,group):
    """One exact owned leaf's cpu.stat; never a caller path or private output."""
    directory=fd=stream=None;failure=None
    try:
        path=group.path
        if path.parent!=worker.CGROOT or not path.name.startswith('bie-chromium-owned-') or path.is_symlink() or type(group.inode) is not int or group.inode<=0:raise ValueError('COUNTER')
        directory=os.open(path,os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        if os.fstat(directory).st_ino!=group.inode:raise ValueError('COUNTER')
        fd=os.open('cpu.stat',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('COUNTER')
        stream=os.fdopen(fd,'rb');fd=None;raw=stream.read(4097)
        if len(raw)>4096:raise ValueError('COUNTER')
        result={}
        for line in raw.decode('ascii').splitlines():
            parts=line.split()
            if parts and parts[0] in CPU:
                if len(parts)!=2:raise ValueError('COUNTER')
                key,text=parts
                if key in result or not text.isascii() or not text.isdigit() or len(text)>13:raise ValueError('COUNTER')
                number=int(text)
                if not 0<=number<=10**12:raise ValueError('COUNTER')
                result[key]=number
        if not {'usage_usec','user_usec','system_usec'}<=set(result):raise ValueError('COUNTER')
        return result
    except BaseException as error:
        failure=error
        raise
    finally:
        first=None
        if stream is not None:
            try:stream.close()
            except BaseException as error:first=error
        for opened in (fd,directory):
            if opened is not None:
                try:os.close(opened)
                except BaseException as error:
                    if first is None:first=error
        if first is not None and failure is None:raise first

class Observer:
    def __init__(self):
        self.safe=empty();self.pending={};self.cpu={};self.last_thaw={}
    def activate(self):
        self.safe.update(availability='VALID',reason='NONE',binding_verified=True)
        self.safe['scopes']={k:{f:0 for f in FIELDS} for k in SCOPES}
    def failed(self,reason='OBSERVER_FAILED'):
        prior=self.safe;self.safe=empty(reason)
        for key in ('binding_verified','binding_restored'):self.safe[key]=prior[key]
        self.safe['availability']='INVALID';self.pending.clear();self.cpu.clear();self.last_thaw.clear()
    def start(self,key,kind,value,wall,cpu):
        if type(value) is not bool or type(wall) is not int or type(cpu) is not int or wall<0 or cpu<0:raise ValueError('CLOCK')
        if len(self.pending)>=16 and key not in self.pending:raise ValueError('BOUND')
        row=self.safe['scopes'][kind]
        if row['acquisitions']>=1000000 or row['thaw_requests']>=1000000:raise ValueError('BOUND')
        if value:
            if key in self.pending:raise ValueError('NESTED')
            row['acquisitions']+=1;self.pending[key]=(kind,wall,cpu,None)
            # Track every authenticated scope: an intervening entry grant must
            # not be mislabeled as time thawed between two monitor requests.
            if key in self.last_thaw:
                gap=wall-self.last_thaw.pop(key)
                if not 0<=gap<=MAX_TIME_NS:raise ValueError('CLOCK')
                row['thawed_gap_ns']+=gap;row['thawed_gaps']+=1
        else:
            row['thaw_requests']+=1
            pending=self.pending.get(key)
            if pending:
                phase,begin,parent,held=pending
                target=self.safe['scopes'][phase]
                if held is not None:
                    duration=wall-held
                    if not 0<=duration<=MAX_TIME_NS:raise ValueError('CLOCK')
                    target['held_lower_bound_ns']+=duration
                    target['max_held_ns']=max(target['max_held_ns'],duration)
    def finish(self,key,kind,value,start,end,parent_start,parent_end,returned):
        duration=end-start;cpu=parent_end-parent_start
        if not 0<=duration<=MAX_TIME_NS or not 0<=cpu<=MAX_TIME_NS:raise ValueError('CLOCK')
        row=self.safe['scopes'][kind]
        row['freeze_calls_parent_cpu_ns']+=cpu
        if value:
            row['acquisition_ns']+=duration
            row['acquired' if returned else 'partial_acquisition_failures']+=1
            phase,begin,parent,_=self.pending[key]
            self.pending[key]=(phase,begin,parent,end if returned else None)
        else:
            row['thaw_ns']+=duration;row['thaws' if returned else 'thaw_failures']+=1
            if not returned:
                # A failed native thaw cannot end a measured frozen interval.
                # Preserve its original rejection, but discard purported bounds.
                self.failed('UNCONFIRMED_THAW')
                return
            pending=self.pending.pop(key,None)
            if pending:
                phase,begin,parent,held=pending
                target=self.safe['scopes'][phase]
                target['scope_upper_bound_ns']+=end-begin;target['completed_scopes']+=1
                if not 0<=parent_end-parent<=MAX_TIME_NS:raise ValueError('CLOCK')
                target['scope_parent_cpu_ns']+=parent_end-parent
            if returned:self.last_thaw[key]=end
    def sample_cpu(self,worker,group,key,finish=False):
        if self.safe['cpu_availability']=='INVALID':return
        try:
            if len(self.cpu)>=16 and key not in self.cpu:raise ValueError('BOUND')
            values=cpu_scalars(worker,group)
            original=self.cpu.setdefault(key,values)
            if finish:
                delta={k:values[k]-original[k] for k in CPU if k in values and k in original}
                if any(n<0 for n in delta.values()):raise ValueError('COUNTER')
                if self.safe['cpu_availability']=='UNAVAILABLE':
                    self.safe['cpu_availability']='VALID';self.safe['cpu_delta']={k:delta.get(k,UNKNOWN) for k in CPU}
                elif self.safe['cpu_availability']=='VALID':
                    for k,n in delta.items():
                        old=self.safe['cpu_delta'][k]
                        self.safe['cpu_delta'][k]=old+n if type(old) is int else UNKNOWN
                self.cpu.pop(key,None);self.last_thaw.pop(key,None)
        except BaseException:
            self.safe['cpu_availability']='INVALID';self.safe['cpu_delta']={k:UNKNOWN for k in CPU};self.cpu.pop(key,None)
    def snapshot(self):
        try:
            if not is_safe(self.safe):return empty('OBSERVER_FAILED')
            value={k:self.safe[k] for k in self.safe}
            value['scopes']={k:dict(v) for k,v in self.safe['scopes'].items()}
            value['cpu_delta']=dict(self.safe['cpu_delta'])
            return value if is_safe(value) else empty('OBSERVER_FAILED')
        except BaseException:return empty('OBSERVER_FAILED')

@contextmanager
def observe_monitor_schedule():
    observer=None;cls=original=wrapper=None
    try:
        observer=Observer();worker,cls,original,targets=binding()
        wall_clock,cpu_clock=native_clocks()
        thread_identity=native_thread_identity();owner=thread_identity()
        from tests.compiler.m1_proc_link_observation import native_frame_reader
        frame_reader=native_frame_reader()
        def wrapped(*args,**kwargs):
            captured=None
            try:
                caller=frame_reader(1)
                kind=next((k for code,namespace,k in targets if type(caller) is FrameType and caller.f_code is code and caller.f_globals is namespace),None)
                del caller
                if thread_identity()==owner and kind is not None and len(args)==2 and not kwargs and type(args[0]) is cls and type(args[1]) is bool and observer.safe['availability']=='VALID':
                    group,value=args;key=id(group)
                    if key not in observer.cpu:observer.sample_cpu(worker,group,key)
                    wall,cpu=wall_clock(),cpu_clock()
                    observer.start(key,kind,value,wall,cpu);captured=(key,kind,value,wall,cpu)
            except BaseException:
                try:observer.failed()
                except BaseException:pass
            returned=False
            try:
                result=original(*args,**kwargs);returned=True;return result
            finally:
                if captured is not None:
                    try:
                        key,kind,value,wall,cpu=captured
                        observer.finish(key,kind,value,wall,wall_clock(),cpu,cpu_clock(),returned)
                        if kind=='CLEANUP' and value is False and returned:observer.sample_cpu(worker,args[0],key,True)
                    except BaseException:
                        try:observer.failed()
                        except BaseException:pass
        wrapper=wrapped;cls.freeze=wrapper;observer.activate()
    except BaseException:pass
    try:yield observer
    finally:
        if wrapper is not None:
            try:
                if cls.freeze is wrapper:cls.freeze=original;observer.safe['binding_restored']=True
                else:observer.failed('RESTORATION_CHANGED');observer.safe['binding_restored']=False
            except BaseException:
                try:observer.failed('RESTORATION_FAILED');observer.safe['binding_restored']=False
                except BaseException:pass
        if observer is not None:
            try:
                if observer.pending and observer.safe['availability']=='VALID':observer.failed()
            except BaseException:pass
            # No transient group identifiers survive the active scope.
            for field in ('pending','cpu','last_thaw'):
                try:getattr(observer,field).clear()
                except BaseException:pass
