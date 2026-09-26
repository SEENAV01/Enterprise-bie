# Director architecture

Dependency flow:
StrategyDecision -> objective/mastery/misconception maps -> mechanic selection -> level sequencing -> difficulty/feedback/hints/scoring/adaptation -> DirectorPlan.

The planner is a composition layer, not a monolithic heuristic. Capability modules remain separately testable and evidence-bearing.
