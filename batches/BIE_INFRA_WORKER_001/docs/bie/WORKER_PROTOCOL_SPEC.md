# BIE-INFRA-WORKER-001 — Distributed Worker Protocol & Capability-Aware Scheduling Contract

Status: IMPLEMENTED + CONTRACT TESTED

## Purpose
Define how BIE advertises worker capabilities, describes stage resource requirements, selects eligible workers, respects concurrency/resource limits, and routes tasks deterministically.

This contract sits above worker leases and below orchestration. It does not decide educational content.

## Worker capability model
A worker may advertise:
- cpu
- memory_gb
- gpu
- gpu_vram_gb
- remotion_render
- browser_runtime
- game_runtime
- python
- node
- ffmpeg
- vision_qa
- model_tool_access
- custom capabilities.

## Stage requirement model
A stage declares:
- required capabilities
- minimum CPU
- minimum memory
- GPU requirement and minimum VRAM
- maximum expected concurrency slot cost
- optional locality/data-affinity tags
- optional sandbox requirement
- optional timeout class.

## Scheduling invariants
1. A worker is eligible only if every hard capability requirement is met.
2. Resource minima are hard floors.
3. Concurrency capacity cannot be overcommitted.
4. GPU-required work cannot silently fall back to CPU.
5. Render/runtime stages may require sandbox/browser/tool capabilities.
6. Scheduler output is deterministic for the same inputs.
7. Worker health and lease ownership remain separate concerns.
8. Capability routing is provider-neutral.
9. Locality/affinity can influence ranking but cannot override hard requirements.
10. Unsupported task requirements fail explicitly.
11. Scheduling does not declare stage success.
12. Cost optimization is not a current priority; quality/capability fit wins first.

## Selection strategy
Reference scheduler ranks eligible workers by:
1. exact capability fit
2. resource headroom
3. affinity matches
4. current load
5. stable worker_id tie-break.

## Future production direction
The contract can later support:
- distributed queues
- Kubernetes worker pools
- GPU pools
- isolated render workers
- browser/game-runtime workers
- model/tool gateway workers
- regional/data-local scheduling.
