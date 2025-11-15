"""Tests for autostart command."""

from unittest.mock import MagicMock

from composer.commands.autostart import cmd_autostart


class TestAutostartCommand:
    """Test cases for the autostart command."""

    def test_autostart_no_stacks(self, mock_manager, mock_args, capsys):
        """Test autostart when no stacks are configured."""
        mock_manager.get_autostart_stacks = MagicMock(return_value=[])

        cmd_autostart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "No stacks configured for auto-start" in captured.out

    def test_autostart_starts_stacks(self, mock_manager, mock_args, capsys):
        """Test autostart starts configured stacks."""
        stacks = [mock_manager.stacks["autostart-stack"]]
        mock_manager.get_autostart_stacks = MagicMock(return_value=stacks)
        stacks[0].up = MagicMock(return_value=True)

        cmd_autostart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Auto-starting 1 stack(s) by priority" in captured.out
        assert "[1] Starting autostart-stack" in captured.out
        assert "✓" in captured.out
        stacks[0].up.assert_called_once()

    def test_autostart_priority_order(self, mock_manager, mock_args, capsys):
        """Test autostart respects priority order."""
        # Create additional auto-start stack with different priority
        stack2 = MagicMock()
        stack2.name = "priority-2-stack"
        stack2.auto_start = True
        stack2.priority = 2
        stack2.up = MagicMock(return_value=True)

        stacks = [
            mock_manager.stacks["autostart-stack"],  # priority 1
            stack2  # priority 2
        ]
        mock_manager.get_autostart_stacks = MagicMock(return_value=stacks)
        mock_manager.stacks["autostart-stack"].up = MagicMock(
            return_value=True
        )

        cmd_autostart(mock_manager, mock_args)

        captured = capsys.readouterr()
        # Priority 1 should appear before priority 2
        assert captured.out.index("[1]") < captured.out.index("[2]")

    def test_autostart_failure(self, mock_manager, mock_args, capsys):
        """Test autostart handles failures."""
        stacks = [mock_manager.stacks["autostart-stack"]]
        mock_manager.get_autostart_stacks = MagicMock(return_value=stacks)
        stacks[0].up = MagicMock(return_value=False)

        cmd_autostart(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "✗ FAILED" in captured.out
