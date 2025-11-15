"""Tests for up command."""

from unittest.mock import MagicMock

import pytest

from composer.commands.up import cmd_up


class TestUpCommand:
    """Test cases for the up command."""

    def test_up_single_stack(self, mock_manager, mock_args, capsys):
        """Test starting a single stack."""
        mock_args.target = "test-stack"
        stack = mock_manager.stacks["test-stack"]
        stack.up = MagicMock(return_value=True)

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Starting 1 stack(s)" in captured.out
        assert "test-stack" in captured.out
        assert "✓" in captured.out
        stack.up.assert_called_once()

    def test_up_stack_not_found(self, mock_manager, mock_args):
        """Test up with non-existent stack."""
        mock_args.target = "nonexistent"

        with pytest.raises(SystemExit):
            cmd_up(mock_manager, mock_args)

    def test_up_no_target_provided(self, mock_manager, mock_args):
        """Test up without specifying target."""
        with pytest.raises(SystemExit):
            cmd_up(mock_manager, mock_args)

    def test_up_all_stacks(self, mock_manager, mock_args, capsys):
        """Test starting all stacks."""
        mock_args.all = True
        for stack in mock_manager.stacks.values():
            stack.up = MagicMock(return_value=True)

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Starting 3 stack(s)" in captured.out

    def test_up_by_category(self, mock_manager, mock_args, capsys):
        """Test starting stacks by category."""
        mock_args.category = "production"
        mock_manager.get_category_stacks = MagicMock(
            return_value=[mock_manager.stacks["autostart-stack"]]
        )
        mock_manager.stacks["autostart-stack"].up = MagicMock(
            return_value=True
        )

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Starting 1 stack(s)" in captured.out

    def test_up_by_tag(self, mock_manager, mock_args, capsys):
        """Test starting stacks by tag."""
        mock_args.tag = "dev"
        mock_manager.stacks["test-stack"].up = MagicMock(return_value=True)

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Starting 1 stack(s)" in captured.out

    def test_up_with_priority(self, mock_manager, mock_args, capsys):
        """Test starting stacks with priority ordering."""
        mock_args.all = True
        mock_args.priority = True
        for stack in mock_manager.stacks.values():
            stack.up = MagicMock(return_value=True)

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        # Priority 1 should start before priority 3
        assert captured.out.index("autostart-stack") < captured.out.index(
            "test-stack"
        )

    def test_up_with_dependencies(self, mock_manager, mock_args, capsys):
        """Test starting stack with dependencies."""
        mock_args.target = "dependent-stack"
        mock_args.with_deps = True
        mock_manager.resolve_dependencies = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )
        for stack in mock_manager.stacks.values():
            stack.up = MagicMock(return_value=True)

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Starting 2 stack(s)" in captured.out

    def test_up_failure(self, mock_manager, mock_args, capsys):
        """Test up when stack fails to start."""
        mock_args.target = "test-stack"
        mock_manager.stacks["test-stack"].up = MagicMock(
            return_value=False
        )

        cmd_up(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "✗ FAILED" in captured.out
