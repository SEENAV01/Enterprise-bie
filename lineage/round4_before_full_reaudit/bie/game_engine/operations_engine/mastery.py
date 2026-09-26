from __future__ import annotations
import time
from ..director_engine.contracts import MasterySignal
from .contracts import MasteryRecord
class PersistentMasteryStore:
    def __init__(self,db):
        self.db=db;self.db.execute('''CREATE TABLE IF NOT EXISTS mastery_state(learner_key_hash TEXT NOT NULL,objective_id TEXT NOT NULL,estimate REAL NOT NULL,confidence REAL NOT NULL,attempts INTEGER NOT NULL,evidence_count INTEGER NOT NULL,version INTEGER NOT NULL,last_event_id TEXT NOT NULL,updated REAL NOT NULL,PRIMARY KEY(learner_key_hash,objective_id))''');self.db.commit()
    def get(self,learner,objective):
        r=self.db.execute('SELECT learner_key_hash,objective_id,estimate,confidence,attempts,evidence_count,version,last_event_id FROM mastery_state WHERE learner_key_hash=? AND objective_id=?',(learner,objective)).fetchone()
        return MasteryRecord(*r).validate() if r else None
    def update(self,learner,objective,outcome_code,mastery_weight,evidence_strength,event_id):
        prior=self.get(learner,objective);estimate=prior.estimate if prior else 0.0;confidence=prior.confidence if prior else 0.0;attempts=prior.attempts if prior else 0;count=prior.evidence_count if prior else 0;version=prior.version if prior else 0
        success=1.0 if outcome_code in {'applied','correct','success','mastered'} else 0.0;weight=max(.01,min(1.0,float(mastery_weight)*float(evidence_strength)));alpha=min(.55,.12+.43*weight)
        new_est=max(0.0,min(1.0,estimate+alpha*(success-estimate)));new_conf=max(0.0,min(1.0,1-(1-confidence)*(1-.28*weight)))
        rec=MasteryRecord(learner,objective,round(new_est,6),round(new_conf,6),attempts+1,count+1,version+1,event_id).validate()
        with self.db:self.db.execute('INSERT INTO mastery_state VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(learner_key_hash,objective_id) DO UPDATE SET estimate=excluded.estimate,confidence=excluded.confidence,attempts=excluded.attempts,evidence_count=excluded.evidence_count,version=excluded.version,last_event_id=excluded.last_event_id,updated=excluded.updated',(rec.learner_key_hash,rec.objective_id,rec.estimate,rec.confidence,rec.attempts,rec.evidence_count,rec.version,rec.last_event_id,time.time()))
        return rec
    def signals_for(self,document,learner):
        rows=[]
        for exp in document.experiences:
            for level in exp.levels:
                for ch in level.challenges:
                    prior=self.get(learner,ch.learning.objective_id)
                    if prior: rows.append(MasterySignal(prior.objective_id,prior.estimate,prior.confidence,prior.attempts,ch.learning.provenance).validate())
        by={x.objective_id:x for x in rows};return tuple(by[k] for k in sorted(by))
    def adaptation_for(self,record,target,had_misconception=False):
        if record.estimate>=target and record.confidence>=.6:return 'advance'
        if had_misconception and record.attempts>=1:return 'remediate'
        if record.confidence<.35:return 'repeat'
        return 'easier' if record.estimate<target*.6 else 'repeat'
