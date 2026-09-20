"""Observe the existing worker; never replace its results or loosen a gate."""
from __future__ import annotations
import dataclasses
import json
import sys
import tempfile
from pathlib import Path


def diagnose(root: Path, evidence: Path) -> None:
    sys.path.insert(0, str(root))
    from bie.compiler.host_toolchain import collect_host_toolchain
    from bie.compiler.isolated_typesetting import MathWorkerLimits
    from bie.compiler.linux_worker import WorkerPolicy, run_isolated
    import sysconfig
    host = collect_host_toolchain()
    record = {
        'parent_identity': host['identity_sha256'],
        'parent_binaries': host['binaries'],
        'parent_libdir': sysconfig.get_config_var('LIBDIR'),
        'parent_executable': sys.executable,
        'diagnostic_only': True,
        'accepted': False,
    }
    with tempfile.TemporaryDirectory(prefix='bie-ci-worker-observation-') as td:
        work = Path(td)
        (work / 'out').mkdir()
        probe = work / 'host.py'
        probe.write_text(
            'import sys,json,sysconfig\n'
            'sys.path.insert(0,"/engine")\n'
            'from bie.compiler.host_toolchain import collect_host_toolchain\n'
            'h=collect_host_toolchain()\n'
            'print(json.dumps({"host":h,"libdir":sysconfig.get_config_var("LIBDIR"),"executable":sys.executable},sort_keys=True))\n'
        )
        p, k = run_isolated([sys.executable, '-I', str(probe)], workspace=work,
                            engine=root, writable=['out'], policy=WorkerPolicy(procfs=False),
                            timeout_s=45, max_output_bytes=4*1024*1024)
        record['probe_process'] = dataclasses.asdict(p)
        record['probe_kernel'] = k
        if p.process.passed:
            child = json.loads(p.process.stdout)
            record['child_libdir'] = child['libdir']
            record['child_executable'] = child['executable']
            record['child_identity'] = child['host']['identity_sha256']
            record['host_record_differences'] = {
                key: {'parent': host.get(key), 'child': child['host'].get(key)}
                for key in set(host) | set(child['host'])
                if host.get(key) != child['host'].get(key)
            }
        limits = MathWorkerLimits()
        request = {'expression': 'x^2', 'element_id': 'ci-observed-math', 'font_size': 32,
                   'expected_identity': host['identity_sha256'], 'limits': dataclasses.asdict(limits)}
        (work / 'input.json').write_text(json.dumps(request))
        p, k = run_isolated([sys.executable, '-I', str(root / 'bie/compiler/isolated_math_worker.py'),
                            str(work / 'input.json'), str(work / 'out/math.json')],
                            workspace=work, engine=root, writable=['out'],
                            policy=WorkerPolicy(procfs=False, cpu_seconds=limits.cpu_seconds,
                                address_space_bytes=limits.memory_mb*1024**2, file_bytes=limits.max_output_bytes),
                            timeout_s=limits.timeout_seconds, max_output_bytes=limits.max_output_bytes)
        record['math_process'] = dataclasses.asdict(p)
        record['math_kernel'] = k
        output = work / 'out/math.json'
        if output.is_file():
            record['math_report'] = json.loads(output.read_text())
    (evidence / 'worker-diagnostic.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('probe_process','probe_kernel','math_report')}, indent=2), flush=True)
    # No pass override: the unchanged required tests execute next.
