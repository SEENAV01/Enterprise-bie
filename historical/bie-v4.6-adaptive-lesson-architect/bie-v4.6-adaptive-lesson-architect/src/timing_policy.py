def timing_requirements(block, content_complexity=0.5):
    # No fixed duration is imposed. This produces relative requirements for
    # the downstream audio/script/timeline engine.
    base={
      "HOOK":1.0,"OBJECTIVE":0.7,"PREREQUISITE_RECALL":1.0,
      "INTUITION":1.4,"CORE_EXPLANATION":1.6,"MECHANISM":1.8,
      "DERIVATION":2.2,"WORKED_EXAMPLE":1.8,"APPLICATION":1.8,
      "COMPARISON":1.6,"MISCONCEPTION_CHECK":1.5,
      "GUIDED_PRACTICE":2.0,"RECAP":1.0,"ASSESSMENT":1.5
    }
    return {"relative_weight":base.get(block["type"],1.0)*
            (0.7+content_complexity),
            "duration_source":"DOWNSTREAM_AUDIO_AND_CONTENT_MODEL"}
