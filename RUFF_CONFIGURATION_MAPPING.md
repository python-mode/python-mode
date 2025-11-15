# Ruff Configuration Mapping Guide

This document explains how python-mode configuration options map to Ruff settings, and how to migrate from the old linting tools to Ruff.

## Overview

Python-mode now uses Ruff for linting and formatting, replacing:
- **pyflakes** - Syntax errors and undefined names
- **pycodestyle** - PEP 8 style guide enforcement
- **mccabe** - Cyclomatic complexity checking
- **pylint** - Comprehensive static analysis
- **pydocstyle** - Docstring style checking
- **pylama** - Multi-tool linting wrapper
- **autopep8** - Automatic PEP 8 formatting

## Configuration Options

### Legacy Options (Still Supported)

These options are maintained for backward compatibility and are automatically converted to Ruff rules:

#### `g:pymode_lint_checkers`
**Default:** `['pyflakes', 'pycodestyle', 'mccabe']`

Maps to Ruff rule categories:
- `'pyflakes'` → Ruff `F` rules (pyflakes)
- `'pycodestyle'` → Ruff `E` and `W` rules (pycodestyle)
- `'mccabe'` → Ruff `C90` rule (mccabe complexity)
- `'pylint'` → Ruff `PL` rules (pylint)
- `'pydocstyle'` → Ruff `D` rules (pydocstyle)

**Example:**
```vim
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle']
" This enables Ruff rules: F (pyflakes), E (pycodestyle errors), W (pycodestyle warnings)
```

#### `g:pymode_lint_ignore`
**Default:** `[]`

Maps to Ruff `--ignore` patterns. Supports both legacy error codes (E501, W503) and Ruff rule codes.

**Example:**
```vim
let g:pymode_lint_ignore = ['E501', 'W503', 'F401']
" Ruff will ignore: E501 (line too long), W503 (line break before binary operator), F401 (unused import)
```

#### `g:pymode_lint_select`
**Default:** `[]`

Maps to Ruff `--select` patterns. Selects specific rules to enable.

**Example:**
```vim
let g:pymode_lint_select = ['E', 'F']
" Ruff will only check E (pycodestyle errors) and F (pyflakes) rules
```

### New Ruff-Specific Options

These options provide direct control over Ruff behavior:

#### `g:pymode_ruff_enabled`
**Default:** `1`

Enable or disable Ruff linting entirely.

**Example:**
```vim
let g:pymode_ruff_enabled = 1  " Enable Ruff (default)
let g:pymode_ruff_enabled = 0  " Disable Ruff
```

#### `g:pymode_ruff_format_enabled`
**Default:** `1`

Enable or disable Ruff formatting (replaces autopep8).

**Example:**
```vim
let g:pymode_ruff_format_enabled = 1  " Enable Ruff formatting (default)
let g:pymode_ruff_format_enabled = 0  " Disable Ruff formatting
```

#### `g:pymode_ruff_select`
**Default:** `[]`

Ruff-specific select rules. If set, overrides `g:pymode_lint_select`.

**Example:**
```vim
let g:pymode_ruff_select = ['E', 'F', 'W', 'C90']
" Enable pycodestyle errors, pyflakes, pycodestyle warnings, and mccabe complexity
```

#### `g:pymode_ruff_ignore`
**Default:** `[]`

Ruff-specific ignore patterns. If set, overrides `g:pymode_lint_ignore`.

**Example:**
```vim
let g:pymode_ruff_ignore = ['E501', 'F401']
" Ignore line too long and unused import warnings
```

#### `g:pymode_ruff_config_file`
**Default:** `""`

Path to Ruff configuration file (pyproject.toml, ruff.toml, etc.). If empty, Ruff will search for configuration files automatically.

**Example:**
```vim
let g:pymode_ruff_config_file = '/path/to/pyproject.toml'
" Use specific Ruff configuration file
```

## Migration Examples

### Example 1: Basic Configuration

**Before (using legacy tools):**
```vim
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle']
let g:pymode_lint_ignore = ['E501', 'W503']
```

**After (using Ruff - backward compatible):**
```vim
" Same configuration works automatically!
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle']
let g:pymode_lint_ignore = ['E501', 'W503']
```

**After (using Ruff-specific options):**
```vim
let g:pymode_ruff_select = ['F', 'E', 'W']  " pyflakes, pycodestyle errors/warnings
let g:pymode_ruff_ignore = ['E501', 'W503']
```

### Example 2: Advanced Configuration

**Before:**
```vim
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle', 'mccabe', 'pylint']
let g:pymode_lint_options_mccabe = {'complexity': 10}
let g:pymode_lint_options_pycodestyle = {'max_line_length': 88}
```

**After:**
```vim
" Option 1: Use legacy options (still works)
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle', 'mccabe', 'pylint']
let g:pymode_lint_options_mccabe = {'complexity': 10}
let g:pymode_lint_options_pycodestyle = {'max_line_length': 88}

" Option 2: Use Ruff-specific options + config file
let g:pymode_ruff_select = ['F', 'E', 'W', 'C90', 'PL']
let g:pymode_ruff_config_file = 'pyproject.toml'
" In pyproject.toml:
" [tool.ruff]
" line-length = 88
" [tool.ruff.mccabe]
" max-complexity = 10
```

### Example 3: Disabling Formatting

**Before:**
```vim
" No direct way to disable autopep8
```

**After:**
```vim
let g:pymode_ruff_format_enabled = 0  " Disable Ruff formatting
```

## Rule Code Reference

### Pycodestyle Rules (E, W)
- **E** - Errors (syntax, indentation, etc.)
- **W** - Warnings (whitespace, line breaks, etc.)
- Common codes: `E501` (line too long), `E302` (expected blank lines), `W503` (line break before binary operator)

### Pyflakes Rules (F)
- **F** - Pyflakes errors
- Common codes: `F401` (unused import), `F811` (redefined while unused), `F841` (unused variable)

### McCabe Rules (C90)
- **C90** - Cyclomatic complexity
- Configured via `g:pymode_lint_options_mccabe` or Ruff config file

### Pylint Rules (PL)
- **PL** - Pylint rules
- Common codes: `PLR0913` (too many arguments), `PLR2004` (magic value)

### Pydocstyle Rules (D)
- **D** - Docstring style rules
- Common codes: `D100` (missing docstring), `D400` (first line should end with period)

## Configuration File Support

Ruff supports configuration via `pyproject.toml` or `ruff.toml` files. Python-mode will automatically use these if found, or you can specify a path with `g:pymode_ruff_config_file`.

**Example pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = ["E501"]

[tool.ruff.mccabe]
max-complexity = 10
```

## Backward Compatibility

All legacy configuration options continue to work. The migration is transparent - your existing configuration will automatically use Ruff under the hood.

## Troubleshooting

### Ruff not found
If you see "Ruff is not available", install it:
```bash
pip install ruff
```

Verify installation:
```bash
./scripts/verify_ruff_installation.sh
```

### Configuration not working
1. Check that `g:pymode_ruff_enabled = 1` (default)
2. Verify Ruff is installed: `ruff --version`
3. Check configuration file path if using `g:pymode_ruff_config_file`
4. Review Ruff output: `:PymodeLint` and check for errors

### Performance issues
Ruff is significantly faster than the old tools. If you experience slowdowns:
1. Check if Ruff config file is being read correctly
2. Verify Ruff version: `ruff --version` (should be recent)
3. Check for large ignore/select lists that might slow down rule processing

## Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rule Reference](https://docs.astral.sh/ruff/rules/)
- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/)

