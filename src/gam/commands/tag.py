import sys

from gam.stack_manager import StackManager


def cmd_tag(manager: StackManager, args) -> None:
    """Tag management commands."""
    if args.tag_action in ('list', 'ls'):
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
            removed_tags = ', '.join(removed)
            print(f"✓ Removed tag(s) from {stack.name}: {removed_tags}")
        else:
            msg = f"None of the specified tags were found on {stack.name}"
            print(msg)

    elif args.tag_action == 'rename':
        count = manager.rename_tag(args.old_tag, args.new_tag)
        if count > 0:
            plural = 's' if count != 1 else ''
            msg = (
                f"✓ Renamed '{args.old_tag}' to '{args.new_tag}' "
                f"across {count} stack{plural}"
            )
            print(msg)
        else:
            print(f"Tag '{args.old_tag}' not found on any stacks")
