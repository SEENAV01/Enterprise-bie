"""Process at most one Section 18 operator-aware durable PDF job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bie.app_product.operator_service import OperatorJobService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one operator-aware BIE delivery")
    parser.add_argument("--once", action="store_true", help="process one job and exit")
    parser.add_argument("--worker-id", default="bie-operator-worker-local")
    args = parser.parse_args()

    service = OperatorJobService()
    try:
        outcome = service.run_once(args.worker_id)
        print(json.dumps(outcome.to_safe_dict(), sort_keys=True, separators=(",", ":")))
        return 0 if outcome.outcome in {"ACKED", "IDLE", "PAUSED", "CANCELLED"} else 1
    except Exception:
        print(json.dumps({"outcome": "FAILED"}, sort_keys=True, separators=(",", ":")))
        return 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
