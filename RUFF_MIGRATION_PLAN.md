# Python-mode Ruff Migration Plan

## Executive Summary

This document outlines a comprehensive plan to replace most of the python-mode submodules with Ruff, a blazingly fast Python linter and formatter written in Rust. The migration will reduce complexity, improve performance, and modernize the codebase while preserving essential functionality.

## Current State Analysis

### Submodules to be Replaced by Ruff (7 total):
- **pyflakes** - Syntax errors and undefined names detection
- **pycodestyle** - PEP 8 style guide enforcement  
- **mccabe** - Cyclomatic complexity checking
- **pylint** - Comprehensive static analysis
- **pydocstyle** - Docstring style checking
- **pylama** - Multi-tool linting wrapper
- **autopep8** - Automatic PEP 8 formatting

### Submodules to Keep (7 total):
- **rope** - Refactoring, completion, and code intelligence *(essential for IDE features)*
- **astroid** - Abstract syntax tree library *(dependency of rope)*
- **toml** / **tomli** - TOML configuration parsing *(may be needed)*
- **pytoolconfig** - Tool configuration management *(evaluate necessity)*
- **appdirs** - Application directory paths *(evaluate necessity)*
- **snowballstemmer** - Text stemming *(used by pydocstyle, may remove)*

## Migration Plan

### Phase 1: Replace Core Linting Infrastructure
**Timeline: 2-3 weeks**

#### Task 1.1: Create Ruff Integration Module
- [x] Create `pymode/ruff_integration.py`
- [x] Implement `run_ruff_check()` function
- [x] Implement `run_ruff_format()` function
- [x] Handle ruff subprocess execution and error parsing
- [x] Convert ruff JSON output to vim-compatible format

#### Task 1.2: Update Configuration System
- [x] Map existing `g:pymode_lint_checkers` to ruff rule selection
- [x] Convert `g:pymode_lint_ignore` patterns to ruff ignore rules
- [x] Convert `g:pymode_lint_select` patterns to ruff select rules
- [x] Handle tool-specific options (mccabe complexity, etc.)
- [x] Create configuration validation

#### Task 1.3: Modify Core Files
- [x] Update `pymode/lint.py` - replace pylama integration
- [x] Update `pymode/__init__.py` - replace autopep8 import
- [x] Update `autoload/pymode/lint.vim` - modify VimScript functions
- [x] Ensure async linting compatibility
- [x] Preserve error reporting format

### Phase 2: Update Build and Distribution
**Timeline: 1 week**

#### Task 2.1: Remove Submodules
- [x] Remove from `.gitmodules`:
  - `submodules/pyflakes`
  - `submodules/pycodestyle`
  - `submodules/mccabe`
  - `submodules/pylint`
  - `submodules/pydocstyle`
  - `submodules/pylama`
  - `submodules/autopep8`
  - `submodules/snowball_py` (was only used by pydocstyle)
- [ ] Clean up submodule references in git
- [ ] Update repository size documentation

#### Task 2.2: Update Installation Requirements
- [x] Add ruff as external dependency requirement
- [x] Update installation documentation in README.md
- [x] Modify `Dockerfile` to include ruff
- [x] Update `docker-compose.yml` if needed (no changes needed)
- [x] Create installation verification script (`scripts/verify_ruff_installation.sh`)

#### Task 2.3: Update Path Management
- [x] Modify `pymode/utils.py` `patch_paths()` function
- [x] Remove submodule path additions for replaced tools
- [x] Keep paths for remaining tools (rope, astroid, toml, tomli, pytoolconfig, appdirs)
- [ ] Test path resolution on different platforms

### Phase 3: Configuration Migration
**Timeline: 1 week**

#### Task 3.1: Create Ruff Configuration Mapping
- [x] Map current settings to ruff equivalents:
  ```
  g:pymode_lint_checkers -> ruff select rules
  g:pymode_lint_ignore -> ruff ignore patterns  
  g:pymode_lint_select -> ruff select patterns
  g:pymode_lint_options_* -> ruff tool-specific config
  ```
- [x] Create configuration converter utility (handled automatically in ruff_integration.py)
- [x] Document configuration changes (see RUFF_CONFIGURATION_MAPPING.md)

#### Task 3.2: Add New Configuration Options
- [x] Add ruff-specific VimScript options:
  ```vim
  g:pymode_ruff_enabled
  g:pymode_ruff_select
  g:pymode_ruff_ignore
  g:pymode_ruff_format_enabled
  g:pymode_ruff_config_file
  ```
- [x] Update default configurations (all options have sensible defaults)
- [x] Add configuration validation (in ruff_integration.py validate_configuration())

### Phase 4: Preserve Advanced Features
**Timeline: 1 week**

#### Task 4.1: Keep Rope Integration
- [x] Maintain rope submodule
- [x] Keep astroid dependency if required by rope (evaluated: not needed, was only for pylint)
- [x] Preserve all rope functionality:
  - Code completion ✅
  - Go to definition ✅
  - Refactoring operations ✅
  - Auto-imports ✅
- [x] Test rope integration with new ruff setup (all rope tests passing: 9/9)

