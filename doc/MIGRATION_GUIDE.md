# Migration Guide: From Old Linting Tools to Ruff

This guide helps you migrate from the old python-mode linting configuration (using pylint, pyflakes, pycodestyle, etc.) to the new Ruff-based system.

## Overview

Python-mode now uses **Ruff** instead of multiple separate linting tools. Ruff is:
- **10-100x faster** than the old tools
- **Single unified tool** replacing pyflakes, pycodestyle, mccabe, pylint, pydocstyle, autopep8
- **Backward compatible** - your existing configuration is automatically mapped to Ruff rules

## Quick Start

### 1. Install Ruff

```bash
pip install ruff
```

Verify installation:
```bash
ruff --version
```

### 2. Your Existing Configuration Still Works!

The good news: **You don't need to change anything immediately**. Your existing `g:pymode_lint_*` options are automatically mapped to Ruff rules.

For example:
```vim
" Your old configuration still works!
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle', 'mccabe']
let g:pymode_lint_ignore = ["E501", "W"]
```

This is automatically converted to equivalent Ruff rules.

### 3. (Optional) Migrate to Ruff-Specific Options

For better control and performance, you can migrate to Ruff-specific options:

```vim
" Enable Ruff linting and formatting
let g:pymode_ruff_enabled = 1
let g:pymode_ruff_format_enabled = 1

" Ruff-specific ignore rules (takes precedence over g:pymode_lint_ignore)
let g:pymode_ruff_ignore = ["E501", "W"]

" Ruff-specific select rules (takes precedence over g:pymode_lint_select)
let g:pymode_ruff_select = []

" Optional: Specify Ruff config file
let g:pymode_ruff_config_file = ""
```

## Configuration Mapping

### Legacy Options → Ruff Rules

| Old Option | Ruff Equivalent | Notes |
|------------|----------------|-------|
| `g:pymode_lint_checkers = ['pyflakes']` | Ruff F rules | F401, F402, F403, etc. |
| `g:pymode_lint_checkers = ['pycodestyle']` | Ruff E/W rules | E501, W292, etc. |
| `g:pymode_lint_checkers = ['mccabe']` | Ruff C90 rules | C901 (complexity) |
| `g:pymode_lint_checkers = ['pylint']` | Ruff PLE/PLR/PLW rules | PLE0001, PLR0913, etc. |
| `g:pymode_lint_checkers = ['pep257']` | Ruff D rules | D100, D101, etc. |
| `g:pymode_lint_ignore = ["E501"]` | Ruff ignore E501 | Same rule code |
| `g:pymode_lint_select = ["W0011"]` | Ruff select W0011 | Same rule code |

**Note:** Rule codes are mostly compatible. See `RUFF_CONFIGURATION_MAPPING.md` for detailed mappings.

### Using Ruff Configuration Files

Ruff supports configuration via `pyproject.toml` or `ruff.toml`:

**pyproject.toml:**
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W"]
ignore = ["E501"]

[tool.ruff.lint]
select = ["E", "F", "W"]
ignore = ["E501"]
```

**ruff.toml:**
```toml
line-length = 88
select = ["E", "F", "W"]
ignore = ["E501"]
```

Python-mode will automatically use these files if they exist in your project root.

## Step-by-Step Migration

### Step 1: Verify Ruff Installation

```bash
pip install ruff
ruff --version
```

### Step 2: Test Your Current Setup

Your existing configuration should work immediately. Try:
```vim
:PymodeLint        " Should work with Ruff
:PymodeLintAuto    " Should format with Ruff
```

### Step 3: (Optional) Create Ruff Config File

Create `pyproject.toml` or `ruff.toml` in your project root:

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "W"]
ignore = ["E501"]
```

### Step 4: (Optional) Migrate to Ruff-Specific Options

Update your `.vimrc`:

```vim
" Old way (still works)
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle']
let g:pymode_lint_ignore = ["E501"]

" New way (recommended)
let g:pymode_ruff_enabled = 1
let g:pymode_ruff_format_enabled = 1
let g:pymode_ruff_ignore = ["E501"]
```

