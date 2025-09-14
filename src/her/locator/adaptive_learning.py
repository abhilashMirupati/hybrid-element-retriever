"""
Adaptive Learning System for HER

This module provides learning capabilities to improve element selection
based on success/failure patterns and user preferences.
"""

from __future__ import annotations

import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path

from .intent_parser import IntentType, ParsedIntent
from .dom_target_binder import DOMMatch

log = logging.getLogger("her.adaptive_learning")


@dataclass
class LearningPattern:
    """Pattern learned from user interactions."""
    intent: str
    element_type: str
    attributes: Dict[str, Any]
    success_count: int = 0
    failure_count: int = 0
    last_used: float = 0.0
    confidence: float = 0.0


@dataclass
class UserPreference:
    """User-specific preferences for element selection."""
    user_id: str
    preferred_selectors: Dict[str, List[str]] = None  # intent -> list of preferred selectors
    avoided_patterns: Dict[str, List[str]] = None     # intent -> list of avoided patterns
    success_threshold: float = 0.8
    learning_rate: float = 0.1
    
    def __post_init__(self):
        if self.preferred_selectors is None:
            self.preferred_selectors = {}
        if self.avoided_patterns is None:
            self.avoided_patterns = {}


class AdaptiveLearningSystem:
    """Adaptive learning system for improving element selection."""
    
    def __init__(self, learning_data_path: str = ".her_cache/learning.json"):
        """Initialize adaptive learning system.
        
        Args:
            learning_data_path: Path to store learning data
        """
        self.learning_data_path = Path(learning_data_path)
        self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Learning data
        self.patterns: Dict[str, LearningPattern] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        self.success_history: deque = deque(maxlen=1000)
        self.failure_history: deque = deque(maxlen=1000)
        
        # Load existing data
        self._load_learning_data()
    
    def learn_from_result(self, intent: IntentType, element: Dict[str, Any], 
                         success: bool, user_id: str = "default") -> None:
        """Learn from element selection result.
        
        Args:
            intent: User intent
            element: Selected element
            success: Whether selection was successful
            user_id: User identifier
        """
        try:
            # Create pattern key
            pattern_key = self._create_pattern_key(intent, element)
            
            # Get or create pattern
            if pattern_key not in self.patterns:
                self.patterns[pattern_key] = LearningPattern(
                    intent=intent.value,
                    element_type=element.get('tag', ''),
                    attributes=element.get('attributes', {}),
                    last_used=time.time()
                )
            
            pattern = self.patterns[pattern_key]
            
            # Update pattern based on result
            if success:
                pattern.success_count += 1
                self.success_history.append({
                    'pattern_key': pattern_key,
                    'timestamp': time.time(),
                    'user_id': user_id
                })
            else:
                pattern.failure_count += 1
                self.failure_history.append({
                    'pattern_key': pattern_key,
                    'timestamp': time.time(),
                    'user_id': user_id
                })
            
            # Update confidence
            total_attempts = pattern.success_count + pattern.failure_count
            pattern.confidence = pattern.success_count / total_attempts if total_attempts > 0 else 0.0
            pattern.last_used = time.time()
            
            # Update user preferences
            self._update_user_preferences(user_id, intent, element, success)
            
            # Save learning data
            self._save_learning_data()
            
            log.debug(f"Learned from result: {intent.value}, success={success}, confidence={pattern.confidence:.2f}")
            
        except Exception as e:
            log.warning(f"Failed to learn from result: {e}")
    
    def get_adaptive_heuristics(self, intent: IntentType, user_id: str = "default") -> Dict[str, Any]:
        """Get adaptive heuristics based on learning.
        
        Args:
            intent: User intent
            user_id: User identifier
            
        Returns:
            Adaptive heuristics dictionary
        """
        try:
            # Get user preferences
            user_pref = self.user_preferences.get(user_id, UserPreference(user_id=user_id))
            
            # Get learned patterns for this intent
            intent_patterns = [
                pattern for pattern in self.patterns.values() 
                if pattern.intent == intent.value and pattern.confidence > 0.5
            ]
            
            # Sort by confidence and recency
            intent_patterns.sort(key=lambda p: (p.confidence, p.last_used), reverse=True)
            
            # Build adaptive heuristics
            heuristics = {
                'prefer_tags': [],
                'prefer_attributes': [],
                'avoid_tags': [],
                'min_interactive_score': 0.5,
                'learned_patterns': []
            }
            
            # Add learned patterns
            for pattern in intent_patterns[:5]:  # Top 5 patterns
                if pattern.element_type:
                    heuristics['prefer_tags'].append(pattern.element_type)
                
                # Add successful attributes
                for attr, value in pattern.attributes.items():
                    if pattern.confidence > 0.7:  # High confidence patterns
                        heuristics['prefer_attributes'].append(f"{attr}={value}")
                
                heuristics['learned_patterns'].append({
                    'element_type': pattern.element_type,
                    'attributes': pattern.attributes,
                    'confidence': pattern.confidence,
                    'success_rate': pattern.success_count / (pattern.success_count + pattern.failure_count)
                })
            
            # Add user-specific preferences
            if intent.value in user_pref.preferred_selectors:
                heuristics['prefer_tags'].extend(user_pref.preferred_selectors[intent.value])
            
            if intent.value in user_pref.avoided_patterns:
                heuristics['avoid_tags'].extend(user_pref.avoided_patterns[intent.value])
            
            # Adjust minimum score based on user success rate
            user_success_rate = self._calculate_user_success_rate(user_id)
            if user_success_rate > 0.8:
                heuristics['min_interactive_score'] = 0.6  # More lenient for successful users
            elif user_success_rate < 0.5:
                heuristics['min_interactive_score'] = 0.8  # More strict for struggling users
            
            return heuristics
            
        except Exception as e:
            log.warning(f"Failed to get adaptive heuristics: {e}")
            return {
                'prefer_tags': [],
                'prefer_attributes': [],
                'avoid_tags': [],
                'min_interactive_score': 0.5,
                'learned_patterns': []
            }
    
    def get_element_confidence_boost(self, element: Dict[str, Any], intent: IntentType, 
                                   user_id: str = "default") -> float:
        """Get confidence boost for element based on learning.
        
        Args:
            element: Element to evaluate
            intent: User intent
            user_id: User identifier
            
        Returns:
            Confidence boost (0.0 to 1.0)
        """
        try:
            pattern_key = self._create_pattern_key(intent, element)
            pattern = self.patterns.get(pattern_key)
            
            if pattern and pattern.confidence > 0.5:
                # Boost based on pattern confidence and recency
                recency_factor = min(1.0, (time.time() - pattern.last_used) / (30 * 24 * 3600))  # 30 days
                return pattern.confidence * (1.0 - recency_factor * 0.5)
            
            return 0.0
            
        except Exception as e:
            log.warning(f"Failed to get confidence boost: {e}")
            return 0.0
    
    def get_learning_insights(self, user_id: str = "default") -> Dict[str, Any]:
        """Get learning insights for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Learning insights dictionary
        """
        try:
            # Calculate success rates by intent
            intent_success_rates = defaultdict(lambda: {'success': 0, 'total': 0})
            
            for pattern in self.patterns.values():
                intent_success_rates[pattern.intent]['success'] += pattern.success_count
                intent_success_rates[pattern.intent]['total'] += pattern.success_count + pattern.failure_count
            
            # Calculate overall success rate
            total_success = sum(p.success_count for p in self.patterns.values())
            total_attempts = sum(p.success_count + p.failure_count for p in self.patterns.values())
            overall_success_rate = total_success / total_attempts if total_attempts > 0 else 0.0
            
            # Get recent patterns
            recent_patterns = sorted(
                [p for p in self.patterns.values() if p.last_used > time.time() - 7 * 24 * 3600],  # Last 7 days
                key=lambda p: p.last_used,
                reverse=True
            )[:10]
            
            return {
                'overall_success_rate': overall_success_rate,
                'intent_success_rates': {
                    intent: data['success'] / data['total'] if data['total'] > 0 else 0.0
                    for intent, data in intent_success_rates.items()
                },
                'total_patterns_learned': len(self.patterns),
                'recent_patterns': [
                    {
                        'intent': p.intent,
                        'element_type': p.element_type,
                        'confidence': p.confidence,
                        'last_used': p.last_used
                    }
                    for p in recent_patterns
                ],
                'user_success_rate': self._calculate_user_success_rate(user_id)
            }
            
        except Exception as e:
            log.warning(f"Failed to get learning insights: {e}")
            return {
                'overall_success_rate': 0.0,
                'intent_success_rates': {},
                'total_patterns_learned': 0,
                'recent_patterns': [],
                'user_success_rate': 0.0
            }
    
    def _create_pattern_key(self, intent: IntentType, element: Dict[str, Any]) -> str:
        """Create pattern key for learning.
        
        Args:
            intent: User intent
            element: Element descriptor
            
        Returns:
            Pattern key string
        """
        tag = element.get('tag', '')
        attrs = element.get('attributes', {})
        
        # Create key from tag and key attributes
        key_attrs = ['id', 'class', 'role', 'type', 'name']
        attr_parts = [f"{attr}={attrs.get(attr, '')}" for attr in key_attrs if attrs.get(attr)]
        
        return f"{intent.value}:{tag}:{':'.join(attr_parts)}"
    
    def _update_user_preferences(self, user_id: str, intent: IntentType, 
                                element: Dict[str, Any], success: bool) -> None:
        """Update user preferences based on result.
        
        Args:
            user_id: User identifier
            intent: User intent
            element: Element descriptor
            success: Whether selection was successful
        """
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreference(user_id=user_id)
        
        user_pref = self.user_preferences[user_id]
        intent_key = intent.value
        
        if success:
            # Add to preferred selectors
            if intent_key not in user_pref.preferred_selectors:
                user_pref.preferred_selectors[intent_key] = []
            
            element_type = element.get('tag', '')
            if element_type and element_type not in user_pref.preferred_selectors[intent_key]:
                user_pref.preferred_selectors[intent_key].append(element_type)
                
                # Keep only top 10 preferred selectors
                if len(user_pref.preferred_selectors[intent_key]) > 10:
                    user_pref.preferred_selectors[intent_key] = user_pref.preferred_selectors[intent_key][-10:]
        else:
            # Add to avoided patterns
            if intent_key not in user_pref.avoided_patterns:
                user_pref.avoided_patterns[intent_key] = []
            
            element_type = element.get('tag', '')
            if element_type and element_type not in user_pref.avoided_patterns[intent_key]:
                user_pref.avoided_patterns[intent_key].append(element_type)
                
                # Keep only top 10 avoided patterns
                if len(user_pref.avoided_patterns[intent_key]) > 10:
                    user_pref.avoided_patterns[intent_key] = user_pref.avoided_patterns[intent_key][-10:]
    
    def _calculate_user_success_rate(self, user_id: str) -> float:
        """Calculate user success rate.
        
        Args:
            user_id: User identifier
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        user_patterns = [
            pattern for pattern in self.patterns.values()
            if any(entry['user_id'] == user_id for entry in self.success_history + self.failure_history)
        ]
        
        if not user_patterns:
            return 0.0
        
        total_success = sum(p.success_count for p in user_patterns)
        total_attempts = sum(p.success_count + p.failure_count for p in user_patterns)
        
        return total_success / total_attempts if total_attempts > 0 else 0.0
    
    def _load_learning_data(self) -> None:
        """Load learning data from file."""
        try:
            if self.learning_data_path.exists():
                with open(self.learning_data_path, 'r') as f:
                    data = json.load(f)
                
                # Load patterns
                self.patterns = {
                    key: LearningPattern(**pattern_data)
                    for key, pattern_data in data.get('patterns', {}).items()
                }
                
                # Load user preferences
                self.user_preferences = {
                    user_id: UserPreference(**pref_data)
                    for user_id, pref_data in data.get('user_preferences', {}).items()
                }
                
                log.info(f"Loaded {len(self.patterns)} patterns and {len(self.user_preferences)} user preferences")
                
        except Exception as e:
            log.warning(f"Failed to load learning data: {e}")
    
    def _save_learning_data(self) -> None:
        """Save learning data to file."""
        try:
            data = {
                'patterns': {
                    key: asdict(pattern)
                    for key, pattern in self.patterns.items()
                },
                'user_preferences': {
                    user_id: asdict(pref)
                    for user_id, pref in self.user_preferences.items()
                },
                'last_updated': time.time()
            }
            
            with open(self.learning_data_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            log.warning(f"Failed to save learning data: {e}")
    
    def reset_learning_data(self) -> None:
        """Reset all learning data."""
        self.patterns.clear()
        self.user_preferences.clear()
        self.success_history.clear()
        self.failure_history.clear()
        
        # Remove learning file
        if self.learning_data_path.exists():
            self.learning_data_path.unlink()
        
        log.info("Learning data reset")