"""Integration tests for down command."""

from argparse import Namespace

from gam.commands.down import cmd_down
from gam.commands.up import cmd_up


def test_down_single_stack(clean_stacks, capsys):
    """Test down command stops a single stack."""

    # First start the stack
    up_args = Namespace(
        target="hello",
        all=False,
        category=None,
        tag=None,
        priority=False,
        with_deps=False
    )
    cmd_up(clean_stacks, up_args)

    # Now stop it
    down_args = Namespace(
        target="hello",
        all=False,
        category=None,
        tag=None
    )
    cmd_down(clean_stacks, down_args)

    captured = capsys.readouterr()
    assert "Stopping 1 stack(s)" in captured.out
    assert "hello" in captured.out


def test_down_all_stacks(clean_stacks, capsys):
    """Test down command stops all stacks."""

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

    # Stop all stacks
    down_args = Namespace(target=None, all=True, category=None, tag=None)
    cmd_down(clean_stacks, down_args)

    captured = capsys.readouterr()
    assert "Stopping 5 stack(s)" in captured.out


def test_down_by_category(clean_stacks, capsys):
    """Test down command stops stacks by category."""

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

    # Stop test category stacks
    down_args = Namespace(target=None, all=False, category="test", tag=None)
    cmd_down(clean_stacks, down_args)

    captured = capsys.readouterr()
    # Should stop hello, stack-a, stack-c
    assert "Stopping 3 stack(s)" in captured.out

    # Cleanup remaining stacks
    for stack in clean_stacks.stacks.values():
        stack.down()


def test_down_by_tag(clean_stacks, capsys):
    """Test down command stops stacks by tag."""

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

    # Stop stacks with dev tag
    down_args = Namespace(target=None, all=False, category=None, tag="dev")
    cmd_down(clean_stacks, down_args)

    captured = capsys.readouterr()
    # Should stop hello and stack-a
    assert "Stopping 2 stack(s)" in captured.out

    # Cleanup remaining stacks
    for stack in clean_stacks.stacks.values():
        stack.down()


def test_down_reverse_priority(clean_stacks, capsys):
    """Test down command uses reverse priority order."""

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

    # Clear captured output from up command
    capsys.readouterr()

    # Stop all stacks
    down_args = Namespace(target=None, all=True, category=None, tag=None)
    cmd_down(clean_stacks, down_args)

    captured = capsys.readouterr()
    # stack-d (priority 5) should stop before stack-b (priority 1)
    output = captured.out
    stack_d_pos = output.find("stack-d")
    stack_b_pos = output.find("stack-b")
    assert stack_d_pos < stack_b_pos
