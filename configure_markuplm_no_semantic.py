#!/usr/bin/env python3
"""
Configuration script for MarkupLM-enhanced no-semantic mode in HER framework.

This script configures the HER framework to use:
- No-semantic mode (semantic_mode = False)
- Hierarchy mode (hierarchy_mode = True)
- MarkupLM integration for enhanced snippet scoring
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.config.settings import get_config, set_config, HERConfig
from her.core.config_service import get_config_service, set_config_service, ConfigService


def configure_markuplm_no_semantic():
    """Configure HER for MarkupLM-enhanced no-semantic mode."""
    print("🔧 Configuring HER for MarkupLM-enhanced no-semantic mode...")
    
    # Set environment variables for no-semantic mode with hierarchy
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "false"  # Disable semantic search
    os.environ["HER_USE_HIERARCHY"] = "true"         # Enable hierarchy mode
    os.environ["HER_USE_MARKUPLM_NO_SEMANTIC"] = "true"  # Enable MarkupLM no-semantic
    os.environ["HER_DEBUG"] = "true"                 # Enable debug for testing
    
    print("✅ Environment variables set:")
    print(f"   HER_USE_SEMANTIC_SEARCH = {os.getenv('HER_USE_SEMANTIC_SEARCH')}")
    print(f"   HER_USE_HIERARCHY = {os.getenv('HER_USE_HIERARCHY')}")
    print(f"   HER_USE_MARKUPLM_NO_SEMANTIC = {os.getenv('HER_USE_MARKUPLM_NO_SEMANTIC')}")
    print(f"   HER_DEBUG = {os.getenv('HER_DEBUG')}")
    
    # Create new configuration
    config = HERConfig()
    
    # Verify configuration
    print("\n🔍 Verifying configuration:")
    print(f"   Semantic search enabled: {config.should_use_semantic_search()}")
    print(f"   Hierarchy enabled: {config.should_use_hierarchy()}")
    print(f"   MarkupLM no-semantic enabled: {config.should_use_markuplm_no_semantic()}")
    print(f"   MarkupLM model: {config.get_markuplm_model_name()}")
    print(f"   MarkupLM device: {config.get_markuplm_device()}")
    print(f"   MarkupLM batch size: {config.get_markuplm_batch_size()}")
    
    # Set global configuration
    set_config(config)
    
    # Create and set config service
    config_service = ConfigService(config)
    set_config_service(config_service)
    
    print("\n✅ Configuration complete!")
    print("\n📋 Configuration Summary:")
    print("   Mode: No-semantic with MarkupLM enhancement")
    print("   Hierarchy: Enabled")
    print("   MarkupLM: Enabled for snippet scoring")
    print("   Strategy: Exact matching + MarkupLM ranking")
    
    return config


def test_configuration():
    """Test the configuration by creating a simple pipeline."""
    print("\n🧪 Testing configuration...")
    
    try:
        from her.core.pipeline import HybridPipeline
        
        # Create pipeline instance
        pipeline = HybridPipeline()
        
        # Check configuration
        config_service = get_config_service()
        
        print(f"   Pipeline created successfully")
        print(f"   Semantic search: {config_service.should_use_semantic_search()}")
        print(f"   Hierarchy mode: {config_service.should_use_hierarchy()}")
        print(f"   MarkupLM no-semantic: {config_service.should_use_markuplm_no_semantic()}")
        
        # Test MarkupLM no-semantic matcher
        from her.locator.markuplm_no_semantic import MarkupLMNoSemanticMatcher
        
        matcher = MarkupLMNoSemanticMatcher()
        print(f"   MarkupLM matcher created: {matcher.is_markup_available()}")
        
        print("✅ Configuration test passed!")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True


def create_test_script():
    """Create a test script for the MarkupLM no-semantic mode."""
    test_script = '''#!/usr/bin/env python3
"""
Test script for MarkupLM-enhanced no-semantic mode.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.locator.markuplm_no_semantic import MarkupLMNoSemanticMatcher

def test_markuplm_scoring():
    """Test MarkupLM snippet scoring."""
    print("🧪 Testing MarkupLM snippet scoring...")
    
    # Sample HTML snippets
    candidates = [
        {
            "tag": "button",
            "text": "Apple",
            "attributes": {
                "id": "apple-btn",
                "class": "filter-button",
                "data-testid": "apple-filter"
            },
            "xpath": "//button[@id='apple-btn']"
        },
        {
            "tag": "a",
            "text": "Apple",
            "attributes": {
                "href": "/apple",
                "class": "brand-link"
            },
            "xpath": "//a[@href='/apple']"
        }
    ]
    
    # Create matcher
    matcher = MarkupLMNoSemanticMatcher()
    
    if not matcher.is_markup_available():
        print("❌ MarkupLM not available, skipping test")
        return False
    
    # Test query
    query = 'Click on "Apple" filter'
    result = matcher.query(query, candidates)
    
    print(f"   Query: {query}")
    print(f"   Result: {result}")
    
    if result.get('xpath'):
        print("✅ MarkupLM scoring test passed!")
        return True
    else:
        print("❌ MarkupLM scoring test failed")
        return False

if __name__ == "__main__":
    success = test_markuplm_scoring()
    sys.exit(0 if success else 1)
'''
    
    with open("test_markuplm_no_semantic.py", "w") as f:
        f.write(test_script)
    
    print("📝 Created test script: test_markuplm_no_semantic.py")


def main():
    """Main configuration function."""
    print("🚀 HER MarkupLM No-Semantic Mode Configuration")
    print("=" * 50)
    
    # Configure the framework
    config = configure_markuplm_no_semantic()
    
    # Test configuration
    if test_configuration():
        print("\n🎉 Configuration successful!")
        
        # Create test script
        create_test_script()
        
        print("\n📖 Next steps:")
        print("1. Install required dependencies: pip install transformers torch")
        print("2. Run the test script: python test_markuplm_no_semantic.py")
        print("3. Use the framework with no-semantic mode enabled")
        
    else:
        print("\n❌ Configuration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()