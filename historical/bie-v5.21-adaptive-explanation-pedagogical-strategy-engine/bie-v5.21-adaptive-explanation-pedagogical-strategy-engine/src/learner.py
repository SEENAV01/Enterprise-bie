def learner_profile(learner_id,level=None,goals=None,
                    mastery=None,preferences=None,language="en"):
    return {"learner_id":learner_id,"level":level,"goals":goals or [],
            "mastery":mastery or {},"preferences":preferences or {},
            "language":language}
