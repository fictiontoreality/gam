from gam.stack_manager import StackManager


def cmd_search(manager: StackManager, args) -> None:
    """Search for stacks."""
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
