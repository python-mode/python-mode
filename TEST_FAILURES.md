# Known Test Failures - Investigation Required

## Status: Partially Fixed

The Vader test infrastructure has been improved with Vader.vim installation in Dockerfile and enhanced test runner script. However, some tests are still failing due to python-mode functionality issues.

## Test Results Summary

### ✅ Passing Test Suites (6/8)
- `folding.vader` - All tests passing
- `lint.vader` - All tests passing  
- `motion.vader` - All tests passing
- `rope.vader` - All tests passing
- `simple.vader` - All tests passing
- `textobjects.vader` - All tests passing

### ⚠️ Failing Test Suites (2/8)

#### 1. autopep8.vader - 1/8 tests passing

**Error:**
```
E117: Unknown function: pymode#lint#auto
```

**Root Cause:**
The `pymode#lint#auto` function is defined in `autoload/pymode/lint.vim` but is not being loaded/available in the Vader test environment.

**Affected Tests:**
- Test multiple formatting issues
- Test autopep8 with class formatting
- Test autopep8 with long lines
- Test autopep8 with imports
- Test autopep8 preserves functionality
- Test autopep8 with well-formatted code

**Investigation Needed:**
1. Verify autoload function loading mechanism in Vader test setup
2. Check if `autoload/pymode/lint.vim` is being sourced properly
3. Verify python-mode plugin initialization sequence in test containers
4. Check if runtimepath includes autoload directories correctly

#### 2. commands.vader - 6/7 tests passing

**Error:**
```
PymodeLintAuto produced no changes
```

**Root Cause:**
One test expects `PymodeLintAuto` to format code, but it's not producing changes. This is likely related to the same autoload function loading issue affecting autopep8.vader.

**Affected Test:**
- Test PymodeLintAuto command

**Investigation Needed:**
1. Same as autopep8.vader - autoload function loading
2. Verify PymodeLintAuto command is properly registered
3. Check if autopep8 functionality is working in test environment

## Fixes Applied

### Commit: 48c868a
- ✅ Added Vader.vim installation to Dockerfile
- ✅ Improved test runner script error handling
- ✅ Enhanced success detection for Vader output
- ✅ Changed to use Vim's -es mode for better output handling

## Next Steps

1. **Investigate autoload function loading**
   - Check `tests/utils/vimrc` runtimepath configuration
   - Verify autoload directory is in runtimepath
   - Test manual loading of `autoload/pymode/lint.vim`

2. **Debug test environment**
   - Run tests with verbose Vim output
   - Check if python-mode plugin is fully initialized
   - Verify all autoload functions are available

3. **Fix autoload loading**
   - Ensure autoload functions are loaded before tests run
   - May need to explicitly source autoload files in test setup
   - Or ensure runtimepath is correctly configured

## Related Files

- `autoload/pymode/lint.vim` - Contains `pymode#lint#auto` function
- `ftplugin/python/pymode.vim` - Defines `PymodeLintAuto` command
- `tests/utils/vimrc` - Test configuration file
- `tests/vader/setup.vim` - Vader test setup
- `tests/vader/autopep8.vader` - Failing test suite
- `tests/vader/commands.vader` - Partially failing test suite

