"""Integration tests for up command."""

from argparse import Namespace
import time

from gam.commands.up import cmd_up


def test_up_single_stack(clean_stacks, capsys):
    """Test up command starts a single stack."""
    args = Namespace(
        target="hello",
        all=False,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        assert "Starting 1 stack(s)" in captured.out
        assert "hello" in captured.out
    finally:
        # Cleanup
        clean_stacks.get_stack("hello").down()


def test_up_all_stacks(clean_stacks, capsys):
    """Test up command starts all stacks."""
    args = Namespace(
        target=None,
        all=True,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        assert "Starting 5 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_up_by_category(clean_stacks, capsys):
    """Test up command starts stacks by category."""
    args = Namespace(
        target=None,
        all=False,
        category="test",
        tag=None,
        priority=False,
        with_deps=False
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        # Should start hello, stack-a, stack-c (all in test category)
        assert "Starting 3 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_up_by_tag(clean_stacks, capsys):
    """Test up command starts stacks by tag."""
    args = Namespace(
        target=None,
        all=False,
        category=None,
        tag="dev",
        priority=False,
        with_deps=False
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        # Should start hello and stack-a (both have dev tag)
        assert "Starting 2 stack(s)" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_up_with_priority(clean_stacks, capsys):
    """Test up command respects priority ordering."""
    args = Namespace(
        target=None,
        all=True,
        category=None,
        tag=None,
        priority=True,
        with_deps=False
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        # stack-b has priority 1, should start before others
        output = captured.out
        stack_b_pos = output.find("stack-b")
        stack_d_pos = output.find("stack-d")
        # stack-b (priority 1) should appear before stack-d (priority 5)
        assert stack_b_pos < stack_d_pos
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_up_with_dependencies(clean_stacks, capsys):
    """Test up command starts dependencies."""
    args = Namespace(
        target="stack-c",
        all=False,
        category=None,
        tag=None,
        priority=False,
        with_deps=True
    )

    try:
        cmd_up(clean_stacks, args)

        captured = capsys.readouterr()
        # Should start stack-a (dependency) and stack-c
        assert "Starting 2 stack(s)" in captured.out
        assert "stack-a" in captured.out
        assert "stack-c" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()
