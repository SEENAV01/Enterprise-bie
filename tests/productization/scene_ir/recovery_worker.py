"""Bounded test-only real process loss/recovery, never a production worker mode."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
PHASES = ('after_SCENE_IR_private_publication', 'after_SCENE_IR_terminal')
_ROOT = None
_PHASE = 'START'
_BOUNDARY = 'UNKNOWN'
_MODE = 'CRASH'


def report(code, exc=None, state='UNKNOWN'):
    # Fixed test-owned safe receipt, not captured stdout/stderr or a private
    # native exception message. Evidence failure never changes the operation.
    try:
        from tests.productization.scene_ir.recovery_observations import child_cpu_guard, write_guard, CLASSES
        name = type(exc).__name__ if exc is not None else 'NONE'
        name = name if name in CLASSES else 'UNKNOWN'
        if _ROOT is not None:
            cpu = time.process_time()
            cpu_ms = int(cpu * 1000) if type(cpu) is float and 0 <= cpu <= 60 else None
            write_guard(_ROOT, child_cpu_guard(_PHASE, _BOUNDARY, code, name, state, _MODE,
                process_cpu_ms=cpu_ms))
    except Exception:
        pass


def main():
    global _ROOT, _PHASE, _BOUNDARY, _MODE
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--phase', choices=PHASES)
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    _ROOT = args.root
    _MODE = 'RECOVER' if args.recover else 'CRASH'
    from apps.operator.process_limits import PdfProcessBudget, enforce_current_process
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
    from bie.productization.scene_ir_contract import PROFILE
    _PHASE = 'ENFORCE'
    enforce_current_process(PdfProcessBudget())
    credentials = Credentials()
    p = Principal('crash036-test', 'local', frozenset({'read', 'worker', 'admin_recover'}), time.time()+60)
    credentials.grant(os.environ.get('BIE_OPERATOR_TOKEN', ''), p)
    port = SceneIRProducerControlPlane(Service(args.root, credentials), enabled_profiles={PROFILE})
    if args.recover:
        _PHASE = 'RECOVERY'
        report('CHILD_OPERATION_STARTED')
        port.recover(p, args.run)
        _PHASE = 'WORK'
        report('CHILD_OPERATION_STARTED')
        result = port.work_once(p, args.run)
        report('CHILD_RECOVERED' if result['stages']['SCENE_IR'] == 'SUCCEEDED' else 'CHILD_RECOVERY_INCOMPLETE',
               state=result['stages']['SCENE_IR'])
        return 0 if result['stages']['SCENE_IR'] == 'SUCCEEDED' else 2
    def fault(phase):
        global _BOUNDARY
        try:
            from tests.productization.scene_ir.recovery_observations import BOUNDARIES
            if phase in BOUNDARIES:
                _BOUNDARY = phase
        except Exception:
            pass  # Optional bookkeeping cannot prevent the original exit.
        if phase == args.phase:
            report('CHILD_EXIT_BOUNDARY_REACHED')
            os._exit(73)  # Actual OS exit, no Python exception/finally simulation.
    _PHASE = 'WORK'
    result = port.work_once(p, args.run, fault=fault)
    report('CHILD_STAGE_RETURNED', state=result['stages']['SCENE_IR'])
    return 2  # Missing injected boundary is never a PASS.


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        report('CHILD_EXCEPTION', exc)
        print('{"code":"scene_ir_recovery_child_failed","product_accepted":false}')
        raise SystemExit(2) from None
