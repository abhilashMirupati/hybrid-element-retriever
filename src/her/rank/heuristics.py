"""Heuristic scoring for element ranking."""
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


def heuristic_score(
    descriptor: Dict[str, Any],
    phrase: str,
    action: Optional[str] = None
) -> float:
    """Calculate heuristic score for an element based on phrase match.
    
    Args:
        descriptor: Element descriptor
        phrase: Search phrase
        action: Optional action type (click, type, select, etc.)
    
    Returns:
        Score between 0.0 and 1.0
    """
    phrase_lower = phrase.lower().strip()
    words = phrase_lower.split()
    score = 0.0
    
    # Extract element properties
    tag = (descriptor.get("tag") or "").lower()
    text = (descriptor.get("text") or "").lower().strip()
    role = (descriptor.get("role") or "").lower()
    name = (descriptor.get("name") or "").lower()
    placeholder = (descriptor.get("placeholder") or "").lower()
    element_id = (descriptor.get("id") or "").lower()
    classes = descriptor.get("classes", [])
    element_type = (descriptor.get("type") or "").lower()
    aria_label = (descriptor.get("aria", {}).get("label", "")).lower()
    alt = (descriptor.get("alt") or "").lower()
    title = (descriptor.get("title") or "").lower()
    value = (descriptor.get("value") or "").lower()
    
    # Action-specific scoring
    if action == "click":
        # Prioritize clickable elements
        if tag in ["button", "a", "input"] or role in ["button", "link"]:
            score += 0.2
        if element_type in ["button", "submit", "reset"]:
            score += 0.2
    elif action == "type":
        # Prioritize input fields
        if tag in ["input", "textarea"] or role in ["textbox", "searchbox"]:
            score += 0.2
        if element_type in ["text", "email", "password", "search", "tel", "url"]:
            score += 0.2
    elif action == "select":
        # Prioritize select elements
        if tag == "select" or role == "combobox":
            score += 0.3
    
    # Text matching
    if text:
        # Exact match
        if phrase_lower == text:
            score += 0.5
        # Contains phrase
        elif phrase_lower in text:
            score += 0.3
        # Word overlap
        else:
            text_words = text.split()
            overlap = len(set(words) & set(text_words))
            if overlap > 0:
                score += 0.2 * (overlap / len(words))
    
    # Name/label matching
    for label_text in [name, aria_label, alt, title]:
        if label_text:
            if phrase_lower == label_text:
                score += 0.4
            elif phrase_lower in label_text:
                score += 0.2
            elif any(word in label_text for word in words):
                score += 0.1
    
    # Placeholder matching (important for input fields)
    if placeholder:
        if phrase_lower == placeholder:
            score += 0.3
        elif phrase_lower in placeholder:
            score += 0.2
        elif any(word in placeholder for word in words):
            score += 0.1
    
    # ID matching
    if element_id:
        # Convert ID from kebab/snake case to words
        id_words = re.split(r'[-_]', element_id)
        if any(word in id_words for word in words):
            score += 0.15
    
    # Class matching
    if classes:
        class_text = " ".join(classes).lower()
        if any(word in class_text for word in words):
            score += 0.1
    
    # Value matching (for current values in inputs)
    if value and phrase_lower in value:
        score += 0.1
    
    # Special patterns
    if "button" in phrase_lower and (
        tag == "button" or 
        role == "button" or 
        element_type == "button"
    ):
        score += 0.2
    
    if "link" in phrase_lower and (tag == "a" or role == "link"):
        score += 0.2
    
    if "input" in phrase_lower or "field" in phrase_lower:
        if tag in ["input", "textarea"] or role in ["textbox", "searchbox"]:
            score += 0.15
    
    # Visibility boost (if not hidden)
    if not descriptor.get("hidden") and not descriptor.get("disabled"):
        score += 0.05
    
    # Cap at 1.0
    return min(score, 1.0)


def rank_by_heuristics(
    descriptors: List[Dict[str, Any]],
    phrase: str,
    action: Optional[str] = None,
    top_k: int = 10
) -> List[Tuple[Dict[str, Any], float]]:
    """Rank elements by heuristic scores.
    
    Args:
        descriptors: List of element descriptors
        phrase: Search phrase
        action: Optional action type
        top_k: Number of top results to return
    
    Returns:
        List of (descriptor, score) tuples sorted by score
    """
    scored = []
    for desc in descriptors:
        score = heuristic_score(desc, phrase, action)
        if score > 0:
            scored.append((desc, score))
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[:top_k]


def explain_heuristic_score(
    descriptor: Dict[str, Any],
    phrase: str,
    action: Optional[str] = None
) -> Dict[str, Any]:
    """Explain how heuristic score was calculated.
    
    Args:
        descriptor: Element descriptor
        phrase: Search phrase
        action: Optional action type
    
    Returns:
        Dictionary with score breakdown
    """
    reasons = []
    phrase_lower = phrase.lower().strip()
    
    # Check various matching criteria and record reasons
    text = (descriptor.get("text") or "").lower().strip()
    if text and phrase_lower in text:
        reasons.append(f"Text contains '{phrase}'")
    
    name = (descriptor.get("name") or "").lower()
    if name and phrase_lower in name:
        reasons.append(f"Name contains '{phrase}'")
    
    placeholder = (descriptor.get("placeholder") or "").lower()
    if placeholder and phrase_lower in placeholder:
        reasons.append(f"Placeholder contains '{phrase}'")
    
    tag = descriptor.get("tag", "").lower()
    if action == "click" and tag in ["button", "a"]:
        reasons.append(f"Element is clickable ({tag})")
    elif action == "type" and tag in ["input", "textarea"]:
        reasons.append(f"Element is typeable ({tag})")
    
    score = heuristic_score(descriptor, phrase, action)
    
    return {
        "score": score,
        "reasons": reasons,
        "matched_properties": {
            "text": bool(text and phrase_lower in text),
            "name": bool(name and phrase_lower in name),
            "placeholder": bool(placeholder and phrase_lower in placeholder),
            "tag_match": bool(action and tag),
        }
    }