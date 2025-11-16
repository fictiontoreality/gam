import os
from pathlib import Path

from composer.stack import Stack

class StackManager:
    """Manages all Docker Compose stacks."""

    def __init__(self, root_dir: Path = Path.cwd()):
        self.root_dir = root_dir
        self.stacks: dict[str, Stack] = {}
        self.discover_stacks()

    def discover_stacks(self) -> None:
        """Find all docker-compose.yml files and load metadata."""
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
        category: str | None = None,
        tag: str | None = None
    ) -> list[Stack]:
        """List stacks with optional filtering."""
        stacks = list(self.stacks.values())

        if category:
            stacks = [s for s in stacks if s.category == category]

        if tag:
            stacks = [s for s in stacks if tag in s.tags]

        return sorted(stacks, key=lambda s: (s.priority, s.category, s.name))

    def get_stack(self, name: str) -> Stack | None:
        """Get stack by name."""
        return self.stacks.get(name)

    def get_category_stacks(self, category: str) -> list[Stack]:
        """Get all stacks in a category."""
        return [s for s in self.stacks.values() if s.category == category]

    def search(self, term: str) -> list[Stack]:
        """Search stacks by name, description, and tags."""
        term_lower = term.lower()
        results = []
        for stack in self.stacks.values():
            if (term_lower in stack.name.lower() or
                term_lower in stack.description.lower() or
                any(term_lower in tag.lower() for tag in stack.tags)):
                results.append(stack)
        return results

    def get_autostart_stacks(self) -> list[Stack]:
        """Get stacks with auto_start=true, sorted by priority."""
        stacks = [s for s in self.stacks.values() if s.auto_start]
        return sorted(stacks, key=lambda s: s.priority)

    def resolve_dependencies(self, stack: Stack) -> list[Stack]:
        """Get dependency chain for a stack."""
        deps = []
        for dep_name in stack.depends_on:
            dep_stack = self.get_stack(dep_name)
            if dep_stack:
                # Recursively get dependencies
                deps.extend(self.resolve_dependencies(dep_stack))
                deps.append(dep_stack)
        return deps

    def get_all_tags(self) -> list[str]:
        """Get all unique tags across all stacks."""
        tags = set()
        for stack in self.stacks.values():
            tags.update(stack.tags)
        return sorted(tags)

    def get_all_categories(self) -> list[tuple]:
        """Get all unique categories (category, subcategory) tuples."""
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
        """Rename a category across all stacks.

        Returns count of affected stacks.
        """
        count = 0
        for stack in self.stacks.values():
            if stack.category == old_category:
                stack.category = new_category
                stack.save_metadata()
                count += 1
        return count
