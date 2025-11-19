# Gam: 🐳 a social gathering of whales 🐋
## Docker Compose Stack Manager

A metadata-driven management tool for organizing and controlling multiple Docker Compose stacks.

## Features

1. **Metadata-Based Organization** - Organize stacks with categories, tags, and custom fields using simple YAML files.
1. **Priority-Based Startup** - Start stacks in defined order with configurable priority levels.
1. **Dependency Management** - Automatically resolve and start stack dependencies in correct order.
1. **Auto-Start on Boot** - Mark stacks for automatic startup with systemd integration.
1. **Bulk Operations** - Start/stop all stacks, by category, or by tag with single commands.
1. **Status Dashboard** - View running status and container counts across all stacks at a glance.
1. **Search & Discovery** - Find stacks by name, description, or tags across your entire infrastructure.
1. **Git-Friendly** - All configuration in version-controllable YAML files, no database required.
1. **Non-Invasive** - Works alongside existing docker-compose.yml files without modification.
1. **Validation** - Verify metadata integrity and check for missing dependencies before deployment.

## Why

The Docker compose ecosystem has tons of tools for container orchestration (Kubernetes), but very little for "I just want to organize my 30+ compose stacks sanely."

## Design Principles

1. **Git-friendly:** YAML files, human-readable
2. **Non-invasive:** Doesn't modify your compose files
3. **Extensible:** Easy to add fields later
4. **Simple:** Python/Bash scripts, no complex frameworks
5. **Flexible:** Works with your existing directory structure

## Metadata File Format

### **`.stack-meta.yaml`** (in each compose directory)

Place a `.stack-meta.yaml` file in each directory containing a `docker-compose.yml` to provide metadata and configuration for that stack.

```yaml
# video/transcoding/.stack-meta.yaml
description: "Video transcoding service using FFmpeg"

# Organization
category: video
subcategory: processing
tags: [media, gpu, production, high-priority]

# Behavior
auto_start: true
priority: 1  # 1=highest, 5=lowest

# Dependencies (optional - for ordered startup)
depends_on:
  - data-redis
  - data-postgres

# Resource hints (for monitoring/alerting)
expected_containers: 3
critical: true  # Alert if down

# Custom fields (whatever you want!)
owner: media-team
documentation: https://wiki.company.com/transcoding
health_check_url: http://localhost:8080/health
```

### Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| **description** | string | No | `""` | Human-readable description. Shown in `gam show` and `gam search`. |
| **category** | string | No | `"uncategorized"` | Primary category for organization. Used for filtering with `--category` flag. Can be hierarchical (see subcategory). |
| **subcategory** | string | No | `""` | Secondary category level. Displayed as `category/subcategory`. Used for finer-grained organization. |
| **tags** | list of strings | No | `[]` | Tags for flexible filtering and searching. Used with `--tag` flag and `gam search`. |
| **auto_start** | boolean | No | `false` | If `true`, stack will be started by `gam autostart` (e.g., on boot via systemd if configured). |
| **priority** | integer (1-5) | No | `5` | Startup/shutdown priority. `1` = highest priority (starts first, stops last). `5` = lowest priority (starts last, stops first). Used with `--priority` flag. |
| **depends_on** | list of strings | No | `[]` | List of stack names this stack depends on. When using `gam up <stack> --with-deps`, dependencies are started first in correct order. |
| **expected_containers** | integer | No | `0` | Expected number of containers for this stack. Informational hint for monitoring/validation. |
| **critical** | boolean | No | `false` | Whether this stack is critical for operations. Informational hint for monitoring/alerting. |
| **owner** | string | No | `""` | Team or person responsible for this stack. Custom field for organization. |
| **documentation** | string | No | `""` | URL to documentation or wiki page. Custom field for reference. |
| **health_check_url** | string | No | `""` | URL for health check endpoint. Custom field for monitoring. |

### How Fields Are Used

**Organization & Discovery:**
- `category`, `subcategory`, `tags` - Used by `gam list --category <cat>`, `gam list --tag <tag>`, and `gam search <term>`
- `description` - Shown in `gam show <stack>` and `gam search` results
- `name` - Primary identifier for all commands

**Lifecycle Management:**
- `auto_start` - Determines if stack is started by `gam autostart` (typically run on boot)
- `priority` - Controls startup order when using `gam up --all --priority` (1=first, 5=last). Shutdown order is reversed.
- `depends_on` - Ensures dependencies start before the stack when using `gam up <stack> --with-deps`

