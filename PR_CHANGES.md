# Pull Request: Critical Bug Fixes for HER Framework

## 🔧 PR Title
Fix: SessionManager compatibility and synthesizer parameter issues

## 📝 Description
This PR fixes two critical bugs that prevent the framework from functioning correctly:

1. **SessionManager Compatibility Issue**: EnhancedSessionManager doesn't have `index_page` method, causing AttributeError
2. **Synthesizer Parameter Issue**: LocatorSynthesizer.synthesize() was called with incorrect 'context' parameter

## 🎯 Changes Made

### File 1: `src/her/cli_api.py`
**Lines modified**: 224-235 and 304-315

**Change 1 (around line 224):**
```python
# BEFORE:
descriptors, _dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))

# AFTER:
# Get descriptors based on session manager type
if hasattr(self.session_manager, 'index_page'):
    descriptors, _dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))
else:
    # EnhancedSessionManager stores descriptors in session state
    session = self.session_manager.get_session(self.current_session_id)
    if session and session.descriptors:
        descriptors, _dom_hash = session.descriptors, session.dom_hash
    else:
        # Fall back to capture_snapshot
        from .bridge.snapshot import capture_snapshot
        descriptors, _dom_hash = capture_snapshot(page) if page else ([], "0"*64)
```

**Change 2 (around line 304):**
```python
# BEFORE:
descriptors, dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))

# AFTER:
# Get descriptors based on session manager type
if hasattr(self.session_manager, 'index_page'):
    descriptors, dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))
else:
    # EnhancedSessionManager stores descriptors in session state
    session = self.session_manager.get_session(self.current_session_id)
    if session and session.descriptors:
        descriptors, dom_hash = session.descriptors, session.dom_hash
    else:
        # Fall back to capture_snapshot
        from .bridge.snapshot import capture_snapshot
        descriptors, dom_hash = capture_snapshot(page) if page else ([], "0"*64)
```

### File 2: `src/her/locator/simple_synthesize.py`
**Line modified**: 20

**Change:**
```python
# BEFORE:
locs = super().synthesize(element, context=None)

# AFTER:
locs = super().synthesize(element)
```

## ✅ Testing
- Verified that both SessionManager and EnhancedSessionManager work correctly
- Confirmed synthesizer no longer throws TypeError
- Integration validation passes

## 🐛 Issues Fixed
- Fixes AttributeError: 'EnhancedSessionManager' object has no attribute 'index_page'
- Fixes TypeError: LocatorSynthesizer.synthesize() got an unexpected keyword argument 'context'

## 📊 Impact
- **Severity**: High - These bugs prevent core functionality from working
- **Risk**: Low - Changes are backward compatible
- **Testing**: Existing tests pass with these changes

## 🔍 Review Notes
These are minimal, targeted fixes that only address the specific bugs without changing any other functionality.