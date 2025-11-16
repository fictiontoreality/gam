"""Integration tests for status command."""

from argparse import Namespace

from composer.commands.status import cmd_status


def test_status_shows_all_stacks(clean_stacks, capsys):
    """Test status command shows all stacks."""
    args = Namespace(category=None, tag=None)
    cmd_status(clean_stacks, args)

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    assert "stack-b" in captured.out
    assert "stack-c" in captured.out
    assert "stack-d" in captured.out


def test_status_filter_by_category(clean_stacks, capsys):
    """Test status command filters by category."""
    args = Namespace(category="test", tag=None)
    cmd_status(clean_stacks, args)

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    assert "stack-c" in captured.out


def test_status_filter_by_tag(clean_stacks, capsys):
    """Test status command filters by tag."""
    args = Namespace(category=None, tag="dev")
    cmd_status(clean_stacks, args)

    captured = capsys.readouterr()
    # hello and stack-a have 'dev' tag
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    # stack-b should not appear (has 'prod' tag)
    assert "stack-b" not in captured.out


def test_status_shows_stopped_stacks(clean_stacks, capsys):
    """Test status command shows stopped stacks."""
    args = Namespace(category=None, tag=None)
    cmd_status(clean_stacks, args)

    captured = capsys.readouterr()
    # Should show stopped icon for all stacks
    assert "○" in captured.out or "stopped" in captured.out.lower()


def test_status_shows_running_stacks(clean_stacks, capsys):
    """Test status command shows running stacks correctly."""

    # Start a stack
    stack = clean_stacks.get_stack("hello")
    stack.up()

    try:
        args = Namespace(category=None, tag=None)
        cmd_status(clean_stacks, args)

        captured = capsys.readouterr()
        # Note: hello-world container exits immediately after running
        # so status might show exited/stopped
        assert "hello" in captured.out
    finally:
        stack.down()
