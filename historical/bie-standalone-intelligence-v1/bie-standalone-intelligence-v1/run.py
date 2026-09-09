#!/usr/bin/env python3
import argparse
from bie.pipeline import BIEPipeline

def main():
    ap=argparse.ArgumentParser(
        description="BIE: Book/PDF -> video-generation code intelligence"
    )
    ap.add_argument("--book", required=True, help="Path to the source PDF/book")
    ap.add_argument("--workspace", default="output")
    args=ap.parse_args()
    state=BIEPipeline(args.workspace).initialize(args.book)
    print("BIE initialized")
    print("Input:", state["book_path"])
    print("Boundary:", state["boundary"])
    print("Stages:", " -> ".join(state["stages"]))

if __name__ == "__main__":
    main()
