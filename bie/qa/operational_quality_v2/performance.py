"""HARD033 authoritative workload accounting and delegated cgroup-v2 control.

Sampled process-group RSS is explicitly a lower-bound observation, not an
aggregate enforcement certificate. Kernel cgroup metrics require an actual
cgroup2 filesystem and a fresh, operator-delegated child group. No fallback.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
from fractions import Fraction
import ctypes,os,time,signal
from .common import *

@dataclass(frozen=True)
class AggregateLimits:
    memory_bytes:int=256*1024*1024
    processes:int=32
    max_jobs:int=16
    max_queue_ns:int=10_000_000_000
    def __post_init__(self):
        integer(self.memory_bytes,'memory',16*1024*1024,16*1024**3)
        integer(self.processes,'processes',1,512);integer(self.max_jobs,'jobs',1,10000)
        integer(self.max_queue_ns,'queue',1,3600*1_000_000_000)
    @property
    def content_digest(self):return digest(asdict(self))


def _cgroup2(path):
    require(os.name=='posix' and Path('/proc/self/mountinfo').exists(),'H7_CGROUP_PLATFORM')
    buf=ctypes.create_string_buffer(512);lib=ctypes.CDLL(None,use_errno=True)
    require(lib.statfs(os.fsencode(path),buf)==0,'H7_CGROUP_STATFS')
    magic=ctypes.cast(buf,ctypes.POINTER(ctypes.c_long))[0]
    require(magic==0x63677270,'H7_NOT_CGROUP2')

class CgroupScope:
    """Only mutates a fresh child of the explicitly supplied delegated parent."""
    def __init__(self,parent,limits=AggregateLimits()):
        self.parent=real_dir(parent);self.limits=limits;self.path=None;self.joined=[]
        require(type(limits) is AggregateLimits,'H7_CGROUP_POLICY');_cgroup2(self.parent)
        require({'memory','pids'}<=set((self.parent/'cgroup.controllers').read_text().split()),'H7_CGROUP_CONTROLLERS')
    def __enter__(self):
        path=self.parent/('bie-qa-'+new_id())
        try:path.mkdir(mode=0o700)
        except OSError as exc:raise ContractError('H7_CGROUP_DELEGATION_UNAVAILABLE') from exc
        self.path=path
        try:
            for name,value in (('memory.max',str(self.limits.memory_bytes)),('memory.swap.max','0'),('memory.oom.group','1'),('pids.max',str(self.limits.processes))):
                (path/name).write_text(value)
                require((path/name).read_text().strip()==value,'H7_CGROUP_LIMIT_READBACK')
            for name in ('memory.peak','memory.current','memory.events','cgroup.kill','cgroup.events'):
                require((path/name).exists(),'H7_CGROUP_REQUIRED_COUNTER')
            require(not (path/'cgroup.procs').read_text().strip(),'H7_CGROUP_NOT_FRESH')
        except BaseException:
            try:self.__exit__(None,None,None)
            except (OSError,ContractError):pass
            raise
        return self
    def join(self,pid):
        integer(pid,'pid',1);require(self.path is not None,'H7_CGROUP_NOT_OPEN')
        (self.path/'cgroup.procs').write_text(str(pid))
        require(str(pid) in (self.path/'cgroup.procs').read_text().split(),'H7_CGROUP_MEMBERSHIP')
        self.joined.append(pid)
    def measure(self):
        require(self.path is not None,'H7_CGROUP_NOT_OPEN');_cgroup2(self.path)
        raw={n:(self.path/n).read_text() for n in ('memory.peak','memory.current','memory.max','pids.max','memory.events','cgroup.events')}
        return dict(schema_version='bie.qa.cgroup-measurement/1',cgroup_id=self.path.name,kernel_cgroup2=True,
            joined_pids=self.joined[:],raw=raw,memory_peak_bytes=int(raw['memory.peak']),memory_limit_bytes=int(raw['memory.max']),
            capture_ns=time.monotonic_ns(),gpu_memory_measured=False,product_accepted=False)
    def __exit__(self,*args):
        if self.path is not None:
            try:
                (self.path/'cgroup.kill').write_text('1')
                deadline=time.monotonic()+3
                while 'populated 1' in (self.path/'cgroup.events').read_text() and time.monotonic()<deadline:time.sleep(.01)
                require('populated 1' not in (self.path/'cgroup.events').read_text(),'H7_CGROUP_CLEANUP_FAILED')
                self.path.rmdir()
            finally:self.path=None


def observe_group(pgid):
    """One complete /proc scan. PIDs may race; reports a sample, never a peak."""
    integer(pgid,'pgid',1);rows=[];page=os.sysconf('SC_PAGE_SIZE')
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():continue
        try:
            fields_= (entry/'stat').read_text().rsplit(')',1)[1].split()
            if int(fields_[2])!=pgid:continue
            rss=int((entry/'statm').read_text().split()[1])*page
            rows.append(dict(pid=int(entry.name),start_ticks=int(fields_[19]),rss_bytes=rss))
        except (OSError,ValueError,IndexError):continue
    return dict(pgid=pgid,captured_ns=time.monotonic_ns(),processes=sorted(rows,key=lambda r:r['pid']),
        sampled_rss_sum=sum(r['rss_bytes'] for r in rows),aggregate_enforced=False,observation_only=True)


def evaluate_workload(expected_jobs,records,limits,*,binding,cgroup=None):
    require(type(limits) is AggregateLimits,'H7_PERF_LIMITS');exact_ids(expected_jobs,'H7_JOB_IDS')
    require(len(expected_jobs)<=limits.max_jobs,'H7_JOB_BUDGET')
    require(type(records) is list and records,'H7_JOB_RECORDS')
    ids_=[r['job_id'] for r in records];require(set(ids_)==set(expected_jobs) and len(ids_)==len(set(ids_)),'H7_JOB_CENSUS')
    errors=[];latency=[];wait=[];starts=[];ends=[];execution_ids=[];valid=0
    for r in records:
        fields(r,('job_id','execution_id','submitted_ns','started_ns','finished_ns','exit_code','output_verified'),'H7_JOB_FIELDS')
        for k in ('submitted_ns','started_ns','finished_ns'):integer(r[k],k)
        require(r['submitted_ns']<=r['started_ns']<r['finished_ns'],'H7_JOB_CLOCK_ORDER')
        token(r['execution_id'],'execution_id');execution_ids.append(r['execution_id'])
        require(type(r['exit_code']) is int and type(r['output_verified']) is bool,'H7_JOB_VERDICT_TYPE')
        w=r['started_ns']-r['submitted_ns'];wait.append(w);latency.append(r['finished_ns']-r['submitted_ns']);starts.append(r['submitted_ns']);ends.append(r['finished_ns'])
        if w>limits.max_queue_ns:errors.append('H7_QUEUE_BUDGET')
        if r['exit_code']!=0 or r['output_verified'] is not True:errors.append('H7_UNVERIFIED_JOB')
        else:valid+=1
    require(len(execution_ids)==len(set(execution_ids)),'H7_PERF_REPLAY')
    # This interface consumes registered validator outcomes. It cannot itself
    # certify them; no trusted caller may use a producer's self-reported flag.
    if cgroup is None:errors.append('H7_AGGREGATE_MEASUREMENT_MISSING')
    else:
        require(type(cgroup) is dict and cgroup.get('kernel_cgroup2') is True,'H7_AGGREGATE_NOT_KERNEL')
        require(cgroup.get('memory_limit_bytes')==limits.memory_bytes,'H7_AGGREGATE_LIMIT_MISMATCH')
        require(type(cgroup.get('memory_peak_bytes')) is int and cgroup['memory_peak_bytes']>=0,'H7_AGGREGATE_PEAK')
        if cgroup['memory_peak_bytes']>limits.memory_bytes:errors.append('H7_AGGREGATE_MEMORY_EXCEEDED')
        events=cgroup.get('raw',{}).get('memory.events','')
        try:ev={k:int(v) for k,v in (x.split() for x in events.splitlines())}
        except (ValueError,TypeError):raise ContractError('H7_MEMORY_EVENTS')
        require({'oom','oom_kill'}<=set(ev) and all(v>=0 for v in ev.values()),'H7_MEMORY_EVENTS_MISSING')
        if ev['oom'] or ev['oom_kill']:errors.append('H7_AGGREGATE_OOM')
    duration=max(ends)-min(starts);throughput=Fraction(valid*1_000_000_000,duration)
    p95=sorted(latency)[(95*len(latency)+99)//100-1]
    return local_report('BIE-QA-HARD-033',binding,dict(submitted=len(records),verified_outputs=valid,
        throughput_per_second=f'{throughput.numerator}/{throughput.denominator}',p95_latency_ns=p95,
        max_queue_wait_ns=max(wait),workload_duration_ns=duration,authoritative_jobs=expected_jobs),errors)
