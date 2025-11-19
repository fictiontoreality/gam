"""Integration tests for ls command."""

from argparse import Namespace

from gam.commands.ls import cmd_ls


def test_ls_lists_all_stacks(clean_stacks, capsys):
    """Test ls command lists all test stacks."""
    args = Namespace(category=None, tag=None)
    cmd_ls(clean_stacks, args)

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    assert "stack-b" in captured.out
    assert "stack-c" in captured.out
    assert "stack-d" in captured.out


def test_ls_filter_by_category(clean_stacks, capsys):
    """Test ls command filters by category."""
    args = Namespace(category="test", tag=None)
    cmd_ls(clean_stacks, args)

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    assert "stack-c" in captured.out
    assert "stack-b" not in captured.out
    assert "stack-d" not in captured.out


def test_ls_filter_by_tag(clean_stacks, capsys):
    """Test ls command filters by tag."""
    args = Namespace(category=None, tag="dev")
    cmd_ls(clean_stacks, args)

    captured = capsys.readouterr()
    assert "hello" in captured.out
    assert "stack-a" in captured.out
    assert "stack-b" not in captured.out


def test_ls_shows_autostart_indicator(clean_stacks, capsys):
    """Test ls command shows auto-start indicator."""
    args = Namespace(category=None, tag=None)
    cmd_ls(clean_stacks, args)

    captured = capsys.readouterr()
    # stack-b has auto_start: true
    output_lines = captured.out.split('\n')
    stack_b_section = '\n'.join(
        [line for line in output_lines if 'stack-b' in line or
         (output_lines.index(line) > 0 and 'stack-b' in
          output_lines[output_lines.index(line) - 1])]
    )
    assert "auto-start" in stack_b_section.lower() or "●" in stack_b_section
