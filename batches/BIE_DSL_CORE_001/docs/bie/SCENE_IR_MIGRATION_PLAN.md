# Scene IR Migration Plan
1. Preserve current `scene_dsl.py` only as a legacy adapter during migration.
2. Introduce SceneDocument/Scene/SceneElement contracts beside it.
3. Visual Director emits Scene IR; Animation Director enriches semantic animation tracks.
4. Remotion compiler consumes Scene IR through a capability registry.
5. Existing five-pane output becomes, at most, one optional layout strategy/component—not the default architecture.
6. Characterization tests protect current rendering while new multi-domain golden scenes are added.
7. Remove legacy Scene DSL only after representative physics, biology, history/geography and mathematics scenes compile/render and pass QA.
