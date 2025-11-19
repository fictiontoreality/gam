#! /usr/bin/env python3
"""
gam - Docker Compose Stack Manager with Metadata Support

Usage:
    gam autostart
    gam category list
    gam category rename <old-category> <new-category>
    gam category set <stack> <category> [subcategory]
    gam down <stack|--all> [-c CAT] [-t TAG]
    gam ls [-c|--category=CAT] [-t|--tag=TAG]
    gam restart <stack|--all> [-c CAT] [-t TAG]
    gam search <term>
    gam show <stack>
    gam status [-c|--category=CAT] [-t|--tag=TAG]
    gam tag add <stack> <tag> [<tag> ...]
    gam tag ls
    gam tag remove <stack> <tag> [<tag> ...]
    gam tag rename <old-tag> <new-tag>
    gam up <stack|--all> [-c CAT] [-t TAG] [--priority]
    gam validate [<stack>]
"""

import argparse
import sys

from .commands import (
    cmd_autostart,
    cmd_category,
    cmd_down,
    cmd_ls,
    cmd_restart,
    cmd_search,
    cmd_show,
    cmd_status,
    cmd_tag,
    cmd_up,
    cmd_validate,
)
from .stack_manager import StackManager


def main():
    parser = argparse.ArgumentParser(
        description="Docker Compose Stack Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # autostart
    subparsers.add_parser('autostart', help='Start all auto-start stacks')

    # category
    category_parser = subparsers.add_parser(
        'category', aliases=['cat'], help='Manage categories'
    )
    category_subparsers = category_parser.add_subparsers(
        dest='category_action', help='Category actions'
    )

    # category list
    category_subparsers.add_parser(
        'ls', aliases=['list'], help='List all unique categories'
    )

    # category rename
    category_rename_parser = category_subparsers.add_parser(
        'rename', help='Rename a category across all stacks'
    )
    category_rename_parser.add_argument(
        'old_category', help='Old category name'
    )
    category_rename_parser.add_argument(
        'new_category', help='New category name'
    )

    # category set
    category_set_parser = category_subparsers.add_parser(
        'set', help='Set category for a stack'
    )
    category_set_parser.add_argument('stack', help='Stack name')
    category_set_parser.add_argument('new_category', help='Category name')
    category_set_parser.add_argument(
        'subcategory', nargs='?', help='Subcategory name (optional)'
    )

    # down
    down_parser = subparsers.add_parser('down', help='Stop stack(s)')
    down_parser.add_argument(
        'target', nargs='?', help='Stack name or category'
    )
    down_parser.add_argument(
        '--all', action='store_true', help='Stop all stacks'
    )
    down_parser.add_argument(
        '-c', '--category', help='Stop all stacks in category'
    )
    down_parser.add_argument(
        '-t', '--tag', help='Stop all stacks with tag'
    )

    # ls (with 'list' alias)
    ls_parser = subparsers.add_parser(
        'ls', aliases=['list'], help='List stacks'
    )
    ls_parser.add_argument(
        '-c', '--category', help='Filter by category'
    )
    ls_parser.add_argument('-t', '--tag', help='Filter by tag')

    # restart
    restart_parser = subparsers.add_parser('restart', help='Restart stack(s)')
    restart_parser.add_argument(
        'target', nargs='?', help='Stack name or category'
    )
    restart_parser.add_argument(
        '--all', action='store_true', help='Restart all stacks'
    )
    restart_parser.add_argument(
        '-c', '--category', help='Restart all stacks in category'
    )
    restart_parser.add_argument(
        '-t', '--tag', help='Restart all stacks with tag'
    )

    # search
    search_parser = subparsers.add_parser('search', help='Search stacks')
    search_parser.add_argument('term', help='Search term')

    # show
    show_parser = subparsers.add_parser('show', help='Show stack details')
    show_parser.add_argument('stack', help='Stack name')

    # status
    status_parser = subparsers.add_parser(
        'status', help='Show status of stacks'
    )
    status_parser.add_argument(
        '-c', '--category', help='Filter by category'
    )
    status_parser.add_argument('-t', '--tag', help='Filter by tag')

    # tag
    tag_parser = subparsers.add_parser('tag', help='Manage tags')
    tag_subparsers = tag_parser.add_subparsers(
        dest='tag_action', help='Tag actions'
    )

    # tag add
    tag_add_parser = tag_subparsers.add_parser(
        'add', help='Add tag(s) to a stack'
    )
    tag_add_parser.add_argument('stack', help='Stack name')
    tag_add_parser.add_argument('tags', nargs='+', help='Tag(s) to add')

    # tag list
    tag_subparsers.add_parser(
        'ls', aliases=['list'], help='List all unique tags'
    )

    # tag remove
    tag_remove_parser = tag_subparsers.add_parser(
        'remove', help='Remove tag(s) from a stack'
    )
    tag_remove_parser.add_argument('stack', help='Stack name')
    tag_remove_parser.add_argument(
        'tags', nargs='+', help='Tag(s) to remove'
    )

    # tag rename
    tag_rename_parser = tag_subparsers.add_parser(
        'rename', help='Rename a tag across all stacks'
    )
    tag_rename_parser.add_argument('old_tag', help='Old tag name')
    tag_rename_parser.add_argument('new_tag', help='New tag name')

    # up
    up_parser = subparsers.add_parser('up', help='Start stack(s)')
    up_parser.add_argument(
        'target', nargs='?', help='Stack name or category'
    )
    up_parser.add_argument(
        '--all', action='store_true', help='Start all stacks'
    )
    up_parser.add_argument(
        '-c', '--category', help='Start all stacks in category'
    )
    up_parser.add_argument(
        '-t', '--tag', help='Start all stacks with tag'
    )
    up_parser.add_argument(
        '--priority', action='store_true', help='Start in priority order'
    )
    up_parser.add_argument(
        '--with-deps', action='store_true', help='Start dependencies first'
    )

    # validate
    validate_parser = subparsers.add_parser('validate', help='Validate stack metadata')
    validate_parser.add_argument(
        'target', nargs='?', help='Stack name or category'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize manager
    manager = StackManager()

    # Dispatch to command
    commands = {
        'autostart': cmd_autostart,
        'category': cmd_category,
        'cat': cmd_category, # Alias for category
        'down': cmd_down,
        'list': cmd_ls,  # Alias for ls
        'ls': cmd_ls,
        'restart': cmd_restart,
        'search': cmd_search,
        'show': cmd_show,
        'status': cmd_status,
        'tag': cmd_tag,
        'up': cmd_up,
        'validate': cmd_validate,
    }

    commands[args.command](manager, args)


if __name__ == '__main__':
    main()
