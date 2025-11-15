# Phase 4: Dependency Evaluation

This document evaluates which submodules are still needed after the Ruff migration.

## Summary

| Submodule | Status | Reason |
|-----------|--------|--------|
| **rope** | ✅ **KEEP** | Essential for code completion, refactoring, go-to-definition |
| **astroid** | ❓ **EVALUATE** | May be needed by rope, but rope doesn't directly import it |
| **toml** | ❌ **REMOVE** | Not used in pymode code; Ruff handles its own TOML parsing |
| **tomli** | ✅ **KEEP** | Required by pytoolconfig (rope dependency) |
| **pytoolconfig** | ✅ **KEEP** | Required by rope (rope depends on pytoolconfig[global]) |
| **appdirs** | ❌ **REMOVE** | Not used in pymode code |
| **snowball_py** | ❌ **REMOVE** | Was only used by pydocstyle, which is replaced by Ruff |

## Detailed Analysis

### ✅ Rope - KEEP
**Status:** Essential, must keep

**Reason:**
- Provides core IDE features: code completion, go-to-definition, refactoring
- All rope tests passing (9/9)
- No conflicts with Ruff migration
- Used extensively in `pymode/rope.py`

**Dependencies:**
- Rope depends on `pytoolconfig[global] >= 1.2.2` (per rope's pyproject.toml)
- Rope uses pytoolconfig for configuration management

### ✅ Tomli - KEEP
**Status:** Required by rope (via pytoolconfig)

**Reason:**
- `pytoolconfig` uses `tomli` (or `tomllib` in Python 3.11+) to parse TOML config files
- Required for rope to read pyproject.toml configuration
- Python 3.11+ has built-in `tomllib`, but tomli provides backport for older Python versions

**Usage:**
- Indirect dependency through pytoolconfig
- Not directly imported in pymode code

### ✅ Pytoolconfig - KEEP
**Status:** Required by rope

**Reason:**
- Rope explicitly depends on `pytoolconfig[global] >= 1.2.2`
- Used by rope to read configuration from pyproject.toml and other config files
- Essential for rope functionality

**Usage:**
- Required dependency of rope
- Not directly imported in pymode code

### ❌ Toml - REMOVE
**Status:** Not needed

**Reason:**
- Not used anywhere in pymode code
- Ruff handles its own TOML parsing internally
- Python-mode doesn't need to parse TOML files directly
- tomli is sufficient for rope's needs (via pytoolconfig)

**Action:** Remove from `.gitmodules` and `pymode/utils.py`

### ❌ Appdirs - REMOVE
**Status:** Not needed

**Reason:**
- Not imported or used anywhere in pymode codebase
- No references found in pymode Python files
- Not a dependency of rope or any other kept submodule

**Action:** Remove from `.gitmodules` and `pymode/utils.py`

### ❌ Snowball_py - REMOVE
**Status:** Not needed (already removed from .gitmodules)

**Reason:**
- Was only used by pydocstyle for text stemming
- Pydocstyle is replaced by Ruff
- No longer needed

**Action:** Already removed from `.gitmodules` in Phase 2

### ❓ Astroid - EVALUATE
**Status:** May not be needed

**Reason:**
- Originally thought to be a dependency of rope
- No direct imports of astroid found in pymode code
- Rope's pyproject.toml doesn't list astroid as a dependency
- May have been needed only for pylint (which is replaced by Ruff)

**Investigation:**
- Check if rope actually uses astroid internally
- If not used, can be removed

**Action:** Test rope functionality without astroid, then decide

## Recommended Actions

1. **Remove toml submodule** - Not used
2. **Remove appdirs submodule** - Not used  
3. **Keep tomli** - Required by pytoolconfig (rope dependency)
4. **Keep pytoolconfig** - Required by rope
5. **Keep rope** - Essential functionality
6. **Test astroid removal** - Verify rope works without it

## Final Submodule List

After Phase 4, the following submodules should remain:
- `submodules/rope` - Essential IDE features
- `submodules/tomli` - Required by pytoolconfig
- `submodules/pytoolconfig` - Required by rope

**Total:** 3 submodules (down from 13 original submodules)

## Testing Plan

1. ✅ Rope tests already passing (9/9) - verified in Phase 5
2. Test rope functionality with only required submodules
3. Verify code completion works
4. Verify go-to-definition works
5. Verify refactoring operations work

