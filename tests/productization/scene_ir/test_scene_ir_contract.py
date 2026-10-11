"""Profile, isolation, privacy and historical delegation contracts."""
import ast
from pathlib import Path
import unittest

from bie.productization.scene_ir_contract import PROFILE, scene_ir_config, profile_config
from bie.productization.scene_ir_slice import STAGES, SceneIRProducerService, INPUT_STAGES, safe_failure_code
from bie.productization.contracts import ProducerError
from bie.productization.durable_slice import KnowledgeProducerService
from bie.infrastructure.orchestrator import EnterpriseOrchestrator

ROOT = Path(__file__).resolve().parents[3]


class SceneContractControls(unittest.TestCase):
    def test_eleven_ordered_stages_only(self):
        self.assertEqual(STAGES, ('SOURCE', 'DOCUMENT_INTELLIGENCE', 'KNOWLEDGE', 'PREREQUISITE', 'MATH',
            'REASONING', 'PEDAGOGY', 'DIRECTOR', 'VISUAL', 'ANIMATION', 'SCENE_IR'))

    def test_ordered_consumed_inputs_and_unmodified_predecessor_list(self):
        graph = SceneIRProducerService.graph_for().stages['SCENE_IR']
        self.assertEqual(graph.consumes, ['visual.plan', 'animation.plan', 'director.plan'])
        self.assertEqual(graph.emits, 'scene.ir')
        self.assertEqual(graph.required_predecessors, ['VISUAL', 'ANIMATION'])
        self.assertEqual(INPUT_STAGES, ('VISUAL', 'ANIMATION', 'DIRECTOR'))

    def test_historical_default_orchestrator_remains_native(self):
        self.assertIs(KnowledgeProducerService.orchestrator_type, EnterpriseOrchestrator)

    def test_historical_scopes_are_unchanged(self):
        from bie.productization.durable_slice import STAGES as s29
        from bie.productization.reasoning_slice import STAGES as s30
        from bie.productization.math_slice import STAGES as s31
        from bie.productization.pedagogy_slice import STAGES as s32
        from bie.productization.director_slice import STAGES as s33
        from bie.productization.visual_slice import STAGES as s34
        from bie.productization.animation_slice import STAGES as s35
        self.assertEqual([len(s) for s in (s29, s30, s31, s32, s33, s34, s35, STAGES)], [3, 5, 6, 7, 8, 9, 10, 11])

    def test_current_native_scope_requires_explicit_configuration(self):
        with self.assertRaises(ProducerError):
            profile_config()

    def test_config_has_no_audio_or_acceptance_promotion(self):
        value = scene_ir_config()
        self.assertFalse(value['audio_complete'])
        self.assertTrue(value['audio_reconciliation_open'])
        self.assertEqual(value['scope'], 'COMPLETE_SINGLE_SCENE')
        self.assertEqual(value['capability_profile'], 'producer-motion-v1')

    def test_no_audio_stage_added(self):
        self.assertNotIn('AUDIO', STAGES)

    def test_later_stages_are_not_in_this_profile(self):
        self.assertFalse(set(('VIDEO_CODE', 'COMPILE', 'RENDER', 'QA', 'GAME')) & set(STAGES))

    def test_failure_messages_cannot_escape_as_codes(self):
        marker = 'private book text and token C:/private/source'
        self.assertEqual(safe_failure_code(ProducerError(marker)), 'scene_ir_execution_failed')
        self.assertEqual(safe_failure_code(ValueError(marker)), 'scene_ir_execution_failed')

    def test_known_audio_rejection_is_not_erased(self):
        self.assertEqual(safe_failure_code(ProducerError('scene_ir_audio_replan_required')), 'scene_ir_audio_replan_required')

    def test_unknown_code_type_does_not_escape(self):
        self.assertEqual(safe_failure_code(ProducerError(True)), 'scene_ir_execution_failed')

    def test_changing_exception_property_never_executes_or_leaks(self):
        class ChangingCode(ProducerError):
            def __init__(self):
                self.reads = 0

            @property
            def code(self):
                self.reads += 1
                return 'scene_ir_audio_replan_required' if self.reads < 3 else 'synthetic private marker'

        exc = ChangingCode()
        self.assertEqual(safe_failure_code(exc), 'scene_ir_execution_failed')
        self.assertEqual(exc.reads, 0)

    def test_raising_exception_property_never_executes(self):
        class RaisingCode(ProducerError):
            def __init__(self):
                self.reads = 0

            @property
            def code(self):
                self.reads += 1
                raise RuntimeError('synthetic private marker')

        exc = RaisingCode()
        self.assertEqual(safe_failure_code(exc), 'scene_ir_execution_failed')
        self.assertEqual(exc.reads, 0)

    def test_hostile_subclass_attribute_hook_is_not_consulted(self):
        class HostileCode(ProducerError):
            def __init__(self):
                pass

            def __getattribute__(self, name):
                if name == 'code':
                    raise AssertionError('synthetic private marker')
                return super().__getattribute__(name)

        self.assertEqual(safe_failure_code(HostileCode()), 'scene_ir_execution_failed')

    def test_string_subclass_cannot_self_certify_a_code(self):
        class HostileString(str):
            def __hash__(self):
                raise AssertionError('synthetic private marker')

        self.assertEqual(safe_failure_code(ProducerError(HostileString('scene_ir_audio_replan_required'))),
                         'scene_ir_execution_failed')

    def test_trusted_exception_missing_code_is_fail_closed(self):
        exc = ProducerError('scene_ir_audio_replan_required')
        del exc.code
        self.assertEqual(safe_failure_code(exc), 'scene_ir_execution_failed')

    def test_engine_does_not_import_test_catalog_or_fixture_renderer(self):
        for path in (ROOT / 'bie/productization').glob('scene_ir_*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            self.assertFalse(any(m and m.startswith('tests.') for m in imports))
            self.assertNotIn('bie.compiler.hardened_scene_compile', imports)
            self.assertNotIn('bie.compiler.real_paint', imports)

    def test_original_math_and_director_fail_closed_codes_retained(self):
        for source, code in (('math_slice.py', 'math_evidence_required'), ('director_slice.py', 'director_math_teaching_contract_required')):
            self.assertIn(code, (ROOT / 'bie/productization' / source).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
