"""Tests for ls (list) command."""

from unittest.mock import MagicMock, patch

import pytest

from gam.commands.ls import cmd_ls


class TestLsCommand:
    """Test cases for the ls command."""

    def test_ls_no_stacks(self, mock_manager, mock_args, capsys):
        """Test ls when no stacks exist."""
        mock_manager.stacks = {}
        mock_manager.list_stacks = MagicMock(return_value=[])

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "No stacks found" in captured.out

    def test_ls_all_stacks(self, mock_manager, mock_args, capsys):
        """Test ls lists all stacks."""
        stacks = list(mock_manager.stacks.values())
        mock_manager.list_stacks = MagicMock(return_value=stacks)

        # Mock get_status for each stack
        for stack in stacks:
            stack.get_status = MagicMock(
                return_value={
                    'status': 'running',
                    'containers': 2,
                    'running': 2
                }
            )

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "test-stack" in captured.out
        assert "autostart-stack" in captured.out
        assert "dependent-stack" in captured.out

    def test_ls_filter_by_category(self, mock_manager, mock_args, capsys):
        """Test ls filters by category."""
        mock_args.category = "production"
        filtered = [mock_manager.stacks["autostart-stack"]]
        mock_manager.list_stacks = MagicMock(return_value=filtered)

        filtered[0].get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "autostart-stack" in captured.out
        assert "PRODUCTION" in captured.out

    def test_ls_filter_by_tag(self, mock_manager, mock_args, capsys):
        """Test ls filters by tag."""
        mock_args.tag = "prod"
        filtered = [mock_manager.stacks["autostart-stack"]]
        mock_manager.list_stacks = MagicMock(return_value=filtered)

        filtered[0].get_status = MagicMock(
            return_value={'status': 'running', 'containers': 1, 'running': 1}
        )

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "autostart-stack" in captured.out

    def test_ls_shows_status_icon(self, mock_manager, mock_args, capsys):
        """Test ls shows correct status icon."""
        stacks = [mock_manager.stacks["test-stack"]]
        mock_manager.list_stacks = MagicMock(return_value=stacks)

        stacks[0].get_status = MagicMock(
            return_value={'status': 'running', 'containers': 2, 'running': 2}
        )

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "●" in captured.out  # Running icon

    def test_ls_shows_autostart_priority(
        self, mock_manager, mock_args, capsys
    ):
        """Test ls shows auto-start priority."""
        stacks = [mock_manager.stacks["autostart-stack"]]
        mock_manager.list_stacks = MagicMock(return_value=stacks)

        stacks[0].get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_ls(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Auto-start: yes (priority 1)" in captured.out
