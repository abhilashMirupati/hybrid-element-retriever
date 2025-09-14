#!/usr/bin/env python3
"""
Test script to verify smart snapshot manager functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.her.core.smart_snapshot_manager import SmartSnapshotManager, SnapshotReason

def test_smart_snapshot_manager():
    """Test the smart snapshot manager logic."""
    print("🧪 Testing Smart Snapshot Manager...")
    
    # Initialize manager
    manager = SmartSnapshotManager(
        snapshot_cooldown=1.0,
        max_consecutive_failures=2,
        dynamic_content_threshold=0.1
    )
    
    # Test initial load
    should_take, reason, explanation = manager.should_take_snapshot(
        current_url="https://www.google.com",
        action_type="click",
        force=False,
        element_found=True,
        confidence=1.0
    )
    
    print(f"Initial load: should_take={should_take}, reason={reason.value}, explanation={explanation}")
    
    # Simulate a snapshot
    if should_take:
        fake_snapshot = {
            'url': 'https://www.google.com',
            'dom_hash': 'fake_hash',
            'elements': [{'tag': 'div', 'text': 'test'}]
        }
        manager.update_state_after_snapshot(fake_snapshot, reason)
        print("✅ Updated state after snapshot")
    
    # Test same page action
    should_take2, reason2, explanation2 = manager.should_take_snapshot(
        current_url="https://www.google.com",  # Same URL
        action_type="click",
        force=False,
        element_found=True,
        confidence=1.0
    )
    
    print(f"Same page action: should_take={should_take2}, reason={reason2.value}, explanation={explanation2}")
    
    # Test page transition
    should_take3, reason3, explanation3 = manager.should_take_snapshot(
        current_url="https://www.google.com/search",  # Different URL
        action_type="click",
        force=False,
        element_found=True,
        confidence=1.0
    )
    
    print(f"Page transition: should_take={should_take3}, reason={reason3.value}, explanation={explanation3}")
    
    # Get performance stats
    stats = manager.get_performance_stats()
    print(f"📊 Performance stats: {stats}")
    
    print("✅ Smart Snapshot Manager test completed!")

if __name__ == "__main__":
    test_smart_snapshot_manager()