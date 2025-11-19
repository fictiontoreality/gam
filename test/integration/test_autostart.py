"""Integration tests for autostart command."""

from argparse import Namespace

from gam.commands.autostart import cmd_autostart


def test_autostart_starts_configured_stacks(clean_stacks, capsys):
    """Test autostart command starts configured stacks."""
    args = Namespace()

    try:
        cmd_autostart(clean_stacks, args)

        captured = capsys.readouterr()
        # stack-b has auto_start: true
        assert "Auto-starting" in captured.out
        assert "stack-b" in captured.out
    finally:
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()


def test_autostart_priority_order(clean_stacks, capsys):
    """Test autostart respects priority order."""

    # Temporarily set another stack to auto-start with different priority
    stack_a = clean_stacks.get_stack("stack-a")
    original_auto_start = stack_a.auto_start
    original_priority = stack_a.priority
    stack_a.auto_start = True
    stack_a.priority = 2

    try:
        args = Namespace()
        cmd_autostart(clean_stacks, args)

        captured = capsys.readouterr()
        # stack-b (priority 1) should start before stack-a (priority 2)
        output = captured.out
        stack_b_pos = output.find("[1]")
        stack_a_pos = output.find("[2]")
        assert stack_b_pos < stack_a_pos
    finally:
        # Restore original values
        stack_a.auto_start = original_auto_start
        stack_a.priority = original_priority
        # Cleanup
        for stack in clean_stacks.stacks.values():
            stack.down()
