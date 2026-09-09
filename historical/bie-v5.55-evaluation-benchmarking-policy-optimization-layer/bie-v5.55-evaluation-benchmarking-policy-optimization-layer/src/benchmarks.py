def benchmark(benchmark_id,suite_ref,target_ref,
              results=None,baseline=None):
    return {"benchmark_id":benchmark_id,"suite_ref":suite_ref,
            "target_ref":target_ref,"results":results or [],
            "baseline":baseline}

def relative_improvement(value,baseline,higher_is_better=True):
    if baseline in (None,0): return None
    return ((value-baseline)/abs(baseline)
            if higher_is_better else
            ((baseline-value)/abs(baseline)))
