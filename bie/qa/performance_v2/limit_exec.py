"""Trusted-program launcher. Resource bounds, NOT a hostile-code sandbox.

Executed as a separate Python process: no unsafe threaded preexec_fn. Limits are
installed/read back, then this PID execs the operator-pinned program. Commands are
constructed by the collector, never by a receipt being audited.
"""
import os,sys,json,resource,hashlib

def main():
    path,receipt=sys.argv[1:3]
    cfg=json.load(open(path,encoding='utf-8'))
    exe=cfg['argv'][0]
    if hashlib.sha256(open(exe,'rb').read()).hexdigest()!=cfg['executable_sha256']:return 91
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    for name,value in (('RLIMIT_AS',cfg['address_space_bytes']),('RLIMIT_CPU',cfg['cpu_seconds']),('RLIMIT_FSIZE',cfg['max_file_bytes']),('RLIMIT_NOFILE',64)):
        resource.setrlimit(getattr(resource,name),(value,value))
    d={'schema_version':'bie.qa.performance-limits/1','execution_id':cfg['execution_id'],
       'address_space':list(resource.getrlimit(resource.RLIMIT_AS)),
       'file_size':list(resource.getrlimit(resource.RLIMIT_FSIZE)),
       'cpu':list(resource.getrlimit(resource.RLIMIT_CPU)),
       'nofile':list(resource.getrlimit(resource.RLIMIT_NOFILE)),
       'memory_scope':'RLIMIT_AS_PER_PROCESS_NOT_RSS_OR_CGROUP'}
    with open(receipt,'x',encoding='utf-8') as f:json.dump(d,f,sort_keys=True,separators=(',',':'))
    os.execve(exe,cfg['argv'],cfg['env'])
if __name__=='__main__':raise SystemExit(main())
