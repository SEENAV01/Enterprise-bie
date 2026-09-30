"""Leakage checks and transactional attempt/denominator ledger (REG-004).

Candidate identities, campaign assignment, custody and training attestations
must come from the trusted scheduler. This module cannot prove what a model
has seen. Text near-duplicate checks are conservative triage, not a semantic
contamination detector. No public diagnostic can become a genuine holdout by
renaming its split.
"""
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any
from .models import BenchmarkError, canonical_json, digest, digest_string, ident, strict_loads
from .registry import Registry
from .versioning import Snapshot
from .governance import Approval, AuthorityStore


def leakage_report(snapshot: Snapshot, *, training_case_ids: frozenset[str] = frozenset(),
                   training_fingerprints: frozenset[str] = frozenset(),
                   training_groups: frozenset[str] = frozenset()) -> dict:
    cases = snapshot.cases
    findings: list[dict] = []
    for c in cases:
        if c.split in {"CALIBRATION", "HOLDOUT"} and (
            c.case_id in training_case_ids or c.problem_fingerprint in training_fingerprints or
            c.leakage_group in training_groups):
            findings.append({"code": "TRAIN_EVAL_OVERLAP", "case_ids": [c.case_id]})
    # Bounded reference implementation. Large corpora require an indexed adapter.
    # Reject excessive work before near-duplicate comparisons, never truncate cases.
    if len(cases) > 512 or any(len(c.prompt) > 2048 for c in cases):
        raise BenchmarkError("LEAKAGE_REVIEW_CAPACITY_EXCEEDED")
    problems = {c.case_id: c.problem_fingerprint for c in cases}
    prompts = {c.case_id: c.prompt_fingerprint for c in cases}
    normalized = {c.case_id: c.prompt.casefold() for c in cases}
    comparison_budget = 2_000_000
    for i, a in enumerate(cases):
        for b in cases[i + 1:]:
            if a.split != b.split and prompts[a.case_id] != prompts[b.case_id]:
                comparison_budget -= len(normalized[a.case_id]) * len(normalized[b.case_id])
                if comparison_budget < 0:
                    raise BenchmarkError("LEAKAGE_REVIEW_CAPACITY_EXCEEDED")
    for i, a in enumerate(cases):
        for b in cases[i + 1:]:
            if problems[a.case_id] == problems[b.case_id]:
                findings.append({"code": "DUPLICATE_PROBLEM", "case_ids": [a.case_id, b.case_id]})
            if a.split != b.split:
                if a.leakage_group == b.leakage_group:
                    findings.append({"code": "GROUP_SPLIT_LEAK", "case_ids": [a.case_id, b.case_id]})
                if prompts[a.case_id] == prompts[b.case_id]:
                    findings.append({"code": "PROMPT_SPLIT_LEAK", "case_ids": [a.case_id, b.case_id]})
                elif SequenceMatcher(None, normalized[a.case_id], normalized[b.case_id], autojunk=False).ratio() >= .94:
                    findings.append({"code": "NEAR_DUPLICATE_REVIEW_REQUIRED", "case_ids": [a.case_id, b.case_id]})
    return {"dataset_sha256": snapshot.sha256, "case_count": len(cases),
            "status": "BLOCKED" if findings else "CHECKED", "findings": findings,
            "training_history_independently_verified": False}


