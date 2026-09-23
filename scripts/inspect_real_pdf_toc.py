"""Safely inspect native PDF outline reconciliation without emitting titles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bie.document_intelligence.real_pdf_toc_runtime import (  # noqa: E402
    RealPdfTocRuntimeError,
    inspect_real_pdf_toc,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely inspect deterministic native PDF TOC reconciliation"
    )
    parser.add_argument("pdf", type=Path, help="path to a native-text PDF document")
    args = parser.parse_args(argv)

    try:
        result = inspect_real_pdf_toc(args.pdf.read_bytes())
    except (OSError, RealPdfTocRuntimeError) as exc:
        print(f"PDF TOC inspection failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_safe_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
