"""Product intent/access/control index, NOT a second engine or queue.

    Local hash-chained events detect ordinary row/event tampering. A trusted DB
    administrator can rewrite the chain; no external notarization is claimed.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json, sqlite3
from .contracts import canonical, digest, require, private_path, OperatorError,ident
from .catalog_budget import CatalogBudget

def timestamp(): return datetime.now(timezone.utc).isoformat()

class Catalog:
    def __init__(self,root,budget=None):
        self.budget=CatalogBudget() if budget is None else budget
        require(type(self.budget) is CatalogBudget,'catalog_budget_invalid',400)
        self.path = private_path(root,'operator.sqlite3')
        with self.tx(initial=True) as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS intents(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,key_hash TEXT NOT NULL,
              fingerprint TEXT NOT NULL,body TEXT NOT NULL,control TEXT NOT NULL,revision INTEGER NOT NULL,
              UNIQUE(tenant,key_hash));
            CREATE TABLE IF NOT EXISTS graphs(run TEXT NOT NULL,kind TEXT NOT NULL,artifact TEXT NOT NULL,
              sha TEXT NOT NULL, PRIMARY KEY(run,kind));
            CREATE TABLE IF NOT EXISTS audit(n INTEGER PRIMARY KEY,body TEXT NOT NULL,prev TEXT NOT NULL,sha TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS provider_versions(tenant TEXT NOT NULL,id TEXT NOT NULL,revision INTEGER NOT NULL,
              body TEXT NOT NULL,PRIMARY KEY(tenant,id,revision));
            CREATE TABLE IF NOT EXISTS workers(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS governance_versions(tenant TEXT NOT NULL,kind TEXT NOT NULL,id TEXT NOT NULL,
              revision INTEGER NOT NULL,body TEXT NOT NULL,PRIMARY KEY(tenant,kind,id,revision));
            CREATE TABLE IF NOT EXISTS governance_active(tenant TEXT NOT NULL,kind TEXT NOT NULL,body TEXT NOT NULL,
              PRIMARY KEY(tenant,kind));
            CREATE TABLE IF NOT EXISTS audit_reservations(id TEXT PRIMARY KEY,credits INTEGER NOT NULL CHECK(credits BETWEEN 1 AND 3));
            CREATE TABLE IF NOT EXISTS control_operations(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,body TEXT NOT NULL);
            ''')
            # executescript commits its initial DDL. Re-enter the transaction.
            db.execute('BEGIN IMMEDIATE')
            self.verify(db)

    @contextmanager
    def tx(self,initial=False,read_only=False,reservation=None):
        private_path(self.path.parent,self.path.name)
        self.budget.files(self.path)
        db = sqlite3.connect(self.path,timeout=1,isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA journal_mode=WAL'); db.execute('PRAGMA synchronous=FULL')
            if read_only:db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN' if read_only else 'BEGIN IMMEDIATE')
            if not initial:
                self.verify(db)
                if not read_only:
                    credit=0
                    if reservation is not None:
                        row=db.execute('SELECT credits FROM audit_reservations WHERE id=?',(ident(reservation),)).fetchone()
                        require(row is not None,'audit_reservation_missing')
                        credit=row[0]
                    self.budget.admit(self.budget.inventory(db),credit)
            yield db
            if db.in_transaction: db.execute('COMMIT')
        except sqlite3.OperationalError:
            if db.in_transaction: db.execute('ROLLBACK')
            raise OperatorError('storage_busy_or_unavailable',503) from None
        except BaseException:
            if db.in_transaction: db.execute('ROLLBACK')
            raise
        finally: db.close()

    def projection(self,db):
        self.budget.inventory(db)
        state={t:[list(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY 1,2')]
               for t in ('sources','intents','graphs')}
        # Addition-only schema migration: an unused new table must not invalidate
        # a verified older catalog. Once populated its complete rows are bound
        # into the same append-only projection; deletion still fails verification.
        for t in ('provider_versions','workers','governance_versions','governance_active','control_operations'):
            order='1,2,3,4' if t=='governance_versions' else '1,2,3'
            rows=[list(r) for r in db.execute('SELECT * FROM '+t+' ORDER BY '+order)]
            if rows:state[t]=rows
        rows=[list(r) for r in db.execute('SELECT * FROM audit_reservations ORDER BY id')]
        if rows:state['audit_reservations']=rows
        return digest(state)

    def verify(self,db):
        self.budget.inventory(db)
        previous = '0'*64; n = 0; last = None
        for row in db.execute('SELECT * FROM audit ORDER BY n'):
            body = json.loads(row['body']); n += 1
            if hasattr(self,'storage_policy_sha256') and 'storage_policy_sha256' in body:
                require(body['storage_policy_sha256']==self.storage_policy_sha256,'cas_policy_tampered')
            require(row['n']==n and row['prev']==previous and
                    row['sha']==digest(dict(n=n,body=body,previous=previous)), 'catalog_tampered')
            previous, last = row['sha'], body
        if last is None:
            require(all(db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] == 0
                        for t in ('sources','intents','graphs','provider_versions','workers','governance_versions','governance_active','audit_reservations','control_operations')),
                    'catalog_missing_history')
        else: require(last['projection']==self.projection(db), 'catalog_state_tampered')
        return n, previous

    def reserve_worker(self,db,worker_id):
        # Three catalogue receipts: dispatch-start, native-outcome, finish. Credits
        # are hash-bound durable state, not a hidden/in-memory capacity bypass.
        ident(worker_id);stats=self.budget.inventory(db)
        require(stats['events']+stats['reserved']+3<=self.budget.max_events,'audit_capacity_reached',429)
        require(stats['history_bytes']+(stats['reserved']+3)*self.budget.max_row_bytes<=self.budget.max_history_bytes,
                'audit_byte_capacity_reached',429)
        db.execute('INSERT INTO audit_reservations VALUES(?,3)',(worker_id,))

    def event(self,db,actor,action,target,details=None,*,tenant=None,before_hash=None,after_hash=None,authorization='ALLOW',reservation=None,final_reservation=False):
        row = db.execute('SELECT n,sha FROM audit ORDER BY n DESC LIMIT 1').fetchone()
        n,prev = (1,'0'*64) if row is None else (row['n']+1,row['sha'])
        if reservation is not None:
            credit=db.execute('SELECT credits FROM audit_reservations WHERE id=?',(ident(reservation),)).fetchone()
            require(credit is not None,'audit_reservation_missing')
            if final_reservation or credit[0]==1:db.execute('DELETE FROM audit_reservations WHERE id=?',(reservation,))
            else:db.execute('UPDATE audit_reservations SET credits=credits-1 WHERE id=?',(reservation,))
        else:
            require(not final_reservation,'audit_reservation_missing')
            stats=self.budget.inventory(db)
            require(stats['events']+stats['reserved']<self.budget.max_events,'audit_capacity_reached',429)
        body = dict(actor=actor,action=action,target=target,timestamp=timestamp(),
                    details=details or {},projection=self.projection(db))
        if hasattr(self,'storage_policy_sha256'):body['storage_policy_sha256']=self.storage_policy_sha256
        if tenant is not None:
            body.update(tenant=tenant,before_hash=before_hash,after_hash=after_hash,authorization=authorization)
        sha = digest(dict(n=n,body=body,previous=prev))
        encoded=canonical(body)
        self.budget.event(n,encoded,self.budget.inventory(db))
        db.execute('INSERT INTO audit VALUES(?,?,?,?)',(n,encoded.decode(),prev,sha))
        return sha

    def source(self,db,principal,source_id):
        row = db.execute('SELECT * FROM sources WHERE id=? AND tenant=?',(source_id,principal.tenant)).fetchone()
        require(row is not None, 'source_not_found',404)
        return json.loads(row['body'])

    def intent(self,db,principal,run_id):
        row = db.execute('SELECT * FROM intents WHERE id=? AND tenant=?',(run_id,principal.tenant)).fetchone()
        require(row is not None, 'run_not_found',404)
        return row,json.loads(row['body'])
