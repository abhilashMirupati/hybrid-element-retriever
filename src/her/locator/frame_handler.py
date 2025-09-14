"""
Enhanced Frame Handler for both semantic and no-semantic modes.

This module provides robust frame detection, switching, and element location
across different frame contexts while maintaining compatibility with both
retrieval modes.
"""

from __future__ import annotations

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger("her.frame_handler")


class FrameType(Enum):
    """Types of frames that can be encountered."""
    MAIN = "main"
    IFRAME = "iframe"
    SHADOW_DOM = "shadow_dom"
    POPUP = "popup"
    MODAL = "modal"


@dataclass
class FrameContext:
    """Context information for a frame."""
    frame_id: str
    frame_type: FrameType
    frame_url: str
    parent_frame_id: Optional[str] = None
    depth: int = 0
    is_active: bool = True
    selector: Optional[str] = None
    shadow_root: Optional[str] = None


class FrameHandler:
    """Enhanced frame handler for both retrieval modes."""
    
    def __init__(self):
        """Initialize frame handler."""
        self.frame_contexts: Dict[str, FrameContext] = {}
        self.current_frame_id: Optional[str] = None
        self.frame_stack: List[str] = []
    
    def detect_frames(self, elements: List[Dict[str, Any]]) -> List[FrameContext]:
        """Detect all frames in the current page.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of detected frame contexts
        """
        frames = []
        frame_elements = []
        
        # Find iframe elements
        for element in elements:
            tag = element.get('tag', '').lower()
            if tag == 'iframe':
                frame_elements.append(element)
        
        # Process each iframe
        for i, iframe in enumerate(frame_elements):
            frame_id = f"frame_{i}_{iframe.get('xpath', '')}"
            frame_url = iframe.get('attributes', {}).get('src', '')
            
            context = FrameContext(
                frame_id=frame_id,
                frame_type=FrameType.IFRAME,
                frame_url=frame_url,
                depth=0,
                selector=iframe.get('xpath', '')
            )
            
            frames.append(context)
            self.frame_contexts[frame_id] = context
        
        # Add main frame
        main_context = FrameContext(
            frame_id="main",
            frame_type=FrameType.MAIN,
            frame_url="",
            depth=0
        )
        frames.append(main_context)
        self.frame_contexts["main"] = main_context
        
        log.info(f"Detected {len(frames)} frames: {[f.frame_id for f in frames]}")
        return frames
    
    def switch_to_frame(self, frame_id: str) -> bool:
        """Switch to a specific frame.
        
        Args:
            frame_id: ID of the frame to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if frame_id not in self.frame_contexts:
            log.warning(f"Frame {frame_id} not found")
            return False
        
        # Update current frame
        self.current_frame_id = frame_id
        
        # Add to frame stack
        if frame_id not in self.frame_stack:
            self.frame_stack.append(frame_id)
        
        # Update frame context
        self.frame_contexts[frame_id].is_active = True
        
        log.info(f"Switched to frame: {frame_id}")
        return True
    
    def switch_to_parent_frame(self) -> bool:
        """Switch to parent frame.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.frame_stack:
            log.warning("No frames in stack")
            return False
        
        # Remove current frame from stack
        current = self.frame_stack.pop()
        self.frame_contexts[current].is_active = False
        
        # Switch to parent
        if self.frame_stack:
            parent = self.frame_stack[-1]
            self.current_frame_id = parent
            self.frame_contexts[parent].is_active = True
            log.info(f"Switched to parent frame: {parent}")
        else:
            self.current_frame_id = "main"
            log.info("Switched to main frame")
        
        return True
    
    def get_current_frame_context(self) -> Optional[FrameContext]:
        """Get current frame context.
        
        Returns:
            Current frame context or None
        """
        if self.current_frame_id:
            return self.frame_contexts.get(self.current_frame_id)
        return None
    
    def is_in_frame(self) -> bool:
        """Check if currently in a frame.
        
        Returns:
            True if in a frame, False if in main
        """
        return self.current_frame_id != "main" and self.current_frame_id is not None
    
    def get_frame_selector(self, frame_id: str) -> Optional[str]:
        """Get selector for a specific frame.
        
        Args:
            frame_id: ID of the frame
            
        Returns:
            Frame selector or None
        """
        context = self.frame_contexts.get(frame_id)
        return context.selector if context else None
    
    def resolve_element_selector(self, element: Dict[str, Any], 
                                frame_id: Optional[str] = None) -> str:
        """Resolve element selector with frame context.
        
        Args:
            element: Element descriptor
            frame_id: Target frame ID (uses current if None)
            
        Returns:
            Resolved selector with frame context
        """
        if frame_id is None:
            frame_id = self.current_frame_id or "main"
        
        element_selector = element.get('xpath', '')
        
        # If element is in main frame, return as-is
        if frame_id == "main":
            return element_selector
        
        # Get frame selector
        frame_selector = self.get_frame_selector(frame_id)
        if not frame_selector:
            return element_selector
        
        # Combine frame and element selectors
        if element_selector.startswith('//'):
            # XPath element in iframe
            return f"{frame_selector}{element_selector}"
        else:
            # CSS element in iframe
            return f"{frame_selector} >>> {element_selector}"
    
    def detect_shadow_dom(self, elements: List[Dict[str, Any]]) -> List[FrameContext]:
        """Detect shadow DOM elements.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of shadow DOM contexts
        """
        shadow_contexts = []
        
        for element in elements:
            attrs = element.get('attributes', {})
            
            # Check for shadow DOM indicators
            if any(attr in attrs for attr in ['shadowroot', 'shadow-root', 'data-shadow']):
                shadow_id = f"shadow_{len(shadow_contexts)}"
                
                context = FrameContext(
                    frame_id=shadow_id,
                    frame_type=FrameType.SHADOW_DOM,
                    frame_url="",
                    depth=0,
                    shadow_root=attrs.get('shadowroot', '')
                )
                
                shadow_contexts.append(context)
                self.frame_contexts[shadow_id] = context
        
        log.info(f"Detected {len(shadow_contexts)} shadow DOM elements")
        return shadow_contexts
    
    def handle_dynamic_frames(self, elements: List[Dict[str, Any]]) -> List[FrameContext]:
        """Handle dynamically loaded frames.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            List of dynamic frame contexts
        """
        dynamic_frames = []
        
        # Look for elements that might indicate dynamic content
        for element in elements:
            tag = element.get('tag', '').lower()
            attrs = element.get('attributes', {})
            
            # Check for dynamic loading indicators
            if any(indicator in attrs for indicator in [
                'data-dynamic', 'data-lazy', 'data-async', 'loading'
            ]):
                frame_id = f"dynamic_{len(dynamic_frames)}"
                
                context = FrameContext(
                    frame_id=frame_id,
                    frame_type=FrameType.IFRAME,
                    frame_url=attrs.get('src', ''),
                    depth=0,
                    selector=element.get('xpath', '')
                )
                
                dynamic_frames.append(context)
                self.frame_contexts[frame_id] = context
        
        log.info(f"Detected {len(dynamic_frames)} dynamic frames")
        return dynamic_frames
    
    def get_frame_hierarchy(self) -> Dict[str, List[str]]:
        """Get frame hierarchy structure.
        
        Returns:
            Dictionary mapping parent frames to child frames
        """
        hierarchy = {}
        
        for frame_id, context in self.frame_contexts.items():
            parent = context.parent_frame_id or "main"
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(frame_id)
        
        return hierarchy
    
    def cleanup(self):
        """Clean up frame handler state."""
        self.frame_contexts.clear()
        self.current_frame_id = None
        self.frame_stack.clear()
        log.info("Frame handler cleaned up")


