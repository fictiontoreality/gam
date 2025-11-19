"""Tests for status command."""

from unittest.mock import MagicMock

from gam.commands.status import cmd_status


class TestStatusCommand:
    """Test cases for the status command."""

    def test_status_all_stacks(self, mock_manager, mock_args, capsys):
        """Test status of all stacks."""
        mock_manager.list_stacks = MagicMock(
            return_value=list(mock_manager.stacks.values())
        )
        for stack in mock_manager.stacks.values():
            stack.get_status = MagicMock(
                return_value={
                    'status': 'running',
                    'containers': 2,
                    'running': 1
                }
            )

        cmd_status(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Stack" in captured.out
        assert "Category" in captured.out
        assert "Status" in captured.out
        assert "test-stack" in captured.out
        assert "1/2" in captured.out

    def test_status_filter_by_category(
        self, mock_manager, mock_args, capsys
    ):
        """Test status filtered by category."""
        mock_args.category = "production"
        mock_manager.list_stacks = MagicMock(
            return_value=[mock_manager.stacks["autostart-stack"]]
        )
        mock_manager.stacks["autostart-stack"].get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_status(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "autostart-stack" in captured.out
        assert "production" in captured.out

    def test_status_shows_icons(self, mock_manager, mock_args, capsys):
        """Test status shows correct icons."""
        mock_manager.list_stacks = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )
        mock_manager.stacks["test-stack"].get_status = MagicMock(
            return_value={'status': 'running', 'containers': 1, 'running': 1}
        )

        cmd_status(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "●" in captured.out  # Running icon

    def test_status_stopped_icon(self, mock_manager, mock_args, capsys):
        """Test status shows stopped icon."""
        mock_manager.list_stacks = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )
        mock_manager.stacks["test-stack"].get_status = MagicMock(
            return_value={'status': 'stopped', 'containers': 0, 'running': 0}
        )

        cmd_status(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "○" in captured.out  # Stopped icon

    def test_status_filter_by_tag(self, mock_manager, mock_args, capsys):
        """Test status filtered by tag."""
        mock_args.tag = "dev"
        mock_manager.list_stacks = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )
        mock_manager.stacks["test-stack"].get_status = MagicMock(
            return_value={'status': 'running', 'containers': 1, 'running': 1}
        )

        cmd_status(mock_manager, mock_args)

        # Verify list_stacks was called with tag parameter
        mock_manager.list_stacks.assert_called_once_with(
            category=None, tag="dev"
        )
        captured = capsys.readouterr()
        assert "test-stack" in captured.out
