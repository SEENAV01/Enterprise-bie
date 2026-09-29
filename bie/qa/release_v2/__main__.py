"""Read-only preview CLI. It never loads trust keys from the candidate or grants release."""
from __future__ import annotations
import argparse
import json
import sys
from .codec import load
from .contracts import ContractError
from .evaluator import ReleaseEvaluator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", help="Section 16 v2 evidence-bundle JSON")
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--as-of", required=True, type=int, help="Explicit UTC epoch seconds for replay")
    args = parser.parse_args(argv)
    try:
        report = ReleaseEvaluator().evaluate(load(args.bundle), args.artifact_root, as_of=args.as_of)
        print(report.to_bytes().decode("utf-8"))
        return 2  # Preview has no authorized trust source, and can never authorize release.
    except (ContractError, OSError) as exc:
        code = exc.code if isinstance(exc, ContractError) else "INPUT_READ_FAILED"
        print(json.dumps({"release_status": "BLOCKED", "release_authorized": False,
                          "product_accepted": False, "diagnostic": code}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
