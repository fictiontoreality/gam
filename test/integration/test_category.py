"""Integration tests for category command."""

from argparse import Namespace

from gam.commands.category import cmd_category


def test_category_list(clean_stacks, capsys):
    """Test category list command."""
    args = Namespace(category_action='list')
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    assert "test" in captured.out
    assert "production" in captured.out
    assert "app" in captured.out


def test_category_list_with_subcategories(clean_stacks, capsys):
    """Test category list shows subcategories."""
    args = Namespace(category_action='list')
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    # stack-c has test/integration
    assert "test/integration" in captured.out


def test_category_ls_alias(clean_stacks, capsys):
    """Test that 'ls' works as alias for 'list'."""
    args = Namespace(category_action='ls')
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    assert "test" in captured.out
    assert "production" in captured.out
    assert "app" in captured.out


def test_category_set(clean_stacks, capsys):
    """Test setting category for a stack."""
    args = Namespace(
        category_action='set',
        stack='hello',
        new_category='services',
        subcategory=None
    )
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Changed category for hello" in captured.out
    assert "test → services" in captured.out

    # Verify category was changed
    stack = clean_stacks.get_stack('hello')
    assert stack.category == 'services'


def test_category_set_with_subcategory(clean_stacks, capsys):
    """Test setting category with subcategory."""
    args = Namespace(
        category_action='set',
        stack='stack-d',
        new_category='services',
        subcategory='frontend'
    )
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Changed category for stack-d" in captured.out
    assert "services/frontend" in captured.out

    # Verify category was changed
    stack = clean_stacks.get_stack('stack-d')
    assert stack.category == 'services'
    assert stack.subcategory == 'frontend'


def test_category_rename(clean_stacks, capsys):
    """Test renaming a category across all stacks."""
    args = Namespace(
        category_action='rename',
        old_category='test',
        new_category='testing'
    )
    cmd_category(clean_stacks, args)

    captured = capsys.readouterr()
    assert "Renamed category 'test' to 'testing'" in captured.out

    # Verify rename worked
    hello = clean_stacks.get_stack('hello')
    assert hello.category == 'testing'
