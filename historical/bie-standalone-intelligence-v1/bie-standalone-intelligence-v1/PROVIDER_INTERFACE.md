# Provider Interface

The BIE architecture separates the intelligence/orchestration layer from the underlying model provider.

A future adapter must implement:

- `extract_structure(source_chunk)`
- `extract_knowledge(source_chunk)`
- `resolve_relationships(knowledge_state)`
- `plan_course(book_state)`
- `plan_lessons(course_state)`
- `plan_scenes(lesson_state)`
- `plan_visuals(scene_state)`
- `generate_code(code_spec)`

The provider is replaceable; BIE state, schemas, provenance and orchestration remain stable.

**No provider/API key is embedded in this package.**
