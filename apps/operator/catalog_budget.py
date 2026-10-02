"""Local catalogue resource ceilings, not engine/CAS/distributed quotas.

Every producer uses Catalog.tx/event. Integrity verification remains complete;
oversized histories fail closed, never truncate, cache or synthesize a receipt.
Existing data above these ceilings needs an explicit governed storage decision.
"""
from dataclasses import dataclass,fields
from pathlib import Path
from .contracts import private_path,require

TABLES=('sources','intents','graphs','provider_versions','workers','governance_versions','governance_active','audit_reservations')
BODY_TABLES=frozenset(TABLES)-{'graphs','audit_reservations'}

@dataclass(frozen=True)
class CatalogBudget:
    max_events:int=65536
    max_state_rows:int=32768
    max_state_bytes:int=16*1024*1024
    max_history_bytes:int=32*1024*1024
    max_row_bytes:int=32*1024
    max_database_bytes:int=128*1024*1024
    max_wal_bytes:int=32*1024*1024

    def __post_init__(self):
        ceilings={'max_events':65536,'max_state_rows':32768,'max_state_bytes':16*1024*1024,
            'max_history_bytes':32*1024*1024,'max_row_bytes':32*1024,
            'max_database_bytes':128*1024*1024,'max_wal_bytes':32*1024*1024}
        for field in fields(self):
            value=getattr(self,field.name)
            require(type(value) is int and 0<value<=ceilings[field.name],'catalog_budget_invalid',400)

    def files(self,path):
        path=Path(path)
        for suffix,limit in (('',self.max_database_bytes),('-wal',self.max_wal_bytes),('-shm',1024*1024)):
            target=private_path(path.parent,path.name+suffix)
            require(not target.exists() or (target.is_file() and target.stat().st_size<=limit),
                    'catalog_storage_capacity_reached',503)

    def inventory(self,db):
        rows=state_bytes=0
        for table in TABLES:
            # Closed internal table/column names. SQL aggregate bounds before
            # Python materializes a projection or decodes any row body.
            columns=('body',) if table in BODY_TABLES else ('id','credits') if table=='audit_reservations' else ('run','kind','artifact','sha')
            size='+'.join('length(CAST('+column+' AS BLOB))' for column in columns)
            count,total,largest=db.execute('SELECT COUNT(*),COALESCE(SUM('+size+'),0),COALESCE(MAX('+size+'),0) FROM '+table).fetchone()
            require(largest<=self.max_row_bytes,'catalog_row_capacity_reached',503)
            rows+=count;state_bytes+=total
        count,total,largest,last=db.execute('SELECT COUNT(*),COALESCE(SUM(length(CAST(body AS BLOB))),0),'
            'COALESCE(MAX(length(CAST(body AS BLOB))),0),COALESCE(MAX(n),0) FROM audit').fetchone()
        reserved=db.execute('SELECT COALESCE(SUM(credits),0) FROM audit_reservations').fetchone()[0]
        require(count+reserved<=self.max_events and last<=self.max_events,'audit_capacity_reached',429)
        require(largest<=self.max_row_bytes,'catalog_row_capacity_reached',503)
        require(rows<=self.max_state_rows and state_bytes<=self.max_state_bytes,'catalog_state_capacity_reached',429)
        require(total+reserved*self.max_row_bytes<=self.max_history_bytes,'audit_byte_capacity_reached',429)
        return dict(events=count,state_rows=rows,state_bytes=state_bytes,history_bytes=total,reserved=reserved)

    def admit(self,stats,reserved_credits=0):
        # Conservative write admission; even an idempotent no-op may be rejected
        # at capacity. Reads stay available at the exact ceiling. This is not a
        # atomicity guarantee over canonical queue/persistence/CAS. Internal
        # worker credits reserve catalogue receipts only, not native store space.
        require(reserved_credits>0 or stats['events']+stats['reserved']<self.max_events,'audit_capacity_reached',429)
        require(reserved_credits>0 or (stats['state_rows']<self.max_state_rows and stats['state_bytes']<self.max_state_bytes),
                'catalog_state_capacity_reached',429)
        require(reserved_credits>0 or stats['history_bytes']+stats['reserved']*self.max_row_bytes<self.max_history_bytes,
                'audit_byte_capacity_reached',429)

    def event(self,number,encoded,stats):
        require(number+stats['reserved']<=self.max_events,'audit_capacity_reached',429)
        require(len(encoded)<=self.max_row_bytes,'catalog_row_capacity_reached',503)
        require(stats['history_bytes']+len(encoded)+stats['reserved']*self.max_row_bytes<=self.max_history_bytes,
                'audit_byte_capacity_reached',429)
