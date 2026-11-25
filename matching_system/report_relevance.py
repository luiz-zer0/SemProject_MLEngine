"""Conservative text-only relevance guard, independent of the found inventory.

This is a rule-based NLP check, not a trained classifier. It rejects clearly
off-topic standalone sentences and non-descriptions; uncertain text is allowed
through rather than rejecting an unfamiliar but legitimate lost item.
"""
import re

from matching_system.nlp_retrieval import normalize_report_text

INVALID_DESCRIPTION = (
    "Invalid item description. Describe the item itself, for example its colour, "
    "brand, size or identifying features."
)

# Full-sentence patterns, not keyword blacklists: chicken-shaped keyrings and
# descriptions of lost food containers must remain possible reports.
_OFF_TOPIC = (
    re.compile(r"(?:i|we) (?:had|ate|eat|eating|have eaten|was eating|were eating|am eating|are eating) [\w ]+ for (?:breakfast|lunch|dinner|supper)(?: today| yesterday| this morning| last night)?"),
    re.compile(r"(?:i|we) (?:had|ate) (?:breakfast|lunch|dinner|supper)(?: today| yesterday| this morning| last night)?"),
    re.compile(r"(?:hello|hi|hey|good morning|good afternoon|good evening|how are you|how are you doing|what is your name|what s your name|thank you|thanks|this is a test|testing|test|lorem ipsum(?: dolor sit amet)?)"),
)
# Do not reject words merely because they are outside the inventory vocabulary.
_ITEM_CONTEXT = re.compile(r"\b(?:lost|missing|found|misplaced|forgot|left behind|stolen|bag|bottle|box|container|keyring|keychain|charger|phone|wallet|book|case|toy|laptop|umbrella)\b")

def is_relevant_description(description: str) -> bool:
    """False only for recognizable off-topic or clearly unusable descriptions."""
    text = normalize_report_text(description)
    if not any(character.isalnum() for character in text):
        return False
    # These are unmistakable keyboard/filler patterns, not general short codes.
    if re.fullmatch(r"(?:asdf(?:ghjkl)?|qwerty(?:uiop)?|zxcv(?:bnm)?|abc(?:def)?|xyz)(?: (?:asdf(?:ghjkl)?|qwerty(?:uiop)?|zxcv(?:bnm)?|abc(?:def)?|xyz))*", text):
        return False
    if re.fullmatch(r"(\w)\1{5,}", text):
        return False
    if _ITEM_CONTEXT.search(text):
        return True
    return not any(pattern.fullmatch(text) for pattern in _OFF_TOPIC)
