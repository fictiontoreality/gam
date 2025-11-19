import sys

from gam.stack_manager import StackManager


def cmd_restart(manager: StackManager, args) -> None:
    """Restart stack(s)."""
    stacks_to_restart = []

    if args.all:
        stacks_to_restart = list(manager.stacks.values())
    elif args.category:
        stacks_to_restart = manager.get_category_stacks(args.category)
    elif args.tag:
        stacks_to_restart = [
            s for s in manager.stacks.values() if args.tag in s.tags
        ]
    else:
        if not args.target:
            print("Error: Provide a stack name or use --all, -c, or -t")
            sys.exit(1)

        stack = manager.get_stack(args.target)
        if not stack:
            print(f"Stack '{args.target}' not found")
            sys.exit(1)
        stacks_to_restart = [stack]

    # Restart in reverse priority order (stop), then normal (start)
    stacks_to_restart.sort(key=lambda s: -s.priority)

    print(f"Restarting {len(stacks_to_restart)} stack(s)...\n")

    for stack in stacks_to_restart:
        print(f"  Restarting {stack.name}...", end=" ")
        if stack.restart():
            print("✓")
        else:
            print("✗ FAILED")
