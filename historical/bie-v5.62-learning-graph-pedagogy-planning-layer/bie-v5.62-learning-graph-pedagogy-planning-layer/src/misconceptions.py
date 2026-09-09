def misconception(misconception_id,statement,
                   target_concept,diagnostic_signals=None,
                   remediation=None,evidence_refs=None):
    return {"misconception_id":misconception_id,
            "statement":statement,"target_concept":target_concept,
            "diagnostic_signals":diagnostic_signals or [],
            "remediation":remediation or [],
            "evidence_refs":evidence_refs or []}
