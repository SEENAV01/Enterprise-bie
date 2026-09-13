from dataclasses import dataclass
@dataclass(frozen=True)
class LearnerProfile:
    learner_id:str; mastery:tuple[tuple[str,float],...]; preferences:tuple[str,...]=(); accessibility_needs:tuple[str,...]=()
def make_learner_profile(learner_id,mastery,preferences=(),accessibility_needs=()):
    if not learner_id.strip() or any(not c.strip() or not 0<=v<=1 for c,v in mastery.items()): raise ValueError('profile')
    return LearnerProfile(learner_id,tuple(sorted(mastery.items())),tuple(sorted(set(preferences))),tuple(sorted(set(accessibility_needs))))
