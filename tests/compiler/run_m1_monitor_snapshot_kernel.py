"""Declared root-owned synthetic kernel proof; no browser or product witness.

Preserves the original six controls using authenticated immutable actual native
preimage bytes. Exercises the new real monitor's frozen observation/restoration.
Only closed scalar facts escape; no PID/path/command/source/exception text.
"""
import argparse
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bie.compiler import chromium_resource_worker as worker
from scripts.compiler_monitor_snapshot_amendment import validate,DIRECTORY,TARGETS
from tests.compiler import run_m1_proc_lifecycle as probe

SCHEMA='bie.task036.m1.monitor-snapshot-kernel-proof/1'
BASELINE_NAME='bie.compiler._m1_monitor_snapshot_baseline'
KINDS=('LIVE_MEMBER','BODY_REJECTION_RESTORATION','PARTIAL_FREEZE_RESTORATION')

def require(value):
    if not value:raise ValueError('M1_MONITOR_KERNEL_CONTROL_REJECTED')

def safe_exception_class(error):
    # Foreign metaclasses can spoof equality and class names. Identity-only
    # matching and fixed literals keep this surface independent of private data.
    actual=type(error)
    for expected,label in ((ValueError,'ValueError'),(PermissionError,'PermissionError'),
            (FileNotFoundError,'FileNotFoundError'),(ProcessLookupError,'ProcessLookupError'),
            (TimeoutError,'TimeoutError'),(worker.CompilerQAError,'CompilerQAError')):
        if actual is expected:return label
    return 'OTHER'

def baseline_controls():
    validate(ROOT)
    require(BASELINE_NAME not in sys.modules)
    path=ROOT/DIRECTORY/'chromium_resource_worker.py.before'
    loader=importlib.machinery.SourceFileLoader(BASELINE_NAME,str(path))
    spec=importlib.util.spec_from_loader(BASELINE_NAME,loader)
    baseline=importlib.util.module_from_spec(spec)
    original=probe.worker
    try:
        sys.modules[BASELINE_NAME]=baseline;loader.exec_module(baseline)
        require(baseline.__package__=='bie.compiler' and Path(baseline.__file__)==path)
        probe.worker=baseline
        result=probe.run()
        require(result['passed'] is True and result['controls_completed'] is True and
            result['pinned_task_removal_denial_observed'] is True and len(result['observations'])==6)
        return result
    finally:
        probe.worker=original
        if sys.modules.get(BASELINE_NAME) is baseline:del sys.modules[BASELINE_NAME]

