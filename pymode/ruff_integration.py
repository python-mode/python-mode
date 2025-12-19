"""Ruff integration for Python-mode.

This module provides integration with Ruff, a fast Python linter and formatter.
It replaces the previous pylama-based linting system with a single, modern tool.
"""

import json
import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any

from .environment import env
from .utils import silence_stderr


class RuffError:
    """Represents a Ruff linting error/warning."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize from Ruff JSON output."""
        self.filename = data.get('filename', '')
        self.line = data.get('location', {}).get('row', 1)
        self.col = data.get('location', {}).get('column', 1)
        self.code = data.get('code', '')
        self.message = data.get('message', '')
        self.severity = data.get('severity', 'error')
        self.rule = data.get('rule', '')
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to vim-compatible error dictionary."""
        return {
            'filename': self.filename,
            'lnum': self.line,
            'col': self.col,
            'text': f"{self.code}: {self.message}",
            'type': 'E' if self.severity == 'error' else 'W',
            'code': self.code,
        }


def _get_ruff_executable() -> str:
    """Get the ruff executable path."""
    # Try to get from vim configuration first
    ruff_path = env.var('g:pymode_ruff_executable', silence=True, default='ruff')
    
    # Verify ruff is available
    try:
        subprocess.run([ruff_path, '--version'], 
                      capture_output=True, check=True, timeout=5)
        return ruff_path
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        env.error("Ruff not found. Please install ruff: pip install ruff")
        raise RuntimeError("Ruff executable not found")


def _add_tool_specific_options(config: Dict[str, Any], linters: List[str]) -> None:
    """Add tool-specific configuration options."""
    
    # Handle mccabe complexity
    if 'mccabe' in linters:
        mccabe_opts = env.var('g:pymode_lint_options_mccabe', silence=True, default={})
        if mccabe_opts and 'complexity' in mccabe_opts:
            # Ruff uses mccabe.max-complexity
            config['mccabe'] = {'max-complexity': mccabe_opts['complexity']}
    
    # Handle pycodestyle options
    if 'pycodestyle' in linters or 'pep8' in linters:
        pycodestyle_opts = env.var('g:pymode_lint_options_pycodestyle', silence=True, default={})
        if pycodestyle_opts:
            if 'max_line_length' in pycodestyle_opts:
                config['line-length'] = pycodestyle_opts['max_line_length']
    
    # Handle pylint options
    if 'pylint' in linters:
        pylint_opts = env.var('g:pymode_lint_options_pylint', silence=True, default={})
        if pylint_opts:
            if 'max-line-length' in pylint_opts:
                config['line-length'] = pylint_opts['max-line-length']
    
    # Handle pydocstyle/pep257 options
    if 'pydocstyle' in linters or 'pep257' in linters:
        pydocstyle_opts = env.var('g:pymode_lint_options_pep257', silence=True, default={})
        # Most pydocstyle options don't have direct ruff equivalents
        # Users should configure ruff directly for advanced docstring checking
    
    # Handle pyflakes options
    if 'pyflakes' in linters:
        pyflakes_opts = env.var('g:pymode_lint_options_pyflakes', silence=True, default={})
        # Pyflakes builtins option doesn't have a direct ruff equivalent
        # Users can use ruff's built-in handling or per-file ignores


def validate_configuration() -> List[str]:
    """Validate pymode configuration for ruff compatibility.
    
    Returns:
        List of warning messages about configuration issues
    """
    warnings = []
    
    # Check if ruff is available
    if not check_ruff_available():
        warnings.append("Ruff is not installed. Please install with: pip install ruff")
        return warnings
    
    # Check linter configuration
    linters = env.var('g:pymode_lint_checkers', default=['pyflakes', 'pycodestyle'])
    supported_linters = {'pyflakes', 'pycodestyle', 'pep8', 'mccabe', 'pylint', 'pydocstyle', 'pep257'}
    
    for linter in linters:
        if linter not in supported_linters:
            warnings.append(f"Linter '{linter}' is not supported by ruff integration")
    
    # Check mccabe complexity configuration
    if 'mccabe' in linters:
        mccabe_opts = env.var('g:pymode_lint_options_mccabe', silence=True, default={})
        if mccabe_opts and 'complexity' in mccabe_opts:
            warnings.append("McCabe complexity setting requires ruff configuration file (pyproject.toml or ruff.toml)")
    
    # Check for deprecated pep8 linter
    if 'pep8' in linters:
        warnings.append("'pep8' linter is deprecated, use 'pycodestyle' instead")
    
    # Check for deprecated pep257 linter
    if 'pep257' in linters:
        warnings.append("'pep257' linter is deprecated, use 'pydocstyle' instead")
    
    return warnings


def run_ruff_check(file_path: str, content: str = None) -> List[RuffError]:
    """Run ruff check on a file and return errors.
    
    Args:
        file_path: Path to the file to check
        content: Optional file content (for checking unsaved buffers)
        
    Returns:
        List of RuffError objects
    """
    # Check if Ruff is enabled
    ruff_enabled = env.var('g:pymode_ruff_enabled', silence=True, default=True)
    if not ruff_enabled:
        return []
    
    try:
        ruff_path = _get_ruff_executable()
    except RuntimeError:
        return []
    # Prepare command
    cmd = [ruff_path, 'check', '--output-format=json']
    # Handle content checking (for unsaved buffers)
    temp_file_path = None
    if content is not None:
        # Write content to temporary file
        fd, temp_file_path = tempfile.mkstemp(suffix='.py', prefix='pymode_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            cmd.append(temp_file_path)
        except Exception:
            os.close(fd)
            if temp_file_path:
                os.unlink(temp_file_path)
            raise
    else:
        cmd.append(file_path)
    
    errors = []
    try:
        with silence_stderr():
            # Run ruff
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=env.curdir
            )
            
            # Ruff returns non-zero exit code when issues are found
            if result.stdout:
                try:
                    # Parse JSON output
                    ruff_output = json.loads(result.stdout)
                    for item in ruff_output:
                        # Map temp file path back to original if needed
                        if temp_file_path and item.get('filename') == temp_file_path:
                            item['filename'] = file_path
                        errors.append(RuffError(item))
                except json.JSONDecodeError as e:
                    env.debug(f"Failed to parse ruff JSON output: {e}")
                    env.debug(f"Raw output: {result.stdout}")
            
            if result.stderr:
                env.debug(f"Ruff stderr: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        env.error("Ruff check timed out")
    except Exception as e:
        env.debug(f"Ruff check failed: {e}")
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
    
    return errors


def run_ruff_format(file_path: str, content: str = None) -> Optional[str]:
    """Run ruff format on a file and return formatted content.
    
    Args:
        file_path: Path to the file to format
        content: Optional file content (for formatting unsaved buffers)
        
    Returns:
        Formatted content as string, or None if formatting failed
    """
    try:
        ruff_path = _get_ruff_executable()
    except RuntimeError:
        return None
    
    # Check if formatting is enabled
    if not env.var('g:pymode_ruff_format_enabled', silence=True, default=True):
        return None
    
    # Prepare command
    cmd = [ruff_path, 'format', '--stdin-filename', file_path]
    try:
        with silence_stderr():
            # Run ruff format
            result = subprocess.run(
                cmd,
                input=content if content is not None else open(file_path).read(),
                capture_output=True,
                text=True,
                timeout=30,
                cwd=env.curdir
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                # If ruff fails due to syntax errors, return original content
                # This maintains backward compatibility with autopep8 behavior
                # if "Failed to parse" in result.stderr or "SyntaxError" in result.stderr:
                #     env.debug(f"Ruff format skipped due to syntax errors: {result.stderr}")
                #     return content if content else None
                env.debug(f"Ruff format failed: {result.stderr}")
                return None
                
    except subprocess.TimeoutExpired:
        env.error("Ruff format timed out")
        return None
    except Exception as e:
        env.debug(f"Ruff format failed: {e}")
        return None


def check_ruff_available() -> bool:
    """Check if ruff is available and working."""
    try:
        _get_ruff_executable()
        return True
    except RuntimeError:
        return False


# Legacy compatibility function
def code_check():
    """Run ruff check on current buffer (replaces pylama integration).
    
    This function maintains compatibility with the existing pymode interface.
    """
    if not env.curbuf.name:
        return env.stop()
    
    # Get file content from current buffer
    content = '\n'.join(env.curbuf) + '\n'
    file_path = env.curbuf.name
    
    # Use relpath if possible, but handle Windows drive letter differences
    try:
        rel_path = os.path.relpath(file_path, env.curdir)
        env.debug("Start ruff code check: ", rel_path)
    except ValueError:
        # On Windows, relpath fails if paths are on different drives
        # Fall back to absolute path in this case
        env.debug("Start ruff code check (abs path): ", file_path)
    
    # Run ruff check
    errors = run_ruff_check(file_path, content)
    
    env.debug("Find errors: ", len(errors))
    
    # Convert to vim-compatible format
    errors_list = []
    for error in errors:
        err_dict = error.to_dict()
        err_dict['bufnr'] = env.curbuf.number
        errors_list.append(err_dict)
    
    # Apply sorting if configured
    sort_rules = env.var('g:pymode_lint_sort', default=[])
    if sort_rules:
        def __sort(e):
            try:
                return sort_rules.index(e.get('type'))
            except ValueError:
                return 999
        errors_list = sorted(errors_list, key=__sort)
    
    # Add to location list
    env.run('g:PymodeLocList.current().extend', errors_list)