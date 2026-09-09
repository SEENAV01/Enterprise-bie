def reproducibility_check(declared_digest,observed_digest):
    return {"category":"REPRODUCIBILITY",
            "status":"PASS" if declared_digest==observed_digest else "FAIL",
            "declared":declared_digest,"observed":observed_digest}
