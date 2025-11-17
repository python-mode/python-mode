#!/usr/bin/env python3
"""Configuration converter script for migrating python-mode configs to Ruff.

This script helps users migrate their existing python-mode configuration
from the old linting tools (pylint, pyflakes, pycodestyle, etc.) to Ruff.

Usage:
    python scripts/migrate_to_ruff.py [--vimrc-file <path>] [--output <path>]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


# Mapping of old linter names to Ruff rule categories
LINTER_TO_RUFF_RULES = {
    'pyflakes': ['F'],
    'pycodestyle': ['E', 'W'],
    'pep8': ['E', 'W'],
    'mccabe': ['C90'],
    'pylint': ['PLE', 'PLR', 'PLW'],
    'pydocstyle': ['D'],
    'pep257': ['D'],
    'autopep8': ['E', 'W'],
}


def find_vimrc_files() -> List[Path]:
    """Find common vimrc file locations."""
    candidates = [
        Path.home() / '.vimrc',
        Path.home() / '.vim' / 'vimrc',
        Path.home() / '.config' / 'nvim' / 'init.vim',
        Path.home() / '.config' / 'nvim' / 'init.lua',
    ]
    return [p for p in candidates if p.exists()]


def parse_vimrc_config(file_path: Path) -> dict:
    """Parse vimrc file and extract python-mode configuration."""
    config = {
        'lint_checkers': [],
        'lint_ignore': [],
        'lint_select': [],
        'ruff_enabled': None,
        'ruff_format_enabled': None,
        'ruff_ignore': [],
        'ruff_select': [],
        'max_line_length': None,
        'mccabe_complexity': None,
    }
    
    if not file_path.exists():
        return config
    
    content = file_path.read_text()
    
    # Extract g:pymode_lint_checkers
    checkers_match = re.search(r'let\s+g:pymode_lint_checkers\s*=\s*\[(.*?)\]', content)
    if checkers_match:
        checkers_str = checkers_match.group(1)
        config['lint_checkers'] = [
            c.strip().strip("'\"") 
            for c in re.findall(r"['\"]([^'\"]+)['\"]", checkers_str)
        ]
    
    # Extract g:pymode_lint_ignore
    ignore_match = re.search(r'let\s+g:pymode_lint_ignore\s*=\s*\[(.*?)\]', content)
    if ignore_match:
        ignore_str = ignore_match.group(1)
        config['lint_ignore'] = [
            i.strip().strip("'\"") 
            for i in re.findall(r"['\"]([^'\"]+)['\"]", ignore_str)
        ]
    
    # Extract g:pymode_lint_select
    select_match = re.search(r'let\s+g:pymode_lint_select\s*=\s*\[(.*?)\]', content)
    if select_match:
        select_str = select_match.group(1)
        config['lint_select'] = [
            s.strip().strip("'\"") 
            for s in re.findall(r"['\"]([^'\"]+)['\"]", select_str)
        ]
    
    # Extract g:pymode_ruff_enabled
    ruff_enabled_match = re.search(r'let\s+g:pymode_ruff_enabled\s*=\s*(\d+)', content)
    if ruff_enabled_match:
        config['ruff_enabled'] = ruff_enabled_match.group(1) == '1'
    
    # Extract g:pymode_ruff_format_enabled
    ruff_format_match = re.search(r'let\s+g:pymode_ruff_format_enabled\s*=\s*(\d+)', content)
    if ruff_format_match:
        config['ruff_format_enabled'] = ruff_format_match.group(1) == '1'
    
    # Extract g:pymode_ruff_ignore
    ruff_ignore_match = re.search(r'let\s+g:pymode_ruff_ignore\s*=\s*\[(.*?)\]', content)
    if ruff_ignore_match:
        ruff_ignore_str = ruff_ignore_match.group(1)
        config['ruff_ignore'] = [
            i.strip().strip("'\"") 
            for i in re.findall(r"['\"]([^'\"]+)['\"]", ruff_ignore_str)
        ]
    
    # Extract g:pymode_ruff_select
    ruff_select_match = re.search(r'let\s+g:pymode_ruff_select\s*=\s*\[(.*?)\]', content)
    if ruff_select_match:
        ruff_select_str = ruff_select_match.group(1)
        config['ruff_select'] = [
            s.strip().strip("'\"") 
            for s in re.findall(r"['\"]([^'\"]+)['\"]", ruff_select_str)
        ]
    
    # Extract g:pymode_options_max_line_length
    max_line_match = re.search(r'let\s+g:pymode_options_max_line_length\s*=\s*(\d+)', content)
    if max_line_match:
        config['max_line_length'] = int(max_line_match.group(1))
    
    # Extract g:pymode_lint_options_mccabe_complexity
    mccabe_match = re.search(r'let\s+g:pymode_lint_options_mccabe_complexity\s*=\s*(\d+)', content)
    if mccabe_match:
        config['mccabe_complexity'] = int(mccabe_match.group(1))
    
    return config


def convert_to_ruff_config(old_config: dict) -> dict:
    """Convert old python-mode config to Ruff-specific config."""
    ruff_config = {
        'ruff_enabled': True,
        'ruff_format_enabled': old_config.get('lint_checkers') and 'autopep8' in old_config['lint_checkers'],
        'ruff_select': [],
        'ruff_ignore': old_config.get('lint_ignore', []).copy(),
        'max_line_length': old_config.get('max_line_length'),
        'mccabe_complexity': old_config.get('mccabe_complexity'),
    }
    
    # Convert lint_checkers to ruff_select rules
    select_rules = set()
    
    # Add rules from explicit select
    if old_config.get('lint_select'):
        select_rules.update(old_config['lint_select'])
    
    # Add rules from enabled linters
    for linter in old_config.get('lint_checkers', []):
        if linter in LINTER_TO_RUFF_RULES:
            select_rules.update(LINTER_TO_RUFF_RULES[linter])
    
    # If no specific rules selected, use a sensible default
    if not select_rules:
        select_rules = {'F', 'E', 'W'}  # Pyflakes + pycodestyle by default
    
    ruff_config['ruff_select'] = sorted(list(select_rules))
    
    # If ruff-specific config already exists, preserve it
    if old_config.get('ruff_enabled') is not None:
        ruff_config['ruff_enabled'] = old_config['ruff_enabled']
    if old_config.get('ruff_format_enabled') is not None:
        ruff_config['ruff_format_enabled'] = old_config['ruff_format_enabled']
    if old_config.get('ruff_ignore'):
        ruff_config['ruff_ignore'] = old_config['ruff_ignore']
    if old_config.get('ruff_select'):
        ruff_config['ruff_select'] = old_config['ruff_select']
    
    return ruff_config


def generate_vimrc_snippet(config: dict) -> str:
    """Generate VimScript configuration snippet."""
    lines = [
        '" Ruff configuration for python-mode',
        '" Generated by migrate_to_ruff.py',
        '',
    ]
    
    if config.get('ruff_enabled'):
        lines.append('let g:pymode_ruff_enabled = 1')
    
    if config.get('ruff_format_enabled'):
        lines.append('let g:pymode_ruff_format_enabled = 1')
    
    if config.get('ruff_select'):
        select_str = ', '.join(f'"{r}"' for r in config['ruff_select'])
        lines.append(f'let g:pymode_ruff_select = [{select_str}]')
    
    if config.get('ruff_ignore'):
        ignore_str = ', '.join(f'"{i}"' for i in config['ruff_ignore'])
        lines.append(f'let g:pymode_ruff_ignore = [{ignore_str}]')
    
    if config.get('max_line_length'):
        lines.append(f'let g:pymode_options_max_line_length = {config["max_line_length"]}')
    
    if config.get('mccabe_complexity'):
        lines.append(f'let g:pymode_lint_options_mccabe_complexity = {config["mccabe_complexity"]}')
    
    lines.append('')
    return '\n'.join(lines)


def generate_pyproject_toml(config: dict) -> str:
    """Generate pyproject.toml configuration snippet."""
    lines = [
        '[tool.ruff]',
    ]
    
    if config.get('max_line_length'):
        lines.append(f'line-length = {config["max_line_length"]}')
    
    if config.get('ruff_select'):
        select_str = ', '.join(f'"{r}"' for r in config['ruff_select'])
        lines.append(f'select = [{select_str}]')
    
    if config.get('ruff_ignore'):
        ignore_str = ', '.join(f'"{i}"' for i in config['ruff_ignore'])
        lines.append(f'ignore = [{ignore_str}]')
    
    if config.get('mccabe_complexity'):
        lines.append('')
        lines.append('[tool.ruff.lint.mccabe]')
        lines.append(f'max-complexity = {config["mccabe_complexity"]}')
    
    lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Convert python-mode configuration to Ruff',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze default vimrc file
  python scripts/migrate_to_ruff.py

  # Analyze specific vimrc file
  python scripts/migrate_to_ruff.py --vimrc-file ~/.vimrc

  # Generate migration output to file
  python scripts/migrate_to_ruff.py --output migration.txt
        """
    )
    parser.add_argument(
        '--vimrc-file',
        type=Path,
        help='Path to vimrc file (default: auto-detect)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file for migration suggestions (default: stdout)'
    )
    parser.add_argument(
        '--format',
        choices=['vimrc', 'pyproject', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    args = parser.parse_args()
    
    # Find vimrc file
    if args.vimrc_file:
        vimrc_path = args.vimrc_file
        if not vimrc_path.exists():
            print(f"Error: File not found: {vimrc_path}", file=sys.stderr)
            sys.exit(1)
    else:
        vimrc_files = find_vimrc_files()
        if not vimrc_files:
            print("Error: Could not find vimrc file. Please specify with --vimrc-file", file=sys.stderr)
            sys.exit(1)
        vimrc_path = vimrc_files[0]
        print(f"Found vimrc file: {vimrc_path}", file=sys.stderr)
    
    # Parse configuration
    old_config = parse_vimrc_config(vimrc_path)
    
    # Check if already using Ruff
    if old_config.get('ruff_enabled'):
        print("Note: Ruff is already enabled in your configuration.", file=sys.stderr)
    
    # Convert to Ruff config
    ruff_config = convert_to_ruff_config(old_config)
    
    # Generate output
    output_lines = [
        f"# Migration suggestions for {vimrc_path}",
        "#",
        "# Old configuration detected:",
        f"#   lint_checkers: {old_config.get('lint_checkers', [])}",
        f"#   lint_ignore: {old_config.get('lint_ignore', [])}",
        f"#   lint_select: {old_config.get('lint_select', [])}",
        "#",
        "# Recommended Ruff configuration:",
        "",
    ]
    
    if args.format in ('vimrc', 'both'):
        output_lines.append("## VimScript Configuration (.vimrc)")
        output_lines.append("")
        output_lines.append(generate_vimrc_snippet(ruff_config))
    
    if args.format in ('pyproject', 'both'):
        output_lines.append("## pyproject.toml Configuration")
        output_lines.append("")
        output_lines.append("Add this to your pyproject.toml:")
        output_lines.append("")
        output_lines.append(generate_pyproject_toml(ruff_config))
    
    output_text = '\n'.join(output_lines)
    
    # Write output
    if args.output:
        args.output.write_text(output_text)
        print(f"Migration suggestions written to: {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == '__main__':
    main()

