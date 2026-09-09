from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Callable, Any, List, Optional
import math

class QueueWorkerError(ValueError): pass
class PermanentTaskError(QueueWorkerError): pass
class RetryableTaskError(QueueWorkerError): pass

@dataclass(frozen=True)
class RetryPolicy:
    base_delay_seconds:float=1.0
    max_delay_seconds:float=60.0
    multiplier:float=2.0

    def validate(self):
        if self.base_delay_seconds<0: raise QueueWorkerError("base delay must be >=0")
        if self.max_delay_seconds<self.base_delay_seconds: raise QueueWorkerError("max delay must be >= base")
        if self.multiplier<1.0: raise QueueWorkerError("multiplier must be >=1")

    def delay_for_delivery(self,delivery_count:int)->float:
        self.validate()
        if delivery_count<1: raise QueueWorkerError("delivery_count must be >=1")
        delay=self.base_delay_seconds*(self.multiplier**(delivery_count-1))
        return min(self.max_delay_seconds,delay)

@dataclass(frozen=True)
class ConsumerResult:
    task_id:str
    outcome:str
    delivery_count:int
    reason:str

class QueueWorkerConsumer:
    def __init__(
        self,
        queue,
        worker_runtime,
        requirements:Dict[str,Any],
        executors:Dict[str,Callable],
        commits:Dict[str,Callable],
        remediation_owners:Dict[str,str],
        retry_policy:Optional[RetryPolicy]=None
    ):
        self.queue=queue
        self.worker_runtime=worker_runtime
        self.requirements=requirements
        self.executors=executors
        self.commits=commits
        self.remediation_owners=remediation_owners
        self.retry_policy=retry_policy or RetryPolicy()
        self.retry_policy.validate()

    def _resolve_stage(self,stage_id:str):
        if stage_id not in self.requirements:
            raise PermanentTaskError(f"missing resource requirement for stage {stage_id}")
        if stage_id not in self.executors:
            raise PermanentTaskError(f"missing executor for stage {stage_id}")
        if stage_id not in self.commits:
            raise PermanentTaskError(f"missing commit adapter for stage {stage_id}")
        owner=self.remediation_owners.get(stage_id)
        if not owner:
            raise PermanentTaskError(f"missing remediation owner for stage {stage_id}")
        return self.requirements[stage_id],self.executors[stage_id],self.commits[stage_id],owner

    def consume_one(self,consumer_id:str,capability_tags:List[str],visibility_timeout:float=30.0)->Optional[ConsumerResult]:
        delivery=self.queue.poll(consumer_id,visibility_timeout,capability_tags)
        if delivery is None:
            return None

        task_msg=delivery.task
        count=delivery.delivery_count

        try:
            req,executor,commit,owner=self._resolve_stage(task_msg.stage_id)
        except PermanentTaskError as e:
            self.queue.dead_letter(task_msg.task_id,str(e))
            return ConsumerResult(task_msg.task_id,"DEAD_LETTER",count,str(e))

        # Lazy import shape adapter: the runtime only requires these fields.
        task=type("WorkerTaskAdapter",(),{
            "run_id":task_msg.run_id,
            "stage_id":task_msg.stage_id,
            "attempt":task_msg.attempt,
            "input_artifact_refs":list(task_msg.input_artifact_refs),
            "configuration":{}
        })()

        try:
            self.worker_runtime.execute(task,req,executor,commit,owner)
        except PermanentTaskError as e:
            self.queue.dead_letter(task_msg.task_id,str(e))
            return ConsumerResult(task_msg.task_id,"DEAD_LETTER",count,str(e))
        except Exception as e:
            delay=self.retry_policy.delay_for_delivery(count)
            try:
                self.queue.nack(task_msg.task_id,consumer_id,delay_seconds=delay,reason=f"retryable: {type(e).__name__}: {e}")
                state=self.queue.get(task_msg.task_id).state if hasattr(self.queue,"get") else "READY"
                outcome="DEAD_LETTER" if state=="DEAD_LETTER" else "RETRY"
                return ConsumerResult(task_msg.task_id,outcome,count,str(e))
            except Exception:
                # If NACK itself fails, do not ACK. Visibility timeout remains the fallback.
                return ConsumerResult(task_msg.task_id,"VISIBILITY_RECOVERY_PENDING",count,str(e))

        # Critical invariant: ACK only after runtime.execute returns, which occurs after fenced commit.
        self.queue.ack(task_msg.task_id,consumer_id)
        return ConsumerResult(task_msg.task_id,"ACKED",count,"fenced commit completed")

    def run_batch(self,consumer_id:str,capability_tags:List[str],max_messages:int=100,visibility_timeout:float=30.0)->List[ConsumerResult]:
        if max_messages<1: raise QueueWorkerError("max_messages must be >=1")
        out=[]
        for _ in range(max_messages):
            r=self.consume_one(consumer_id,capability_tags,visibility_timeout)
            if r is None: break
            out.append(r)
        return out
