#!/usr/bin/env python3
import argparse
from canonical_pipeline import CanonicalBIE


def main():
    parser = argparse.ArgumentParser(description="Canonical BIE: Book/PDF -> video-generation code")
    parser.add_argument("--book", required=True, help="Path to a PDF book")
    parser.add_argument("--workspace", default="output")
    args = parser.parse_args()
    ctx = CanonicalBIE(work_dir=args.workspace).run(args.book)
    print("BIE run:", ctx.run_id)
    print("Status:", ctx.artifacts["manifest"]["status"])
    print("Generated artifacts:", ", ".join(ctx.artifacts["manifest"]["artifacts"]))


if __name__ == "__main__":
    main()
