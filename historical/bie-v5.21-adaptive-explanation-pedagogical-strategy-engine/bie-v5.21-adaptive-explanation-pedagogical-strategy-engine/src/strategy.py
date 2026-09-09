def strategy(strategy_id,explanation_depth="ADAPTIVE",
            analogy_policy="WHEN_USEFUL",visual_modality="BEST_FIT",
            practice_density="ADAPTIVE",retrieval_interval=None,
            pacing="CONTENT_DRIVEN"):
    return {"strategy_id":strategy_id,
            "explanation_depth":explanation_depth,
            "analogy_policy":analogy_policy,
            "visual_modality":visual_modality,
            "practice_density":practice_density,
            "retrieval_interval":retrieval_interval,
            "pacing":pacing}
