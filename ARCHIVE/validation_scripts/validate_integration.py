#!/usr/bin/env python3
"""Validation script to ensure all enhanced features are properly integrated."""

import sys
import importlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_imports():
    """Validate all enhanced modules can be imported."""
    print("=" * 60)
    print("VALIDATING MODULE IMPORTS")
    print("=" * 60)
    
    modules_to_check = [
        ("src.her.session.enhanced_manager", ["EnhancedSessionManager"]),
        ("src.her.locator.enhanced_verify", ["EnhancedLocatorVerifier", "PopupHandler"]),
        ("src.her.recovery.enhanced_promotion", ["EnhancedPromotionStore"]),
        ("src.her.cli_api", ["HybridClient"])
    ]
    
    all_ok = True
    for module_name, classes in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            for cls_name in classes:
                if hasattr(module, cls_name):
                    print(f"✅ {module_name}.{cls_name} - OK")
                else:
                    print(f"❌ {module_name}.{cls_name} - NOT FOUND")
                    all_ok = False
        except Exception as e:
            print(f"❌ {module_name} - IMPORT FAILED: {e}")
            all_ok = False
    
    return all_ok

def validate_integration():
    """Validate enhanced modules are integrated in cli_api."""
    print("\n" + "=" * 60)
    print("VALIDATING INTEGRATION IN CLI_API")
    print("=" * 60)
    
    try:
        from src.her.cli_api import HybridClient
        
        # Create instance with enhanced features
        her = HybridClient(use_enhanced=True)
        
        # Check if enhanced components are used
        checks = [
            ("Session Manager", "EnhancedSessionManager", type(her.session_manager).__name__),
            ("Locator Verifier", "EnhancedLocatorVerifier", type(her.verifier).__name__),
            ("Promotion Store", "EnhancedPromotionStore", type(her.promotion_store).__name__ if her.promotion_store else "None")
        ]
        
        all_ok = True
        for name, expected, actual in checks:
            if expected in actual:
                print(f"✅ {name}: {actual}")
            else:
                print(f"❌ {name}: Expected {expected}, got {actual}")
                all_ok = False
        
        # Check key attributes
        print("\n" + "=" * 60)
        print("CHECKING KEY ATTRIBUTES")
        print("=" * 60)
        
        attributes = [
            ("use_enhanced", True),
            ("promotion_store", "not None")
        ]
        
        for attr, expected in attributes:
            value = getattr(her, attr, None)
            if attr == "promotion_store":
                ok = value is not None
            else:
                ok = value == expected
            
            if ok:
                print(f"✅ {attr}: {value}")
            else:
                print(f"❌ {attr}: Expected {expected}, got {value}")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Integration validation failed: {e}")
        return False

def validate_features():
    """Validate feature availability."""
    print("\n" + "=" * 60)
    print("VALIDATING FEATURE AVAILABILITY")
    print("=" * 60)
    
    try:
        from src.her.session.enhanced_manager import EnhancedSessionManager
        from src.her.locator.enhanced_verify import PopupHandler
        from src.her.recovery.enhanced_promotion import EnhancedPromotionStore
        
        features = []
        
        # Check session manager features
        sm = EnhancedSessionManager()
        features.extend([
            ("Cold Start Support", hasattr(sm, '_load_from_cache')),
            ("Incremental Updates", hasattr(sm, 'enable_incremental')),
            ("SPA Tracking", hasattr(sm, 'enable_spa_tracking')),
            ("Page Idle Check", hasattr(sm, '_wait_for_page_idle'))
        ])
        
        # Check popup handler
        features.extend([
            ("Popup Detection", hasattr(PopupHandler, 'detect_popup')),
            ("Popup Closing", hasattr(PopupHandler, 'close_popup'))
        ])
        
        # Check promotion store
        ps = EnhancedPromotionStore()
        features.extend([
            ("Fallback Support", hasattr(ps, 'get_best_fallback')),
            ("Confidence Scoring", hasattr(ps, 'min_confidence'))
        ])
        
        all_ok = True
        for feature, available in features:
            if available:
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature}")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Feature validation failed: {e}")
        return False

def main():
    """Run all validations."""
    print("\n" + "🔍 HYBRID ELEMENT RETRIEVER - INTEGRATION VALIDATION")
    print("=" * 60)
    
    results = []
    
    # Run validations
    results.append(("Module Imports", validate_imports()))
    results.append(("Integration", validate_integration()))
    results.append(("Feature Availability", validate_features()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED - SYSTEM IS PRODUCTION READY!")
    else:
        print("⚠️ SOME VALIDATIONS FAILED - NEEDS FIXING")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())