class AttemptLedger:
    def __init__(self, registry: Registry):
        self.registry = registry
        with registry.transaction():
            registry.connection.execute("""CREATE TABLE IF NOT EXISTS attempts (
                run_id TEXT PRIMARY KEY, scope_sha TEXT NOT NULL UNIQUE,
                state TEXT NOT NULL, roster_json TEXT NOT NULL, roster_sha TEXT NOT NULL,
                binding_json TEXT NOT NULL, binding_sha TEXT NOT NULL, report_json TEXT, report_sha TEXT)""")

    def start(self, *, run_id: str, campaign_id: str, candidate_sha256: str,
              policy_sha256: str, snapshot: Snapshot, split: str,
              authority_store: AuthorityStore | None = None,
              approvals: tuple[Approval, ...] = (), now: float = 0,
              review_evidence: dict[str, bytes] | None = None,
              training_case_ids: frozenset[str] = frozenset(),
              training_fingerprints: frozenset[str] = frozenset(),
              training_groups: frozenset[str] = frozenset()) -> str:
        ident(run_id)
        ident(campaign_id)
        digest_string(candidate_sha256)
        digest_string(policy_sha256)
        if split not in {"DEVELOPMENT", "CALIBRATION", "HOLDOUT"}:
            raise BenchmarkError("INVALID_SPLIT")
        roster = sorted(c.case_id for c in snapshot.cases if c.split == split)
        if not roster:
            raise BenchmarkError("EMPTY_EVALUATION_ROSTER")
        report = leakage_report(snapshot, training_case_ids=training_case_ids,
            training_fingerprints=training_fingerprints, training_groups=training_groups)
        if report["status"] != "CHECKED":
            raise BenchmarkError("LEAKAGE_BLOCKED")
        if split != "DEVELOPMENT":
            if authority_store is None:
                raise BenchmarkError("PROTECTED_EVALUATION_REQUIRES_AUTHORITY")
            authority_store.authorize_holdout(snapshot, approvals, now=now, evidence=review_evidence or {})
        binding = {"run_id": run_id, "campaign_id": campaign_id,
                   "candidate_sha256": candidate_sha256, "policy_sha256": policy_sha256,
                   "dataset_sha256": snapshot.sha256, "split": split}
        # Policy or run-ID changes do not buy another attempt at the same dataset/candidate.
        scope = digest({k: binding[k] for k in ("campaign_id", "candidate_sha256", "dataset_sha256", "split")})
        with self.registry.transaction():
            if self.registry.connection.execute("SELECT 1 FROM attempts WHERE run_id=? OR scope_sha=?", (run_id, scope)).fetchone():
                raise BenchmarkError("ATTEMPT_ALREADY_CLAIMED")
            self.registry.connection.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?)",
                (run_id, scope, "OPEN", canonical_json(roster), digest(roster), canonical_json(binding), digest(binding), None, None))
            self.registry._event("START_EVALUATION", {**binding, "roster_sha256": digest(roster), "denominator": len(roster)})
        return scope

    def _row(self, run_id: str) -> Any:
        ident(run_id)
        row = self.registry.connection.execute("SELECT * FROM attempts WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise BenchmarkError("RUN_NOT_FOUND")
        roster = strict_loads(row["roster_json"])
        if digest(roster) != row["roster_sha"] or type(roster) is not list or not roster or roster != sorted(set(roster)):
            raise BenchmarkError("ROSTER_TAMPERED")
        binding = strict_loads(row["binding_json"])
        scope = digest({k: binding[k] for k in ("campaign_id", "candidate_sha256", "dataset_sha256", "split")})
        if digest(binding) != row["binding_sha"] or binding["run_id"] != run_id or scope != row["scope_sha"]:
            raise BenchmarkError("RUN_BINDING_TAMPERED")
        return row

    def finalize(self, run_id: str, results: list[dict]) -> dict:
        """Results are written by trusted evaluator, never accepted as worker scores."""
        if type(results) is not list:
            raise BenchmarkError("INVALID_RESULTS")
        by: dict[str, dict] = {}
        for result in results:
            if type(result) is not dict or set(result) != {"case_id", "status", "evidence_sha256"}:
                raise BenchmarkError("INVALID_RESULT_FIELDS")
            ident(result["case_id"])
            digest_string(result["evidence_sha256"])
            if result["status"] not in {"PASS", "FAIL", "ERROR", "ABSTAIN"}:
                raise BenchmarkError("INVALID_RESULT_STATUS")
            if result["case_id"] in by:
                raise BenchmarkError("DUPLICATE_RESULT")
            by[result["case_id"]] = dict(result)
        with self.registry.transaction():
            row = self._row(run_id)
            if row["state"] != "OPEN":
                raise BenchmarkError("RUN_ALREADY_CLOSED")
            roster = strict_loads(row["roster_json"])
            if by.keys() - set(roster):
                raise BenchmarkError("UNEXPECTED_CASE_RESULT")
            missing = sorted(set(roster) - by.keys())
            passed = sum(r["status"] == "PASS" for r in by.values())
            report = {"binding": strict_loads(row["binding_json"]), "denominator": len(roster),
                "received_count": len(by), "passed_count": passed, "score": passed / len(roster),
                "missing_case_ids": missing, "results": [by[k] for k in sorted(by)],
                "status": "PASS" if not missing and passed == len(roster) else "FAIL",
                "release_authorized": False, "product_accepted": False}
            self.registry.connection.execute("UPDATE attempts SET state='CLOSED',report_json=?,report_sha=? WHERE run_id=?",
                (canonical_json(report), digest(report), run_id))
            self.registry._event("FINALIZE_EVALUATION", {"run_id": run_id, "report_sha256": digest(report)})
        return report

    def get_report(self, run_id: str) -> dict:
        row = self._row(run_id)
        if row["state"] != "CLOSED" or row["report_json"] is None:
            raise BenchmarkError("RUN_NOT_CLOSED")
        report = strict_loads(row["report_json"])
        if digest(report) != row["report_sha"] or report["binding"] != strict_loads(row["binding_json"]):
            raise BenchmarkError("REPORT_TAMPERED")
        return report