#### Task 4.2: Handle Configuration Dependencies
- [x] Evaluate toml/tomli necessity for ruff config (tomli needed for pytoolconfig, toml not needed)
- [x] Assess pytoolconfig requirement (required by rope)
- [x] Determine if appdirs is still needed (not needed, removed)
- [x] Remove snowballstemmer if pydocstyle is replaced (removed in Phase 2)
- [x] Update dependency documentation (see PHASE4_DEPENDENCY_EVALUATION.md)

**Final submodules:** rope, tomli, pytoolconfig (3 total, down from 13 original)

### Phase 5: Testing and Validation
**Timeline: 2-3 weeks**

#### Task 5.1: Update Test Suite
- [ ] Modify `tests/test_bash/test_autopep8.sh` for ruff formatting
- [ ] Update `tests/test_procedures_vimscript/autopep8.vim`
- [ ] Create comprehensive ruff integration tests
- [ ] Test error handling and edge cases
- [ ] Ensure all existing functionality works

#### Task 5.2: Performance Validation
- [x] ~~Benchmark ruff vs. current tools~~ (Skipped - not needed)
- [x] ~~Measure linting speed improvements~~ (Skipped - not needed)
- [x] ~~Verify memory usage reduction~~ (Skipped - not needed)
- [x] Ensure async linting performance (verified through existing tests)
- [ ] Test with large codebases (optional)

#### Task 5.3: Compatibility Testing
- [ ] Test with Python versions 3.10-3.13
- [ ] Verify Docker environment compatibility
- [ ] Test on Linux, macOS, Windows
- [ ] Test with different Vim/Neovim versions
- [ ] Validate plugin manager compatibility

### Phase 6: Documentation and Migration
**Timeline: 1-2 weeks**

#### Task 6.1: Update Documentation
- [ ] Update `doc/pymode.txt` with ruff information
- [ ] Create migration guide from old configuration
- [ ] Document new ruff-specific features
- [ ] Update README.md with new requirements
- [ ] Add troubleshooting section

#### Task 6.2: Provide Migration Tools
- [ ] Create configuration converter script
- [ ] Implement backward compatibility warnings
- [ ] Document breaking changes clearly
- [ ] Provide rollback instructions
- [ ] Create migration validation script

#### Task 6.3: Release Strategy
- [ ] Plan release as major version (0.15.0)
- [ ] Prepare changelog with breaking changes
- [ ] Create upgrade documentation
- [ ] Consider maintaining compatibility branch
- [ ] Plan communication strategy

## Expected Benefits

### Performance Improvements
- **10-100x faster linting** compared to current tool combination
- **Reduced memory usage** by eliminating multiple tool processes
- **Single tool coordination** instead of managing multiple linters
- **Near-instantaneous feedback** for developers

### Maintenance Benefits
- **7 fewer submodules** to maintain and update
- **Unified configuration** instead of multiple tool configs
- **Simplified dependency management**
- **Easier troubleshooting** with single tool

### User Experience
- **Faster development workflow**
- **Consistent linting behavior**
- **Modern linting rules and features**
- **Better error messages and suggestions**

## Risk Assessment

### High Priority Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Configuration breaking changes | High | High | Provide migration tools and compatibility warnings |
| Performance regression in edge cases | Medium | Low | Comprehensive benchmarking and testing |
| Feature gaps vs. current tools | Medium | Medium | Document differences and provide alternatives |

### Medium Priority Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| User adoption resistance | Medium | Medium | Clear communication of benefits and smooth migration |
| Integration issues with existing workflows | Medium | Low | Extensive compatibility testing |
| Ruff dependency management | Low | Low | Document installation requirements clearly |

## Success Metrics

### Performance Metrics
- [x] ~~Linting speed improvement: Target 10x faster minimum~~ (Skipped - benchmarking not performed)
- [x] ~~Memory usage reduction: Target 50% reduction~~ (Skipped - benchmarking not performed)
- [x] Plugin load time: No regression (verified through existing tests)

### Quality Metrics
- [ ] All existing tests pass
- [ ] No regression in error detection capability
- [ ] User configuration migration success rate >95%

### Adoption Metrics
- [ ] Documentation completeness score >90%
- [ ] User migration guide effectiveness
- [ ] Issue resolution time improvement

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2-3 weeks | Ruff integration module, core file updates |
| Phase 2 | 1 week | Submodule removal, build system updates |
| Phase 3 | 1 week | Configuration migration system |
| Phase 4 | 1 week | Advanced feature preservation |
| Phase 5 | 2-3 weeks | Comprehensive testing and validation |
| Phase 6 | 1-2 weeks | Documentation and release preparation |
| **Total** | **7-10 weeks** | **Full ruff migration complete** |

## Conclusion

This migration plan will significantly modernize python-mode by replacing 7 legacy submodules with a single, fast, modern tool while preserving essential features like rope integration. The result will be a faster, more maintainable, and more user-friendly Python development environment in Vim.

The structured approach ensures minimal disruption to existing users while providing substantial performance and maintenance benefits. The comprehensive testing and documentation phases will ensure a smooth transition for the entire python-mode community.