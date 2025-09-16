"""
MarkupLM-based snippet scorer for HER framework.

This module provides snippet scoring capabilities using MarkupLM model
for ranking HTML snippets based on user queries in no-semantic mode.
"""

from __future__ import annotations

import logging
import os
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

import torch
import numpy as np
from transformers import MarkupLMProcessor, MarkupLMForQuestionAnswering

log = logging.getLogger("her.markuplm_snippet_scorer")


@dataclass
class SnippetScore:
    """Result of snippet scoring."""
    snippet: str
    score: float
    xpath: str
    element: Dict[str, Any]
    confidence: float
    reasons: List[str]


class MarkupLMSnippetScorer:
    """MarkupLM-based snippet scorer for ranking HTML snippets."""
    
    def __init__(self, model_name: str = "microsoft/markuplm-base-finetuned-websrc", 
                 device: str = "cpu", batch_size: int = 8):
        """Initialize MarkupLM snippet scorer.
        
        Args:
            model_name: Name of the MarkupLM model to use
            device: Device to run the model on ('cpu' or 'cuda')
            batch_size: Batch size for processing snippets
        """
        self.model_name = model_name
        self.device = torch.device(device)
        self.batch_size = batch_size
        
        # Initialize model and processor
        self._initialize_model()
        
        log.info(f"MarkupLM Snippet Scorer initialized with model: {model_name}, device: {device}")
    
    def _initialize_model(self):
        """Initialize MarkupLM model and processor."""
        try:
            self.processor = MarkupLMProcessor.from_pretrained(self.model_name)
            self.model = MarkupLMForQuestionAnswering.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            log.info(f"Successfully loaded MarkupLM model: {self.model_name}")
            
        except Exception as e:
            log.error(f"Failed to load MarkupLM model: {e}")
            raise RuntimeError(f"MarkupLM model initialization failed: {e}")
    
    def score_snippets(self, candidates: List[Dict[str, Any]], query: str) -> List[SnippetScore]:
        """Score HTML snippets based on user query using MarkupLM.
        
        Args:
            candidates: List of candidate elements with hierarchical context
            query: User query string
            
        Returns:
            List of SnippetScore objects sorted by score (highest first)
        """
        if not candidates or not query:
            return []
        
        log.info(f"Scoring {len(candidates)} snippets with query: '{query}'")
        
        # Build hierarchical HTML context for each candidate
        html_snippets = []
        for candidate in candidates:
            html_snippet = self._build_hierarchical_html(candidate)
            html_snippets.append(html_snippet)
        
        # Score snippets using MarkupLM
        scores = self._score_with_markuplm(html_snippets, query)
        
        # Create SnippetScore objects
        results = []
        for i, (candidate, html_snippet, score) in enumerate(zip(candidates, html_snippets, scores)):
            xpath = self._generate_xpath(candidate)
            element = candidate.get('element', candidate)
            
            # Calculate confidence based on score
            confidence = min(max(score, 0.0), 1.0)
            
            # Generate reasons for the score
            reasons = self._generate_score_reasons(candidate, score, query)
            
            results.append(SnippetScore(
                snippet=html_snippet,
                score=score,
                xpath=xpath,
                element=element,
                confidence=confidence,
                reasons=reasons
            ))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x.score, reverse=True)
        
        log.info(f"Scored {len(results)} snippets, top score: {results[0].score:.3f}" if results else "No results")
        
        return results
    
    def _build_hierarchical_html(self, candidate: Dict[str, Any]) -> str:
        """Build hierarchical HTML context for a candidate element.
        
        Args:
            candidate: Candidate element with hierarchical context
            
        Returns:
            HTML string with hierarchical context
        """
        # Get the main element
        element = candidate.get('element', candidate)
        
        # Build parent context
        parent_context = self._build_parent_context(candidate)
        
        # Build sibling context
        sibling_context = self._build_sibling_context(candidate)
        
        # Build target element
        target_element = self._build_target_element(element)
        
        # Combine all parts
        html_parts = []
        
        if parent_context:
            html_parts.append(parent_context)
        
        if sibling_context:
            html_parts.append(sibling_context)
        
        html_parts.append(target_element)
        
        # Close parent tags
        if parent_context:
            # Count opening tags to close them
            opening_tags = parent_context.count('<') - parent_context.count('</')
            for _ in range(opening_tags):
                html_parts.append('</div>')  # Simple closing
        
        return ''.join(html_parts)
    
    def _build_parent_context(self, candidate: Dict[str, Any]) -> str:
        """Build parent element context."""
        parents = candidate.get('parents', [])
        if not parents:
            return ""
        
        html_parts = []
        for parent in parents[-3:]:  # Limit to last 3 parents
            tag = parent.get('tag', 'div')
            attrs = parent.get('attributes', {})
            attr_str = self._build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>')
        
        return ''.join(html_parts)
    
    def _build_sibling_context(self, candidate: Dict[str, Any]) -> str:
        """Build sibling element context."""
        siblings = candidate.get('siblings', [])
        if not siblings:
            return ""
        
        html_parts = ['<div class="sibling-context">']
        
        for sibling in siblings[:3]:  # Limit to 3 siblings
            tag = sibling.get('tag', 'span')
            text = sibling.get('text', '')[:50]  # Truncate long text
            attrs = sibling.get('attributes', {})
            attr_str = self._build_attribute_string(attrs)
            html_parts.append(f'<{tag}{attr_str}>{text}</{tag}>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
    
    def _build_target_element(self, element: Dict[str, Any]) -> str:
        """Build target element HTML."""
        tag = element.get('tag', 'div')
        text = element.get('text', '')
        attrs = element.get('attributes', {})
        attr_str = self._build_attribute_string(attrs)
        
        return f'<{tag}{attr_str}>{text}</{tag}>'
    
    def _build_attribute_string(self, attrs: Dict[str, Any]) -> str:
        """Build attribute string for HTML."""
        if not attrs:
            return ""
        
        attr_parts = []
        
        # Include important attributes
        important_attrs = ['class', 'id', 'role', 'type', 'name', 'aria-label', 'data-testid']
        
        for attr in important_attrs:
            value = attrs.get(attr, '')
            if value:
                # Escape quotes in attribute values
                escaped_value = str(value).replace('"', '&quot;')
                attr_parts.append(f'{attr}="{escaped_value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''
    
    def _score_with_markuplm(self, html_snippets: List[str], query: str) -> List[float]:
        """Score HTML snippets using MarkupLM model.
        
        Args:
            html_snippets: List of HTML snippet strings
            query: User query string
            
        Returns:
            List of scores for each snippet
        """
        if not html_snippets or not query:
            return []
        
        scores = []
        
        # Process snippets in batches
        for i in range(0, len(html_snippets), self.batch_size):
            batch_snippets = html_snippets[i:i + self.batch_size]
            batch_scores = self._score_batch(batch_snippets, query)
            scores.extend(batch_scores)
        
        return scores
    
    def _score_batch(self, html_snippets: List[str], query: str) -> List[float]:
        """Score a batch of HTML snippets.
        
        Args:
            html_snippets: List of HTML snippet strings
            query: User query string
            
        Returns:
            List of scores for the batch
        """
        try:
            # Prepare inputs for MarkupLM
            inputs = self.processor(
                questions=[query] * len(html_snippets),
                html_strings=html_snippets,
                return_tensors="pt"
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Combine start and end logits as scoring metric
                start_logits = outputs.start_logits
                end_logits = outputs.end_logits
                
                # Use max logits as score
                batch_scores = []
                for i in range(len(html_snippets)):
                    start_score = torch.max(start_logits[i]).item()
                    end_score = torch.max(end_logits[i]).item()
                    combined_score = (start_score + end_score) / 2.0
                    batch_scores.append(combined_score)
                
                return batch_scores
                
        except Exception as e:
            log.error(f"MarkupLM scoring failed: {e}")
            # Return zero scores as fallback
            return [0.0] * len(html_snippets)
    
    def _generate_xpath(self, candidate: Dict[str, Any]) -> str:
        """Generate XPath for a candidate element.
        
        Args:
            candidate: Candidate element
            
        Returns:
            XPath string
        """
        element = candidate.get('element', candidate)
        tag = element.get('tag', 'div')
        attrs = element.get('attributes', {})
        text = element.get('text', '').strip()
        
        # Priority order for XPath generation
        if attrs.get('id'):
            return f"//*[@id='{attrs['id']}']"
        elif attrs.get('data-testid'):
            return f"//*[@data-testid='{attrs['data-testid']}']"
        elif attrs.get('aria-label'):
            return f"//*[@aria-label='{attrs['aria-label']}']"
        elif attrs.get('name'):
            return f"//{tag}[@name='{attrs['name']}']"
        elif attrs.get('class'):
            # Use first class for specificity
            first_class = attrs['class'].split()[0]
            return f"//{tag}[@class='{first_class}']"
        elif text and len(text) < 100:  # Avoid very long text
            # Escape quotes in text
            escaped_text = text.replace("'", "\\'").replace('"', '\\"')
            return f"//{tag}[normalize-space()='{escaped_text}']"
        else:
            # Generic fallback
            return f"//{tag}"
    
    def _generate_score_reasons(self, candidate: Dict[str, Any], score: float, query: str) -> List[str]:
        """Generate reasons for the score.
        
        Args:
            candidate: Candidate element
            score: Calculated score
            query: User query
            
        Returns:
            List of reason strings
        """
        reasons = []
        
        # Add score-based reasons
        if score > 0.8:
            reasons.append("high_markuplm_score")
        elif score > 0.5:
            reasons.append("medium_markuplm_score")
        else:
            reasons.append("low_markuplm_score")
        
        # Add element type reasons
        element = candidate.get('element', candidate)
        tag = element.get('tag', '').lower()
        
        if tag in ['button', 'a', 'input']:
            reasons.append("interactive_element")
        
        if tag == 'button':
            reasons.append("button_element")
        elif tag == 'a':
            reasons.append("link_element")
        elif tag == 'input':
            reasons.append("input_element")
        
        # Add attribute reasons
        attrs = element.get('attributes', {})
        if attrs.get('id'):
            reasons.append("has_id")
        if attrs.get('data-testid'):
            reasons.append("has_test_id")
        if attrs.get('aria-label'):
            reasons.append("has_aria_label")
        
        # Add hierarchy reasons
        if candidate.get('parents'):
            reasons.append("has_parent_context")
        if candidate.get('siblings'):
            reasons.append("has_sibling_context")
        
        return reasons
    
    def get_top_candidates(self, candidates: List[Dict[str, Any]], query: str, 
                          top_k: int = 5) -> List[SnippetScore]:
        """Get top-k scored candidates.
        
        Args:
            candidates: List of candidate elements
            query: User query string
            top_k: Number of top candidates to return
            
        Returns:
            List of top SnippetScore objects
        """
        all_scores = self.score_snippets(candidates, query)
        return all_scores[:top_k]
    
    def is_available(self) -> bool:
        """Check if MarkupLM scorer is available.
        
        Returns:
            True if MarkupLM is available and loaded
        """
        try:
            return hasattr(self, 'model') and self.model is not None
        except Exception:
            return False