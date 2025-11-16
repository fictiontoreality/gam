"""Integration tests for tag command."""

from argparse import Namespace

from composer.commands.tag import cmd_tag


def test_tag_list(clean_stacks, capsys):
    """Test tag list command."""
    args = Namespace(tag_action='list')
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "dev" in captured.out
    assert "testing" in captured.out
    assert "prod" in captured.out
    assert "backend" in captured.out
    assert "frontend" in captured.out


def test_tag_ls_alias(clean_stacks, capsys):
    """Test that 'ls' works as alias for 'list'."""
    args = Namespace(tag_action='ls')
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "dev" in captured.out
    assert "testing" in captured.out
    assert "prod" in captured.out
    assert "backend" in captured.out
    assert "frontend" in captured.out


def test_tag_add(clean_stacks, capsys):
    """Test adding tags to a stack."""
    args = Namespace(
        tag_action='add',
        stack='hello',
        tags=['new-tag', 'another-tag']
    )
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Added tag(s) to hello" in captured.out

    # Verify tags were added
    stack = clean_stacks.get_stack('hello')
    assert 'new-tag' in stack.tags
    assert 'another-tag' in stack.tags


def test_tag_add_duplicate(clean_stacks, capsys):
    """Test adding duplicate tags."""
    args = Namespace(
        tag_action='add',
        stack='hello',
        tags=['dev']  # Already exists
    )
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "All specified tags already exist" in captured.out


def test_tag_remove(clean_stacks, capsys):
    """Test removing tags from a stack."""
    args = Namespace(
        tag_action='remove',
        stack='hello',
        tags=['testing']
    )
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Removed tag(s) from hello" in captured.out

    # Verify tag was removed
    stack = clean_stacks.get_stack('hello')
    assert 'testing' not in stack.tags


def test_tag_rename(clean_stacks, capsys):
    """Test renaming a tag across all stacks."""
    args = Namespace(
        tag_action='rename',
        old_tag='dev',
        new_tag='development'
    )
    cmd_tag(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Renamed 'dev' to 'development'" in captured.out
    assert "across" in captured.out

    # Verify rename worked
    hello = clean_stacks.get_stack('hello')
    assert 'development' in hello.tags
    assert 'dev' not in hello.tags
