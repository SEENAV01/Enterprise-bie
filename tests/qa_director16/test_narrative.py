from dir_helpers import *

class Narrative(FixtureCase):
    def test_parent_cannot_be_removed(self):
        r=replace(self.request,scenes=change(self.request.scenes,'scene_id','s2',parent_scene_ids=()))
        self.assertCode(self.run_check(r),'narrative','DIR_SCENE_REQUIREMENT_MISMATCH')
    def test_dependent_scene_before_foundation(self):
        r=replace(self.request,routes=(Route('route-main',('s2','s1')),))
        self.assertCode(self.run_check(r),'narrative','DIR_PARENT_NOT_READY')
    def test_route_omission(self):
        r=replace(self.request,routes=(Route('route-main',('s2',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_ROUTE_MEMBERSHIP')
    def test_bad_branch_not_hidden_by_good_default(self):
        alt=RouteRequirement('route-alt',('s1','s2'),('obj-count',),('facet-definition','facet-example','facet-payoff'))
        p=replace(self.policy,routes=self.policy.routes+(alt,))
        r=replace(self.request,routes=self.request.routes+(Route('route-alt',('s2','s1')),))
        self.assertCode(self.run_check(r,p),'narrative','DIR_PARENT_NOT_READY')
    def test_two_good_routes_are_checked(self):
        alt=replace(self.policy.routes[0],route_id='route-alt')
        p=replace(self.policy,routes=self.policy.routes+(alt,))
        r=replace(self.request,routes=self.request.routes+(Route('route-alt',('s1','s2')),))
        x=self.run_check(r,p);self.assertEqual(x.status,'CHECKS_PASSED');self.assertEqual(dict(x.narrative.measurements)['routes_checked'],2)
    def test_missing_bridge(self):
        self.assertCode(self.run_check(replace(self.request,transitions=())),'narrative','DIR_TRANSITION_NOT_PRESENTED')
    def test_bridge_in_wrong_text(self):
        r=replace(self.request,transitions=(replace(self.request.transitions[0],claim_ids=('c-example',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_TRANSITION_NOT_PRESENTED')
    def test_bridge_must_be_at_scene_start(self):
        r=self.beat('b-transition',start_ms=21000,end_ms=27000)
        self.assertCode(self.run_check(r),'narrative','DIR_TRANSITION_NOT_PRESENTED')
    def test_duplicate_bridge(self):
        r=replace(self.request,transitions=self.request.transitions+(replace(self.request.transitions[0],transition_id='bridge-copy'),))
        self.assertCode(self.run_check(r),'narrative','DIR_DUPLICATE_TRANSITION')
    def test_unused_bridge(self):
        r=replace(self.request,transitions=self.request.transitions+(Transition('unused','s2','s1',('c-recap',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_UNUSED_TRANSITION')
    def test_unknown_bridge(self):
        r=replace(self.request,transitions=(Transition('bridge-12','absent','s2',('c-transition',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_TRANSITION_REFERENCE')
    def test_missing_hook(self):
        self.assertCode(self.run_check(self.beat('b-hook',role='explanation')),'narrative','DIR_ROUTE_ARC_BOUNDARY')
    def test_missing_close(self):
        self.assertCode(self.run_check(self.beat('b-recap',role='explanation')),'narrative','DIR_ROUTE_ARC_BOUNDARY')
    def test_promise_cannot_be_removed(self):
        self.assertCode(self.run_check(replace(self.request,promises=())),'narrative','DIR_PROMISE_SCOPE_MISMATCH')
    def test_promise_unknown_payoff(self):
        r=replace(self.request,promises=(replace(self.request.promises[0],payoff_beat_ids=('absent',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_PROMISE_REFERENCE')
    def test_promise_not_satisfied_by_recap(self):
        r=replace(self.request,promises=(replace(self.request.promises[0],payoff_beat_ids=('b-recap',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_PROMISE_WITHOUT_PAYOFF')
    def test_promise_not_satisfied_by_itself(self):
        r=replace(self.request,promises=(replace(self.request.promises[0],payoff_beat_ids=('b-hook',)),))
        self.assertCode(self.run_check(r),'narrative','DIR_PROMISE_WITHOUT_PAYOFF')
    def test_promise_setup_requires_problem_or_hook(self):
        self.assertCode(self.run_check(self.beat('b-hook',role='orientation')),'narrative','DIR_PROMISE_WITHOUT_PAYOFF')
    def test_mentions_not_explanations(self):
        r=replace(self.request,beats=tuple(replace(b,role='emphasis') if b.role in ('explanation','demonstration','payoff') else b for b in self.request.beats))
        self.assertCode(self.run_check(r),'narrative','DIR_ROUTE_OBJECTIVE_UNEXPLAINED')
    def test_early_recap_not_teaching(self):
        self.assertCode(self.run_check(self.beat('b-hook',role='recap')),'narrative','DIR_RECAP_BEFORE_TEACHING')
    def test_teaching_needs_objective(self):
        self.assertCode(self.run_check(self.beat('b-definition',objective_ids=())),'narrative','DIR_BEAT_OBJECTIVE_MISSING')
    def test_unapproved_objective(self):
        self.assertCode(self.run_check(self.beat('b-definition',objective_ids=('other',))),'narrative','DIR_BEAT_OBJECTIVE_OUTSIDE_SCENE')
    def test_native_cycle_rejected(self):
        r=replace(self.request,scenes=change(self.request.scenes,'scene_id','s1',parent_scene_ids=('s2',)))
        self.assertCode(self.run_check(r),'narrative','DIR_NATIVE_CONTRACT_INVALID')
