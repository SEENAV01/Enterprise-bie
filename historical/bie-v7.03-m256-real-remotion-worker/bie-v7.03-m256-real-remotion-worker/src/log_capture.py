def capture_output(stream, text, level="INFO"):
    return {"stream":stream,"level":level,"text":text}

def summarize_output(events):
    return {"stdout":[e for e in events if e["stream"]=="stdout"],
            "stderr":[e for e in events if e["stream"]=="stderr"],
            "error_count":sum(1 for e in events if e["level"]=="ERROR")}
