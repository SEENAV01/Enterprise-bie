"""Process at most one local durable PDF inspection job."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.job_service import PdfInspectionJobService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one local BIE PDF worker delivery")
    parser.add_argument("--once", action="store_true", help="process one job and exit (default)")
    parser.add_argument("--worker-id", default="bie-pdf-worker-local")
    args = parser.parse_args()
    service = PdfInspectionJobService()
    try:
        outcome = service.run_once(args.worker_id)
        print(json.dumps(outcome.to_safe_dict(), sort_keys=True, separators=(",", ":")))
        return 0 if outcome.outcome in {"ACKED", "IDLE"} else 1
    except Exception:
        print(json.dumps({"outcome": "FAILED"}, sort_keys=True, separators=(",", ":")))
        return 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
