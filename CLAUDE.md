# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gam is a metadata-driven management tool for organizing and controlling multiple Docker Compose stacks. It enables priority-based startup, dependency management, auto-start on boot, and bulk operations across stacks using simple YAML metadata files.

The tool is designed to be non-invasive (doesn't modify docker-compose.yml files), git-friendly (all configuration in YAML), and simple (single Python script with no complex frameworks).

## Development Commands

### Running the Tool

The tool is packaged as a proper Python package and can be installed via pip/pipx/uv:

```bash
# Install in development mode
uv pip install -e .

# Run commands (after installation)
gam ls                     # List all stacks
gam ls -c video            # Filter by category (shortcut)
gam ls --category video    # Filter by category (full flag)
gam ls -t production       # Filter by tag (shortcut)
gam list                   # Alias for 'ls'

gam show <stack-name>

# Start, stop, restart with filters
gam up <stack-name>
gam up -c video            # Start all stacks in category
gam up -t production       # Start all stacks with tag
gam up --all               # Start all stacks

gam down <stack-name>
gam down -c video          # Stop all stacks in category
gam down -t production     # Stop all stacks with tag
gam down --all             # Stop all stacks

gam restart <stack-name>
gam restart -c video       # Restart all stacks in category
gam restart -t production  # Restart all stacks with tag
gam restart --all          # Restart all stacks

gam status
gam status -c video        # Show status filtered by category

gam validate
gam tag list
gam category list
```

**Tip**: Use `-c` as a shortcut for `--category` and `-t` as a shortcut for `--tag`.

Alternatively, run directly from source:

```bash
python -m gam.cli list
```

### Testing

The project includes comprehensive unit tests using pytest.

**Running Tests:**
```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/gam --cov-report=term-missing

# Run specific test file
uv run pytest test/unit/test_ls.py

# Run specific test
uv run pytest test/unit/test_ls.py::TestLsCommand::test_ls_all_stacks
```

**Test Structure:**
```
test/
├── conftest.py              # Shared fixtures
└── unit/
    ├── test_ls.py           # Tests for ls/list command
    ├── test_up_down_restart.py    # Tests for up/down/restart
    ├── test_show_status_search.py # Tests for show/status/search
    ├── test_tag_category.py       # Tests for tag/category
    └── test_autostart_validate.py # Tests for autostart/validate
```

**Manual Testing:**
When testing changes manually:

1. Create test stack directories with docker-compose.yml files
2. Add .stack-meta.yaml files with test metadata
3. Run commands against test stacks to verify behavior
4. Test edge cases: missing metadata files, broken dependencies, non-existent stacks

## Package Structure

The project follows modern Python packaging conventions:

```
gam/
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # User documentation
├── CLAUDE.md              # Developer documentation
└── src/
    └── gam/
        ├── __init__.py         # Package initialization
        ├── cli.py              # Main CLI implementation and argument parsing
        ├── stack.py            # Stack dataclass with metadata operations
        ├── stack_manager.py    # StackManager orchestrator class
        └── commands/           # Individual command implementations
            ├── __init__.py
            ├── list.py
            ├── show.py
            ├── up.py
            ├── down.py
            ├── restart.py
            ├── status.py
            ├── search.py
            ├── autostart.py
            ├── validate.py
            ├── tag.py
            └── category.py
```

**Entry Points**: The package defines a console script entry point `gam` that maps to `gam.cli:main`, making the command available system-wide after installation.

## Architecture

### Core Components

**Stack (dataclass)**: Represents a single Docker Compose stack with metadata. Key properties:
- `name`: Derived from directory path relative to root (e.g., "video-transcoding")
- `path`: Absolute path to stack directory
- `compose_file`: Path to docker-compose.yml
- `meta_file`: Path to .stack-meta.yaml
- Metadata fields: category, tags, priority, auto_start, depends_on, etc.

**StackManager (class)**: Central orchestrator for all stack operations. Key methods:
- `discover_stacks()`: Recursively finds all docker-compose.yml files, creates Stack objects, loads metadata
- `list_stacks()`: Filter stacks by category/tag
- `resolve_dependencies()`: Recursively builds dependency chain for a stack
- `get_autostart_stacks()`: Returns stacks with auto_start=true, sorted by priority

### Command Flow

1. `main()` sets up argparse subparsers for each command
2. Creates `StackManager` which discovers all stacks in current directory tree
3. Dispatches to command function (e.g., `cmd_up`, `cmd_list`)
4. Command functions use StackManager to find/filter stacks
5. Stack methods execute docker compose commands via subprocess

### Filtering Support

Commands support multiple filtering options:
- **`ls`** (alias: `list`): Filter by `--category` or `--tag`
- **`up`**: Filter by `--all`, `--category`, or `--tag`
- **`down`**: Filter by `--all`, `--category`, or `--tag`
- **`restart`**: Filter by `--all`, `--category`, or `--tag`
- **`status`**: Filter by `--category`

All category/tag filters support shortcuts: `-c` for category, `-t` for tag.

**Command Aliases**: Similar to Docker Compose, `list` is an alias for `ls`.

### Key Design Patterns

**Metadata Loading**: Each Stack loads its .stack-meta.yaml on initialization, merging values into dataclass fields using `setattr()`. Missing metadata files are tolerated (stack uses defaults).

**Status Checking**: `Stack.get_status()` runs `docker compose ps --format json` and parses output to determine if containers are running. Returns dict with status, container count, and running count.

**Priority-Based Operations**: Stacks have priority 1-5 (1=highest). Up operations sort ascending, down operations sort descending to reverse startup order.

**Dependency Resolution**: `resolve_dependencies()` recursively traverses `depends_on` lists to build complete dependency chains. Dependencies start before the target stack.

**Category Organization**: Stacks can have categories/subcategories (e.g., "video/processing"). Category is derived from directory structure or explicitly set in metadata.

## Metadata File Format

Stacks are configured via `.stack-meta.yaml` in each docker-compose directory:

```yaml
description: "Video transcoding service"
category: video
subcategory: processing
tags: [media, gpu, production]
auto_start: true
priority: 1  # 1=highest, 5=lowest
depends_on:
  - data-redis
  - data-postgres
expected_containers: 3
critical: true
owner: media-team
documentation: https://wiki.example.com/transcoding
health_check_url: http://localhost:8080/health
```

All fields are optional. Stack names are always derived from the directory path. The tool is extensible - custom fields can be added without code changes.

## Dependencies

- **Python 3.10+** (uses dataclass features, type hints)
- **PyYAML** (>=6.0) - Only external dependency, used for YAML parsing
- **Standard library**: subprocess, pathlib, argparse, dataclasses

The package intentionally keeps dependencies minimal for easy installation and maintenance.

## Directory Assumptions

The tool expects to be run from a root directory containing nested stack directories:

```
root/
├── category1/
│   ├── stack1/
│   │   ├── docker-compose.yml
│   │   └── .stack-meta.yaml
│   └── stack2/
│       ├── docker-compose.yml
│       └── .stack-meta.yaml
└── category2/
    └── stack3/
        ├── docker-compose.yml
        └── .stack-meta.yaml
```

Stack names are derived from relative paths (e.g., "category1-stack1"). Directories starting with '.' are skipped during discovery.

## Code Style Conventions

When working with this codebase, follow these conventions:

### Line Length
- **Maximum line length: 80 characters**
- Break long lines using parentheses for implicit continuation
- Example:
  ```python
  msg = (
      f"Long message that would exceed 80 characters "
      f"split across multiple lines"
  )
  ```

### Import Organization
- **Imports must be alphabetized** within their respective groups
- Group imports in this order:
  1. Standard library imports
  2. Third-party library imports (e.g., `yaml`)
  3. Local application imports
- **Absolute imports** for parent-level modules: Use `from gam.module import Class` (not `from ..module import Class`)
- **Relative imports** only for immediate siblings within the same package
- Example:
  ```python
  import subprocess
  from dataclasses import dataclass, field
  from pathlib import Path
  from typing import Dict, List, Optional

  import yaml

  from gam.stack_manager import StackManager
  ```

### YAML Formatting
- All YAML files must be written with **2-space indentation**
- Use `yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)` when writing metadata files
- This ensures consistent, readable YAML output across all generated files

### Module Organization
- **Command implementations** are organized in individual files under `src/gam/commands/`
- Each command file contains a single `cmd_*` function that implements the command logic
- Command files do NOT have module-level docstrings (the folder structure and function name make the purpose clear)

### Documentation
- **All docstrings** must be complete sentences ending with punctuation (period)
- Class docstrings: `"""Represents a Docker Compose stack with metadata."""`
- Method docstrings: `"""Load metadata from .stack-meta.yaml."""`
- Function docstrings: `"""List all stacks."""`

## Common Gotchas

1. **Stack naming**: Stack names use hyphens (e.g., "data-redis"), derived from path with os.sep replaced by '-'
2. **Dependency references**: Use stack names (not paths) in depends_on lists
3. **JSON parsing**: docker compose ps output is newline-delimited JSON (one object per line), not a JSON array
4. **Current directory**: StackManager discovers from cwd() by default - run from your stacks root directory
5. **Missing metadata**: Stacks work without .stack-meta.yaml (uses defaults), but validation warns about missing metadata
6. **YAML indentation**: Always use 2-space indentation when writing YAML files (set `indent=2` in yaml.dump)
7. **Line length**: Keep all lines at or under 80 characters for readability
8. **Import order**: Always alphabetize imports within their groups (stdlib, third-party, local)
9. **CLI shortcuts**: `-c` is available as a shortcut for `--category`, `-t` for `--tag` in all commands that accept these flags
10. **Command aliases**: The `list` command is an alias for `ls` (similar to Docker Compose interface)
