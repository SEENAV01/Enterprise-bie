DEFAULT_HARD_FAILURES={"RENDER_BROKEN","AUDIO_MISSING","CAPTIONS_MISSING",
"SEMANTIC_CRITICAL","DIAGRAM_INVALID"}

def collect_hard_failures(results, hard_codes=None):
    hard_codes=set(hard_codes or DEFAULT_HARD_FAILURES)
    failures=[]
    for domain,result in results.items():
        for error in result.get("errors",[]):
            if error in hard_codes or any(error.startswith(c+":") for c in hard_codes):
                failures.append(f"{domain}:{error}")
    return failures
