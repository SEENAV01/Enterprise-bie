from __future__ import annotations
from dataclasses import dataclass
from .contracts import DirectorPlan
from .studio_policy import StudioPolicyResult
from ..canonical import fingerprint
from ..errors import GameContractError

@dataclass(frozen=True)
class DirectorReceipt:
    schema_version:str; plan_id:str; plan_fingerprint:str; strategy_fingerprint:str; component_fingerprints:tuple[tuple[str,str],...]; studio_policy_fingerprint:str; receipt_fingerprint:str; deterministic:bool=True; product_accepted:bool=False
    def validate(self):
        if self.schema_version!='bie.game.director-receipt/1':raise GameContractError('GAME_DIR_RECEIPT_SCHEMA')
        if self.deterministic is not True or self.product_accepted is not False:raise GameContractError('GAME_DIR_RECEIPT_BOUNDARY')
        if not self.component_fingerprints:raise GameContractError('GAME_DIR_RECEIPT_COMPONENTS')
        return self

def create_director_receipt(plan:DirectorPlan,policy:StudioPolicyResult):
    plan.validate();policy.validate()
    components=(('objectives',fingerprint(plan.objective_assignments)),('mechanics',fingerprint(plan.mechanic_assignments)),('misconceptions',fingerprint(plan.misconception_assignments)),('mastery',fingerprint(plan.mastery_targets)),('levels',fingerprint(plan.levels)),('difficulty',fingerprint(plan.difficulty)),('feedback',fingerprint(plan.feedback)),('hints',fingerprint(plan.hints)),('scoring',fingerprint(plan.scoring)),('adaptations',fingerprint(plan.adaptations)))
    material={'plan_id':plan.plan_id,'plan_fingerprint':plan.plan_fingerprint,'strategy_fingerprint':plan.strategy_fingerprint,'components':components,'studio_policy_fingerprint':policy.policy_fingerprint}
    return DirectorReceipt('bie.game.director-receipt/1',plan.plan_id,plan.plan_fingerprint,plan.strategy_fingerprint,components,policy.policy_fingerprint,fingerprint(material),True,False).validate()
