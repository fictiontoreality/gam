#! /usr/bin/env python3
"""
composer - Docker Compose Stack Manager with Metadata Support

Usage:
    composer list [--category=CAT] [--tag=TAG]
    composer show <stack>
    composer up <stack|category|--all> [--priority]
    composer down <stack|category|--all>
    composer restart <stack>
    composer status [--category=CAT]
    composer search <term>
    composer autostart
    composer validate
"""

import os
import sys
import yaml
import subprocess
import glob
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from dataclasses import dataclass, field

@dataclass
class Stack:
    """Represents a Docker Compose stack with metadata"""
    name: str
    path: Path
    category: str = "uncategorized"
    subcategory: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    auto_start: bool = False
    priority: int = 5
    restart_policy: str = "manual"
    depends_on: List[str] = field(default_factory=list)
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
        """Load metadata from .stack-meta.yaml"""
        if self.meta_file.exists():
            with open(self.meta_file) as f:
                meta = yaml.safe_load(f) or {}
                for key, value in meta.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

    def get_status(self) -> Dict:
        """Get running status using docker compose ps"""
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
                running = sum(1 for c in containers if c.get('State') == 'running')
                return {
                    'status': 'running' if running > 0 else 'stopped',
                    'containers': len(containers),
                    'running': running
                }
        except subprocess.CalledProcessError:
            pass
        return {'status': 'stopped', 'containers': 0, 'running': 0}

    def up(self, detached: bool = True) -> bool:
        """Start the stack"""
        cmd = ["docker", "compose", "up"]
        if detached:
            cmd.append("-d")
        try:
            subprocess.run(cmd, cwd=self.path, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def down(self) -> bool:
        """Stop the stack"""
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
        """Restart the stack"""
        return self.down() and self.up()


class StackManager:
    """Manages all Docker Compose stacks"""

    def __init__(self, root_dir: Path = Path.cwd()):
        self.root_dir = root_dir
        self.stacks: Dict[str, Stack] = {}
        self.discover_stacks()

    def discover_stacks(self) -> None:
        """Find all docker-compose.yml files and load metadata"""
        for compose_file in self.root_dir.rglob("docker-compose.yml"):
            stack_path = compose_file.parent
            # Skip if in hidden directory
            if any(part.startswith('.') for part in stack_path.parts):
                continue

            # Derive stack name from path
            rel_path = stack_path.relative_to(self.root_dir)
            stack_name = str(rel_path).replace(os.sep, '-')

            # Create and load stack
            stack = Stack(name=stack_name, path=stack_path)
            stack.load_metadata()

            self.stacks[stack_name] = stack

    def list_stacks(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Stack]:
        """List stacks with optional filtering"""
        stacks = list(self.stacks.values())

        if category:
            stacks = [s for s in stacks if s.category == category]

        if tag:
            stacks = [s for s in stacks if tag in s.tags]

        return sorted(stacks, key=lambda s: (s.priority, s.category, s.name))

    def get_stack(self, name: str) -> Optional[Stack]:
        """Get stack by name"""
        return self.stacks.get(name)

    def get_category_stacks(self, category: str) -> List[Stack]:
        """Get all stacks in a category"""
        return [s for s in self.stacks.values() if s.category == category]

    def search(self, term: str) -> List[Stack]:
        """Search stacks by name, description, tags"""
        term_lower = term.lower()
        results = []
        for stack in self.stacks.values():
            if (term_lower in stack.name.lower() or
                term_lower in stack.description.lower() or
                any(term_lower in tag.lower() for tag in stack.tags)):
                results.append(stack)
        return results

    def get_autostart_stacks(self) -> List[Stack]:
        """Get stacks with auto_start=true, sorted by priority"""
        stacks = [s for s in self.stacks.values() if s.auto_start]
        return sorted(stacks, key=lambda s: s.priority)

    def resolve_dependencies(self, stack: Stack) -> List[Stack]:
        """Get dependency chain for a stack"""
        deps = []
        for dep_name in stack.depends_on:
            dep_stack = self.get_stack(dep_name)
            if dep_stack:
                # Recursively get dependencies
                deps.extend(self.resolve_dependencies(dep_stack))
                deps.append(dep_stack)
        return deps


def cmd_list(manager: StackManager, args) -> None:
    """List all stacks"""
    stacks = manager.list_stacks(category=args.category, tag=args.tag)

    if not stacks:
        print("No stacks found")
        return

    # Group by category
    by_category = {}
    for stack in stacks:
        by_category.setdefault(stack.category, []).append(stack)

    for category, cat_stacks in sorted(by_category.items()):
        print(f"\n{'='*60}")
        print(f"{category.upper()}")
        print(f"{'='*60}")

        for stack in cat_stacks:
            status = stack.get_status()
            status_icon = "●" if status['status'] == 'running' else "○"

            print(f"\n  {status_icon} {stack.name}")
            if stack.description:
                print(f"     {stack.description}")
            print(f"     Path: {stack.path}")
            print(f"     Tags: {', '.join(stack.tags) if stack.tags else 'none'}")
            print(f"     Status: {status['status']} ({status['running']}/{status['containers']} containers)")
            if stack.auto_start:
                print(f"     Auto-start: yes (priority {stack.priority})")


def cmd_show(manager: StackManager, args) -> None:
    """Show detailed info about a stack"""
    stack = manager.get_stack(args.stack)
    if not stack:
        print(f"Stack '{args.stack}' not found")
        sys.exit(1)

    status = stack.get_status()

    print(f"\nStack: {stack.name}")
    print(f"{'='*60}")
    print(f"Description:  {stack.description or 'N/A'}")
    print(f"Category:     {stack.category}/{stack.subcategory}" if stack.subcategory else f"Category:     {stack.category}")
    print(f"Tags:         {', '.join(stack.tags) if stack.tags else 'none'}")
    print(f"Path:         {stack.path}")
    print(f"Status:       {status['status']} ({status['running']}/{status['containers']} containers)")
    print(f"Auto-start:   {'yes' if stack.auto_start else 'no'}")
    if stack.auto_start:
        print(f"Priority:     {stack.priority}")
    print(f"Critical:     {'yes' if stack.critical else 'no'}")

    if stack.depends_on:
        print(f"Dependencies: {', '.join(stack.depends_on)}")

    if stack.owner:
        print(f"Owner:        {stack.owner}")

    if stack.documentation:
        print(f"Docs:         {stack.documentation}")

    if stack.health_check_url:
        print(f"Health:       {stack.health_check_url}")


def cmd_up(manager: StackManager, args) -> None:
    """Start stack(s)"""
    stacks_to_start = []

    if args.all:
        stacks_to_start = list(manager.stacks.values())
    elif args.category:
        stacks_to_start = manager.get_category_stacks(args.category)
    else:
        stack = manager.get_stack(args.target)
        if not stack:
            print(f"Stack '{args.target}' not found")
            sys.exit(1)

        # Include dependencies if requested
        if args.with_deps:
            deps = manager.resolve_dependencies(stack)
            stacks_to_start = deps + [stack]
        else:
            stacks_to_start = [stack]

    # Sort by priority if requested
    if args.priority:
        stacks_to_start.sort(key=lambda s: s.priority)

    print(f"Starting {len(stacks_to_start)} stack(s)...\n")

    for stack in stacks_to_start:
        print(f"  Starting {stack.name}...", end=" ")
        if stack.up():
            print("✓")
        else:
            print("✗ FAILED")


def cmd_down(manager: StackManager, args) -> None:
    """Stop stack(s)"""
    stacks_to_stop = []

    if args.all:
        stacks_to_stop = list(manager.stacks.values())
    elif args.category:
        stacks_to_stop = manager.get_category_stacks(args.category)
    else:
        stack = manager.get_stack(args.target)
        if not stack:
            print(f"Stack '{args.target}' not found")
            sys.exit(1)
        stacks_to_stop = [stack]

    # Stop in reverse priority order
    stacks_to_stop.sort(key=lambda s: -s.priority)

    print(f"Stopping {len(stacks_to_stop)} stack(s)...\n")

    for stack in stacks_to_stop:
        print(f"  Stopping {stack.name}...", end=" ")
        if stack.down():
            print("✓")
        else:
            print("✗ FAILED")


def cmd_autostart(manager: StackManager, args) -> None:
    """Start all stacks marked for auto-start"""
    stacks = manager.get_autostart_stacks()

    if not stacks:
        print("No stacks configured for auto-start")
        return

    print(f"Auto-starting {len(stacks)} stack(s) by priority...\n")

    for stack in stacks:
        print(f"  [{stack.priority}] Starting {stack.name}...", end=" ")
        if stack.up():
            print("✓")
        else:
            print("✗ FAILED")


def cmd_status(manager: StackManager, args) -> None:
    """Show status of all stacks"""
    stacks = manager.list_stacks(category=args.category)

    print(f"\n{'Stack':<30} {'Category':<15} {'Status':<10} {'Containers'}")
    print(f"{'-'*70}")

    for stack in stacks:
        status = stack.get_status()
        status_icon = "●" if status['status'] == 'running' else "○"
        containers_str = f"{status['running']}/{status['containers']}"

        print(f"{status_icon} {stack.name:<28} {stack.category:<15} {status['status']:<10} {containers_str}")


def cmd_search(manager: StackManager, args) -> None:
    """Search for stacks"""
    results = manager.search(args.term)

    if not results:
        print(f"No stacks found matching '{args.term}'")
        return

    print(f"\nFound {len(results)} stack(s):\n")

    for stack in results:
        print(f"  • {stack.name}")
        print(f"    {stack.description or 'No description'}")
        print(f"    Category: {stack.category}, Tags: {', '.join(stack.tags)}")
        print()


def cmd_validate(manager: StackManager, args) -> None:
    """Validate all stack metadata"""
    print("Validating stacks...\n")

    issues = []

    for stack in manager.stacks.values():
        # Check compose file exists
        if not stack.compose_file.exists():
            issues.append(f"  ✗ {stack.name}: docker-compose.yml not found")

        # Check dependencies exist
        for dep in stack.depends_on:
            if not manager.get_stack(dep):
                issues.append(f"  ✗ {stack.name}: dependency '{dep}' not found")

        # Warn about missing metadata
        if not stack.meta_file.exists():
            issues.append(f"  ⚠ {stack.name}: no .stack-meta.yaml file")

    if issues:
        print("\n".join(issues))
        print(f"\n{len(issues)} issue(s) found")
    else:
        print("✓ All stacks valid")


def main():
    parser = argparse.ArgumentParser(
        description="Docker Compose Stack Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # list
    list_parser = subparsers.add_parser('list', help='List stacks')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--tag', help='Filter by tag')

    # show
    show_parser = subparsers.add_parser('show', help='Show stack details')
    show_parser.add_argument('stack', help='Stack name')

    # up
    up_parser = subparsers.add_parser('up', help='Start stack(s)')
    up_parser.add_argument('target', nargs='?', help='Stack name or category')
    up_parser.add_argument('--all', action='store_true', help='Start all stacks')
    up_parser.add_argument('--category', help='Start all stacks in category')
    up_parser.add_argument('--priority', action='store_true', help='Start in priority order')
    up_parser.add_argument('--with-deps', action='store_true', help='Start dependencies first')

    # down
    down_parser = subparsers.add_parser('down', help='Stop stack(s)')
    down_parser.add_argument('target', nargs='?', help='Stack name or category')
    down_parser.add_argument('--all', action='store_true', help='Stop all stacks')
    down_parser.add_argument('--category', help='Stop all stacks in category')

    # restart
    restart_parser = subparsers.add_parser('restart', help='Restart a stack')
    restart_parser.add_argument('stack', help='Stack name')

    # status
    status_parser = subparsers.add_parser('status', help='Show status of stacks')
    status_parser.add_argument('--category', help='Filter by category')

    # search
    search_parser = subparsers.add_parser('search', help='Search stacks')
    search_parser.add_argument('term', help='Search term')

    # autostart
    subparsers.add_parser('autostart', help='Start all auto-start stacks')

    # validate
    subparsers.add_parser('validate', help='Validate stack metadata')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize manager
    manager = StackManager()

    # Dispatch to command
    commands = {
        'list': cmd_list,
        'show': cmd_show,
        'up': cmd_up,
        'down': cmd_down,
        'restart': lambda m, a: m.get_stack(a.stack).restart(),
        'status': cmd_status,
        'search': cmd_search,
        'autostart': cmd_autostart,
        'validate': cmd_validate,
    }

    commands[args.command](manager, args)


if __name__ == '__main__':
    main()
