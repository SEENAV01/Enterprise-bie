"""Explicit resource ownership for the Section 18 adapter; native source unchanged.

The canonical persistence methods use SQLite context managers, which commit but
do not close connections. Scope their same native connection to one operation.
This adapter does not change schema, transactions, SQL or persisted semantics.
"""
from contextlib import contextmanager
from bie.infrastructure.persistence import SQLitePersistence

class OwnedPersistence(SQLitePersistence):
    @contextmanager
    def _conn(self):
        connection=super()._conn()
        try:
            with connection: yield connection
        finally: connection.close()
