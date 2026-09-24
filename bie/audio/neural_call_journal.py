"""H8-002: durable paid/remote POST intent and uncertain-completion journal.

Exactly-once remote synthesis is not asserted. A POST that becomes ambiguous is
persisted as UNCERTAIN and the same content/configuration identity is fail-closed
until an explicit operator resolution authorizes a new attempt. Confirmed cached
responses can reconcile the journal without a network call.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import re
import sqlite3
import time
import uuid
from .common import AudioError, fingerprint, text
from .tts_cache import safe_directory, key_lock
from .tts_contract import ProviderFailure

STATES = ('PREPARED','IN_FLIGHT','CONFIRMED','UNCERTAIN','REJECTED','REISSUE_AUTHORIZED')

@dataclass(frozen=True)
class CallTicket:
    call_key: str
    attempt_id: str
    attempt_no: int
    payload_sha256: str


class PaidCallJournal:
    def __init__(self, root, *, lock_timeout=10.0):
        if type(lock_timeout) not in (int, float) or not 0.1 <= lock_timeout <= 60:
            raise AudioError('NEURAL_CALL_JOURNAL_LOCK_POLICY')
        self.root = safe_directory(root)
        self.db = self.root / 'paid-calls.sqlite'
        self.lock = self.root / 'paid-calls.lock'
        self.lock_timeout = float(lock_timeout)
        self._initialize()

    def _connect(self):
        c = sqlite3.connect(self.db, timeout=self.lock_timeout, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA journal_mode=DELETE')
        c.execute('PRAGMA synchronous=FULL')
        return c

    def _initialize(self):
        with key_lock(self.lock, timeout=self.lock_timeout):
            c = self._connect()
            try:
                c.execute('''CREATE TABLE IF NOT EXISTS paid_calls(
                    call_key TEXT PRIMARY KEY,
                    request_fingerprint TEXT NOT NULL,
                    deployment_fingerprint TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempt_no INTEGER NOT NULL,
                    attempt_id TEXT NOT NULL,
                    provider_request_id TEXT,
                    response_sha256 TEXT,
                    http_status INTEGER,
                    resolution_ref TEXT,
                    authority_revision TEXT,
                    updated_ns INTEGER NOT NULL
                )''')
            finally: c.close()
        try: os.chmod(self.db, 0o600)
        except FileNotFoundError: pass

    @staticmethod
    def call_key(request_fingerprint, deployment_fingerprint, payload_sha256):
        for value in (request_fingerprint, deployment_fingerprint):
            if type(value) is not str or not value.startswith('sha256:'):
                raise AudioError('NEURAL_CALL_IDENTITY_INVALID')
        if type(payload_sha256) is not str or not re.fullmatch(r'[0-9a-f]{64}', payload_sha256):
            raise AudioError('NEURAL_CALL_PAYLOAD_HASH_INVALID')
        return fingerprint(('bie.audio.paid-neural-call/1', request_fingerprint, deployment_fingerprint, payload_sha256))

    def _row(self, c, call_key):
        return c.execute('SELECT * FROM paid_calls WHERE call_key=?',(call_key,)).fetchone()

    def prepare(self, *, request_fingerprint, deployment_fingerprint, payload_sha256):
        call_key = self.call_key(request_fingerprint, deployment_fingerprint, payload_sha256)
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:
                c.execute('BEGIN IMMEDIATE')
                row=self._row(c,call_key)
                now=time.time_ns()
                if row is None:
                    attempt_id='call-'+uuid.uuid4().hex
                    c.execute('INSERT INTO paid_calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                        call_key,request_fingerprint,deployment_fingerprint,payload_sha256,'PREPARED',1,attempt_id,None,None,None,None,None,now))
                    c.execute('COMMIT')
                    return CallTicket(call_key,attempt_id,1,payload_sha256)
                if row['request_fingerprint']!=request_fingerprint or row['deployment_fingerprint']!=deployment_fingerprint or row['payload_sha256']!=payload_sha256:
                    raise AudioError('NEURAL_CALL_JOURNAL_IDENTITY_CONFLICT')
                state=row['state']
                if state=='IN_FLIGHT':
                    c.execute('UPDATE paid_calls SET state=?,updated_ns=? WHERE call_key=?',('UNCERTAIN',now,call_key));c.execute('COMMIT')
                    raise ProviderFailure('NEURAL_UNCERTAIN_REMOTE_COMPLETION_REQUIRES_RESOLUTION')
                if state in ('UNCERTAIN','REJECTED'):
                    raise ProviderFailure('NEURAL_REMOTE_REISSUE_REQUIRES_RESOLUTION')
                if state=='CONFIRMED':
                    raise ProviderFailure('NEURAL_CONFIRMED_REMOTE_RESPONSE_REQUIRES_CACHE')
                if state=='REISSUE_AUTHORIZED':
                    attempt_no=row['attempt_no']+1;attempt_id='call-'+uuid.uuid4().hex
                    c.execute('UPDATE paid_calls SET state=?,attempt_no=?,attempt_id=?,provider_request_id=NULL,response_sha256=NULL,http_status=NULL,updated_ns=? WHERE call_key=?',
                              ('PREPARED',attempt_no,attempt_id,now,call_key));c.execute('COMMIT')
                    return CallTicket(call_key,attempt_id,attempt_no,payload_sha256)
                if state!='PREPARED': raise AudioError('NEURAL_CALL_JOURNAL_STATE')
                c.execute('COMMIT');return CallTicket(call_key,row['attempt_id'],row['attempt_no'],payload_sha256)
            except Exception:
                if c.in_transaction:c.execute('ROLLBACK')
                raise
            finally:c.close()

    def _transition(self,ticket,expected,state,**fields):
        if type(ticket) is not CallTicket:raise AudioError('NEURAL_CALL_TICKET_REQUIRED')
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:
                c.execute('BEGIN IMMEDIATE');row=self._row(c,ticket.call_key)
                if row is None or row['attempt_id']!=ticket.attempt_id or row['attempt_no']!=ticket.attempt_no or row['payload_sha256']!=ticket.payload_sha256:
                    raise AudioError('NEURAL_CALL_TICKET_STALE')
                if row['state'] not in expected:raise AudioError('NEURAL_CALL_STATE_TRANSITION')
                allowed={'provider_request_id','response_sha256','http_status'}
                if set(fields)-allowed:raise AudioError('NEURAL_CALL_TRANSITION_FIELDS')
                values={'provider_request_id':row['provider_request_id'],'response_sha256':row['response_sha256'],'http_status':row['http_status']};values.update(fields)
                c.execute('UPDATE paid_calls SET state=?,provider_request_id=?,response_sha256=?,http_status=?,updated_ns=? WHERE call_key=?',
                    (state,values['provider_request_id'],values['response_sha256'],values['http_status'],time.time_ns(),ticket.call_key));c.execute('COMMIT')
            except Exception:
                if c.in_transaction:c.execute('ROLLBACK')
                raise
            finally:c.close()

    def mark_in_flight(self,ticket):self._transition(ticket,('PREPARED',),'IN_FLIGHT')
    def mark_uncertain(self,ticket):self._transition(ticket,('IN_FLIGHT',),'UNCERTAIN')
    def mark_rejected(self,ticket,*,http_status=None):
        if http_status is not None and (type(http_status)is not int or not 100<=http_status<=599):raise AudioError('NEURAL_CALL_HTTP_STATUS')
        self._transition(ticket,('IN_FLIGHT',),'REJECTED',http_status=http_status)
    def mark_confirmed(self,ticket,*,provider_request_id,response_sha256,http_status=200):
        text(provider_request_id,'provider request id',256)
        if type(response_sha256)is not str or not re.fullmatch(r'[0-9a-f]{64}',response_sha256):raise AudioError('NEURAL_CALL_RESPONSE_HASH')
        if http_status!=200:raise AudioError('NEURAL_CALL_CONFIRMED_STATUS')
        self._transition(ticket,('IN_FLIGHT',),'CONFIRMED',provider_request_id=provider_request_id,response_sha256=response_sha256,http_status=http_status)

    def reconcile_cached(self,*,request_fingerprint,deployment_fingerprint,payload_sha256,provider_request_id,response_sha256):
        call_key=self.call_key(request_fingerprint,deployment_fingerprint,payload_sha256);text(provider_request_id,'provider request id',256)
        if type(response_sha256)is not str or not re.fullmatch(r'[0-9a-f]{64}',response_sha256):raise AudioError('NEURAL_CALL_RESPONSE_HASH')
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:
                c.execute('BEGIN IMMEDIATE');row=self._row(c,call_key);now=time.time_ns()
                if row is None:
                    c.execute('INSERT INTO paid_calls VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                        call_key,request_fingerprint,deployment_fingerprint,payload_sha256,'CONFIRMED',1,'reconciled-cache',provider_request_id,response_sha256,200,'cached-response-reconciliation','cache',now))
                else:
                    if row['request_fingerprint']!=request_fingerprint or row['deployment_fingerprint']!=deployment_fingerprint or row['payload_sha256']!=payload_sha256:raise AudioError('NEURAL_CALL_JOURNAL_IDENTITY_CONFLICT')
                    if row['state']=='CONFIRMED' and ((row['provider_request_id'] and row['provider_request_id']!=provider_request_id) or (row['response_sha256'] and row['response_sha256']!=response_sha256)):
                        raise AudioError('NEURAL_CALL_CONFIRMED_CACHE_CONFLICT')
                    c.execute('UPDATE paid_calls SET state=?,provider_request_id=?,response_sha256=?,http_status=200,updated_ns=? WHERE call_key=?',('CONFIRMED',provider_request_id,response_sha256,now,call_key))
                c.execute('COMMIT')
            except Exception:
                if c.in_transaction:c.execute('ROLLBACK')
                raise
            finally:c.close()
        return call_key

    def authorize_reissue(self,call_key,*,resolution_ref,authority_revision):
        text(resolution_ref,'remote-call resolution evidence',2048);text(authority_revision,'resolution authority revision',256)
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:
                c.execute('BEGIN IMMEDIATE');row=self._row(c,call_key)
                if row is None:raise AudioError('NEURAL_CALL_NOT_FOUND')
                if row['state'] not in ('UNCERTAIN','REJECTED'):raise AudioError('NEURAL_CALL_RESOLUTION_STATE')
                c.execute('UPDATE paid_calls SET state=?,resolution_ref=?,authority_revision=?,updated_ns=? WHERE call_key=?',
                    ('REISSUE_AUTHORIZED',resolution_ref,authority_revision,time.time_ns(),call_key));c.execute('COMMIT')
            except Exception:
                if c.in_transaction:c.execute('ROLLBACK')
                raise
            finally:c.close()

    def safe_state(self,call_key):
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:row=self._row(c,call_key)
            finally:c.close()
        if row is None:raise AudioError('NEURAL_CALL_NOT_FOUND')
        return {k:row[k] for k in ('call_key','state','attempt_no','attempt_id','provider_request_id','response_sha256','http_status','resolution_ref','authority_revision')}

    def safe_states(self):
        with key_lock(self.lock, timeout=self.lock_timeout):
            c=self._connect()
            try:rows=c.execute('SELECT call_key,state,attempt_no,attempt_id,provider_request_id,response_sha256,http_status,resolution_ref,authority_revision FROM paid_calls ORDER BY call_key').fetchall()
            finally:c.close()
        return [dict(r) for r in rows]
