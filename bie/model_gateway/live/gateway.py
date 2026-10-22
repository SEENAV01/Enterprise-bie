"""LiveGateway: one validated structured answer per request, with bounded retries and a ledger.

Flow per request: validate → cache lookup → adapter call (transient failures retried with the
existing ``retry_policy``) → JSON parse (existing ``structured_output`` / ``malformed_repair``) →
strict schema validation (existing ``schema_validation``) → at most ``max_repairs`` repair turns
that show the model its validation error → cache store → ``ModelResponse`` with provenance.
Every provider call, failed or cached, becomes one ledger row with tokens and estimated cost.
With a ``CostGuard`` (``budget.py``) every call, retries and repairs included, first reserves its projected
cost; a call that would cross the run's rupee cap is not sent (ledger outcome ``stopped``).
"""
from __future__ import annotations

import time
from dataclasses import replace

from ..malformed_repair import RepairError, repair_json
from ..model_interface import ModelRequest, ModelResponse, validate_request
from ..model_provenance import ModelProvenance, request_hash, validate as validate_provenance
from ..retry_policy import RetryPolicy, delay, should_retry
from ..schema_validation import SchemaValidationError, validate as validate_schema
from ..structured_output import StructuredOutputError, parse_json
from .budget import STOP_KINDS, output_cap
from .disk_cache import cache_key
from .errors import ProviderError
from .ledger import UsageLedger
from .pricing import estimate_cost

DEFAULT_RETRY = RetryPolicy(max_attempts=4, base_delay=2.0, max_delay=60.0)
REPAIR_INSTRUCTION = ("Your previous answer did not match the required JSON schema: {problem}. "
                      "Reply again with the complete corrected JSON object only, matching the schema exactly.")