## Common Scenarios

### Scenario 1: Using pyflakes + pycodestyle

**Before:**
```vim
let g:pymode_lint_checkers = ['pyflakes', 'pycodestyle']
let g:pymode_lint_ignore = ["E501"]
```

**After (automatic):**
- Works immediately, no changes needed!

**After (Ruff-specific):**
```vim
let g:pymode_ruff_enabled = 1
let g:pymode_ruff_ignore = ["E501"]
" Ruff automatically includes F (pyflakes) and E/W (pycodestyle) rules
```

### Scenario 2: Using autopep8 for formatting

**Before:**
```vim
" autopep8 was used automatically by :PymodeLintAuto
```

**After:**
```vim
let g:pymode_ruff_format_enabled = 1
" :PymodeLintAuto now uses Ruff format (faster!)
```

### Scenario 3: Custom pylint configuration

**Before:**
```vim
let g:pymode_lint_checkers = ['pylint']
let g:pymode_lint_options_pylint = {'max-line-length': 100}
```

**After:**
```vim
let g:pymode_ruff_enabled = 1
" Use pyproject.toml for Ruff configuration:
" [tool.ruff]
" line-length = 100
" select = ["PLE", "PLR", "PLW"]  # pylint rules
```

## Troubleshooting

### Ruff not found

**Error:** `ruff: command not found`

**Solution:**
```bash
pip install ruff
# Verify:
ruff --version
```

### Different formatting output

**Issue:** Ruff formats code differently than autopep8

**Solution:** This is expected. Ruff follows PEP 8 and Black formatting style. If you need specific formatting, configure Ruff via `pyproject.toml`:

```toml
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Rule codes don't match

**Issue:** Some rule codes might differ between old tools and Ruff

**Solution:** See `RUFF_CONFIGURATION_MAPPING.md` for detailed rule mappings. Most common rules (E501, F401, etc.) are compatible.

### Performance issues

**Issue:** Linting seems slower than expected

**Solution:** 
1. Ensure Ruff is installed: `pip install ruff`
2. Check if legacy options are causing overhead (migrate to Ruff-specific options)
3. Verify Ruff config file is being used

## Breaking Changes

### Removed Tools

The following tools are **no longer available** as separate checkers:
- `pylint` (use Ruff PLE/PLR/PLW rules)
- `pyflakes` (use Ruff F rules)
- `pycodestyle` (use Ruff E/W rules)
- `mccabe` (use Ruff C90 rules)
- `pep257` (use Ruff D rules)
- `autopep8` (use Ruff format)

### Configuration Changes

- `g:pymode_lint_checkers` values are mapped to Ruff rules (not actual tools)
- `g:pymode_lint_options_*` are mapped to Ruff configuration
- Old tool-specific options may not have exact equivalents

### Behavior Changes

- **Formatting:** Ruff format may produce slightly different output than autopep8
- **Linting:** Ruff may report different errors than pylint/pyflakes (usually fewer false positives)
- **Performance:** Should be significantly faster

## Rollback Instructions

If you need to rollback to the old system:

1. **Checkout previous version:**
   ```bash
   git checkout <previous-version-tag>
   ```

2. **Reinstall old dependencies** (if needed):
   ```bash
   pip install pylint pyflakes pycodestyle mccabe pydocstyle autopep8
   ```

3. **Restore old configuration** in your `.vimrc`

**Note:** The old tools are no longer maintained as submodules. You'll need to install them separately if rolling back.

## Need Help?

- **Configuration mapping:** See `RUFF_CONFIGURATION_MAPPING.md`
- **Ruff documentation:** https://docs.astral.sh/ruff/
- **Ruff rules:** https://docs.astral.sh/ruff/rules/
- **Python-mode help:** `:help pymode-ruff-configuration`

## Summary

✅ **No immediate action required** - your existing config works  
✅ **Install Ruff:** `pip install ruff`  
✅ **Optional:** Migrate to Ruff-specific options for better control  
✅ **Use Ruff config files:** `pyproject.toml` or `ruff.toml` for project-specific settings  
✅ **Enjoy faster linting and formatting!**

