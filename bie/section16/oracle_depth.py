"""Operator-owned depth census for finite playable-game QA routes.

This checks declared branch, remediation, transfer and reset paths against the
existing finite oracle. It does not execute a browser, attest a producer, or
infer pedagogy from an action name. Runtime observation remains a separate gate.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..qa.release_v2.contracts import ContractError, token
from ..qa.game_v2.evaluator import GameResult, oracle_paths
from ..qa.game_v2.models import GamePolicy

KINDS = ('branch', 'remediation', 'transfer', 'reset')


@dataclass(frozen=True, slots=True)
class DepthRequirement:
    kind: str
    scenario_ids: tuple[str, ...]
    challenge_ids: tuple[str, ...]

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ContractError('GAME_DEPTH_KIND')
        if type(self.scenario_ids) is not tuple or not self.scenario_ids:
            raise ContractError('GAME_DEPTH_SCENARIOS')
        if type(self.challenge_ids) is not tuple:
            raise ContractError('GAME_DEPTH_CHALLENGES')
        for value in self.scenario_ids + self.challenge_ids:
            token(value, 'game-depth-id')
        if len(set(self.scenario_ids)) != len(self.scenario_ids):
            raise ContractError('GAME_DEPTH_SCENARIOS')
        if len(set(self.challenge_ids)) != len(self.challenge_ids):
            raise ContractError('GAME_DEPTH_CHALLENGES')
        expected = 0 if self.kind == 'reset' else 2 if self.kind == 'transfer' else 1
        if len(self.challenge_ids) != expected:
            raise ContractError('GAME_DEPTH_CHALLENGE_CENSUS')
        if self.kind in ('remediation', 'transfer', 'reset') and len(self.scenario_ids) != 1:
            raise ContractError('GAME_DEPTH_ROUTE_CENSUS')


@dataclass(frozen=True, slots=True)
class DepthResult:
    policy_digest: str
    findings: tuple[str, ...]
    required_transition_ids: tuple[str, ...]
    observed_transition_ids: tuple[str, ...]
    observation_status: str

    @property
    def structural_status(self):
        return 'BLOCKED' if self.findings else 'CHECKS_PASSED'

    def to_safe_dict(self):
        return {
            'policy_digest': self.policy_digest,
            'required_roles': KINDS,
            'structural_status': self.structural_status,
            'findings': self.findings,
            'required_transition_ids': self.required_transition_ids,
            'observed_transition_ids': self.observed_transition_ids,
            'observation_status': self.observation_status,
            'native_game_acceptance': False,
            'learner_mastery_proven': False,
            'product_accepted': False,
        }


def assess_oracle_depth(policy: GamePolicy, requirements: tuple[DepthRequirement, ...], *, game_result: GameResult | None = None) -> DepthResult:
    """Require explicit routes; only an independently evaluated result can observe them.

    Even a CHECKS_PASSED result is labelled bounded diagnostic evidence here:
    producer authentication, isolation and real learner outcomes are separate.
    """
    if type(policy) is not GamePolicy or type(requirements) is not tuple or len(requirements) != len(KINDS) or any(type(r) is not DepthRequirement for r in requirements):
        raise ContractError('GAME_DEPTH_INPUT')
    if {r.kind for r in requirements} != set(KINDS):
        raise ContractError('GAME_DEPTH_ROLE_CENSUS')
    if game_result is not None and type(game_result) is not GameResult:
        raise ContractError('GAME_DEPTH_RESULT_TYPE')
    if game_result is not None and (len(game_result.reports) != 4 or any(r.policy_digest != policy.content_digest for r in game_result.reports)):
        raise ContractError('GAME_DEPTH_RESULT_POLICY_MISMATCH')
    routes = oracle_paths(policy)
    targets = {x.challenge_id: x for x in policy.learning}
    findings: set[str] = set()
    required: set[str] = set()

    for requirement in requirements:
        if not set(requirement.scenario_ids) <= set(routes):
            findings.add('GAME_DEPTH_UNKNOWN_SCENARIO')
            continue
        if not set(requirement.challenge_ids) <= set(targets):
            findings.add('GAME_DEPTH_UNKNOWN_CHALLENGE')
            continue
        paths = [routes[s] for s in requirement.scenario_ids]
        chosen: list[object] = []
        if requirement.kind == 'branch':
            target = targets[requirement.challenge_ids[0]]
            success = next((t for path in paths for t in path if t.action_id in target.response_action_ids and t.after == target.success_state), None)
            failure = next((t for path in paths for t in path if t.action_id in target.response_action_ids and t.after == target.failure_state), None)
            if success is None or failure is None:
                findings.add('GAME_DEPTH_BRANCH_MISSING')
            else:
                chosen.extend((success, failure))
        elif requirement.kind == 'remediation':
            target = targets[requirement.challenge_ids[0]]
            path = paths[0]
            pairs = [(i, t) for i, t in enumerate(path) if t.action_id in target.response_action_ids]
            candidate = next(((a, b) for a in pairs for b in pairs if a[0] < b[0] and a[1].after == target.failure_state and b[1].after == target.success_state), None)
            if candidate is None:
                findings.add('GAME_DEPTH_REMEDIATION_MISSING')
            else:
                start, end = candidate[0][0], candidate[1][0]
                chosen.extend(path[start:end + 1])
        elif requirement.kind == 'transfer':
            first, second = (targets[x] for x in requirement.challenge_ids)
            if first.objective_id == second.objective_id or first.prompt_claim_id == second.prompt_claim_id:
                findings.add('GAME_DEPTH_TRANSFER_NOT_DISTINCT')
            else:
                path = paths[0]
                a = next((i for i, t in enumerate(path) if t.action_id in first.response_action_ids and t.after == first.success_state), None)
                b = next((i for i, t in enumerate(path) if a is not None and i > a and t.action_id in second.response_action_ids and t.after == second.success_state), None)
                if b is None:
                    findings.add('GAME_DEPTH_TRANSFER_MISSING')
                else:
                    chosen.extend(path[a:b + 1])
        else:
            terminal = {s.state_id for s in policy.states if s.terminal}
            reset = next((t for t in paths[0] if t.before in terminal and t.after == policy.initial_state), None)
            if reset is None:
                findings.add('GAME_DEPTH_RESET_MISSING')
            else:
                chosen.append(reset)
        required.update(t.transition_id for t in chosen)

    observed = set(game_result.covered_transition_ids) if game_result else set()
    if game_result is None:
        observation_status = 'NOT_RUN'
    elif game_result.status == 'BLOCKED' or not required <= observed:
        observation_status = 'BLOCKED'
        findings.add('GAME_DEPTH_OBSERVATION_MISSING')
    else:
        observation_status = 'BOUNDED_DIAGNOSTIC_ONLY'
    return DepthResult(policy.content_digest, tuple(sorted(findings)), tuple(sorted(required)), tuple(sorted(observed & required)), observation_status)
