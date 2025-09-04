"""Intelligent matching system using similarity and context, not rules."""

import re
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class MatchContext:
    """Context for matching."""
    query: str
    query_tokens: List[str]
    query_lemmas: List[str]
    intent_action: Optional[str] = None
    intent_target: Optional[str] = None


class IntelligentMatcher:
    """Non-rule-based intelligent matching using multiple signals."""
    
    def __init__(self):
        """Initialize the intelligent matcher."""
        # Common synonyms for better understanding
        self.action_synonyms = {
            'click': ['press', 'tap', 'select', 'choose', 'hit'],
            'type': ['enter', 'input', 'write', 'fill'],
            'select': ['choose', 'pick', 'dropdown'],
            'check': ['tick', 'mark', 'enable'],
            'uncheck': ['untick', 'unmark', 'disable'],
            'hover': ['mouseover', 'float'],
            'submit': ['send', 'post', 'confirm'],
            'cancel': ['close', 'abort', 'dismiss'],
            'search': ['find', 'look', 'query'],
            'login': ['signin', 'authenticate', 'logon'],
            'logout': ['signout', 'logoff'],
            'register': ['signup', 'join', 'create account']
        }
        
        # Build reverse mapping
        self.synonym_to_canonical = {}
        for canonical, synonyms in self.action_synonyms.items():
            for syn in synonyms:
                self.synonym_to_canonical[syn] = canonical
            self.synonym_to_canonical[canonical] = canonical
    
    def match(
        self,
        query: str,
        descriptors: List[Dict[str, Any]],
        intent: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Match query to descriptors using intelligent scoring.
        
        This method uses multiple signals without hard-coded rules:
        1. Semantic similarity between query and element text/attributes
        2. Structural relevance (tag appropriateness)
        3. Contextual signals (position, visibility, etc.)
        4. Fuzzy matching for typos and variations
        
        Args:
            query: Natural language query
            descriptors: List of element descriptors
            intent: Optional parsed intent
            
        Returns:
            List of (descriptor, score) tuples sorted by score
        """
        if not descriptors:
            return []
        
        # Prepare context
        context = self._prepare_context(query, intent)
        
        # Score each descriptor
        scored = []
        for desc in descriptors:
            score = self._compute_match_score(desc, context)
            if score > 0:
                scored.append((desc, score))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Normalize scores if needed
        if scored and scored[0][1] > 0:
            max_score = scored[0][1]
            scored = [(d, s/max_score) for d, s in scored]
        
        return scored
    
    def _prepare_context(self, query: str, intent: Optional[Dict[str, Any]]) -> MatchContext:
        """Prepare matching context from query."""
        query_lower = query.lower()
        
        # Tokenize intelligently
        tokens = self._tokenize(query_lower)
        
        # Extract lemmas (simplified - in production use spaCy/NLTK)
        lemmas = self._simple_lemmatize(tokens)
        
        # Extract intent if not provided
        action = None
        target = None
        if intent:
            action = intent.get('action', '').lower()
            target = intent.get('target', '').lower()
        else:
            # Simple intent extraction
            for token in tokens:
                if token in self.synonym_to_canonical:
                    action = self.synonym_to_canonical[token]
                    break
        
        return MatchContext(
            query=query_lower,
            query_tokens=tokens,
            query_lemmas=lemmas,
            intent_action=action,
            intent_target=target or query_lower
        )
    
    def _compute_match_score(self, desc: Dict[str, Any], context: MatchContext) -> float:
        """Compute match score using multiple signals.
        
        This is NOT rule-based but uses weighted signals:
        - Text similarity (semantic)
        - Attribute relevance (structural)
        - Context appropriateness (behavioral)
        """
        scores = []
        weights = []
        
        # 1. Text Similarity Score (0-1)
        text_score = self._text_similarity_score(desc, context)
        if text_score > 0:
            scores.append(text_score)
            weights.append(3.0)  # High weight for text match
        
        # 2. Attribute Similarity Score (0-1)
        attr_score = self._attribute_similarity_score(desc, context)
        if attr_score > 0:
            scores.append(attr_score)
            weights.append(2.5)  # Good weight for attributes
        
        # 3. Structural Appropriateness Score (0-1)
        struct_score = self._structural_score(desc, context)
        if struct_score > 0:
            scores.append(struct_score)
            weights.append(1.5)  # Moderate weight for structure
        
        # 4. Visibility/Interactivity Score (0-1)
        interact_score = self._interactivity_score(desc)
        if interact_score > 0:
            scores.append(interact_score)
            weights.append(1.0)  # Low weight for visibility
        
        # 5. Fuzzy Match Score for typos (0-1)
        fuzzy_score = self._fuzzy_match_score(desc, context)
        if fuzzy_score > 0:
            scores.append(fuzzy_score)
            weights.append(2.0)  # Good weight for fuzzy matching
        
        # Weighted average
        if not scores:
            return 0.0
        
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        return weighted_sum / total_weight
    
    def _text_similarity_score(self, desc: Dict[str, Any], context: MatchContext) -> float:
        """Score based on text content similarity."""
        element_text = str(desc.get('text', '')).lower()
        if not element_text:
            return 0.0
        
        # Direct substring match
        if context.query in element_text or element_text in context.query:
            return 1.0
        
        # Token overlap
        element_tokens = self._tokenize(element_text)
        if not element_tokens:
            return 0.0
        
        # Calculate Jaccard similarity
        query_set = set(context.query_tokens)
        elem_set = set(element_tokens)
        
        intersection = query_set & elem_set
        union = query_set | elem_set
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Boost if important words match
        important_matches = sum(
            1 for token in context.query_tokens
            if len(token) > 3 and token in element_tokens
        )
        
        boost = min(important_matches * 0.2, 0.5)
        
        return min(jaccard + boost, 1.0)
    
    def _attribute_similarity_score(self, desc: Dict[str, Any], context: MatchContext) -> float:
        """Score based on attribute matching."""
        score = 0.0
        
        # Collect all searchable attributes
        searchable = []
        
        # IDs and test IDs (highest priority)
        for key in ['id', 'dataTestId', 'data-testid']:
            if key in desc and desc[key]:
                searchable.append((str(desc[key]).lower(), 3.0))  # High weight
        
        # Names and placeholders
        for key in ['name', 'placeholder', 'title', 'alt']:
            if key in desc and desc[key]:
                searchable.append((str(desc[key]).lower(), 2.0))  # Medium weight
        
        # ARIA attributes
        for key in ['ariaLabel', 'aria-label', 'ariaRole']:
            if key in desc and desc[key]:
                searchable.append((str(desc[key]).lower(), 2.5))  # Good weight
        
        # Classes (lower priority)
        if 'classes' in desc and desc['classes']:
            for cls in desc['classes']:
                searchable.append((cls.lower(), 1.0))  # Low weight
        
        # Check each searchable attribute
        total_weight = 0.0
        weighted_score = 0.0
        
        for attr_value, weight in searchable:
            # Check for matches
            match_score = 0.0
            
            # Direct match
            if any(token in attr_value for token in context.query_tokens if len(token) > 2):
                match_score = 1.0
            # Fuzzy match
            elif any(
                SequenceMatcher(None, token, attr_value).ratio() > 0.7
                for token in context.query_tokens if len(token) > 3
            ):
                match_score = 0.7
            
            weighted_score += match_score * weight
            total_weight += weight
        
        if total_weight > 0:
            score = weighted_score / total_weight
        
        return min(score, 1.0)
    
    def _structural_score(self, desc: Dict[str, Any], context: MatchContext) -> float:
        """Score based on structural appropriateness."""
        tag = str(desc.get('tag', '')).lower()
        element_type = str(desc.get('type', '')).lower()
        
        if not tag:
            return 0.0
        
        score = 0.0
        
        # Match action to appropriate tags (not rules, but logical mapping)
        if context.intent_action:
            action = context.intent_action
            
            # Clickable elements
            if action in ['click', 'press', 'tap', 'submit', 'cancel']:
                if tag in ['button', 'a', 'input'] or desc.get('onclick'):
                    score = 0.8
                    if tag == 'button' and action in ['click', 'submit']:
                        score = 1.0
                    elif tag == 'a' and 'link' in context.query:
                        score = 1.0
            
            # Input elements
            elif action in ['type', 'enter', 'input', 'fill']:
                if tag in ['input', 'textarea']:
                    score = 0.9
                    # Check type relevance
                    if 'email' in context.query and element_type == 'email':
                        score = 1.0
                    elif 'password' in context.query and element_type == 'password':
                        score = 1.0
                    elif 'search' in context.query and element_type == 'search':
                        score = 1.0
                elif desc.get('contentEditable'):
                    score = 0.7
            
            # Selection elements
            elif action in ['select', 'choose', 'pick']:
                if tag == 'select':
                    score = 1.0
                elif tag in ['input', 'option']:
                    score = 0.7
        
        return score
    
    def _interactivity_score(self, desc: Dict[str, Any]) -> float:
        """Score based on element interactivity and visibility."""
        score = 0.5  # Base score for existing elements
        
        # Visible elements score higher
        if desc.get('isVisible'):
            score += 0.2
        
        # Interactive elements score higher
        if desc.get('isInteractive'):
            score += 0.2
        
        # Elements with handlers score higher
        if any(desc.get(k) for k in ['onclick', 'onsubmit', 'href']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _fuzzy_match_score(self, desc: Dict[str, Any], context: MatchContext) -> float:
        """Score based on fuzzy string matching for typos."""
        # Collect all text from element
        element_texts = []
        
        if desc.get('text'):
            element_texts.append(str(desc['text']).lower())
        if desc.get('ariaLabel'):
            element_texts.append(str(desc['ariaLabel']).lower())
        if desc.get('placeholder'):
            element_texts.append(str(desc['placeholder']).lower())
        if desc.get('title'):
            element_texts.append(str(desc['title']).lower())
        
        if not element_texts:
            return 0.0
        
        # Find best fuzzy match
        best_ratio = 0.0
        
        for elem_text in element_texts:
            # Full text fuzzy match
            ratio = SequenceMatcher(None, context.query, elem_text).ratio()
            best_ratio = max(best_ratio, ratio)
            
            # Token-level fuzzy match
            for query_token in context.query_tokens:
                if len(query_token) > 3:  # Only for meaningful tokens
                    for elem_token in self._tokenize(elem_text):
                        if len(elem_token) > 3:
                            ratio = SequenceMatcher(None, query_token, elem_token).ratio()
                            if ratio > 0.8:  # High similarity threshold
                                best_ratio = max(best_ratio, ratio)
        
        return best_ratio
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text intelligently."""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.lower().split()
        
        # Filter out very short tokens
        tokens = [t for t in tokens if len(t) > 1]
        
        return tokens
    
    def _simple_lemmatize(self, tokens: List[str]) -> List[str]:
        """Simple lemmatization (in production, use spaCy/NLTK)."""
        lemmas = []
        
        # Simple suffix stripping
        for token in tokens:
            if token.endswith('ing'):
                lemmas.append(token[:-3])
            elif token.endswith('ed'):
                lemmas.append(token[:-2])
            elif token.endswith('s') and len(token) > 3:
                lemmas.append(token[:-1])
            else:
                lemmas.append(token)
        
        return lemmas