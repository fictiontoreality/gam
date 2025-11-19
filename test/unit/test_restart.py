"""Tests for restart command."""

from unittest.mock import MagicMock

from gam.commands.restart import cmd_restart


class TestRestartCommand:
    """Test cases for the restart command."""

    def test_restart_single_stack(self, mock_manager, mock_args, capsys):
        """Test restarting a single stack."""
        mock_args.target = "test-stack"
        stack = mock_manager.stacks["test-stack"]
        stack.restart = MagicMock(return_value=True)

        cmd_restart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Restarting 1 stack(s)" in captured.out
        assert "✓" in captured.out
        stack.restart.assert_called_once()

    def test_restart_all_stacks(self, mock_manager, mock_args, capsys):
        """Test restarting all stacks."""
        mock_args.all = True
        for stack in mock_manager.stacks.values():
            stack.restart = MagicMock(return_value=True)

        cmd_restart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Restarting 3 stack(s)" in captured.out

    def test_restart_by_category(self, mock_manager, mock_args, capsys):
        """Test restarting stacks by category."""
        mock_args.category = "app"
        mock_manager.get_category_stacks = MagicMock(
            return_value=[mock_manager.stacks["dependent-stack"]]
        )
        mock_manager.stacks["dependent-stack"].restart = MagicMock(
            return_value=True
        )

        cmd_restart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Restarting 1 stack(s)" in captured.out

    def test_restart_by_tag(self, mock_manager, mock_args, capsys):
        """Test restarting stacks by tag."""
        mock_args.tag = "testing"
        mock_manager.stacks["test-stack"].restart = MagicMock(
            return_value=True
        )

        cmd_restart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Restarting 1 stack(s)" in captured.out

    def test_restart_failure(self, mock_manager, mock_args, capsys):
        """Test restart when stack fails."""
        mock_args.target = "test-stack"
        mock_manager.stacks["test-stack"].restart = MagicMock(
            return_value=False
        )

        cmd_restart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "✗ FAILED" in captured.out
