from dataclasses import replace
from helpers import Base, case
from bie.evaluation.benchmarks.models import canonical_json, digest
from bie.evaluation.benchmarks.registry import Registry
from bie.evaluation.benchmarks.versioning import Snapshot, VersionStore, snapshot_diff

class VersionTests(Base):
    def setUp(self):
        super().setUp(); self.registry.register([case('a',1),case('b',2)]); self.store=VersionStore(self.registry)
    def first(self): return self.store.create('dataset','1.0.0',['a'])
    def test_snapshot_round_trip(self): self.assertEqual(self.first(),self.store.get('dataset','1.0.0'))
    def test_case_order_does_not_change_hash(self):
        first=self.store.create('dataset','1.0.0',['b','a'])
        with Registry(self.root/'other.sqlite3') as r:
            r.register([case('a',1),case('b',2)]); other=VersionStore(r).create('dataset','1.0.0',['a','b'])
        self.assertEqual(first.sha256,other.sha256)
    def test_duplicate_version_rejected(self):
        s=self.first(); self.code('VERSION_NOT_INCREASING',self.store.create,'dataset','1.0.0',['a'],parent_sha256=s.sha256)
    def test_version_roll_back_rejected(self):
        s=self.first(); self.code('VERSION_NOT_INCREASING',self.store.create,'dataset','0.9.0',['a'],parent_sha256=s.sha256)
    def test_wrong_parent_rejected(self):
        self.first(); self.code('PARENT_MISMATCH',self.store.create,'dataset','1.1.0',['a'],parent_sha256='0'*64)
    def test_initial_parent_rejected(self): self.code('UNEXPECTED_PARENT',self.store.create,'dataset','1.0.0',['a'],parent_sha256='0'*64)
    def test_old_snapshot_remains_immutable(self):
        a=self.first(); self.store.create('dataset','1.1.0',['a','b'],parent_sha256=a.sha256)
        self.assertEqual(['a'],[c.case_id for c in self.store.get('dataset','1.0.0').cases])
    def test_explicit_diff_added_and_removed(self):
        a=self.first(); b=self.store.create('dataset','2.0.0',['b'],parent_sha256=a.sha256)
        d=snapshot_diff(a,b); self.assertEqual(['a'],d['removed']); self.assertEqual(['b'],d['added'])
    def test_lineage_exact_parent_chain(self):
        a=self.first(); b=self.store.create('dataset','1.1.0',['a','b'],parent_sha256=a.sha256)
        self.assertEqual((b.sha256,a.sha256),self.store.verify_lineage(b))
    def test_snapshot_body_tamper(self):
        s=self.first(); b=s.body; b['version']='1.9.0'; self.code('SNAPSHOT_TAMPERED',Snapshot,canonical_json(b),s.sha256)
    def test_database_snapshot_tamper(self):
        self.first(); self.registry.connection.execute("UPDATE snapshots SET sha256=?",('0'*64,))
        self.code('SNAPSHOT_TAMPERED',self.store.get,'dataset','1.0.0')
    def test_duplicate_roster_rejected(self): self.code('INVALID_SNAPSHOT_CASE_IDS',self.store.create,'dataset','1.0.0',['a','a'])
    def test_missing_case_rolls_back(self):
        self.code('CASE_NOT_FOUND',self.store.create,'dataset','1.0.0',['a','missing'])
        self.code('SNAPSHOT_NOT_FOUND',self.store.get,'dataset','1.0.0')
    def test_empty_snapshot_rejected(self): self.code('INVALID_SNAPSHOT_CASE_IDS',self.store.create,'dataset','1.0.0',[])
    def test_version_syntax_strict(self): self.code('INVALID_VERSION',self.store.create,'dataset','01.0.0',['a'])
    def test_unknown_schema_rejected(self):
        s=self.first(); b=s.body; b['schema_version']='99'; self.code('INVALID_SNAPSHOT',Snapshot,canonical_json(b),digest(b))
    def test_cross_dataset_diff_rejected(self):
        a=self.first(); b=self.store.create('other','1.0.0',['b']); self.code('DIFFERENT_DATASETS',snapshot_diff,a,b)
    def test_public_manifest_no_reference_leak(self): self.assertNotIn('cases',self.first().public_manifest())
    def test_forged_parent_not_found(self):
        s=self.first(); b=s.body; b['parent_sha256']='1'*64
        self.code('PARENT_NOT_FOUND',self.store.verify_lineage,Snapshot(canonical_json(b),digest(b)))
