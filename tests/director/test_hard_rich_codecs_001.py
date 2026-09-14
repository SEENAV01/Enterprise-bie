import copy
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from bie.director.rich_teaching import GroundedWorkedExample
from bie.director.teaching_context import SourceExcerpt, load_teaching_context, publish_teaching_context
from context_fixtures import context_upstream
from completion_fixtures import excerpt, rich_context, rich_specs


class RichCodecTests(unittest.TestCase):
    def fixture(self):
        return context_upstream(Path(tempfile.mkdtemp()), 'science')

    def test_all_five_typed_codecs_compile_to_exact_obligations(self):
        f = self.fixture(); ref, _, inputs = rich_context(f)
        context = load_teaching_context(f.io, ref, f.source_ref).model_data()['rich_teaching']
        self.assertEqual(5, len(context['strategies']))
        self.assertEqual(17, len(context['obligations']))
        self.assertIn('RICH_TEACHING_EFFECTIVENESS_REQUIRES_REVIEW', inputs.review_reasons)
        self.assertFalse(context['accepted'])

    def test_each_strategy_and_obligation_has_unique_identity(self):
        f = self.fixture(); specs = rich_specs(f)
        with self.assertRaises(ValueError): rich_context(f, specs + (specs[0],))

    def test_unknown_concept_is_rejected(self):
        f = self.fixture(); spec = rich_specs(f)[0]
        changed = GroundedWorkedExample(spec.example_id, 'concept:missing', spec.setup, spec.steps, spec.outcome)
        with self.assertRaises(ValueError): rich_context(f, (changed,))

    def test_source_offsets_are_revalidated_not_just_quote_matched(self):
        f = self.fixture(); spec = rich_specs(f)[0]
        bad = SourceExcerpt(spec.setup.evidence_id, spec.setup.start_char + 1, spec.setup.end_char + 1, spec.setup.quote)
        changed = GroundedWorkedExample(spec.example_id, spec.concept_id, bad, spec.steps, spec.outcome)
        with self.assertRaises(ValueError): rich_context(f, (changed,))

    def test_worked_example_cannot_omit_steps(self):
        f = self.fixture(); spec = rich_specs(f)[0]
        with self.assertRaises(ValueError): rich_context(f, (GroundedWorkedExample(
            spec.example_id, spec.concept_id, spec.setup, (), spec.outcome),))

    def test_persisted_rich_compilation_is_recomputed_on_load(self):
        f = self.fixture(); ref, _, _ = rich_context(f)
        artifact = f.io.load(ref); payload=copy.deepcopy(artifact.payload)
        payload['compiled']['rich_teaching']['obligations'][0]['required_texts'] = ['edited']
        changed=f.io.derive('pedagogy.teaching_context',f.run_id,tuple(artifact.parent_refs),payload,
            stage_id='PEDAGOGY',metadata={'requires_review':True,'accepted':False,'release_ready':False})
        with self.assertRaises(ValueError): load_teaching_context(f.io, changed, f.source_ref)

    def test_lesson_binding_retains_only_selected_grounded_concepts(self):
        f = self.fixture(); _, _, inputs = rich_context(f)
        data = inputs.teaching_context.model_data()
        self.assertTrue(data['rich_teaching']['obligations'])
        self.assertTrue(all(row['concept_id'] in inputs.teaching_context.selected_concept_ids
                            for row in data['rich_teaching']['obligations']))

    def test_plain_context_bytes_and_schema_remain_backward_compatible(self):
        f = self.fixture(); artifact = f.io.load(f.context_ref)
        self.assertEqual('bie.dir.teaching_context/1.0.0', artifact.payload['schema_version'])
        self.assertNotIn('rich_teaching', artifact.payload)


if __name__ == '__main__': unittest.main()
