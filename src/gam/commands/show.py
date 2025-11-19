import sys

from gam.stack_manager import StackManager


def cmd_show(manager: StackManager, args) -> None:
    """Show detailed info about a stack."""
    stack = manager.get_stack(args.stack)
    if not stack:
        print(f"Stack '{args.stack}' not found")
        sys.exit(1)

    status = stack.get_status()

    print(f"\nStack: {stack.name}")
    print(f"{'='*60}")
    print(f"Description:  {stack.description or 'N/A'}")
    if stack.subcategory:
        category_display = f"{stack.category}/{stack.subcategory}"
    else:
        category_display = stack.category
    print(f"Category:     {category_display}")
    tags_display = ', '.join(stack.tags) if stack.tags else 'none'
    print(f"Tags:         {tags_display}")
    print(f"Path:         {stack.path}")
    containers_info = (
        f"({status['running']}/{status['containers']} containers)"
    )
    print(f"Status:       {status['status']} {containers_info}")
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
