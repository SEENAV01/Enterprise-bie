"""Run only bundled fixed probes in a disposable child. No generic code launcher."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys,tempfile,time,uuid
from ..release_v2.contracts import ContractError,sha256,canonical_bytes
from ..source_v2.codec import loads
from .models import PROBES,CONTROLS

def collect_boundary(snapshot_digest,*,timeout=8):
    sha256(snapshot_digest,'snapshot_digest')
    if type(timeout) is not int or not 1<=timeout<=15:raise ContractError('SEC_PROBE_TIMEOUT_BOUND')
    worker=Path(__file__).with_name('boundary_worker.py');worker_hash=hashlib.sha256(worker.read_bytes()).hexdigest()
    execution_id='sec-'+uuid.uuid4().hex;started=int(time.time());processes=[];observations=[]
    with tempfile.TemporaryDirectory(prefix='bie-sec-boundary-') as d:
        outer=Path(d);canary=outer/'outside-canary.txt';canary.write_bytes(b'SYNTHETIC-OUTSIDE-CANARY-NOT-A-SECRET\n');before=canary.read_bytes()
        for case in ('standard','file_limit','descriptor_limit'):
            jail=outer/case;jail.mkdir(mode=0o755);os.chmod(jail,0o755)
            inp=jail/'inputs';out=jail/'outputs';inp.mkdir(mode=0o755);out.mkdir(mode=0o700)
            (inp/'input.txt').write_bytes(b'BIE-DIAGNOSTIC-INPUT\n');os.chmod(inp/'input.txt',0o444)
            # Deliberate diagnostic link points only at the synthetic parent canary.
            (inp/'outside-link').symlink_to(canary)
            if os.geteuid()==0:os.chown(out,65534,65534)
            nonce=uuid.uuid4().hex
            env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','BIE_DIAGNOSTIC_SENTINEL':'SYNTHETIC-NOT-A-SECRET'}
            t0=time.monotonic();p=None
            try:
                p=subprocess.Popen([sys.executable,'-I','-S','-B',str(worker),str(jail),case,nonce],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=outer,env=env,close_fds=True,start_new_session=True)
                stdout,stderr=p.communicate(timeout=timeout)
                if len(stdout)>65536 or len(stderr)>65536:raise ContractError('SEC_PROBE_OUTPUT_LIMIT')
                row=loads(stdout)
                if row.get('nonce')!=nonce or row.get('case')!=case:raise ContractError('SEC_PROBE_NONCE_MISMATCH')
                processes.append(dict(case=case,execution_id=execution_id+'-'+case,exit_code=p.returncode,elapsed_ms=int((time.monotonic()-t0)*1000),stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest(),stdout=stdout.decode(),stderr=stderr.decode(),receipt=row))
                observations.extend(row.get('observations',[]))
            except (subprocess.TimeoutExpired,ContractError,ValueError) as exc:
                if p and p.poll() is None:
                    import signal
                    os.killpg(p.pid,signal.SIGKILL);p.communicate()
                processes.append(dict(case=case,execution_id=execution_id+'-'+case,exit_code=None,error=type(exc).__name__,elapsed_ms=int((time.monotonic()-t0)*1000),receipt=dict(status='NOT_RUN',controls={},observations=[])))
        unchanged=canary.read_bytes()==before
    ok=unchanged and len(observations)==len(PROBES) and {x['probe'] for x in observations}==set(PROBES) and all(x['passed'] for x in observations) and all(x['exit_code']==0 and x['receipt']['status']=='CHECKS_PASSED' for x in processes)
    result=dict(schema_version='bie.qa.sandbox-diagnostics/1',execution_id=execution_id,snapshot_digest=snapshot_digest,
        started_at=started,finished_at=int(time.time()),worker_sha256=worker_hash,interpreter_sha256=hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),
        profile='LINUX_CHROOT_SECCOMP_FIXED_PROBES_V1',platform=platform.platform(),processes=processes,observations=observations,
        outside_canary_unchanged=unchanged,status='CHECKS_PASSED' if ok else 'BLOCKED',candidate_executed=False,product_accepted=False)
    if hashlib.sha256(worker.read_bytes()).hexdigest()!=worker_hash:raise ContractError('SEC_PROBE_WORKER_CHANGED')
    return result
