from dataclasses import FrozenInstanceError, replace
import json, math, sqlite3
from helpers import Base, case
from bie.evaluation.benchmarks.models import BenchmarkCase, BenchmarkError, canonical_json, digest, strict_loads
from bie.evaluation.benchmarks.registry import Registry

class RegistryTests(Base):
    def test_register_read_identity(self):
        c=case(); self.registry.register([c]); self.assertEqual(c,self.registry.get_case(c.case_id))
    def test_reopen_persists_cases(self):
        c=case(); self.registry.register([c])
        with Registry(self.root/'unit.sqlite3') as other: self.assertEqual(c,other.get_case(c.case_id))
    def test_frozen_outer_record(self):
        with self.assertRaises(FrozenInstanceError): case().title='changed'
    def test_nested_inputs_are_detached(self):
        c=case(); v=c.inputs; v['x']=99; self.assertEqual(1,c.inputs['x'])
    def test_public_view_redacts_reference(self):
        self.assertEqual({'case_id','task_id','prompt','inputs'},set(case().candidate_view()))
    def test_duplicate_batch_id_rejected(self):
        self.code('DUPLICATE_CASE_ID',self.registry.register,[case(),case()])
    def test_existing_id_not_overwritten(self):
        self.registry.register([case()]); self.code('CASE_ALREADY_REGISTERED',self.registry.register,[case(x=99)])
        self.assertEqual(1,self.registry.get_case('unit.case.1').inputs['x'])
    def test_batch_rollback_is_all_or_nothing(self):
        self.registry.register([case()]); self.code('CASE_ALREADY_REGISTERED',self.registry.register,[case('new',2),case()])
        self.code('CASE_NOT_FOUND',self.registry.get_case,'new')
    def test_empty_batch_rejected(self): self.code('INVALID_CASE_BATCH',self.registry.register,[])
    def test_invalid_id_rejected(self): self.code('INVALID_ID',case,case_id='../escape')
    def test_boolean_tolerance_rejected(self): self.code('INVALID_NUMBER',case,absolute_tolerance=True)
    def test_nan_rejected(self): self.code('NONFINITE_OR_OUT_OF_RANGE',case,inputs={'x':float('nan')})
    def test_infinite_tolerance_rejected(self): self.code('NONFINITE_OR_OUT_OF_RANGE',case,relative_tolerance=float('inf'))
    def test_mutable_source_collection_rejected(self): self.code('SOURCE_REQUIRED',replace,case(),sources=list(case().sources))
    def test_missing_provenance_rejected(self): self.code('SOURCE_REQUIRED',case,sources=())
    def test_duplicate_source_id_rejected(self): self.code('DUPLICATE_SOURCE',case,sources=case().sources*2)
    def test_unknown_json_fields_rejected(self):
        d=case().to_dict(); d['accepted']=True; self.code('INVALID_FIELDS',BenchmarkCase.from_dict,d)
    def test_noncanonical_nested_payload_rejected(self): self.code('NONCANONICAL_PAYLOAD',replace,case(),inputs_json='{"x": 1}')
    def test_duplicate_json_keys_rejected(self): self.code('DUPLICATE_JSON_KEY',strict_loads,'{"a":1,"a":2}')
    def test_untrusted_json_constant_rejected(self): self.code('NONFINITE_JSON',strict_loads,'{"a":NaN}')
    def test_tampered_case_bytes_rejected(self):
        self.registry.register([case()]); self.registry.connection.execute("UPDATE cases SET content_sha=?",('0'*64,))
        self.code('CASE_CONTENT_TAMPERED',self.registry.get_case,'unit.case.1')
    def test_event_chain_detects_body_change(self):
        self.registry.register([case()]); self.registry.connection.execute("UPDATE events SET body='{}'")
        self.code('EVENT_CHAIN_TAMPERED',self.registry.audit_head)
    def test_inventory_is_sorted_and_redacted(self):
        self.registry.register([case('z',1),case('a',2)])
        inventory=self.registry.inventory(); self.assertEqual(['a','z'],[x['case_id'] for x in inventory]); self.assertNotIn('expected',str(inventory))
    def test_unknown_database_version_fail_closed(self):
        path=self.root/'future.sqlite3'
        db=sqlite3.connect(path)
        try: db.execute('PRAGMA user_version=999')
        finally: db.close()
        self.code('UNSUPPORTED_DATABASE_VERSION',Registry,path)
    def test_json_depth_limit(self):
        value=0
        for _ in range(26): value=[value]
        self.code('JSON_DEPTH_LIMIT',canonical_json,value)
    def test_hash_independent_of_mapping_order(self): self.assertEqual(digest({'a':1,'b':2}),digest({'b':2,'a':1}))
