# Game IR Migration Plan

1. Keep current `game_generator.py` only as a legacy characterization target.
2. Introduce revision reasoning and Game Director upstream of Game IR.
3. Replace title-keyword branches with reasoning-driven mechanic selection.
4. Compile Game IR through a versioned mechanic/component registry.
5. Preserve domain-specific mechanics as plugins, not hard-coded central branching.
6. Add runtime validation for rules, interactions, reachability, success/failure states, accessibility and learning-objective coverage.
7. Retire generic-physics fallback once representative multi-domain golden games pass.
