#!/usr/bin/env python3
"""Run COMP-QA-001..005 on a frozen synthetic corpus. No network/install/writeback.

Exit 0: full positive compile gates verified; 1: source QA expectation failure;
2: source checks match but full dependency/typecheck/render acceptance is incomplete.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.compiler.multidomain_compile_benchmark import load_benchmark_corpus, run_multidomain_compile_benchmark

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus', type=Path, default=root / 'fixtures/comp_h2/extended_corpus.json')
    p.add_argument('--baselines', type=Path, default=root / 'fixtures/comp_h2/baselines')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--runs', type=int, default=3)
    p.add_argument('--source-only', action='store_true', help='explicitly omit full typechecking; never returns full-compile PASS')
    args = p.parse_args()
    result = run_multidomain_compile_benchmark(load_benchmark_corpus(args.corpus),
       output_directory=args.output, baseline_directory=args.baselines, runs=args.runs,
       require_full_typecheck=not args.source_only, worker_script=root / 'scripts/qa_compile_worker.py')
    summary = {k: v for k, v in asdict(result).items() if k != 'cases'}
    print(json.dumps(summary, indent=2))
    return 0 if result.full_compile_benchmark_passed else (2 if result.source_benchmark_passed else 1)
if __name__ == '__main__':
    raise SystemExit(main())
