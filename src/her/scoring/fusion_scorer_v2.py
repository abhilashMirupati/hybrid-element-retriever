"""Production-ready fusion scorer with optimized logic."""

import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import re
from difflib import SequenceMatcher


@dataclass
class ScoringSignals:
    """All scoring signals for transparency."""
    text_similarity: float = 0.0
    attribute_match: float = 0.0
    structural_relevance: float = 0.0
    semantic_embedding: float = 0.0
    keyword_match: float = 0.0
    phrase_match: float = 0.0
    penalty: float = 0.0
    
    def compute_final_score(self) -> float:
        """Compute final score with proper weighting."""
        # Base scores (additive)
        base = (
            self.text_similarity * 2.0 +
            self.attribute_match * 3.0 +  # Higher weight for precise matches
            self.structural_relevance * 1.5 +
            self.semantic_embedding * 1.0
        )
        
        # Bonuses (additive)
        bonuses = (
            self.keyword_match * 1.0 +
            self.phrase_match * 2.0
        )
        
        # Apply penalties (multiplicative for stronger effect)
        final = (base + bonuses) * (1.0 - self.penalty)
        
        # Don't cap - let natural scoring work
        return max(0.0, final)


class FusionScorerV2:
    """Optimized fusion scorer without rule-based hacks."""
    
    def __init__(self):
        """Initialize the fusion scorer."""
        self.debug = False
    
    def score(
        self,
        query: str,
        element: Dict[str, Any],
        query_embedding: Optional[List[float]] = None,
        element_embedding: Optional[List[float]] = None,
        intent: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, ScoringSignals]:
        """Score element against query with full transparency.
        
        Returns:
            Tuple of (final_score, signals) for debugging
        """
        signals = ScoringSignals()
        
        # Normalize query
        query_lower = query.lower()
        query_tokens = self._tokenize(query_lower)
        
        # 1. Text Similarity
        signals.text_similarity = self._compute_text_similarity(
            query_lower, query_tokens, element
        )
        
        # 2. Attribute Matching (IDs, data-testid, etc.)
        signals.attribute_match = self._compute_attribute_match(
            query_tokens, element
        )
        
        # 3. Structural Relevance
        signals.structural_relevance = self._compute_structural_relevance(
            element, intent
        )
        
        # 4. Semantic Embedding Similarity
        if query_embedding and element_embedding:
            signals.semantic_embedding = self._compute_embedding_similarity(
                query_embedding, element_embedding
            )
        
        # 5. Keyword and Phrase Matching (no double counting)
        signals.keyword_match, signals.phrase_match = self._compute_keyword_phrase_match(
            query_lower, query_tokens, element, 
            already_counted_text=signals.text_similarity > 0.5
        )
        
        # 6. Compute Penalties (for wrong matches)
        signals.penalty = self._compute_penalties(query_lower, query_tokens, element)
        
        final_score = signals.compute_final_score()
        
        if self.debug:
            print(f"Scoring '{element.get('text', '')[:30]}...':")
            print(f"  Text: {signals.text_similarity:.2f}")
            print(f"  Attr: {signals.attribute_match:.2f}")
            print(f"  Struct: {signals.structural_relevance:.2f}")
            print(f"  Embed: {signals.semantic_embedding:.2f}")
            print(f"  Keywords: {signals.keyword_match:.2f}")
            print(f"  Phrases: {signals.phrase_match:.2f}")
            print(f"  Penalty: {signals.penalty:.2f}")
            print(f"  Final: {final_score:.2f}")
        
        return final_score, signals
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for matching."""
        # Remove punctuation, keep alphanumeric and spaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        tokens = text.lower().split()
        # Filter very short tokens except important ones
        tokens = [t for t in tokens if len(t) > 1 or t in ['a', 'i']]
        return tokens
    
    def _compute_text_similarity(
        self, 
        query: str, 
        query_tokens: List[str],
        element: Dict[str, Any]
    ) -> float:
        """Compute text similarity score."""
        element_text = str(element.get('text', '')).lower()
        
        if not element_text:
            return 0.0
        
        # Exact substring match
        if query in element_text:
            return 1.0
        if element_text in query:
            return 0.8
        
        # Token overlap (Jaccard similarity)
        element_tokens = self._tokenize(element_text)
        if not element_tokens:
            return 0.0
        
        intersection = set(query_tokens) & set(element_tokens)
        union = set(query_tokens) | set(element_tokens)
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # Boost for important word matches
        important_matches = sum(
            1 for token in query_tokens
            if len(token) > 3 and token in element_tokens
        )
        boost = min(important_matches * 0.1, 0.3)
        
        return min(jaccard + boost, 1.0)
    
    def _compute_attribute_match(
        self,
        query_tokens: List[str],
        element: Dict[str, Any]
    ) -> float:
        """Score based on attribute matching."""
        score = 0.0
        matches = []
        
        # Priority 1: data-testid (highest weight)
        testid = element.get('dataTestId', '') or element.get('data-testid', '')
        if testid:
            testid_lower = str(testid).lower()
            if any(token in testid_lower for token in query_tokens if len(token) > 2):
                matches.append(1.0)
        
        # Priority 2: ID
        elem_id = element.get('id', '')
        if elem_id:
            id_lower = str(elem_id).lower()
            if any(token in id_lower for token in query_tokens if len(token) > 2):
                matches.append(0.9)
        
        # Priority 3: name, aria-label
        for attr in ['name', 'ariaLabel', 'aria-label']:
            value = element.get(attr, '')
            if value:
                value_lower = str(value).lower()
                if any(token in value_lower for token in query_tokens if len(token) > 2):
                    matches.append(0.8)
                    break
        
        # Priority 4: placeholder, title
        for attr in ['placeholder', 'title', 'alt']:
            value = element.get(attr, '')
            if value:
                value_lower = str(value).lower()
                if any(token in value_lower for token in query_tokens if len(token) > 2):
                    matches.append(0.6)
                    break
        
        # Priority 5: type attribute for inputs
        if element.get('tag') == 'input':
            input_type = element.get('type', '')
            if input_type:
                # Special handling for common types
                if 'email' in query_tokens and input_type == 'email':
                    matches.append(1.0)
                elif 'password' in query_tokens and input_type == 'password':
                    matches.append(1.0)
                elif 'search' in query_tokens and input_type == 'search':
                    matches.append(1.0)
                elif any(token in input_type.lower() for token in query_tokens):
                    matches.append(0.7)
        
        # Return best match
        return max(matches) if matches else 0.0
    
    def _compute_structural_relevance(
        self,
        element: Dict[str, Any],
        intent: Optional[Dict[str, Any]]
    ) -> float:
        """Compute structural relevance based on element type and intent."""
        if not intent:
            return 0.5  # Neutral score
        
        tag = element.get('tag', '').lower()
        action = intent.get('action', '').lower()
        
        if not tag or not action:
            return 0.5
        
        # Map actions to appropriate tags
        relevance_map = {
            'click': {'button': 1.0, 'a': 0.9, 'input': 0.7, 'div': 0.5},
            'type': {'input': 1.0, 'textarea': 1.0, 'div': 0.3},
            'enter': {'input': 1.0, 'textarea': 1.0, 'div': 0.3},
            'select': {'select': 1.0, 'input': 0.6, 'div': 0.4},
            'submit': {'button': 1.0, 'input': 0.8, 'a': 0.6},
            'search': {'input': 1.0, 'button': 0.7, 'a': 0.5},
        }
        
        # Get relevance score
        if action in relevance_map:
            return relevance_map[action].get(tag, 0.4)
        
        return 0.5
    
    def _compute_embedding_similarity(
        self,
        query_embedding: List[float],
        element_embedding: List[float]
    ) -> float:
        """Compute cosine similarity between embeddings."""
        if not query_embedding or not element_embedding:
            return 0.0
        
        # Ensure same dimension
        min_len = min(len(query_embedding), len(element_embedding))
        if min_len == 0:
            return 0.0
        
        # Compute cosine similarity
        dot_product = sum(a * b for a, b in zip(query_embedding[:min_len], element_embedding[:min_len]))
        norm_q = math.sqrt(sum(a * a for a in query_embedding[:min_len]))
        norm_e = math.sqrt(sum(b * b for b in element_embedding[:min_len]))
        
        if norm_q * norm_e == 0:
            return 0.0
        
        similarity = dot_product / (norm_q * norm_e)
        
        # Normalize to [0, 1]
        return (similarity + 1.0) / 2.0
    
    def _compute_keyword_phrase_match(
        self,
        query: str,
        query_tokens: List[str],
        element: Dict[str, Any],
        already_counted_text: bool
    ) -> Tuple[float, float]:
        """Compute keyword and phrase matching without double counting."""
        keyword_score = 0.0
        phrase_score = 0.0
        
        # Skip if text similarity already high (avoid double counting)
        if already_counted_text:
            return 0.0, 0.0
        
        # Collect all searchable text from element
        searchable = []
        for key in ['text', 'ariaLabel', 'placeholder', 'title', 'alt']:
            value = element.get(key, '')
            if value:
                searchable.append(str(value).lower())
        
        combined_text = ' '.join(searchable)
        
        if not combined_text:
            return 0.0, 0.0
        
        # Keyword matching (individual important words)
        important_words = [w for w in query_tokens if len(w) > 3]
        if important_words:
            matches = sum(1 for word in important_words if word in combined_text)
            keyword_score = matches / len(important_words) * 0.5
        
        # Phrase matching (consecutive words)
        if len(query_tokens) > 1:
            # Check for bigrams
            for i in range(len(query_tokens) - 1):
                bigram = f"{query_tokens[i]} {query_tokens[i+1]}"
                if bigram in combined_text:
                    phrase_score = max(phrase_score, 0.7)
            
            # Check for trigrams
            if len(query_tokens) > 2:
                for i in range(len(query_tokens) - 2):
                    trigram = f"{query_tokens[i]} {query_tokens[i+1]} {query_tokens[i+2]}"
                    if trigram in combined_text:
                        phrase_score = 1.0
        
        return keyword_score, phrase_score
    
    def _compute_penalties(
        self,
        query: str,
        query_tokens: List[str],
        element: Dict[str, Any]
    ) -> float:
        """Compute penalties for mismatches."""
        penalty = 0.0
        
        # Product mismatch penalty
        products = ['laptop', 'phone', 'tablet', 'watch', 'camera', 'tv', 'headphones']
        
        # Check if query mentions a product
        query_product = None
        for product in products:
            if product in query:
                query_product = product
                break
        
        if query_product:
            # Check element for different products
            element_text = str(element.get('text', '')).lower()
            element_attrs = ' '.join([
                str(element.get('dataTestId', '')),
                str(element.get('id', '')),
                str(element.get('name', ''))
            ]).lower()
            
            element_content = f"{element_text} {element_attrs}"
            
            # Apply penalty if element contains a different product
            for product in products:
                if product != query_product and product in element_content:
                    penalty = max(penalty, 0.5)  # 50% penalty for wrong product
                    break
        
        # Form field mismatch penalty
        form_fields = {
            'email': ['email', 'mail'],
            'password': ['password', 'pwd', 'pass'],
            'username': ['username', 'user', 'login'],
            'phone': ['phone', 'tel', 'mobile'],
            'address': ['address', 'street', 'location']
        }
        
        # Check if query mentions a form field
        query_field = None
        for field, keywords in form_fields.items():
            if any(kw in query for kw in keywords):
                query_field = field
                break
        
        if query_field and element.get('tag') in ['input', 'textarea']:
            # Check if element is for a different field
            element_type = element.get('type', '')
            element_name = element.get('name', '').lower()
            element_placeholder = element.get('placeholder', '').lower()
            
            element_field_info = f"{element_type} {element_name} {element_placeholder}"
            
            # Check for conflicting field
            for field, keywords in form_fields.items():
                if field != query_field:
                    if any(kw in element_field_info for kw in keywords):
                        penalty = max(penalty, 0.4)  # 40% penalty for wrong field
                        break
        
        return min(penalty, 0.8)  # Cap at 80% to allow some signal through