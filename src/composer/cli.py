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
    composer tag list
    composer tag add <stack> <tag> [<tag> ...]
    composer tag remove <stack> <tag> [<tag> ...]
    composer tag rename <old-tag> <new-tag>
    composer category list
    composer category set <stack> <category> [subcategory]
    composer category rename <old-category> <new-category>
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

    def save_metadata(self) -> None:
        """Save metadata to .stack-meta.yaml"""
        # Build metadata dict from current values
        meta = {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags,
            'auto_start': self.auto_start,
            'priority': self.priority,
            'restart_policy': self.restart_policy,
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
            yaml.dump(meta, f, default_flow_style=False, sort_keys=False)

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

    def get_all_tags(self) -> List[str]:
        """Get all unique tags across all stacks"""
        tags = set()
        for stack in self.stacks.values():
            tags.update(stack.tags)
        return sorted(tags)

    def get_all_categories(self) -> List[tuple]:
        """Get all unique categories (category, subcategory) tuples"""
        categories = set()
        for stack in self.stacks.values():
            categories.add((stack.category, stack.subcategory))
        return sorted(categories)

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """Rename a tag across all stacks. Returns count of affected stacks."""
        count = 0
        for stack in self.stacks.values():
            if old_tag in stack.tags:
                stack.tags.remove(old_tag)
                if new_tag not in stack.tags:
                    stack.tags.append(new_tag)
                stack.save_metadata()
                count += 1
        return count

    def rename_category(self, old_category: str, new_category: str) -> int:
        """Rename a category across all stacks. Returns count of affected stacks."""
        count = 0
        for stack in self.stacks.values():
            if stack.category == old_category:
                stack.category = new_category
                stack.save_metadata()
                count += 1
        return count


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


def cmd_tag(manager: StackManager, args) -> None:
    """Tag management commands"""
    if args.tag_action == 'list':
        tags = manager.get_all_tags()
        if not tags:
            print("No tags found")
            return

        print(f"\nFound {len(tags)} unique tag(s):\n")
        for tag in tags:
            # Count how many stacks use this tag
            count = sum(1 for s in manager.stacks.values() if tag in s.tags)
            print(f"  • {tag} ({count} stack{'s' if count != 1 else ''})")

    elif args.tag_action == 'add':
        stack = manager.get_stack(args.stack)
        if not stack:
            print(f"Stack '{args.stack}' not found")
            sys.exit(1)

        added = []
        for tag in args.tags:
            if tag not in stack.tags:
                stack.tags.append(tag)
                added.append(tag)

        if added:
            stack.save_metadata()
            print(f"✓ Added tag(s) to {stack.name}: {', '.join(added)}")
        else:
            print(f"All specified tags already exist on {stack.name}")

    elif args.tag_action == 'remove':
        stack = manager.get_stack(args.stack)
        if not stack:
            print(f"Stack '{args.stack}' not found")
            sys.exit(1)

        removed = []
        for tag in args.tags:
            if tag in stack.tags:
                stack.tags.remove(tag)
                removed.append(tag)

        if removed:
            stack.save_metadata()
            print(f"✓ Removed tag(s) from {stack.name}: {', '.join(removed)}")
        else:
            print(f"None of the specified tags were found on {stack.name}")

    elif args.tag_action == 'rename':
        count = manager.rename_tag(args.old_tag, args.new_tag)
        if count > 0:
            print(f"✓ Renamed '{args.old_tag}' to '{args.new_tag}' across {count} stack{'s' if count != 1 else ''}")
        else:
            print(f"Tag '{args.old_tag}' not found on any stacks")


def cmd_category(manager: StackManager, args) -> None:
    """Category management commands"""
    if args.category_action == 'list':
        categories = manager.get_all_categories()
        if not categories:
            print("No categories found")
            return

        print(f"\nFound {len(categories)} unique categor{'ies' if len(categories) != 1 else 'y'}:\n")
        for category, subcategory in categories:
            # Count how many stacks use this category
            count = sum(1 for s in manager.stacks.values()
                       if s.category == category and s.subcategory == subcategory)

            display = f"{category}/{subcategory}" if subcategory else category
            print(f"  • {display} ({count} stack{'s' if count != 1 else ''})")

    elif args.category_action == 'set':
        stack = manager.get_stack(args.stack)
        if not stack:
            print(f"Stack '{args.stack}' not found")
            sys.exit(1)

        old_category = f"{stack.category}/{stack.subcategory}" if stack.subcategory else stack.category

        stack.category = args.new_category
        stack.subcategory = args.subcategory or ""
        stack.save_metadata()

        new_category = f"{stack.category}/{stack.subcategory}" if stack.subcategory else stack.category
        print(f"✓ Changed category for {stack.name}: {old_category} → {new_category}")

    elif args.category_action == 'rename':
        count = manager.rename_category(args.old_category, args.new_category)
        if count > 0:
            print(f"✓ Renamed category '{args.old_category}' to '{args.new_category}' across {count} stack{'s' if count != 1 else ''}")
        else:
            print(f"Category '{args.old_category}' not found on any stacks")


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

    # tag
    tag_parser = subparsers.add_parser('tag', help='Manage tags')
    tag_subparsers = tag_parser.add_subparsers(dest='tag_action', help='Tag actions')

    # tag list
    tag_subparsers.add_parser('list', help='List all unique tags')

    # tag add
    tag_add_parser = tag_subparsers.add_parser('add', help='Add tag(s) to a stack')
    tag_add_parser.add_argument('stack', help='Stack name')
    tag_add_parser.add_argument('tags', nargs='+', help='Tag(s) to add')

    # tag remove
    tag_remove_parser = tag_subparsers.add_parser('remove', help='Remove tag(s) from a stack')
    tag_remove_parser.add_argument('stack', help='Stack name')
    tag_remove_parser.add_argument('tags', nargs='+', help='Tag(s) to remove')

    # tag rename
    tag_rename_parser = tag_subparsers.add_parser('rename', help='Rename a tag across all stacks')
    tag_rename_parser.add_argument('old_tag', help='Old tag name')
    tag_rename_parser.add_argument('new_tag', help='New tag name')

    # category
    category_parser = subparsers.add_parser('category', help='Manage categories')
    category_subparsers = category_parser.add_subparsers(dest='category_action', help='Category actions')

    # category list
    category_subparsers.add_parser('list', help='List all unique categories')

    # category set
    category_set_parser = category_subparsers.add_parser('set', help='Set category for a stack')
    category_set_parser.add_argument('stack', help='Stack name')
    category_set_parser.add_argument('new_category', help='Category name')
    category_set_parser.add_argument('subcategory', nargs='?', help='Subcategory name (optional)')

    # category rename
    category_rename_parser = category_subparsers.add_parser('rename', help='Rename a category across all stacks')
    category_rename_parser.add_argument('old_category', help='Old category name')
    category_rename_parser.add_argument('new_category', help='New category name')

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
        'tag': cmd_tag,
        'category': cmd_category,
    }

    commands[args.command](manager, args)


if __name__ == '__main__':
    main()
