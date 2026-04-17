"""Service matcher — multilingual fuzzy matching with salon-specific aliases."""

from __future__ import annotations

import re

from thefuzz import fuzz

from models.service import Service

_FALLBACK_ALIASES: dict[str, list[str]] = {
    "haircut": [
        "hair cut",
        "haircutting",
        "hair cutting",
        "cutting",
        "baal katna",
        "baal katvana",
        "વાલ કાપવા",
        "વાળ કાપવા",
        "વાલ કપાવા",
        "વાળ કપાવા",
        "val kapva",
        "val kapava",
        "hair kat",
        "હેર કટ",
        "હેરકટ",
    ],
    "hair color": [
        "hair colour",
        "colouring",
        "coloring",
        "baal rangna",
        "વાલ રંગવા",
        "વાળ રંગવા",
        "val rangva",
        "હેર કલર",
        "હેર કલરિંગ",
    ],
    "facial": [
        "face treatment",
        "facial treatment",
        "ફેશિયલ",
        "ફેસિયલ",
        "feshiyal",
        "fesial",
    ],
    "manicure": [
        "મેનિક્યોર",
        "mani cure",
        "nail service",
    ],
    "pedicure": [
        "પેડિક્યોર",
        "pedi cure",
        "foot service",
    ],
    "hair spa": [
        "હેર સ્પા",
        "વાલ સ્પા",
        "વાળ સ્પા",
        "val spa",
        "hair treatment",
    ],
    "beard trim": [
        "દાઢી ટ્રિમ",
        "daadhi trim",
        "beard",
        "shaving",
        "trim",
    ],
    "threading": [
        "થ્રેડિંગ",
        "થ્રેડીંગ",
        "eyebrow",
        "eyebrow threading",
    ],
}


def _normalize(value: str) -> str:
    """Normalize text for matching across scripts and ASR variations."""
    value = value.strip().lower()
    value = re.sub(r"[^\w\s\u0900-\u097f\u0a80-\u0aff]", " ", value)
    return " ".join(value.split())


def _compact(value: str) -> str:
    """Remove spacing so split words like 'hair cut' and 'હેર કટ' still compare well."""
    return _normalize(value).replace(" ", "")


def _candidate_aliases(service: Service) -> list[str]:
    """Return DB aliases plus hard-coded salon-specific variants."""
    key = _normalize(service.name)
    aliases = [service.name, *(service.aliases or []), *(_FALLBACK_ALIASES.get(key, []))]

    deduped: list[str] = []
    seen = set()
    for alias in aliases:
        normalized = _normalize(alias)
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(alias)
    return deduped


def _score_pair(query: str, candidate: str) -> int:
    """Score a query against one candidate phrase using multiple fuzzy strategies."""
    normalized_query = _normalize(query)
    normalized_candidate = _normalize(candidate)
    compact_query = _compact(query)
    compact_candidate = _compact(candidate)

    return max(
        fuzz.ratio(normalized_query, normalized_candidate),
        fuzz.partial_ratio(normalized_query, normalized_candidate),
        fuzz.token_sort_ratio(normalized_query, normalized_candidate),
        fuzz.token_set_ratio(normalized_query, normalized_candidate),
        fuzz.ratio(compact_query, compact_candidate),
        fuzz.partial_ratio(compact_query, compact_candidate),
    )


def find_service(query: str, services: list[Service]) -> Service | None:
    """
    Match a spoken service name against DB services and their aliases.

    Uses a two-pass strategy:
    1. Exact match (normalized) — prevents 'haircut' from fuzzy-matching 'hair color'.
    2. Fuzzy match with a 65-point threshold.

    Supports English, Hindi, Gujarati, and common Romanized variants.
    """
    normalized_query = _normalize(query)
    if not normalized_query:
        return None

    compact_query = _compact(query)

    # ── Pass 1: Exact match on normalized or compact form ──
    for service in services:
        if normalized_query == _normalize(service.name):
            return service
        if compact_query == _compact(service.name):
            return service
        for alias in _candidate_aliases(service):
            if normalized_query == _normalize(alias):
                return service
            if compact_query == _compact(alias):
                return service

    # ── Pass 2: Fuzzy match with higher threshold ──
    best_match = None
    best_score = 0
    threshold = 65

    for service in services:
        for alias in _candidate_aliases(service):
            score = _score_pair(normalized_query, alias)
            if score > best_score:
                best_score = score
                best_match = service

    if best_score >= threshold:
        return best_match

    return None


def get_service_list_for_speech(services: list[Service]) -> str:
    """Format all services into a voice-friendly list for the AI to speak."""
    lines = []
    for service in services:
        lines.append(f"{service.name} ({service.duration} minutes, ₹{int(service.price)})")
    return ", ".join(lines)
