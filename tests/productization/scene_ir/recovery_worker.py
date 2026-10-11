"""Bounded test-only real process loss/recovery, never a production worker mode."""
import argparse
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
PHASES = ('after_SCENE_IR_private_publication', 'after_SCENE_IR_terminal')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--phase', choices=PHASES)
    parser.add_argument('--recover', action='store_true')
    args = parser.parse_args()
    from apps.operator.process_limits import PdfProcessBudget, enforce_current_process
    from apps.operator.contracts import Credentials, Principal
    from apps.operator.service import Service
    from apps.operator.scene_ir_producer import SceneIRProducerControlPlane
    from bie.productization.scene_ir_contract import PROFILE
    enforce_current_process(PdfProcessBudget())
    credentials = Credentials()
    p = Principal('crash036-test', 'local', frozenset({'read', 'worker', 'admin_recover'}), time.time()+60)
    credentials.grant(os.environ.get('BIE_OPERATOR_TOKEN', ''), p)
    port = SceneIRProducerControlPlane(Service(args.root, credentials), enabled_profiles={PROFILE})
    if args.recover:
        port.recover(p, args.run)
        result = port.work_once(p, args.run)
        return 0 if result['stages']['SCENE_IR'] == 'SUCCEEDED' else 2
    def fault(phase):
        if phase == args.phase:
            os._exit(73)  # Actual OS exit, no Python exception/finally simulation.
    port.work_once(p, args.run, fault=fault)
    return 2  # Missing injected boundary is never a PASS.


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        print('{"code":"scene_ir_recovery_child_failed","product_accepted":false}')
        raise SystemExit(2) from None