class FrameAwareTargetMatcher:
    """Target matcher that is aware of frame contexts."""
    
    def __init__(self, frame_handler: FrameHandler, base_matcher):
        """Initialize frame-aware target matcher.
        
        Args:
            frame_handler: Frame handler instance
            base_matcher: Base target matcher (semantic or no-semantic)
        """
        self.frame_handler = frame_handler
        self.base_matcher = base_matcher
    
    def match_elements_in_frames(self, elements: List[Dict[str, Any]], 
                                target: str) -> List[Tuple[FrameContext, List]]:
        """Match elements across all frames.
        
        Args:
            elements: List of element descriptors
            target: Target string to match
            
        Returns:
            List of tuples (frame_context, matches)
        """
        results = []
        
        # Group elements by frame
        elements_by_frame = self._group_elements_by_frame(elements)
        
        # Match in each frame
        for frame_id, frame_elements in elements_by_frame.items():
            frame_context = self.frame_handler.frame_contexts.get(frame_id)
            if not frame_context:
                continue
            
            # Switch to frame context
            self.frame_handler.switch_to_frame(frame_id)
            
            # Match elements in this frame
            matches = self.base_matcher.match_elements(frame_elements, target)
            
            if matches:
                results.append((frame_context, matches))
                log.info(f"Found {len(matches)} matches in frame {frame_id}")
        
        return results
    
    def _group_elements_by_frame(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group elements by their frame context.
        
        Args:
            elements: List of element descriptors
            
        Returns:
            Dictionary mapping frame IDs to elements
        """
        elements_by_frame = {"main": []}
        
        for element in elements:
            # Determine frame from element metadata
            frame_id = self._extract_frame_id(element)
            if frame_id not in elements_by_frame:
                elements_by_frame[frame_id] = []
            elements_by_frame[frame_id].append(element)
        
        return elements_by_frame
    
    def _extract_frame_id(self, element: Dict[str, Any]) -> str:
        """Extract frame ID from element metadata.
        
        Args:
            element: Element descriptor
            
        Returns:
            Frame ID
        """
        meta = element.get('meta', {})
        frame_hash = meta.get('frame_hash')
        
        if frame_hash:
            # Look up frame ID by hash
            for frame_id, context in self.frame_handler.frame_contexts.items():
                if context.frame_id == frame_hash:
                    return frame_id
        
        return "main"