**Metadata Management:**
- All fields can be modified using `gam tag` and `gam category` commands
- Metadata is persisted to `.stack-meta.yaml` when changed via CLI
- Fields are extensible - add custom fields as needed (they'll be preserved but not used by commands)

**Validation:**
- `gam validate` checks that:
  - `docker-compose.yml` exists for each stack
  - Dependencies listed in `depends_on` exist
  - Metadata files are valid YAML

### Benefits
- ✅ **Self-documenting** - Metadata lives alongside your compose files
- ✅ **Git-friendly** - YAML format, easy to version control
- ✅ **Extensible** - Add custom fields anytime without breaking existing functionality
- ✅ **Machine-parseable** - Easy to integrate with other tools
- ✅ **Non-invasive** - Doesn't modify your `docker-compose.yml` files

## Directory Structure

```
~/docker/
├── video/
│   ├── transcoding/
│   │   ├── docker-compose.yml
│   │   └── .stack-meta.yaml
│   └── streaming/
│       ├── docker-compose.yml
│       └── .stack-meta.yaml
├── data/
│   ├── backup/
│   │   ├── docker-compose.yml
│   │   └── .stack-meta.yaml
│   └── redis/
│       ├── docker-compose.yml
│       └── .stack-meta.yaml
├── web/
│   └── blog/
│       ├── docker-compose.yml
│       └── .stack-meta.yaml
└── gam  # Your management script
```

## Usage Examples

```bash
# List all stacks
./gam list

# List stacks in video category
./gam list --category video

# List stacks with 'production' tag
./gam list --tag production

# Show details about a stack
./gam show video-transcoding

# Start a stack
./gam up video-transcoding

# Start with dependencies
./gam up video-transcoding --with-deps

# Start all stacks in a category
./gam up --category video

# Start all stacks by priority
./gam up --all --priority

# Stop a stack
./gam down video-transcoding

# Stop all in category
./gam down --category video

# Show status of all stacks
./gam status

# Search for stacks
./gam search media

# Auto-start all configured stacks (e.g., on boot)
./gam autostart

# Validate all metadata
./gam validate

# Tag Management
./gam tag list                              # List all tags
./gam tag add video-transcoding production   # Add tag(s) to a stack
./gam tag remove web-blog staging           # Remove tag(s) from a stack
./gam tag rename production prod             # Rename tag across all stacks

# Category Management
./gam category list                                    # List all categories
./gam category set web-blog application frontend       # Set category/subcategory
./gam category set data-redis database                 # Set category only
./gam category rename data database                    # Rename category across all stacks
```

## Installation

Install using pip, pipx, or uv:

```bash
# Using pip (system-wide)
pip install docker-gam

# Using pipx (isolated environment, recommended)
pipx install docker-gam

# Using uv (fast, modern)
uv tool install docker-gam
```

Once installed, the `gam` command will be available system-wide.

### Development Installation

For development or local testing:

```bash
# Clone the repository
git clone https://github.com/yourusername/gam.git
cd gam

# Install in editable mode
pip install -e .

# Or with pipx
pipx install -e .
```

## Getting Started

1. **Create metadata files:**
```bash
# For each stack directory
cd video/transcoding
cat > .stack-meta.yaml <<EOF
name: transcoding
description: "Video transcoding service"
category: video
tags: [media, production]
auto_start: true
priority: 2
EOF
```

Alternatively, use the CLI to manage metadata:
```bash
gam tag add video-transcoding media production
gam category set video-transcoding video processing
```

2. **Test it:**
```bash
gam list
gam show video-transcoding
gam status
gam tag list
gam category list
```

3. **Set up autostart (optional):**
```bash
# Create systemd service
sudo cat > /etc/systemd/system/docker-autostart.service <<EOF
[Unit]
Description=Auto-start Docker Compose stacks
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
# Note: Update gam path as needed (`which gam`).
ExecStart=/usr/local/bin/gam autostart
WorkingDirectory=/path/to/your/docker/compose/stacks
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable docker-autostart
```

## Future Enhancements

Once you have the basics working, you can add:

1. **Web UI:** Simple Flask/FastAPI dashboard
2. **Webhooks:** Trigger from Git commits
3. **Health checks:** Monitor stack health
4. **Logs:** `gam logs <stack>`
5. **Export:** Generate reports, integrate with monitoring
6. **Backup:** `gam backup <stack>` for volumes
7. **Template generation:** Create new stacks from templates
