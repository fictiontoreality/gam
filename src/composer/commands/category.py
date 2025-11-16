import sys

from composer.stack_manager import StackManager


def cmd_category(manager: StackManager, args) -> None:
    """Category management commands."""
    if args.category_action in ('list', 'ls'):
        categories = manager.get_all_categories()
        if not categories:
            print("No categories found")
            return

        plural = 'ies' if len(categories) != 1 else 'y'
        print(f"\nFound {len(categories)} unique categor{plural}:\n")
        for category, subcategory in categories:
            # Count how many stacks use this category
            count = sum(
                1 for s in manager.stacks.values()
                if s.category == category and s.subcategory == subcategory
            )

            display = (
                f"{category}/{subcategory}" if subcategory else category
            )
            plural = 's' if count != 1 else ''
            print(f"  • {display} ({count} stack{plural})")

    elif args.category_action == 'set':
        stack = manager.get_stack(args.stack)
        if not stack:
            print(f"Stack '{args.stack}' not found")
            sys.exit(1)

        if stack.subcategory:
            old_category = f"{stack.category}/{stack.subcategory}"
        else:
            old_category = stack.category

        stack.category = args.new_category
        stack.subcategory = args.subcategory or ""
        stack.save_metadata()

        if stack.subcategory:
            new_category = f"{stack.category}/{stack.subcategory}"
        else:
            new_category = stack.category
        msg = (
            f"✓ Changed category for {stack.name}: "
            f"{old_category} → {new_category}"
        )
        print(msg)

    elif args.category_action == 'rename':
        count = manager.rename_category(args.old_category, args.new_category)
        if count > 0:
            plural = 's' if count != 1 else ''
            msg = (
                f"✓ Renamed category '{args.old_category}' to "
                f"'{args.new_category}' across {count} stack{plural}"
            )
            print(msg)
        else:
            print(f"Category '{args.old_category}' not found on any stacks")
