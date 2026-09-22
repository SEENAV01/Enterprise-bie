"""Safely inspect source-linked native PDF text without emitting book text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bie.document_intelligence.real_pdf_text_runtime import (  # noqa: E402
    RealPdfTextRuntimeError,
    inspect_real_pdf_text,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Safely inspect source-linked native PDF text"
    )
    parser.add_argument("pdf", type=Path, help="path to a native-text PDF document")
    args = parser.parse_args(argv)

    try:
        data = args.pdf.read_bytes()
        result = inspect_real_pdf_text(data)
    except (OSError, RealPdfTextRuntimeError) as exc:
        print(f"PDF text inspection failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.to_safe_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
