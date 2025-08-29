# 🚀 Ready-to-Merge PR: Critical Bug Fixes

## Files to Change: 2 files only

---

## 📄 File 1: `src/her/cli_api.py`

### Location 1: Line ~224 (in `query` method)
**Find this line:**
```python
descriptors, _dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))
```

**Replace with:**
```python
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

### Location 2: Line ~293 (in `act` method)
**Find this line:**
```python
descriptors, dom_hash = (self.session_manager.index_page(self.current_session_id, page) if page else ([], "0"*64))
```

**Replace with:**
```python
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

---

## 📄 File 2: `src/her/locator/simple_synthesize.py`

### Location: Line 20
**Find this line:**
```python
locs = super().synthesize(element, context=None)
```

**Replace with:**
```python
locs = super().synthesize(element)
```

---

## ✅ PR Checklist

- [ ] Only modify these 2 files
- [ ] Make exactly these changes
- [ ] Don't include any test files
- [ ] Don't include any documentation files
- [ ] Run tests to verify fixes work

## 🎯 What These Fixes Do

1. **cli_api.py fix**: Handles both `SessionManager` and `EnhancedSessionManager` properly, preventing AttributeError
2. **simple_synthesize.py fix**: Removes incorrect parameter that causes TypeError

## 🐛 Bugs Fixed

- `AttributeError: 'EnhancedSessionManager' object has no attribute 'index_page'`
- `TypeError: LocatorSynthesizer.synthesize() got an unexpected keyword argument 'context'`

## 📝 Commit Message

```
fix: resolve SessionManager compatibility and synthesizer issues

- Add compatibility layer for EnhancedSessionManager in cli_api.py
- Remove incorrect context parameter in simple_synthesize.py
- Fixes AttributeError and TypeError in core functionality
```

---

**That's it! Just these 2 files with these specific changes. This is a minimal, focused fix that addresses only the critical bugs.**