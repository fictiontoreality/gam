"""Tests for show command."""

from unittest.mock import MagicMock

import pytest

from composer.commands.show import cmd_show


class TestShowCommand:
    """Test cases for the show command."""

    def test_show_stack(self, mock_manager, mock_args, capsys):
        """Test showing stack details."""
        mock_args.stack = "test-stack"
        stack = mock_manager.stacks["test-stack"]
        stack.get_status = MagicMock(
            return_value={'status': 'running', 'containers': 2, 'running': 2}
        )

        cmd_show(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stack: test-stack" in captured.out
        assert "Description:  Test stack" in captured.out
        assert "Category:     test" in captured.out
        assert "Tags:         dev, testing" in captured.out
        assert "running" in captured.out

    def test_show_stack_with_subcategory(
        self, mock_manager, mock_args, capsys
    ):
        """Test showing stack with subcategory."""
        mock_args.stack = "test-stack"
        stack = mock_manager.stacks["test-stack"]
        stack.subcategory = "unit"
        stack.get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_show(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Category:     test/unit" in captured.out

    def test_show_stack_not_found(self, mock_manager, mock_args):
        """Test show with non-existent stack."""
        mock_args.stack = "nonexistent"

        with pytest.raises(SystemExit):
            cmd_show(mock_manager, mock_args)

    def test_show_stack_with_dependencies(
        self, mock_manager, mock_args, capsys
    ):
        """Test showing stack with dependencies."""
        mock_args.stack = "dependent-stack"
        stack = mock_manager.stacks["dependent-stack"]
        stack.get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_show(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Dependencies: test-stack" in captured.out

    def test_show_autostart_stack(self, mock_manager, mock_args, capsys):
        """Test showing auto-start stack."""
        mock_args.stack = "autostart-stack"
        stack = mock_manager.stacks["autostart-stack"]
        stack.get_status = MagicMock(
            return_value={'status': 'running', 'containers': 1, 'running': 1}
        )

        cmd_show(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Auto-start:   yes" in captured.out
        assert "Priority:     1" in captured.out
