from __future__ import annotations
import hashlib,json,time
from ..canonical import canonical_json
from .errors import GameOperationsError
_FORBIDDEN={'source_text','answer_text','student_name','email','phone','prompt_text','book_text','raw_text'}
_ALLOWED={'event','game_id','level_id','challenge_id','attempt_number','outcome_code','mechanic_id','duration_bucket','objective_id','adaptation_id'}
class GovernedTelemetrySink:
    def __init__(self,db):
        self.db=db
        self.db.execute('''CREATE TABLE IF NOT EXISTS telemetry_events(session_id TEXT NOT NULL,sequence_id INTEGER NOT NULL,event_id TEXT NOT NULL UNIQUE,event_type TEXT NOT NULL,payload_json TEXT NOT NULL,policy_id TEXT NOT NULL,created REAL NOT NULL,PRIMARY KEY(session_id,sequence_id))''');self.db.commit()
    def record(self,session_id,event,consent,program_events,*,event_key=None):
        consent.validate()
        if not consent.enabled:return None
        if type(event) is not dict:raise GameOperationsError('GAME_TELEMETRY_EVENT_OBJECT')
        bad=set(event)-_ALLOWED
        sensitive=set(event)&_FORBIDDEN
        if bad or sensitive:raise GameOperationsError('GAME_TELEMETRY_FIELD_FORBIDDEN:'+','.join(sorted(bad or sensitive)))
        et=event.get('event')
        if et not in set(program_events):raise GameOperationsError('GAME_TELEMETRY_EVENT_NOT_ALLOWLISTED')
        if event_key is not None:
            from ..ids import require_id
            require_id(event_key,'GAME_TELEMETRY_REPLAY_KEY')
        payload=canonical_json(event).decode()
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            stable='telemetry:'+hashlib.sha256((session_id+'|'+event_key).encode()).hexdigest()[:24] if event_key is not None else None
            old=self.db.execute('SELECT sequence_id,payload_json,policy_id,event_type FROM telemetry_events WHERE event_id=?',(stable,)).fetchone() if stable else None
            if old:
                if old[1]!=payload or old[2]!=consent.policy_id:raise GameOperationsError('GAME_TELEMETRY_REPLAY_CONFLICT')
                return {'session_id':session_id,'sequence_id':old[0],'event_id':stable,'event_type':old[3],'payload':json.loads(payload),'policy_id':old[2]}
            seq=self.db.execute('SELECT COALESCE(MAX(sequence_id),0)+1 FROM telemetry_events WHERE session_id=?',(session_id,)).fetchone()[0]
            eid=stable or 'telemetry:'+hashlib.sha256(f'{session_id}|{seq}|{payload}|{consent.policy_id}'.encode()).hexdigest()[:24]
            self.db.execute('INSERT INTO telemetry_events VALUES(?,?,?,?,?,?,?)',(session_id,seq,eid,et,payload,consent.policy_id,time.time()))
        return {'session_id':session_id,'sequence_id':seq,'event_id':eid,'event_type':et,'payload':json.loads(payload),'policy_id':consent.policy_id}
    def export(self,session_id):
        rows=self.db.execute('SELECT sequence_id,event_id,event_type,payload_json,policy_id FROM telemetry_events WHERE session_id=? ORDER BY sequence_id',(session_id,)).fetchall()
        return tuple({'sequence_id':r[0],'event_id':r[1],'event_type':r[2],'payload':json.loads(r[3]),'policy_id':r[4]} for r in rows)
