"""Structural-only preflight tests; no real-book or stage execution claim."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import replace

from bie.document_intelligence.real_pdf_toc_runtime import RealPdfTocRuntimeError, inspect_real_pdf_toc
from bie.qa.assurance_quality_v2.harness import BookPlan, PipelineStep, STAGES
from bie.qa.operational_quality_v2.rebuild import Stage
from bie.qa.operational_quality_v2.runtime import NativeWorkerProfile, Program
from bie.qa.release_v2.contracts import ContractError
from bie.section16.native_book_preflight import preflight_native_pdf_book
from tests.productization.document_intelligence.structural_pdf_fixtures import structural_pdf


class NativeBookPreflightTests(unittest.TestCase):
    def setUp(self):
        self.data = structural_pdf(1, text_pages={0}, text='Synthetic preflight content')
        self.source_hash = hashlib.sha256(self.data).hexdigest()
        self.blocks = inspect_real_pdf_toc(self.data).total_blocks
        self.plan = BookPlan(({'path': 'fixture.pdf', 'bytes': len(self.data), 'sha256': self.source_hash},), 'fixture.pdf', ())

    def inspect(self, data=None, plan=None, **kw):
        return preflight_native_pdf_book(
            self.data if data is None else data,
            self.plan if plan is None else plan,
            expected_source_hash=kw.get('expected_source_hash', self.source_hash),
            expected_page_count=kw.get('expected_page_count', 1),
            expected_total_blocks=kw.get('expected_total_blocks', self.blocks),
        )

    def test_real_canonical_pdf_runtime_is_composed_without_stage_execution(self):
        result = self.inspect().to_safe_dict()
        self.assertEqual((result['page_count'], result['total_blocks']), (1, self.blocks))
        self.assertEqual(result['source_hash'], self.source_hash)
        self.assertEqual(len(result['stage_status']), len(STAGES))
        self.assertTrue(all(v == 'NOT_REGISTERED' for v in result['stage_status'].values()))
        self.assertEqual(result['native_stage_execution'], 'NOT_RUN')
        self.assertFalse(result['section16_signed_off'])

    def test_no_pdf_text_in_safe_output(self):
        self.assertNotIn('Synthetic preflight content', str(self.inspect().to_safe_dict()))

    def test_repeated_output_is_deterministic(self):
        self.assertEqual(self.inspect().to_safe_dict(), self.inspect().to_safe_dict())

    def test_different_source_hash_fails_closed(self):
        self.assertRaises(ContractError, self.inspect, expected_source_hash='0' * 64)

    def test_wrong_page_baseline_fails_closed(self):
        self.assertRaises(ContractError, self.inspect, expected_page_count=2)

    def test_wrong_block_baseline_fails_closed(self):
        self.assertRaises(ContractError, self.inspect, expected_total_blocks=self.blocks + 1)

    def test_plan_inventory_mismatch_fails_closed(self):
        changed = replace(self.plan, source_rows=({'path': 'fixture.pdf', 'bytes': len(self.data) + 1, 'sha256': self.source_hash},))
        self.assertRaises(ContractError, self.inspect, plan=changed)

    def test_diagnostic_profile_remains_blocked(self):
        result = self.inspect(plan=replace(self.plan, profile='DIAGNOSTIC'))
        self.assertIn('H39_DIAGNOSTIC_PLAN_NOT_NATIVE', result.blockers)

    def registered_bi(self, checkout):
        script = checkout / 'bi.py'
        script.write_text('raise SystemExit("never executed")\n', encoding='utf-8')
        compiler = checkout / 'bie' / 'compiler'
        compiler.mkdir(parents=True)
        worker = compiler / 'linux_worker.py'
        launcher = compiler / 'namespace_launcher.py'
        worker.write_text('# synthetic worker identity only\n', encoding='utf-8')
        launcher.write_text('# synthetic launcher identity only\n', encoding='utf-8')
        executable = Path(sys.executable).resolve()
        program = Program(
            'registered-bi', (str(executable), str(script)),
            hashlib.sha256(executable.read_bytes()).hexdigest(), str(script),
            hashlib.sha256(script.read_bytes()).hexdigest(),
        )
        rows = tuple({'path': p.relative_to(checkout).as_posix(), 'bytes': p.stat().st_size,
                      'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                     for p in sorted(checkout.rglob('*')) if p.is_file())
        profile = NativeWorkerProfile(rows, hashlib.sha256(worker.read_bytes()).hexdigest(),
                                      hashlib.sha256(launcher.read_bytes()).hexdigest())
        stage = Stage('bi', 'compile', program, ('qa-result.json',), profile, str(checkout))
        return replace(self.plan, steps=(PipelineStep('BI', stage, (), ('source-check',)),)), script

    def test_registered_native_program_bytes_checked_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            plan, script = self.registered_bi(Path(directory))
            result = self.inspect(plan=plan).to_safe_dict()
            self.assertEqual(result['stage_status']['BI'],
                             'NATIVE_REGISTRATION_BYTES_VERIFIED' if hasattr(os, 'O_NOFOLLOW') else 'PLATFORM_UNSUPPORTED')
            self.assertEqual(result['native_stage_execution'], 'NOT_RUN')
            self.assertEqual(script.read_text(), 'raise SystemExit("never executed")\n')

    def test_changed_registered_program_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan, script = self.registered_bi(Path(directory))
            script.write_text('raise SystemExit("changed")\n', encoding='utf-8')
            result = self.inspect(plan=plan)
            if hasattr(os, 'O_NOFOLLOW'):
                self.assertEqual(dict(result.stage_status)['BI'], 'PROGRAM_IDENTITY_INVALID')
                self.assertIn('H39_NATIVE_PROGRAM_IDENTITY_INVALID', result.blockers)
            else:
                self.assertEqual(dict(result.stage_status)['BI'], 'PLATFORM_UNSUPPORTED')
                self.assertIn('H39_NATIVE_IDENTITY_PLATFORM_UNSUPPORTED', result.blockers)

    def test_changed_worker_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan, _ = self.registered_bi(Path(directory))
            (Path(directory) / 'bie' / 'compiler' / 'linux_worker.py').write_text('# changed worker\n', encoding='utf-8')
            result = self.inspect(plan=plan)
            if hasattr(os, 'O_NOFOLLOW'):
                self.assertEqual(dict(result.stage_status)['BI'], 'NATIVE_WORKER_IDENTITY_INVALID')
                self.assertIn('H39_NATIVE_WORKER_IDENTITY_INVALID', result.blockers)
            else:
                self.assertEqual(dict(result.stage_status)['BI'], 'PLATFORM_UNSUPPORTED')

    def test_malformed_pdf_fails_closed(self):
        data = b'not a PDF'
        p = BookPlan(({'path': 'fixture.pdf', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()},), 'fixture.pdf', ())
        self.assertRaises(RealPdfTocRuntimeError, self.inspect, data=data, plan=p, expected_source_hash=hashlib.sha256(data).hexdigest())
