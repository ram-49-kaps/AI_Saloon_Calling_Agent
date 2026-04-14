"""Service matcher — fuzzy multilingual service name matching."""

from thefuzz import fuzz

from models.service import Service


def find_service(query: str, services: list[Service]) -> Service | None:
    """
    Fuzzy match a spoken service name against DB services and their aliases.

    Supports English, Hindi, and Gujarati through alias matching.
    Uses thefuzz library with a 60% threshold for flexible matching.

    Args:
        query: The service name spoken by the customer (any language).
        services: List of Service objects from the database.

    Returns:
        Best matching Service, or None if no match above threshold.
    """
    query = query.strip().lower()
    best_match = None
    best_score = 0
    threshold = 60  # Match score threshold

    for service in services:
        # Check against main name
        score = fuzz.ratio(query, service.name.lower())
        if score > best_score:
            best_score = score
            best_match = service

        # Also try partial ratio for substring matches (e.g., "hair" matches "haircut")
        partial_score = fuzz.partial_ratio(query, service.name.lower())
        if partial_score > best_score:
            best_score = partial_score
            best_match = service

        # Check against all aliases (Hindi, Gujarati, etc.)
        for alias in (service.aliases or []):
            alias_score = fuzz.ratio(query, alias.lower())
            if alias_score > best_score:
                best_score = alias_score
                best_match = service

            partial_alias_score = fuzz.partial_ratio(query, alias.lower())
            if partial_alias_score > best_score:
                best_score = partial_alias_score
                best_match = service

    if best_score >= threshold:
        return best_match

    return None


def get_service_list_for_speech(services: list[Service]) -> str:
    """Format all services into a voice-friendly list for the AI to speak."""
    lines = []
    for s in services:
        lines.append(f"{s.name} ({s.duration} minutes, ₹{int(s.price)})")
    return ", ".join(lines)
