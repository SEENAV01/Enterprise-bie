import copy,json,unittest
from pathlib import Path
from bie.qa.governance_v2.reaudit import scope_crosswalk
from bie.qa.release_v2.contracts import ContractError
ROOT=Path(__file__).resolve().parents[2]
class CrosswalkTests(unittest.TestCase):
    def setUp(self):
        self.index=json.loads((ROOT/'metadata/section16/TASK_INTEGRATION_INDEX.json').read_text())
        self.catalog=json.loads((ROOT/'metadata/section16/BASELINE_CATALOG.json').read_text())
        self.registry=json.loads((ROOT/'metadata/section16/OBLIGATION_REGISTRY.json').read_text())
        self.matrices=[json.loads((ROOT/f'hardening/section16_h{n}/CLOSURE_MATRIX.json').read_text()) for n in range(3,9)]
    def result(self):return scope_crosswalk(self.index,self.catalog,self.registry,self.matrices)
    def test_actual_catalog_all117_tasks_and113_obligations_retained(self):
        r=self.result();self.assertEqual((r['original_count'],r['hardening_count'],r['historical_obligation_count']),(76,41,113));self.assertEqual(r['decision'],'BLOCKED')
    def test_open_rows_never_grant_exit_or_integration(self):
        r=self.result();self.assertFalse(r['full_section_complete']);self.assertFalse(r['canonical_integration_authorized']);self.assertEqual(r['historical_obligations_closed'],0)
    def test_missing_original_rejected(self):
        self.index['original_tasks'].pop()
        with self.assertRaises(ContractError):self.result()
    def test_duplicate_original_rejected(self):
        self.index['original_tasks'][1]=self.index['original_tasks'][0]
        with self.assertRaises(ContractError):self.result()
    def test_missing_hardening_task_rejected(self):
        self.index['hardening_tasks'].pop()
        with self.assertRaises(ContractError):self.result()
    def test_omitted_historical_obligation_rejected(self):
        self.registry['records'].pop()
        with self.assertRaises(ContractError):self.result()
    def test_added_unapproved_obligation_rejected(self):
        self.registry['records'].append(dict(self.registry['records'][0],obligation_id='unknown'))
        with self.assertRaises(ContractError):self.result()
    def test_rewritten_obligation_definition_rejected(self):
        self.registry['records'][0]['definition']['description']='waived'
        with self.assertRaises(ContractError):self.result()
    def test_changed_definition_hash_rejected(self):
        self.registry['records'][0]['definition_digest']='0'*64
        with self.assertRaises(ContractError):self.result()
    def test_closed_string_cannot_close_obligation(self):
        self.registry['records'][0]['current_closure_status']='CLOSED'
        with self.assertRaises(ContractError):self.result()
    def test_supplied_receipt_does_not_replace_closure_authority(self):
        self.registry['records'][0]['closure_evidence']={'status':'PASS'}
        with self.assertRaises(ContractError):self.result()
    def test_missing_closure_matrix_rejected(self):
        self.matrices.pop()
        with self.assertRaises(ContractError):self.result()
    def test_duplicate_closure_task_rejected(self):
        self.matrices.append(self.matrices[0])
        with self.assertRaises(ContractError):self.result()
    def test_unverified_scope_closure_rejected(self):
        self.matrices[0]['tasks'][0]['full_scope_closed']=True
        with self.assertRaises(ContractError):self.result()
    def test_erased_remaining_scope_rejected(self):
        self.matrices[0]['tasks'][0]['open']=[]
        with self.assertRaises(ContractError):self.result()
    def test_input_objects_are_not_mutated(self):
        before=copy.deepcopy((self.index,self.catalog,self.registry,self.matrices));self.result()
        self.assertEqual(before,(self.index,self.catalog,self.registry,self.matrices))
    def test_unknown_matrix_schema_rejected(self):
        self.matrices[1]['schema_version']='unknown/1'
        with self.assertRaises(ContractError):self.result()
    def test_h3_legacy_open_scope_preserved(self):
        original=self.matrices[0]['tasks'][0]
        row=next(t for t in self.result()['hardening_tasks'] if t['task_id']==original['task_id'])
        self.assertEqual(row['remaining_scope'],original['open'])
