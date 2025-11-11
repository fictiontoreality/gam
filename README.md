# Composer - Docker Compose Stack Manager

A metadata-driven management tool for organizing and controlling multiple Docker Compose stacks.

## Features

1. **Metadata-Based Organization** - Organize stacks with categories, tags, and custom fields using simple YAML files.
2. **Priority-Based Startup** - Start stacks in defined order with configurable priority levels.
3. **Dependency Management** - Automatically resolve and start stack dependencies in correct order.
4. **Auto-Start on Boot** - Mark stacks for automatic startup with systemd integration.
5. **Bulk Operations** - Start/stop all stacks, by category, or by tag with single commands.
6. **Status Dashboard** - View running status and container counts across all stacks at a glance.
7. **Search & Discovery** - Find stacks by name, description, or tags across your entire infrastructure.
8. **Git-Friendly** - All configuration in version-controllable YAML files, no database required.
9. **Non-Invasive** - Works alongside existing docker-compose.yml files without modification.
10. **Validation** - Verify metadata integrity and check for missing dependencies before deployment.

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

```yaml
# video/transcoding/.stack-meta.yaml
name: transcoding
description: "Video transcoding service using FFmpeg"

# Organization
category: video
subcategory: processing
tags: [media, gpu, production, high-priority]

# Behavior
auto_start: true
priority: 1  # 1=highest, 5=lowest
restart_policy: always  # always, on-failure, manual

# Dependencies (optional - for ordered startup)
depends_on:
  - data/redis
  - data/postgres

# Resource hints (for monitoring/alerting)
expected_containers: 3
critical: true  # Alert if down

# Custom fields (whatever you want!)
owner: media-team
documentation: https://wiki.company.com/transcoding
health_check_url: http://localhost:8080/health
```

**Benefits:**
- ✅ Self-documenting
- ✅ Easy to read/edit
- ✅ Extensible (add fields anytime)
- ✅ Machine-parseable

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
└── composer  # Your management script
```

## Usage Examples

```bash
# List all stacks
./composer list

# List stacks in video category
./composer list --category video

# List stacks with 'production' tag
./composer list --tag production

# Show details about a stack
./composer show video-transcoding

# Start a stack
./composer up video-transcoding

# Start with dependencies
./composer up video-transcoding --with-deps

# Start all stacks in a category
./composer up --category video

# Start all stacks by priority
./composer up --all --priority

# Stop a stack
./composer down video-transcoding

# Stop all in category
./composer down --category video

# Show status of all stacks
./composer status

# Search for stacks
./composer search media

# Auto-start all configured stacks (e.g., on boot)
./composer autostart

# Validate all metadata
./composer validate
```

## Next Steps

1. **Install the script:**
```bash
chmod +x composer
sudo ln -s $(pwd)/composer /usr/local/bin/composer
```

2. **Create metadata files:**
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

3. **Test it:**
```bash
composer list
composer show video-transcoding
composer status
```

4. **Set up autostart (optional):**
```bash
# Create systemd service
sudo cat > /etc/systemd/system/docker-autostart.service <<EOF
[Unit]
Description=Auto-start Docker Compose stacks
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/composer autostart
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable docker-autostart
```

## Future Enhancements

Once you have the basics working, you can add:

0. **Tag/Category Management:** list, add, remove, rename tags/categories
1. **Web UI:** Simple Flask/FastAPI dashboard
2. **Webhooks:** Trigger from Git commits
3. **Health checks:** Monitor stack health
4. **Logs:** `composer logs <stack>` 
5. **Export:** Generate reports, integrate with monitoring
6. **Backup:** `composer backup <stack>` for volumes
7. **Template generation:** Create new stacks from templates
