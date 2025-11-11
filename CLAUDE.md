# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Composer is a metadata-driven management tool for organizing and controlling multiple Docker Compose stacks. It enables priority-based startup, dependency management, auto-start on boot, and bulk operations across stacks using simple YAML metadata files.

The tool is designed to be non-invasive (doesn't modify docker-compose.yml files), git-friendly (all configuration in YAML), and simple (single Python script with no complex frameworks).

## Development Commands

### Running the Tool

The tool is packaged as a proper Python package and can be installed via pip/pipx/uv:

```bash
# Install in development mode
pip install -e .

# Run commands (after installation)
composer list
composer show <stack-name>
composer up <stack-name>
composer down <stack-name>
composer status
composer validate
composer tag list
composer category list
```

Alternatively, run directly from source:

```bash
python -m composer.cli list
```

### Testing

The project currently has no automated tests. When testing changes manually:

1. Create test stack directories with docker-compose.yml files
2. Add .stack-meta.yaml files with test metadata
3. Run commands against test stacks to verify behavior
4. Test edge cases: missing metadata files, broken dependencies, non-existent stacks

## Package Structure

The project follows modern Python packaging conventions:

```
composer/
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # User documentation
├── CLAUDE.md              # Developer documentation
├── main.py                # Legacy entry point (kept for compatibility)
└── src/
    └── composer/
        ├── __init__.py    # Package initialization
        └── cli.py         # Main CLI implementation
```

**Entry Points**: The package defines a console script entry point `composer` that maps to `composer.cli:main`, making the command available system-wide after installation.

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

### Key Design Patterns

**Metadata Loading**: Each Stack loads its .stack-meta.yaml on initialization, merging values into dataclass fields using `setattr()`. Missing metadata files are tolerated (stack uses defaults).

**Status Checking**: `Stack.get_status()` runs `docker compose ps --format json` and parses output to determine if containers are running. Returns dict with status, container count, and running count.

**Priority-Based Operations**: Stacks have priority 1-5 (1=highest). Up operations sort ascending, down operations sort descending to reverse startup order.

**Dependency Resolution**: `resolve_dependencies()` recursively traverses `depends_on` lists to build complete dependency chains. Dependencies start before the target stack.

**Category Organization**: Stacks can have categories/subcategories (e.g., "video/processing"). Category is derived from directory structure or explicitly set in metadata.

## Metadata File Format

Stacks are configured via `.stack-meta.yaml` in each docker-compose directory:

```yaml
name: transcoding
description: "Video transcoding service"
category: video
subcategory: processing
tags: [media, gpu, production]
auto_start: true
priority: 1  # 1=highest, 5=lowest
restart_policy: always
depends_on:
  - data-redis
  - data-postgres
expected_containers: 3
critical: true
owner: media-team
documentation: https://wiki.example.com/transcoding
health_check_url: http://localhost:8080/health
```

All fields are optional except `name`. The tool is extensible - custom fields can be added without code changes.

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

## Common Gotchas

1. **Stack naming**: Stack names use hyphens (e.g., "data-redis"), derived from path with os.sep replaced by '-'
2. **Dependency references**: Use stack names (not paths) in depends_on lists
3. **JSON parsing**: docker compose ps output is newline-delimited JSON (one object per line), not a JSON array
4. **Current directory**: StackManager discovers from cwd() by default - run from your stacks root directory
5. **Missing metadata**: Stacks work without .stack-meta.yaml (uses defaults), but validation warns about missing metadata
