from composer.stack_manager import StackManager


def cmd_status(manager: StackManager, args) -> None:
    """Show status of all stacks."""
    stacks = manager.list_stacks(category=args.category, tag=args.tag)

    header = f"\n{'Stack':<30} {'Category':<15} {'Status':<10} {'Containers'}"
    print(header)
    print(f"{'-'*70}")

    for stack in stacks:
        status = stack.get_status()
        status_icon = "●" if status['status'] == 'running' else "○"
        containers_str = f"{status['running']}/{status['containers']}"

        row = (
            f"{status_icon} {stack.name:<28} {stack.category:<15} "
            f"{status['status']:<10} {containers_str}"
        )
        print(row)
