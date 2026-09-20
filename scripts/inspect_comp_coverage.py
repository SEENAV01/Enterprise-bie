#!/usr/bin/env python3
"""Print exact current DSL-to-compiler dispatch inventory. Missing coverage exits 2."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from bie.compiler.consumer_coverage import inspect_consumer_coverage

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path);args=ap.parse_args()
    result=inspect_consumer_coverage();text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        if args.output.is_symlink():raise ValueError('symlink output rejected')
        args.output.write_text(text,encoding='utf-8')
    else:print(text,end='')
    return 0 if result['dispatch_complete'] else 2
if __name__=='__main__':raise SystemExit(main())
