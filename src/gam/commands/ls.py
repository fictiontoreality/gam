from gam.stack_manager import StackManager


def cmd_ls(manager: StackManager, args) -> None:
    """List all stacks."""
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
            tags_display = ', '.join(stack.tags) if stack.tags else 'none'
            print(f"     Tags: {tags_display}")
            containers_info = (
                f"({status['running']}/{status['containers']} containers)"
            )
            print(f"     Status: {status['status']} {containers_info}")
            if stack.auto_start:
                print(f"     Auto-start: yes (priority {stack.priority})")
