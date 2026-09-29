"""Credential-free, source-bound preflight for a real PDF and H8 book plan.

This is inventory/readiness evidence only. It neither runs a stage nor creates
video/game output. Missing native stage registrations stay explicitly open.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os

from ..document_intelligence.real_pdf_toc_runtime import inspect_real_pdf_toc
from ..qa.assurance_quality_v2.harness import BookPlan, STAGES
from ..qa.operational_quality_v2.common import identity, inventory, regular_bytes
from ..qa.release_v2.contracts import ContractError


@dataclass(frozen=True, slots=True)
class NativeBookPreflight:
    source_hash: str
    byte_length: int
    page_count: int
    total_blocks: int
    plan_digest: str
    stage_status: tuple[tuple[str, str], ...]
    blockers: tuple[str, ...]

    def to_safe_dict(self):
        return {
            'schema_version': 'bie.qa.section16.native-book-preflight/1',
            'source_hash': self.source_hash,
            'byte_length': self.byte_length,
            'page_count': self.page_count,
            'total_blocks': self.total_blocks,
            'plan_digest': self.plan_digest,
            'stage_status': dict(self.stage_status),
            'blockers': self.blockers,
            'native_stage_execution': 'NOT_RUN',
            'generator_live_validation': 'NOT_RUN',
            'independent_assessor_live_validation': 'NOT_RUN',
            'video_native_execution': 'NOT_RUN',
            'game_native_execution': 'NOT_RUN',
            'rights_clearance': 'NOT_RUN',
            'section16_signed_off': False,
            'product_accepted': False,
        }


def preflight_native_pdf_book(
    data: bytes | bytearray,
    plan: BookPlan,
    *,
    expected_source_hash: str,
    expected_page_count: int,
    expected_total_blocks: int,
) -> NativeBookPreflight:
    """Check exact PDF/plan identity, canonical inspection and native registration.

    Program.verify reads installed executable/script bytes but does not run
    those programs. The PDF is not copied to an output or log by this function.
    """
    if type(data) not in (bytes, bytearray) or type(plan) is not BookPlan:
        raise ContractError('H39_REAL_BOOK_INPUT')
    if type(expected_source_hash) is not str or len(expected_source_hash) != 64 or any(c not in '0123456789abcdef' for c in expected_source_hash):
        raise ContractError('H39_REAL_BOOK_EXPECTED_HASH')
    if type(expected_page_count) is not int or expected_page_count < 1 or type(expected_total_blocks) is not int or expected_total_blocks < 0:
        raise ContractError('H39_REAL_BOOK_EXPECTED_INVENTORY')
    source_hash = hashlib.sha256(data).hexdigest()
    if source_hash != expected_source_hash:
        raise ContractError('H39_REAL_BOOK_SOURCE_HASH_MISMATCH')
    if len(plan.source_rows) != 1 or plan.source_rows[0] != {'path': plan.source_path, 'bytes': len(data), 'sha256': source_hash}:
        raise ContractError('H39_REAL_BOOK_PLAN_SOURCE_MISMATCH')
    if not plan.source_path.lower().endswith('.pdf'):
        raise ContractError('H39_REAL_BOOK_SOURCE_NOT_PDF')
    inspection = inspect_real_pdf_toc(data)
    if (inspection.source_hash, inspection.byte_length, inspection.page_count, inspection.total_blocks) != (source_hash, len(data), expected_page_count, expected_total_blocks):
        raise ContractError('H39_REAL_BOOK_BASELINE_MISMATCH')
    steps = {step.name: step for step in plan.steps}
    statuses = []
    blockers = set()
    if plan.profile != 'NATIVE':
        blockers.add('H39_DIAGNOSTIC_PLAN_NOT_NATIVE')
    for stage_name in STAGES:
        step = steps.get(stage_name)
        if step is None:
            status = 'NOT_REGISTERED'
            blockers.add('H39_MISSING_NATIVE_STAGE_REGISTRATION')
        elif step.stage.native_profile is None:
            status = 'DIAGNOSTIC_ONLY'
            blockers.add('H39_STAGE_NOT_NATIVE')
        elif not hasattr(os, 'O_NOFOLLOW'):
            status = 'PLATFORM_UNSUPPORTED'
            blockers.add('H39_NATIVE_IDENTITY_PLATFORM_UNSUPPORTED')
        else:
            try:
                step.stage.program.verify()
            except (ContractError, OSError):
                status = 'PROGRAM_IDENTITY_INVALID'
                blockers.add('H39_NATIVE_PROGRAM_IDENTITY_INVALID')
            else:
                profile = step.stage.native_profile
                checkout = step.stage.native_checkout
                try:
                    if inventory(checkout) != list(profile.checkout_rows):
                        raise ContractError('H39_NATIVE_CHECKOUT_CHANGED')
                    for worker_name, expected in (
                        ('linux_worker.py', profile.worker_sha256),
                        ('namespace_launcher.py', profile.launcher_sha256),
                    ):
                        if identity(regular_bytes(checkout, 'bie/compiler/' + worker_name)) != expected:
                            raise ContractError('H39_NATIVE_WORKER_CHANGED')
                except (ContractError, OSError):
                    status = 'NATIVE_WORKER_IDENTITY_INVALID'
                    blockers.add('H39_NATIVE_WORKER_IDENTITY_INVALID')
                else:
                    status = 'NATIVE_REGISTRATION_BYTES_VERIFIED'
        statuses.append((stage_name, status))
    return NativeBookPreflight(source_hash, len(data), inspection.page_count, inspection.total_blocks,
                               plan.content_digest, tuple(statuses), tuple(sorted(blockers)))
