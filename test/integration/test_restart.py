"""Integration tests for restart command."""

from argparse import Namespace

from gam.commands.restart import cmd_restart
from gam.commands.up import cmd_up


def test_restart_single_stack(clean_stacks, capsys):
    """Test restart command restarts a single stack."""
    # Start the stack first
    up_args = Namespace(
        target="hello",
        all=False,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )
    cmd_up(clean_stacks, up_args)

    # Restart it
    restart_args = Namespace(
        target="hello",
        all=False,
        category=None,
        tag=None
    )

    try:
        cmd_restart(clean_stacks, restart_args)

        captured = capsys.readouterr()
        assert "Restarting 1 stack(s)" in captured.out
        assert "hello" in captured.out
    finally:
        # Cleanup
        clean_stacks.get_stack("hello").down()


def test_restart_all_stacks(clean_stacks, capsys):
    """Test restart command restarts all stacks."""
    # Start all stacks
    up_args = Namespace(
        target=None,
        all=True,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )
    cmd_up(clean_stacks, up_args)

    # Restart all
    restart_args = Namespace(target=None, all=True, category=None, tag=None)

    try:
        cmd_restart(clean_stacks, restart_args)

        captured = capsys.readouterr()
        assert "Restarting 5 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_restart_by_category(clean_stacks, capsys):
    """Test restart command restarts stacks by category."""
    # Start all stacks
    up_args = Namespace(
        target=None,
        all=True,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )
    cmd_up(clean_stacks, up_args)

    # Restart test category
    restart_args = Namespace(
        target=None,
        all=False,
        category="test",
        tag=None
    )

    try:
        cmd_restart(clean_stacks, restart_args)

        captured = capsys.readouterr()
        # Should restart hello, stack-a, stack-c
        assert "Restarting 3 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_restart_by_tag(clean_stacks, capsys):
    """Test restart command restarts stacks by tag."""
    # Start all stacks
    up_args = Namespace(
        target=None,
        all=True,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )
    cmd_up(clean_stacks, up_args)

    # Restart stacks with dev tag
    restart_args = Namespace(
        target=None,
        all=False,
        category=None,
        tag="dev"
    )

    try:
        cmd_restart(clean_stacks, restart_args)

        captured = capsys.readouterr()
        # Should restart hello and stack-a
        assert "Restarting 2 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()
