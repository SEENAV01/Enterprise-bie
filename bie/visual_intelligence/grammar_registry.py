from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from .grammar_contracts import VisualGrammar, GrammarValidationError


class GrammarRegistryError(ValueError):
    pass


class GrammarNotFoundError(GrammarRegistryError):
    pass


class GrammarAmbiguityError(GrammarRegistryError):
    pass


@dataclass(frozen=True)
class RegistryResolution:
    grammar: VisualGrammar
    score: int
    matched_domain: str
    matched_representation: str


class VisualGrammarRegistry:
    """Deterministic, version-aware registry for visual semantic grammars.

    Registration is explicit. Resolution never silently breaks equal-score ties;
    the caller must provide more context instead of receiving an arbitrary grammar.
    """

    def __init__(self) -> None:
        self._grammars: dict[str, VisualGrammar] = {}
        self._aliases: dict[str, str] = {}

    def register(self, grammar: VisualGrammar) -> None:
        if grammar.grammar_id in self._grammars or grammar.grammar_id in self._aliases:
            raise GrammarRegistryError(f"duplicate grammar id: {grammar.grammar_id}")
        for alias in grammar.aliases:
            if alias in self._aliases or alias in self._grammars:
                raise GrammarRegistryError(f"duplicate grammar alias: {alias}")
        self._grammars[grammar.grammar_id] = grammar
        for alias in grammar.aliases:
            self._aliases[alias] = grammar.grammar_id

    def register_many(self, grammars: Iterable[VisualGrammar]) -> None:
        staged = list(grammars)
        probe = VisualGrammarRegistry()
        for existing in self._grammars.values():
            probe.register(existing)
        for grammar in staged:
            probe.register(grammar)
        self._grammars = probe._grammars
        self._aliases = probe._aliases

    def get(self, grammar_id_or_alias: str) -> VisualGrammar:
        if not isinstance(grammar_id_or_alias, str) or not grammar_id_or_alias.strip():
            raise GrammarRegistryError("grammar id must be non-blank")
        key = grammar_id_or_alias.strip()
        key = self._aliases.get(key, key)
        try:
            return self._grammars[key]
        except KeyError as exc:
            raise GrammarNotFoundError(f"unknown grammar: {grammar_id_or_alias}") from exc

    def list(self) -> tuple[VisualGrammar, ...]:
        return tuple(self._grammars[key] for key in sorted(self._grammars))

    def resolve(self, *, domain: str, representation: str, tags: Iterable[str] = ()) -> RegistryResolution:
        if not isinstance(domain, str) or not domain.strip():
            raise GrammarRegistryError("domain must be non-blank")
        if not isinstance(representation, str) or not representation.strip():
            raise GrammarRegistryError("representation must be non-blank")
        domain = domain.strip()
        representation = representation.strip()
        tag_set = {str(tag).strip() for tag in tags if str(tag).strip()}
        matches: list[RegistryResolution] = []
        for grammar in self._grammars.values():
            if domain in grammar.domains:
                domain_score = 4
                matched_domain = domain
            elif "*" in grammar.domains:
                domain_score = 1
                matched_domain = "*"
            else:
                continue
            if representation in grammar.representations:
                representation_score = 4
                matched_representation = representation
            elif "*" in grammar.representations:
                representation_score = 1
                matched_representation = "*"
            else:
                continue
            grammar_tags = set(grammar.tags)
            tag_score = 2 * len(tag_set & grammar_tags)
            missing_requested = len(tag_set - grammar_tags)
            score = domain_score + representation_score + tag_score - missing_requested
            matches.append(RegistryResolution(grammar, score, matched_domain, matched_representation))
        if not matches:
            raise GrammarNotFoundError(f"no grammar for domain={domain!r}, representation={representation!r}")
        matches.sort(key=lambda item: (-item.score, item.grammar.grammar_id))
        best = matches[0]
        tied = [m for m in matches if m.score == best.score]
        if len(tied) > 1:
            raise GrammarAmbiguityError(
                "ambiguous grammar resolution: " + ", ".join(m.grammar.grammar_id for m in tied)
            )
        return best

    def snapshot(self) -> dict:
        grammars = [grammar.snapshot() for grammar in self.list()]
        payload = {"grammars": grammars, "count": len(grammars)}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload["fingerprint"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload
