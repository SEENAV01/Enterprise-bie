from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any

class ExecutorRuntimeError(ValueError): pass

@dataclass(frozen=True)
class WorkerTask:
    run_id:str
    stage_id:str
    attempt:int
    input_artifact_refs:List[str]
    configuration:Dict[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class WorkerExecutionContext:
    task:WorkerTask
    worker_id:str
    fencing_token:int
    heartbeat:Callable[[],None]

@dataclass(frozen=True)
class WorkerExecutionResult:
    output_artifact_refs:List[str]
    evidence_refs:List[str]
    metadata:Dict[str,Any]=field(default_factory=dict)

    def validate(self):
        if not self.output_artifact_refs:
            raise ExecutorRuntimeError("worker result requires output artifacts")
        if not self.evidence_refs:
            raise ExecutorRuntimeError("worker result requires evidence")

@dataclass(frozen=True)
class WorkerExecutionFailure:
    diagnostics:List[str]
    evidence_refs:List[str]
    remediation_owner:str

class LeaseAdapter:
    """Minimal protocol adapter around LeaseManager-like implementations."""
    def acquire(self,key,worker_id,ttl_seconds): ...
    def renew(self,token,ttl_seconds): ...
    def release(self,token): ...
    def commit_guard(self,token): ...

class SchedulerAdapter:
    def select(self,requirement): ...
    def reserve(self,selection,requirement): ...
    def release(self,worker_id,slot_cost=1): ...

class WorkerExecutorRuntime:
    def __init__(
        self,
        scheduler,
        lease_manager,
        ownership_guard,
        lease_key_factory:Callable[[str,str,int],Any],
        lease_ttl_seconds:float=30.0,
    ):
        if lease_ttl_seconds<=0:
            raise ExecutorRuntimeError("lease ttl must be >0")
        self.scheduler=scheduler
        self.leases=lease_manager
        self.guard=ownership_guard
        self.lease_key_factory=lease_key_factory
        self.lease_ttl_seconds=lease_ttl_seconds

    def execute(
        self,
        task:WorkerTask,
        requirement,
        executor:Callable[[WorkerExecutionContext],WorkerExecutionResult],
        commit:Callable[[WorkerExecutionContext,WorkerExecutionResult],None],
        remediation_owner:str
    )->WorkerExecutionResult:
        if not remediation_owner:
            raise ExecutorRuntimeError("remediation_owner required")

        selection=self.scheduler.select(requirement)
        worker_id=selection.worker_id
        reserved=False
        lease=None

        try:
            self.scheduler.reserve(selection,requirement)
            reserved=True

            key=self.lease_key_factory(task.run_id,task.stage_id,task.attempt)
            lease=self.leases.acquire(key,worker_id,self.lease_ttl_seconds)

            current_token=[lease]

            def heartbeat():
                renewed=self.leases.renew(current_token[0],self.lease_ttl_seconds)
                current_token[0]=renewed

            ctx=WorkerExecutionContext(task,worker_id,current_token[0].fencing_token,heartbeat)

            try:
                result=executor(ctx)
            except Exception as e:
                raise ExecutorRuntimeError(f"executor failed: {type(e).__name__}: {e}") from e

            result.validate()

            # Rebuild context using latest lease token after any heartbeats.
            final_lease=current_token[0]
            final_ctx=WorkerExecutionContext(task,worker_id,final_lease.fencing_token,heartbeat)

            self.guard.authorize_state_write(
                final_lease,task.run_id,task.stage_id,task.attempt
            )
            self.guard.authorize_artifact_write(
                final_lease,task.run_id,task.stage_id,task.attempt
            )

            commit(final_ctx,result)
            return result

        finally:
            cleanup_errors=[]
            if lease is not None:
                try:
                    # Release latest active token if executor heartbeated.
                    current=self.leases.active_lease(lease.key)
                    if current is not None and current.worker_id==worker_id:
                        self.leases.release(current)
                except Exception as e:
                    cleanup_errors.append(f"lease cleanup: {e}")
            if reserved:
                try:
                    self.scheduler.release(worker_id,requirement.slot_cost)
                except Exception as e:
                    cleanup_errors.append(f"capacity cleanup: {e}")
            if cleanup_errors:
                # In production these become infra evidence artifacts.
                pass
