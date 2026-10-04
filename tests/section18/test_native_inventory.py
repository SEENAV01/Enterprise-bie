"""H1-005 read-side inventory caps with real private synthetic run storage."""
from pathlib import Path
from dataclasses import replace
import os
from unittest.mock import patch
from test_batch001 import Base
from apps.operator.service import Service

class NativeInventory(Base):
    def tree(self):
        run=self.make_run();root=self.root/'runs'/run
        return run,root
    def test_actual_status_rejects_over_depth_without_changing_persisted_state(self):
        run,root=self.tree();before=self.service.status(self.p,run)
        deep=root
        for _ in range(17):deep=deep/'x'
        deep.mkdir(parents=True)
        response=self.get('runs/'+run)
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['error']['code'],'native_inventory_depth_reached')
        self.assertTrue(deep.is_dir())
        # Restart still rejects; recovery is not allowed to discard unknown data.
        restarted=Service(self.root,self.creds)
        self.error(lambda:restarted.status(self.p,run),'native_inventory_depth_reached')
        self.assertEqual(before['status'],'READY')
    def test_exact_depth_is_admitted(self):
        run,root=self.tree();deep=root
        for _ in range(16):deep=deep/'x'
        deep.mkdir(parents=True)
        self.assertEqual(self.service.status(self.p,run)['status'],'READY')
    def test_exact_entry_cap_is_admitted_and_one_over_is_rejected(self):
        run,root=self.tree();count=sum(1 for _ in root.rglob('*'))
        self.service.cas_budget.limits=replace(self.service.cas_budget.limits,max_inventory_entries=count)
        self.service._verify_native_tree(root)
        (root/'extra').write_bytes(b'SYNTHETIC_TEST')
        self.error(lambda:self.service._verify_native_tree(root),'native_inventory_capacity_reached')
        self.assertEqual((root/'extra').read_bytes(),b'SYNTHETIC_TEST')
    def test_capacity_uses_streaming_scan_and_never_unbounded_rglob(self):
        run,root=self.tree()
        self.service.cas_budget.limits=replace(self.service.cas_budget.limits,max_inventory_entries=1)
        with patch.object(Path,'rglob',side_effect=AssertionError('unbounded scan forbidden')):
            self.error(lambda:self.service._verify_native_tree(root),'native_inventory_capacity_reached')
    def test_hardlinked_non_cas_file_is_rejected(self):
        run,root=self.tree();file=root/'untrusted';file.write_bytes(b'SYNTHETIC_TEST')
        os.link(file,root/'alias')
        self.error(lambda:self.service.status(self.p,run),'storage_link_rejected')
    def test_foreign_tenant_and_revoked_principal_are_rejected_before_scan(self):
        from apps.operator.contracts import Principal,PERMISSIONS
        import secrets,time
        run,root=self.tree();token=secrets.token_hex(32)
        foreign=Principal('foreign','tenant-b',PERMISSIONS,time.time()+3600)
        self.creds.grant(token,foreign)
        with patch.object(self.service,'_verify_native_tree',side_effect=AssertionError('scan before authorization')):
            self.error(lambda:self.service.status(foreign,run),'run_not_found')
            self.creds.revoke(self.token)
            self.error(lambda:self.service.status(self.p,run),'unauthorized')
    def test_volatility_control_does_not_allow_missing_arbitrary_file(self):
        run,root=self.tree();file=root/'untrusted';file.write_bytes(b'SYNTHETIC_TEST')
        actual=os.stat
        def cut(path,*args,**kwargs):
            if Path(path)==file:file.unlink();raise FileNotFoundError()
            return actual(path,*args,**kwargs)
        with patch('apps.operator.service.os.stat',side_effect=cut):
            self.error(lambda:self.service._verify_native_tree(root),'native_inventory_changed')
    def test_actual_sqlite_sidecar_last_close_is_allowed_without_widening_inventory(self):
        import sqlite3
        run,root=self.tree();probe=root/'scan-probe';probe.mkdir()
        # A separate real WAL database makes this connection its actual last
        # owner; canonical service connections must not decide this fault cut.
        db=sqlite3.connect(probe/'runs.sqlite3',isolation_level=None)
        db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE scan_probe(value TEXT)')
        wal=probe/'runs.sqlite3-wal';self.assertTrue(wal.is_file());cuts=[];actual=os.stat
        def cut(path,*args,**kwargs):
            if Path(path)==wal and not cuts:
                db.close();cuts.append('REAL_LAST_CLOSE');self.assertFalse(wal.exists())
            return actual(path,*args,**kwargs)
        try:
            with patch('apps.operator.service.os.stat',side_effect=cut):self.service._verify_native_tree(root)
            self.assertEqual(cuts,['REAL_LAST_CLOSE'])
            self.assertEqual(self.service.status(self.p,run)['status'],'READY')
        finally:db.close()
