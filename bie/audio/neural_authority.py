"""H8-001: explicit live-provider network/credential authority.

This is an application-level authority boundary, not an HSM or cloud secret manager.
Provider credentials are resolved only at request time from an approved environment
binding and are never serialized into AUDIO evidence, call journals or command lines.
Network authority is exact-origin and fail-closed; it does not broaden the transport
allowlist already enforced by :mod:`bie.audio.neural_transport`.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import os
import re
from .common import AudioError, fingerprint, text, integer
from .neural_policy import API_ORIGIN, PROVIDER
from .tts_contract import ProviderFailure


@dataclass(frozen=True)
class LiveProviderPolicy:
    authority_revision: str
    egress_approved: bool
    credential_env: str = 'ELEVENLABS_API_KEY'
    provider_id: str = PROVIDER
    api_origin: str = API_ORIGIN
    max_session_calls: int = 512
    max_session_chars: int = 250_000
    max_inflight: int = 2
    admission_timeout_seconds: float = 10.0
    schema_version: str = 'bie.audio.live-provider-policy/1'

    def __post_init__(self):
        text(self.authority_revision, 'live authority revision', 256)
        if type(self.egress_approved) is not bool:
            raise AudioError('NEURAL_EGRESS_POLICY_BOOLEAN')
        if self.provider_id != PROVIDER or self.api_origin != API_ORIGIN:
            raise AudioError('NEURAL_NETWORK_ORIGIN_NOT_ADOPTED')
        if type(self.credential_env) is not str or not re.fullmatch(r'[A-Z][A-Z0-9_]{2,127}', self.credential_env):
            raise AudioError('NEURAL_CREDENTIAL_BINDING_INVALID')
        integer(self.max_session_calls, 'max session calls', 1, 10000)
        integer(self.max_session_chars, 'max session chars', 1, 10_000_000)
        integer(self.max_inflight, 'max inflight', 1, 32)
        if type(self.admission_timeout_seconds) not in (int, float) or not 0.05 <= self.admission_timeout_seconds <= 120:
            raise AudioError('NEURAL_ADMISSION_TIMEOUT_POLICY')
        if self.schema_version != 'bie.audio.live-provider-policy/1':
            raise AudioError('NEURAL_LIVE_POLICY_SCHEMA')

    def fingerprint(self):
        return fingerprint(self)


class EnvironmentSecretAuthority:
    """Resolve a provider secret from a named environment slot at call time.

    The mapping is held by reference so callers may rotate the environment value
    between calls without rebuilding persisted configuration. Python cannot promise
    memory zeroization; no such claim is made.
    """
    def __init__(self, policy: LiveProviderPolicy, *, environment=None):
        if type(policy) is not LiveProviderPolicy:
            raise AudioError('NEURAL_LIVE_POLICY_REQUIRED')
        self.policy = policy
        self._environment = os.environ if environment is None else environment
        if not hasattr(self._environment, 'get'):
            raise AudioError('NEURAL_CREDENTIAL_SOURCE_INVALID')

    def credential(self) -> str:
        if not self.policy.egress_approved:
            raise ProviderFailure('NEURAL_NETWORK_EGRESS_NOT_APPROVED')
        value = self._environment.get(self.policy.credential_env)
        if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{8,512}', value):
            raise ProviderFailure('NEURAL_CREDENTIALS_NOT_CONFIGURED')
        return value

    def receipt(self):
        return {
            'schema_version': 'bie.audio.secret-authority-receipt/1',
            'provider_id': self.policy.provider_id,
            'api_origin': self.policy.api_origin,
            'credential_binding': self.policy.credential_env,
            'authority_revision': self.policy.authority_revision,
            'authority_fingerprint': self.policy.fingerprint(),
            'secret_serialized': False,
            'secret_manager_or_hsm_verified': False,
            'product_accepted': False,
        }

    def __repr__(self):
        return f'EnvironmentSecretAuthority(provider_id={self.policy.provider_id!r}, credential=<redacted>)'


class LiveProviderAuthority:
    def __init__(self, policy: LiveProviderPolicy, *, environment=None):
        self.policy = policy
        self.secrets = EnvironmentSecretAuthority(policy, environment=environment)
        self.calls_authorized = 0
        self.chars_authorized = 0

    def preflight(self, requests):
        rows = tuple(requests)
        if len(rows) > self.policy.max_session_calls:
            raise ProviderFailure('NEURAL_WORKLOAD_CALL_BUDGET')
        total = 0
        for request in rows:
            try:
                count = len(request.segment.spoken_text)
            except Exception:
                raise ProviderFailure('NEURAL_WORKLOAD_REQUEST_INVALID') from None
            total += count
            if total > self.policy.max_session_chars:
                raise ProviderFailure('NEURAL_WORKLOAD_CHARACTER_BUDGET')
        # Resolve no credentials during preflight. This remains safe to run offline.
        return {'calls': len(rows), 'characters': total, 'truncated': False}

    def authorize(self, method: str, path: str, *, text_chars: int = 0) -> str:
        if not self.policy.egress_approved:
            raise ProviderFailure('NEURAL_NETWORK_EGRESS_NOT_APPROVED')
        # Transport remains the canonical path/method authority. This layer only
        # prevents a future caller from using the credential outside adopted API paths.
        get_ok = method == 'GET' and (path == '/v1/models' or re.fullmatch(r'/v1/voices/[A-Za-z0-9_-]{1,128}', path))
        post_ok = method == 'POST' and re.fullmatch(r'/v1/text-to-speech/[A-Za-z0-9_-]{1,128}/with-timestamps\?output_format=pcm_(16000|22050|24000)&enable_logging=(true|false)', path)
        if not (get_ok or post_ok):
            raise ProviderFailure('NEURAL_NETWORK_PATH_NOT_AUTHORIZED')
        if type(text_chars) is not int or text_chars < 0:
            raise ProviderFailure('NEURAL_WORKLOAD_REQUEST_INVALID')
        if self.calls_authorized + 1 > self.policy.max_session_calls or self.chars_authorized + text_chars > self.policy.max_session_chars:
            raise ProviderFailure('NEURAL_WORKLOAD_SESSION_BUDGET')
        secret = self.secrets.credential()
        self.calls_authorized += 1
        self.chars_authorized += text_chars
        return secret

    def receipt(self):
        return {
            **self.secrets.receipt(),
            'calls_authorized': self.calls_authorized,
            'characters_authorized': self.chars_authorized,
            'network_exact_origin_only': True,
        }

    def __repr__(self):
        return f'LiveProviderAuthority(policy={asdict(self.policy)!r}, credential=<redacted>)'
