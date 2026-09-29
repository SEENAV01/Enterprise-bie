"""Additional independent inventory and closure controls; synthetic credentials only."""
from h2_support import *
from bie.qa.governance_v2.catalog import ORIGINAL_TASK_IDS,HARDENING_TASK_IDS,BASELINE_OBLIGATIONS,CATALOG_DIGEST
from bie.qa.governance_v2.__main__ import main
from contextlib import redirect_stdout
import io

class Extended(InventoryCase):
    def full_authority(self):
        a=self.f.policy.inventory_authority
        obs=tuple(Obligation(k,'QA.GOVERNANCE','RELEASE',v,('closure-check',),digest({'check':k}),('source',)) for k,v in BASELINE_OBLIGATIONS.items())
        return replace(a,profile='SECTION16',task_ids=ORIGINAL_TASK_IDS+HARDENING_TASK_IDS,obligations=obs,catalog_digest=CATALOG_DIGEST)
    def test_full113_configured_and_open(self):
        self.f.policy=replace(self.f.policy,inventory_authority=self.full_authority());self.f.refresh_inventory()
        self.blocked('AUTHORITATIVE_OBLIGATION_OPEN')
        self.assertEqual(len(self.raw()['obligations']),113)
    def test_full113_row_omission(self):
        self.f.policy=replace(self.f.policy,inventory_authority=self.full_authority());self.f.refresh_inventory()
        self.mutate(lambda x:x['obligations'].pop());self.blocked('INVENTORY_OBLIGATION_CENSUS')
    def test_full113_configuration_omission(self):
        a=self.full_authority()
        with self.assertRaisesRegex(ContractError,'SECTION16_OBLIGATION_BASELINE_MISSING'):replace(a,obligations=a.obligations[:-1])
    def test_catalog_cannot_be_substituted(self):
        with self.assertRaisesRegex(ContractError,'SECTION16_CATALOG_MISMATCH'):replace(self.full_authority(),catalog_digest='0'*64)
    def test_baseline_definition_cannot_be_softened(self):
        a=self.full_authority()
        with self.assertRaisesRegex(ContractError,'SECTION16_OBLIGATION_DEFINITION_CHANGED'):replace(a,obligations=(replace(a.obligations[0],definition_digest='0'*64),)+a.obligations[1:])
    def test_secret_not_serialized(self):
        self.need_gap();self.assertNotIn(self.k.secret.decode(),json.dumps(self.f.policy.to_dict()))
    def test_key_not_valid_for_unknown_obligation(self):
        self.need_gap()
        with self.assertRaisesRegex(ContractError,'INVENTORY_KEY_UNKNOWN_OBLIGATION'):replace(self.f.policy.inventory_authority,closure_keys=(replace(self.k,obligation_ids=('UNKNOWN',)),))
    def test_unknown_affected_artifact(self):
        self.need_gap()
        with self.assertRaisesRegex(ContractError,'INVENTORY_UNKNOWN_ARTIFACT'):replace(self.f.policy.inventory_authority,obligations=(replace(self.o,affected_artifact_ids=('other',)),))
    def test_cli_rejects_unpinned_blueprint(self):
        p=self.root/'bp.json';p.write_text('{"test":true}')
        with redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['--root',str(self.root),'--blueprint','bp.json','--blueprint-sha256','0'*64]),2)
        self.assertIn('INDEX_BLUEPRINT_PIN_MISMATCH',out.getvalue())

class ExtendedClosures(GapCase):
    def test_unicode_signature_rejected_not_exception(self):
        self.mutate_closure(lambda d:d['approvals'][0].update(signature='अ'*64),False);self.blocked('BAD_CLOSURE_SIGNATURE')
    def test_two_distinct_closers_can_pass(self):
        second=replace(self.k,key_id='other-key',principal_id='other-principal',independence_group='other-group',secret=b'ANOTHER-SYNTHETIC-SECRET-0000000000')
        self.f.policy=replace(self.f.policy,inventory_authority=replace(self.f.policy.inventory_authority,closure_keys=(self.k,second),minimum_independent_closers=2))
        self.f.refresh_inventory();self.closed();raw=self.closure()
        raw['approvals'].append(dict(key_id=second.key_id,principal_id=second.principal_id,purpose='gap_closure',signature=hmac.new(second.secret,closure_signing_bytes(raw),hashlib.sha256).hexdigest()))
        self.write_closure(raw,False);self.assertTrue(self.f.assess().ready_for_signing)
    def test_two_aliases_same_principal_cannot_pass(self):
        second=replace(self.k,key_id='alias',secret=b'ANOTHER-SYNTHETIC-SECRET-0000000000')
        self.f.policy=replace(self.f.policy,inventory_authority=replace(self.f.policy.inventory_authority,closure_keys=(self.k,second),minimum_independent_closers=2))
        self.f.refresh_inventory();self.closed();raw=self.closure()
        raw['approvals'].append(dict(key_id=second.key_id,principal_id=second.principal_id,purpose='gap_closure',signature=hmac.new(second.secret,closure_signing_bytes(raw),hashlib.sha256).hexdigest()))
        self.write_closure(raw,False);self.blocked('CLOSURE_INDEPENDENCE_FLOOR')
    def test_signature_covers_evidence(self):
        self.mutate_closure(lambda d:d.update(evidence=[]),False);self.blocked('BAD_CLOSURE_SIGNATURE')

class Schemas(GapCase):
    def schema(self,name):
        import jsonschema
        R=Path(__file__).resolve().parents[2]
        d=json.loads((R/'docs/qa_section16/hardening_h2/schemas'/f'{name}.schema.json').read_text())
        jsonschema.Draft202012Validator.check_schema(d);return jsonschema.Draft202012Validator(d)
    def test_inventory_schema_positive(self):self.schema('inventory').validate(self.raw())
    def test_closure_schema_positive(self):self.schema('closure').validate(self.closure())
    def test_inventory_schema_rejects_authority_override(self):
        d=self.raw();d['authority']={};self.assertTrue(list(self.schema('inventory').iter_errors(d)))
    def test_inventory_schema_rejects_missing_tasks(self):
        d=self.raw();d['task_ids']=[];self.assertTrue(list(self.schema('inventory').iter_errors(d)))
    def test_closure_schema_rejects_empty_proof(self):
        d=self.closure();d['evidence']=[];self.assertTrue(list(self.schema('closure').iter_errors(d)))
    def test_index_schema_valid(self):self.schema('index')
