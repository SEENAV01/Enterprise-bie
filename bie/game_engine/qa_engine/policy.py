from dataclasses import dataclass
from .errors import GameQAError
@dataclass(frozen=True)
class GameQAPolicy:
    learning_coverage_min:float=1.0;interactive_coverage_min:float=1.0;mastery_coverage_min:float=1.0;max_nonterminal_dead_ends:int=0;accessibility_min:float=1.0;runtime_required:bool=True;min_benchmark_domains:int=8;min_benchmark_strategy_kinds:int=7;max_clone_ratio:float=.34;product_accepted:bool=False
    def validate(self):
        for v in (self.learning_coverage_min,self.interactive_coverage_min,self.mastery_coverage_min,self.accessibility_min,self.max_clone_ratio):
            if type(v) not in (int,float) or not 0<=v<=1:raise GameQAError('GAME_QA_POLICY_RATIO')
        if type(self.max_nonterminal_dead_ends) is not int or self.max_nonterminal_dead_ends<0 or type(self.min_benchmark_domains) is not int or self.min_benchmark_domains<2 or type(self.min_benchmark_strategy_kinds) is not int or self.min_benchmark_strategy_kinds<2:raise GameQAError('GAME_QA_POLICY_COUNT')
        if type(self.runtime_required) is not bool or self.product_accepted:raise GameQAError('GAME_QA_POLICY_SCOPE')
        return self
