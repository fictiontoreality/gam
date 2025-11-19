import yaml

from gam.stack_manager import StackManager


def cmd_validate(manager: StackManager, args) -> None:
    """Validate all stack metadata."""
    print("Validating stacks...\n")

    if args.target:
        stacks = (manager.get_stack(args.target),)
    else:
        stacks = manager.stacks.values()

    issues = []

    for stack in stacks:
        # Check compose file exists
        if not stack.compose_file.exists():
            issues.append(f"  ✗ {stack.name}: docker-compose.yml not found")

        # Check for name field mismatch in metadata
        if stack.meta_file.exists():
            try:
                with open(stack.meta_file) as f:
                    meta = yaml.safe_load(f) or {}
                    if 'name' in meta and meta['name'] != stack.name:
                        issues.append(
                            f"  ⚠ {stack.name}: metadata contains 'name' field "
                            f"('{meta['name']}') - name is derived from path and "
                            f"cannot be overridden"
                        )
            except FileNotFoundError:
                # File doesn't actually exist (can happen with mocking in tests).
                pass

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