class LiveGateway:
    def __init__(self, routes: dict, *, ledger: UsageLedger | None = None, cache=None, retry: RetryPolicy = DEFAULT_RETRY,
                 max_repairs: int = 1, sleep=None, clock=time.monotonic, wall=time.time, env=None, guard=None):
        if not routes:
            raise ValueError("at least one route is required")
        if max_repairs < 0:
            raise ValueError("max_repairs must be >= 0")
        self.routes = dict(routes)
        self.ledger = ledger or UsageLedger()
        self.cache = cache
        self.retry = retry
        self.max_repairs = max_repairs
        self._sleep, self._clock, self._wall, self._env = sleep or time.sleep, clock, wall, env
        self.guard = guard

    def model_of(self, route: str) -> str:
        return self.routes[route].model

    def complete(self, route: str, request: ModelRequest, *, prompt_version: str, check=None,
                 expected_output_tokens: int | None = None) -> ModelResponse:
        """``check(value)`` may return a list of content problems; they are repaired like schema errors.
        ``expected_output_tokens`` overrides the cost guard's output projection for this request."""
        validate_request(request)
        if route not in self.routes:
            raise ProviderError("config", "unknown route " + repr(route))
        if not prompt_version:
            raise ProviderError("config", "prompt_version required")
        adapter = self.routes[route]
        provider, model, schema = adapter.provider, adapter.model, request.response_schema
        started = self._wall()
        identity = {"provider": provider, "model": model, "messages": list(request.messages), "schema": schema,
                    "temperature": request.temperature, "prompt_version": prompt_version}
        key = cache_key(**identity)
        via = getattr(getattr(adapter, "client", None), "via", "direct")
        base = {"request_id": request.request_id, "provider": provider, "via": via, "model": model, "prompt_version": prompt_version}

        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None and check is not None and list(check(hit.get("content"))):
                hit = None  # the content check changed since this answer was cached
            if hit is not None:
                self.ledger.record(**base, returned_model=hit.get("returned_model"), attempt=0, outcome="ok", cache_hit=True,
                                   input_tokens=0, output_tokens=0, reasoning_tokens=0, cost_usd=0.0, latency_ms=0)
                return self._response(provider, model, hit["content"], hit["usage"], hit["finish_reason"], identity,
                                      prompt_version, started, cache_hit=True, attempts=0, returned_model=hit.get("returned_model"), via=via)

        messages = list(request.messages)
        transient, repairs, attempt = 0, 0, 0
        total = {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "cached_input_tokens": 0}
        while True:
            attempt += 1
            reserved = self._reserve(request, messages, adapter, via, expected_output_tokens, base, attempt)
            t0 = self._clock()
            try:
                raw = adapter.invoke(replace(request, messages=tuple(messages)))
            except ProviderError as exc:
                self.ledger.record(**base, attempt=attempt, outcome="error", error_kind=exc.kind, cache_hit=False,
                                   latency_ms=round((self._clock() - t0) * 1000))
                if self.guard is not None:
                    self.guard.settle(request.request_id, reserved, 0.0, model=model)
                    if exc.kind in STOP_KINDS:
                        self.guard.trip(f"{exc.kind}: {provider} via {via}: {exc.message[:200]}")
                transient += 1
                if should_retry(exc.kind, transient, self.retry):
                    self._sleep(delay(transient, self.retry))
                    continue
                raise
            latency = round((self._clock() - t0) * 1000)
            returned_model = getattr(getattr(adapter, "client", None), "last_model", None) or model
            usage = {k: int((raw.get("usage") or {}).get(k) or 0) for k in total}
            for k in total:
                total[k] += usage[k]
            cost = estimate_cost(returned_model, usage, self._env, via)
            if cost is None:
                cost = estimate_cost(model, usage, self._env, via)
            if self.guard is not None:
                self.guard.settle(request.request_id, reserved, cost, model=model, output_tokens=usage["output_tokens"])
            text = raw.get("content")
            try:
                value = parse_json(text) if isinstance(text, dict) else repair_json(text)
                if schema is not None:
                    validate_schema(value, schema, strict=True)
                problems = list(check(value)) if check is not None else []
                problem = "; ".join(map(str, problems[:5])) if problems else None
            except (RepairError, StructuredOutputError) as exc:
                problem = "the reply was not a JSON object" + (f" ({exc})" if str(exc) else "")
            except SchemaValidationError as exc:
                problem = str(exc)
            row = dict(base, returned_model=returned_model, attempt=attempt, cache_hit=False, latency_ms=latency, cost_usd=cost,
                       input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"],
                       reasoning_tokens=usage["reasoning_tokens"])
            if problem is None:
                self.ledger.record(**row, outcome="ok")
                finish = raw.get("finish_reason", "unknown")
                if self.cache is not None:
                    self.cache.put(key, {"content": value, "usage": total, "finish_reason": finish, "returned_model": returned_model})
                return self._response(provider, model, value, total, finish, identity, prompt_version, started,
                                      cache_hit=False, attempts=attempt, returned_model=returned_model, via=via)
            self.ledger.record(**row, outcome="schema_invalid", error_kind="schema_invalid")
            if repairs >= self.max_repairs:
                raise ProviderError("schema_invalid", problem[:300], provider=provider)
            repairs += 1
            previous = text if isinstance(text, str) else str(text)
            messages += [{"role": "assistant", "content": previous[:20000]},
                         {"role": "user", "content": REPAIR_INSTRUCTION.format(problem=problem[:300])}]

    def _reserve(self, request, messages, adapter, via, expected_output_tokens, base, attempt):
        """Reserve the projected cost of the next call with the guard; record and re-raise a refusal."""
        if self.guard is None:
            return 0.0
        projection = self.guard.project(model=adapter.model, via=via, request=request, messages=messages,
                                        cap=output_cap(adapter), expected_output_tokens=expected_output_tokens)
        try:
            return self.guard.reserve(request.request_id, projection["usd"], model=adapter.model, provider=adapter.provider)
        except ProviderError:
            self.ledger.record(**base, attempt=attempt, outcome="stopped", error_kind="budget", cache_hit=False,
                               cost_usd=0.0, latency_ms=0)
            raise

    def _response(self, provider, model, content, usage, finish, identity, prompt_version, started, *, cache_hit,
                  attempts, returned_model, via="direct"):
        provenance = ModelProvenance(provider=provider, model=model, request_hash=request_hash(identity),
                                     prompt_version=prompt_version, started_at=started, finished_at=max(started, self._wall()))
        validate_provenance(provenance)
        record = dict(vars(provenance), cache_hit=cache_hit, attempts=attempts, returned_model=returned_model, via=via)
        return ModelResponse(provider=provider, model=model, content=content, usage=dict(usage), finish_reason=finish,
                             provenance=record)
