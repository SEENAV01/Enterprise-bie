from dataclasses import asdict,replace
from pathlib import Path
import json
import tempfile
import unittest
from bie.compiler.multidomain_compile_benchmark import *
from tests.compiler.qa_test_support import case,case_raw,FIXTURES,ROOT

class MultidomainBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.receipt=run_multidomain_compile_benchmark(load_benchmark_corpus(FIXTURES/'corpus.json'),
            output_directory=Path(cls.tmp.name)/'all',baseline_directory=FIXTURES/'baselines',runs=2,
            require_full_typecheck=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_all_19_source_expectations_match(self):
        self.assertEqual(self.receipt.expectation_matches,19,[(r.case_id,r.error_codes,r.failure) for r in self.receipt.cases if not r.expectation_matched])
    def test_ten_domains_represented(self):self.assertEqual(len(self.receipt.domains),10)
    def test_thirteen_positive_source_cases_pass(self):self.assertEqual(self.receipt.positive_source_passes,13)
    def test_six_remaining_negative_cases_are_not_positive_outputs(self):
        self.assertEqual(self.receipt.negative_cases_detected,6)
        self.assertTrue(all(not r.source_gate_passed for r in self.receipt.cases if not r.expected_source_passed))
    def test_repeated_actual_generation_samples_recorded(self):
        self.assertTrue(all(len(r.codegen_samples_ms)==3 and r.median_codegen_ms>=0 for r in self.receipt.cases))
    def test_input_and_evidence_hashes_present(self):
        self.assertTrue(all(len(r.fixture_sha256)==64 and r.source_bytes>0 for r in self.receipt.cases))
    def test_source_pass_does_not_satisfy_full_compile(self):
        self.assertTrue(self.receipt.source_benchmark_passed);self.assertFalse(self.receipt.full_compile_benchmark_passed)
    def test_dependency_blocks_are_explicit(self):
        self.assertTrue(all(r.full_typecheck_status=='BLOCKED_DEPENDENCIES' for r in self.receipt.cases))
    def test_source_exception_not_falsely_called_real_book(self):
        self.assertEqual(self.receipt.real_book_e2e,'NOT_RUN');self.assertEqual(self.receipt.learning_quality,'NOT_EVALUATED')
    def test_fixed_literal_has_no_executable_diagnostic(self):
        row=next(r for r in self.receipt.cases if r.case_id=='reject-jsx-braces');self.assertEqual(row.diagnostic_mapping_count,0);self.assertTrue(row.source_gate_passed)
    def test_benchmark_receipt_not_accepted(self):self.assertFalse(self.receipt.accepted)
    def test_single_domain_rejected(self):
        with self.assertRaises(ValueError):validate_corpus((case('math-plain'),case('reject-untypeset-equation')))
    def test_duplicate_case_id_rejected(self):
        with self.assertRaises(ValueError):validate_corpus((case(),case(),case('reject-vector-z')))
    def test_empty_corpus_rejected(self):
        with self.assertRaises(ValueError):validate_corpus(())
    def test_only_positive_corpus_rejected(self):
        with self.assertRaises(ValueError):validate_corpus((case(),case('physics-vector')))
    def test_case_expected_boolean_is_strict(self):
        with self.assertRaises(ValueError):replace(case(),expected_source_passed='true')
    def test_negative_case_must_name_defect(self):
        with self.assertRaises(ValueError):replace(case(),expected_source_passed=False)
    def test_cases_cannot_claim_textbook_provenance(self):
        with self.assertRaises(ValueError):replace(case(),source_kind='REAL_BOOK_VERIFIED')
    def test_fixture_metadata_binds_case_id(self):
        with self.assertRaises(ValueError):replace(case(),case_id='other')
    def test_unsafe_case_filename_rejected(self):
        with self.assertRaises(ValueError):replace(case(),case_id='../escape')
    def test_nonfinite_budget_rejected(self):
        with self.assertRaises(ValueError):replace(case(),max_codegen_ms=float('nan'))
    def test_existing_evidence_never_overwritten(self):
        with self.assertRaises(ValueError):run_multidomain_compile_benchmark((case(),case('reject-vector-z')),
            output_directory=Path(self.tmp.name)/'all',baseline_directory=FIXTURES/'baselines')
    def test_budget_failure_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            r=run_multidomain_compile_benchmark((replace(case(),max_source_bytes=1),case('reject-vector-z')),
                 output_directory=Path(td)/'budget',baseline_directory=FIXTURES/'baselines',runs=2,require_full_typecheck=False)
            self.assertFalse(r.source_benchmark_passed)
            self.assertIn('BENCHMARK_BUDGET_EXCEEDED',next(x for x in r.cases if x.case_id=='math-plain').error_codes)
    def test_unexpected_extra_error_fails_negative_expectation(self):
        with tempfile.TemporaryDirectory() as td:
            r=run_multidomain_compile_benchmark((case(),case('reject-vector-z')),
                 output_directory=Path(td)/'missing',baseline_directory=Path(td)/'absent',runs=2,require_full_typecheck=False)
            self.assertFalse(r.source_benchmark_passed);self.assertEqual(r.expectation_matches,0)
    def test_corpus_roundtrip_preserves_scope(self):
        cases=load_benchmark_corpus(FIXTURES/'corpus.json');self.assertEqual(len(cases),19)
        self.assertTrue(all(c.document['metadata']['not_textbook'] is True for c in cases))

if __name__=='__main__':unittest.main()
