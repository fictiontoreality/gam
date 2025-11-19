from gam.stack_manager import StackManager


def cmd_autostart(manager: StackManager, args) -> None:
    """Start all stacks marked for auto-start."""
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
