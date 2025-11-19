"""Tests for down command."""

from unittest.mock import MagicMock

import pytest

from gam.commands.down import cmd_down


class TestDownCommand:
    """Test cases for the down command."""

    def test_down_single_stack(self, mock_manager, mock_args, capsys):
        """Test stopping a single stack."""
        mock_args.target = "test-stack"
        stack = mock_manager.stacks["test-stack"]
        stack.down = MagicMock(return_value=True)

        cmd_down(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stopping 1 stack(s)" in captured.out
        assert "✓" in captured.out
        stack.down.assert_called_once()

    def test_down_stack_not_found(self, mock_manager, mock_args):
        """Test down with non-existent stack."""
        mock_args.target = "nonexistent"

        with pytest.raises(SystemExit):
            cmd_down(mock_manager, mock_args)

    def test_down_all_stacks(self, mock_manager, mock_args, capsys):
        """Test stopping all stacks."""
        mock_args.all = True
        for stack in mock_manager.stacks.values():
            stack.down = MagicMock(return_value=True)

        cmd_down(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stopping 3 stack(s)" in captured.out

    def test_down_by_category(self, mock_manager, mock_args, capsys):
        """Test stopping stacks by category."""
        mock_args.category = "test"
        mock_manager.get_category_stacks = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )
        mock_manager.stacks["test-stack"].down = MagicMock(
            return_value=True
        )

        cmd_down(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stopping 1 stack(s)" in captured.out

    def test_down_by_tag(self, mock_manager, mock_args, capsys):
        """Test stopping stacks by tag."""
        mock_args.tag = "backend"
        mock_manager.stacks["dependent-stack"].down = MagicMock(
            return_value=True
        )

        cmd_down(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stopping 1 stack(s)" in captured.out

    def test_down_reverse_priority(self, mock_manager, mock_args, capsys):
        """Test stopping in reverse priority order."""
        mock_args.all = True
        for stack in mock_manager.stacks.values():
            stack.down = MagicMock(return_value=True)

        cmd_down(mock_manager, mock_args)

        captured = capsys.readouterr()
        # Priority 3 should stop before priority 1
        assert captured.out.index("test-stack") < captured.out.index(
            "autostart-stack"
        )
