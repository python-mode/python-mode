# Known Test Failures - Investigation Required

## Status: ✅ All Tests Passing

All Vader test suites are now passing! The issues have been resolved by fixing Python path initialization and making imports lazy.

## Test Results Summary

### ✅ Passing Test Suites (8/8)
- `autopep8.vader` - All 8 tests passing ✅
- `commands.vader` - All 7 tests passing ✅
- `folding.vader` - All tests passing
- `lint.vader` - All tests passing  
- `motion.vader` - All tests passing
- `rope.vader` - All tests passing
- `simple.vader` - All tests passing
- `textobjects.vader` - All tests passing

## Fixes Applied

### Track 3: Test Fixes (Completed)

**Issue:** Python module imports were failing because:
1. Python paths were not initialized before autoload files imported Python modules
2. Top-level imports in `autoload/pymode/lint.vim` executed before `patch_paths()` added submodules to sys.path

**Solution:**
1. **Fixed `tests/vader/setup.vim`:**
   - Added Python path initialization (`pymode#init()`) before loading autoload files that import Python modules
   - Ensured `patch_paths()` is called to add submodules to sys.path
   - Used robust plugin root detection

2. **Fixed `autoload/pymode/lint.vim`:**
   - Made `code_check` import lazy (moved from top-level to inside `pymode#lint#check()` function)
   - This ensures Python paths are initialized before the import happens

**Files Modified:**
- `tests/vader/setup.vim` - Added Python path initialization
- `autoload/pymode/lint.vim` - Made imports lazy

### Previous Fixes

#### Commit: 48c868a
- ✅ Added Vader.vim installation to Dockerfile
- ✅ Improved test runner script error handling
- ✅ Enhanced success detection for Vader output
- ✅ Changed to use Vim's -es mode for better output handling

