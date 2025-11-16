import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

@dataclass
class Stack:
    """Represents a Docker Compose stack with metadata."""
    name: str
    path: Path
    category: str = "uncategorized"
    subcategory: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    auto_start: bool = False
    priority: int = 5
    depends_on: list[str] = field(default_factory=list)
    expected_containers: int = 0
    critical: bool = False
    owner: str = ""
    documentation: str = ""
    health_check_url: str = ""

    @property
    def compose_file(self) -> Path:
        return self.path / "docker-compose.yml"

    @property
    def meta_file(self) -> Path:
        return self.path / ".stack-meta.yaml"

    def exists(self) -> bool:
        return self.compose_file.exists()

    def load_metadata(self) -> None:
        """Load metadata from .stack-meta.yaml."""
        if self.meta_file.exists():
            with open(self.meta_file) as f:
                meta = yaml.safe_load(f) or {}
                for key, value in meta.items():
                    # Skip 'name' - it's always derived from path.
                    if key == 'name':
                        continue
                    if hasattr(self, key):
                        setattr(self, key, value)

    def save_metadata(self) -> None:
        """Save metadata to .stack-meta.yaml."""
        # Build metadata dict from current values.
        # Note: 'name' is omitted - it's always derived from directory path.
        meta = {
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'auto_start': self.auto_start,
            'priority': self.priority,
        }

        # Add optional fields if set
        if self.subcategory:
            meta['subcategory'] = self.subcategory
        if self.depends_on:
            meta['depends_on'] = self.depends_on
        if self.expected_containers:
            meta['expected_containers'] = self.expected_containers
        if self.critical:
            meta['critical'] = self.critical
        if self.owner:
            meta['owner'] = self.owner
        if self.documentation:
            meta['documentation'] = self.documentation
        if self.health_check_url:
            meta['health_check_url'] = self.health_check_url

        # Write to file
        with open(self.meta_file, 'w') as f:
            yaml.dump(meta, f, default_flow_style=False,
                      sort_keys=False, indent=2)

    def get_status(self) -> dict:
        """Get running status using docker compose ps."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                containers = [
                    yaml.safe_load(line)
                    for line in result.stdout.strip().split('\n')
                ]
                running = sum(
                    1 for c in containers if c.get('State') == 'running'
                )
                return {
                    'status': 'running' if running > 0 else 'stopped',
                    'containers': len(containers),
                    'running': running
                }
        except subprocess.CalledProcessError:
            pass
        return {'status': 'stopped', 'containers': 0, 'running': 0}

    def up(self, detached: bool = True) -> bool:
        """Start the stack."""
        cmd = ["docker", "compose", "up"]
        if detached:
            cmd.append("-d")
        try:
            subprocess.run(cmd, cwd=self.path, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def down(self) -> bool:
        """Stop the stack."""
        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.path,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def restart(self) -> bool:
        """Restart the stack."""
        return self.down() and self.up()