def fresh_actor_control(kind):
    group=None;pid=pidfd=directory=None
    ready_r=ready_w=release_r=release_w=None
    progress=dict(cleanup_completed=False,phase='CREATE_GROUP')
    try:
        group=worker.OwnedMemoryGroup()
        ready_r,ready_w=os.pipe();release_r,release_w=os.pipe()
        require(signal.getsignal(signal.SIGCHLD)==signal.SIG_DFL)
        pid=os.fork()
        if pid==0:
            try:
                os.close(ready_r);os.close(release_w)
                probe.child('LIVE_DUMPABLE',ready_w,release_r)
            finally:os._exit(94)
        os.close(ready_w);ready_w=None;os.close(release_r);release_r=None
        probe.wait_for(lambda:worker.stopped(pid));group.join(pid)
        directory=os.open('/proc/'+str(pid),os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        bound,_=probe.fresh_identity(directory,pid);pidfd=os.pidfd_open(pid,0)
        require(probe.fresh_identity(directory,pid)[0]==bound)
        os.kill(pid,signal.SIGCONT)
        require(select.select([ready_r],[],[],3)[0] and os.read(ready_r,2)==b'R1')
        original_freeze=group.freeze
        injected=ValueError('M1_MONITOR_DECLARED_SYNTHETIC_FAULT')
        if kind=='PARTIAL_FREEZE_RESTORATION':
            def partial(value):
                original_freeze(value)
                if value:raise injected
            group.freeze=partial
        started=time.monotonic();progress['phase']='FROZEN_OBSERVATION'
        try:
            with worker.frozen_monitor_members(group) as members:
                require(pid in members and worker.counters(group.path/'cgroup.events')['frozen']==1)
                require(worker.observe_frozen_member(group,pid,Path('/synthetic-not-a-browser'),[]) is None)
                # Complete private map equality, never serialized or hashed for
                # export. Child cannot change maps while this leaf is frozen.
                require(worker._monitor_read(directory,'maps',2*1024**2)==
                    worker.bounded_read(Path('/proc',str(pid),'maps'),2*1024**2))
                os.write(release_w,b'X')
                time.sleep(.03)
                require(not probe.terminal(pidfd) and probe.fresh_identity(directory,pid)[0]==bound)
                if kind=='BODY_REJECTION_RESTORATION':raise injected
        except ValueError as error:
            require(kind!='LIVE_MEMBER' and error is injected)
        finally:
            group.freeze=original_freeze
        elapsed=round((time.monotonic()-started)*1000)
        require(0<=elapsed<=6000 and worker.counters(group.path/'cgroup.events')['frozen']==0)
        if kind=='PARTIAL_FREEZE_RESTORATION':os.write(release_w,b'X')
        probe.wait_for(lambda:probe.terminal(pidfd))
        os.waitpid(pid,0);pid=None
        progress['phase']='REAPED_AFTER_RESTORATION'
        return dict(case=kind,passed=True,actual_owned_leaf=True,actual_frozen_observation=kind!='PARTIAL_FREEZE_RESTORATION',
            original_body_or_partial_error_preserved=kind!='LIVE_MEMBER',
            canonical_thaw_verified=True,whole_process_exited_after_thaw=True,
            actual_child_reaped=True,freeze_scope_ms=elapsed,
            complete_anchored_reads_match_original=kind!='PARTIAL_FREEZE_RESTORATION',
            native_test_only=True,render_passed=False,accepted=False,product_accepted=False)
    finally:
        probe.cleanup_probe(group,pid,pidfd,(directory,pidfd,ready_r,ready_w,release_r,release_w),progress)

def owned_reaper_control():
    """Both the child and its actual waitpid reaper are in the frozen leaf."""
    group=None;parent=parent_fd=child_fd=child_directory=exe_fd=None
    ready_r=ready_w=release_r=release_w=hold_r=hold_w=None
    progress=dict(cleanup_completed=False,phase='CREATE_REAPER_GROUP')
    try:
        group=worker.OwnedMemoryGroup()
        ready_r,ready_w=os.pipe();release_r,release_w=os.pipe();hold_r,hold_w=os.pipe()
        require(signal.getsignal(signal.SIGCHLD)==signal.SIG_DFL)
        parent=os.fork()
        if parent==0:
            try:
                os.close(ready_r);os.close(release_w);os.close(hold_w)
                os.kill(os.getpid(),signal.SIGSTOP)
                child=os.fork()
                if child==0:
                    try:os.read(release_r,1)
                    finally:os._exit(0)
                # Private bounded pipe only; no identifier reaches any receipt.
                os.write(ready_w,b'P'+f'{child}'.encode('ascii'))
                os.waitpid(child,0);os.write(ready_w,b'D')
                os.read(hold_r,1)
            finally:os._exit(0)
        os.close(ready_w);ready_w=None;os.close(release_r);release_r=None;os.close(hold_r);hold_r=None
        probe.wait_for(lambda:worker.stopped(parent));group.join(parent)
        parent_fd=os.pidfd_open(parent,0);os.kill(parent,signal.SIGCONT)
        require(select.select([ready_r],[],[],3)[0])
        message=os.read(ready_r,16)
        require(2<=len(message)<=11 and message[:1]==b'P' and message[1:].isdigit())
        child=int(message[1:]);message=None
        require(0<child<2**31 and {parent,child}<=group.members())
        child_directory=os.open('/proc/'+f'{child}',os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        bound,_=probe.fresh_identity(child_directory,child);child_fd=os.pidfd_open(child,0)
        require(probe.fresh_identity(child_directory,child)[0]==bound)
        exe_fd=probe.pin_executable_link(child_directory)
        require(probe.link('',directory=exe_fd)=='READABLE')
        started=time.monotonic();progress['phase']='OWNED_REAPER_FROZEN'
        with worker.frozen_monitor_members(group) as members:
            require({parent,child}<=set(members))
            require(worker.observe_frozen_member(group,parent,Path('/synthetic-not-a-browser'),[]) is None)
            require(worker.observe_frozen_member(group,child,Path('/synthetic-not-a-browser'),[]) is None)
            os.write(release_w,b'X');time.sleep(.03)
            require(not probe.terminal(child_fd) and not probe.terminal(parent_fd) and
                probe.fresh_identity(child_directory,child)[0]==bound and
                probe.link('',directory=exe_fd)=='READABLE')
        elapsed=round((time.monotonic()-started)*1000)
        require(0<=elapsed<=6000 and worker.counters(group.path/'cgroup.events')['frozen']==0)
        require(select.select([ready_r],[],[],3)[0] and os.read(ready_r,1)==b'D')
        require(probe.terminal(child_fd) and probe.link('',directory=exe_fd)=='EACCES')
        os.write(hold_w,b'X');probe.wait_for(lambda:probe.terminal(parent_fd))
        os.waitpid(parent,0);parent=None;progress['phase']='OWNED_REAPER_COMPLETED'
        return dict(case='OWNED_REAPER_AND_CHILD',passed=True,actual_owned_leaf=True,
            owned_reaper_and_child_observed=True,child_stayed_live_while_frozen=True,
            canonical_thaw_verified=True,actual_reaper_completed_after_thaw=True,
            pinned_link_after_actual_reap='EACCES',freeze_scope_ms=elapsed,
            native_test_only=True,render_passed=False,accepted=False,product_accepted=False)
    finally:
        probe.cleanup_probe(group,parent,parent_fd,(exe_fd,child_directory,child_fd,parent_fd,
            ready_r,ready_w,release_r,release_w,hold_r,hold_w),progress)

def run():
    require(sys.platform=='linux' and os.getuid()==0)
    before=validate(ROOT)
    baseline=baseline_controls()
    rows=[fresh_actor_control(kind) for kind in KINDS]+[owned_reaper_control()]
    require(len(rows)==4 and all(row['passed'] for row in rows))
    require(validate(ROOT)==before)
    return dict(schema=SCHEMA,passed=True,baseline=baseline,controls=rows,
        worker_sha256=TARGETS['bie/compiler/chromium_resource_worker.py'][-1],
        security_policy_weakened=False,resource_limits_changed=False,
        historical_painter_cause='UNKNOWN',render_passed=False,accepted=False,product_accepted=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:receipt=run()
    except BaseException as error:
        receipt=dict(schema=SCHEMA,passed=False,exception_class=safe_exception_class(error),
            safe_code='M1_MONITOR_KERNEL_CONTROL_REJECTED',historical_painter_cause='UNKNOWN',
            render_passed=False,accepted=False,product_accepted=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(schema=SCHEMA,passed=receipt['passed'])))
    return 0 if receipt['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
