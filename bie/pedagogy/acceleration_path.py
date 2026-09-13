from dataclasses import dataclass
@dataclass(frozen=True)
class AccelerationPath:
    eligible:bool; actions:tuple[str,...]; reason:str
def choose_acceleration_path(mastery,transfer_score,prerequisite_readiness):
    if any(not 0<=x<=1 for x in (mastery,transfer_score,prerequisite_readiness)): raise ValueError('scores')
    eligible=min(mastery,transfer_score,prerequisite_readiness)>=.85
    return AccelerationPath(eligible,('skip redundant review','increase transfer complexity','offer synthesis/creation task') if eligible else (), 'high demonstrated mastery' if eligible else 'threshold not met')
