import unittest
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError, digest, canonical_json, strict_loads

import sqlite3
from bie.evaluation.benchmarks.registry import Registry
from bie.evaluation.benchmarks import storage
class StorageBoundary(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_memory_explicitly_allowed(self):
        with Registry(':memory:') as db: self.assertEqual('0'*64,db.audit_head())
    def test_memory_durable_port_refuses(self):
        with self.assertRaisesRegex(BenchmarkError,'NOT_DURABLE'): storage.database_path(':memory:')
    def test_file_database_works(self):
        with Registry(self.root/'a.sqlite') as db: self.assertFalse(db.connection.in_transaction)
    def test_file_symlink_refused(self):
        p=self.root/'db';p.touch();link=self.root/'link';link.symlink_to(p)
        with self.assertRaisesRegex(BenchmarkError,'SYMLINK'): Registry(link)
    def test_parent_symlink_refused(self):
        p=self.root/'real';p.mkdir();link=self.root/'link';link.symlink_to(p,target_is_directory=True)
        with self.assertRaisesRegex(BenchmarkError,'SYMLINK'): Registry(link/'db')
    def test_directory_not_database(self):
        with self.assertRaises(BenchmarkError):Registry(self.root)
    def test_nonexistent_parent_refused(self):
        with self.assertRaises(BenchmarkError):Registry(self.root/'absent'/'db')
    def test_uri_refused(self):
        with self.assertRaisesRegex(BenchmarkError,'URI_REFUSED'):Registry('file:abc?mode=memory')
    def test_empty_path_refused(self):
        with self.assertRaises(BenchmarkError):Registry('')
    def test_parent_traversal_refused(self):
        with self.assertRaises(BenchmarkError):storage.database_path(self.root/'child'/'..'/'db')
    def test_311_api_compatibility_branch(self):
        real=sqlite3.connect
        class LegacyModule:
            def connect(self,path,**kw):
                if 'autocommit' in kw: raise TypeError('3.11 API rejects autocommit')
                return real(path,**kw)
        with patch.object(storage,'sqlite3',LegacyModule()):
            c=storage.connect_manual(':memory:',allow_memory=True);c.close()
    def test_manual_transactions_commit_and_rollback(self):
        with Registry(':memory:') as db:
            with db.transaction():db.connection.execute('CREATE TABLE probe (x INT)')
            with self.assertRaises(RuntimeError):
                with db.transaction():
                    db.connection.execute('INSERT INTO probe VALUES (1)');raise RuntimeError('rollback')
            self.assertEqual(0,db.connection.execute('SELECT COUNT(*) FROM probe').fetchone()[0])
    def test_existing_schema_version_preserved(self):
        path=self.root/'db'
        with Registry(path) as db:self.assertEqual(1,db.connection.execute('PRAGMA user_version').fetchone()[0])
        with Registry(path) as db:self.assertEqual(1,db.connection.execute('PRAGMA user_version').fetchone()[0])
