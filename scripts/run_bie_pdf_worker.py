"""Run the local apps/api /v1/jobs PDF worker once or continuously.

Never point this worker at Section18 operator roots or per-run namespaces.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.job_service import PdfInspectionJobService
from apps.api.pdf_worker_service import (
    PdfInspectionWorkerService, api_worker_root, stop_on_stdin_eof, stop_signals,
)


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Invalid worker arguments\n")


def main(argv: list[str] | None = None) -> int:
    parser = SafeParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--once", action="store_true", help="process one job and exit (default)")
    modes.add_argument("--serve", action="store_true", help="continuously process apps/api jobs")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="idle seconds, 0.1 through 60")
    parser.add_argument("--worker-id", default="bie-pdf-worker-local")
    args = parser.parse_args(argv)
    stop = threading.Event()
    result = {"outcome": "FAILED"}
    exit_code = 1
    jobs = None
    try:
        with stop_signals(stop), open(os.devnull, "w", encoding="utf-8") as quiet:
            # Third-party parser logs must not disclose malformed document bytes.
            with redirect_stdout(quiet), redirect_stderr(quiet):
                root = api_worker_root()
                jobs = PdfInspectionJobService(root)
                try:
                    worker = PdfInspectionWorkerService(jobs, poll_interval=args.poll_interval,
                                                        worker_id=args.worker_id)
                    if args.serve:
                        if os.environ.get("BIE_PDF_WORKER_CONTROL_STDIN") == "1":
                            stop_on_stdin_eof(stop, sys.stdin)
                        summary = worker.run(stop)
                        result = {"outcome": "STOPPED", **summary.to_safe_dict()}
                        exit_code = 0
                    elif stop.is_set():
                        result, exit_code = {"outcome": "IDLE"}, 0
                    else:
                        outcome = jobs.run_once(args.worker_id)
                        result = outcome.to_safe_dict()
                        exit_code = 0 if outcome.outcome in {"ACKED", "IDLE"} else 1
                finally:
                    jobs.close()
    except Exception:
        result, exit_code = {"outcome": "FAILED"}, 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
