"""Integration tests for validate command."""

from argparse import Namespace

from composer.commands.validate import cmd_validate


def test_validate_all_stacks_valid(clean_stacks, capsys):
    """Test validate command with all valid stacks."""
    args = Namespace(target=None)
    cmd_validate(clean_stacks, args)

    captured = capsys.readouterr()
    assert "✓ All stacks valid" in captured.out


def test_validate_single_stack(clean_stacks, capsys):
    """Test validate command with a single stack."""
    args = Namespace(target="hello")
    cmd_validate(clean_stacks, args)

    captured = capsys.readouterr()
    assert "✓ All stacks valid" in captured.out


def test_validate_detects_missing_dependency(clean_stacks, capsys, tmp_path):
    """Test validate detects missing dependencies."""

    # Temporarily modify stack-c to depend on non-existent stack
    stack_c = clean_stacks.get_stack("stack-c")
    original_deps = stack_c.depends_on.copy()
    stack_c.depends_on = ["nonexistent-stack"]

    try:
        args = Namespace(target=None)
        cmd_validate(clean_stacks, args)

        captured = capsys.readouterr()
        assert "dependency 'nonexistent-stack' not found" in captured.out
        assert "stack-c" in captured.out
    finally:
        # Restore original dependencies
        stack_c.depends_on = original_deps


def test_validate_detects_name_field_mismatch(clean_stacks, capsys):
    """Test validate detects name field in metadata that doesn't match path."""
    import yaml
    from pathlib import Path

    # Get a stack and add a name field to its metadata
    stack = clean_stacks.get_stack("hello")
    meta_file = stack.meta_file

    # Read existing metadata
    with open(meta_file) as f:
        metadata = yaml.safe_load(f) or {}

    # Add incorrect name field
    metadata['name'] = 'wrong-name'

    # Write modified metadata
    with open(meta_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    try:
        args = Namespace(target=None)
        cmd_validate(clean_stacks, args)

        captured = capsys.readouterr()
        assert "metadata contains 'name' field" in captured.out
        assert "wrong-name" in captured.out
        assert "name is derived from path" in captured.out
        assert "⚠" in captured.out
    finally:
        # The clean_stacks fixture will restore the original metadata
        pass
