"""Tests for logs command."""

from unittest.mock import MagicMock, call, patch

import pytest

from gam.commands.logs import cmd_logs


class TestLogsCommand:
    """Test cases for the logs command."""

    def test_logs_single_stack(self, mock_manager, mock_args, capsys):
        """Test showing logs for a single stack."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0] == [
                "docker", "compose", "logs"
            ]

        captured = capsys.readouterr()
        assert "Showing logs for test-stack" in captured.out

    def test_logs_multiple_stacks_by_name(
        self, mock_manager, mock_args, capsys
    ):
        """Test showing logs for multiple named stacks."""
        mock_args.stacks = ["test-stack", "autostart-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="log line 1\nlog line 2\n", stderr=""
            )
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Showing logs from 2 stack(s)" in captured.out
        # Verify prefixing
        assert "[test-stack]" in captured.out
        assert "[autostart-stack]" in captured.out

    def test_logs_all_stacks_explicit(
        self, mock_manager, mock_args, capsys
    ):
        """Test showing logs from all stacks with --all flag."""
        mock_args.stacks = []
        mock_args.all = True
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Showing logs from 3 stack(s)" in captured.out

    def test_logs_no_args_shows_all(self, mock_manager, mock_args, capsys):
        """Test that logs with no args defaults to showing all stacks."""
        mock_args.stacks = []
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Showing logs from 3 stack(s)" in captured.out

    def test_logs_by_category(self, mock_manager, mock_args, capsys):
        """Test showing logs filtered by category."""
        mock_args.stacks = []
        mock_args.all = False
        mock_args.category = "production"
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        mock_manager.get_category_stacks = MagicMock(
            return_value=[mock_manager.stacks["autostart-stack"]]
        )

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Showing logs for autostart-stack" in captured.out

    def test_logs_by_tag(self, mock_manager, mock_args, capsys):
        """Test showing logs filtered by tag."""
        mock_args.stacks = []
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = "dev"
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Showing logs for test-stack" in captured.out

    def test_logs_nonexistent_stack(self, mock_manager, mock_args):
        """Test logs with non-existent stack."""
        mock_args.stacks = ["nonexistent"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None

        with pytest.raises(SystemExit):
            cmd_logs(mock_manager, mock_args)

    def test_logs_with_follow_flag(self, mock_manager, mock_args):
        """Test logs with --follow flag."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = True
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--follow" in called_cmd

    def test_logs_with_since_flag(self, mock_manager, mock_args):
        """Test logs with --since flag."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = "2024-01-01"
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--since" in called_cmd
            assert "2024-01-01" in called_cmd

    def test_logs_with_tail_flag(self, mock_manager, mock_args):
        """Test logs with -n/--tail flag."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = "100"
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--tail" in called_cmd
            assert "100" in called_cmd

    def test_logs_with_timestamps_flag(self, mock_manager, mock_args):
        """Test logs with -T/--timestamps flag."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = True
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--timestamps" in called_cmd

    def test_logs_with_until_flag(self, mock_manager, mock_args):
        """Test logs with --until flag."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = "2024-12-31"

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--until" in called_cmd
            assert "2024-12-31" in called_cmd

    def test_logs_prefixing_multiple_stacks(
        self, mock_manager, mock_args, capsys
    ):
        """Test that log lines are prefixed with stack names."""
        mock_args.stacks = ["test-stack", "autostart-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = False
        mock_args.since = None
        mock_args.tail = None
        mock_args.timestamps = False
        mock_args.until = None

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="test log line\n", stderr=""
            )
            cmd_logs(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "[test-stack] test log line" in captured.out
        assert "[autostart-stack] test log line" in captured.out

    def test_logs_empty_category(self, mock_manager, mock_args):
        """Test logs with category that has no stacks."""
        mock_args.stacks = []
        mock_args.all = False
        mock_args.category = "nonexistent"
        mock_args.tag = None
        mock_args.follow = False

        mock_manager.get_category_stacks = MagicMock(return_value=[])

        with pytest.raises(SystemExit):
            cmd_logs(mock_manager, mock_args)

    def test_logs_empty_tag(self, mock_manager, mock_args):
        """Test logs with tag that matches no stacks."""
        mock_args.stacks = []
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = "nonexistent"
        mock_args.follow = False

        with pytest.raises(SystemExit):
            cmd_logs(mock_manager, mock_args)

    def test_logs_with_all_flags(self, mock_manager, mock_args):
        """Test logs with all flags combined."""
        mock_args.stacks = ["test-stack"]
        mock_args.all = False
        mock_args.category = None
        mock_args.tag = None
        mock_args.follow = True
        mock_args.since = "2024-01-01"
        mock_args.tail = "50"
        mock_args.timestamps = True
        mock_args.until = "2024-12-31"

        with patch('gam.commands.logs.subprocess.run') as mock_run:
            cmd_logs(mock_manager, mock_args)
            called_cmd = mock_run.call_args[0][0]
            assert "--follow" in called_cmd
            assert "--since" in called_cmd
            assert "2024-01-01" in called_cmd
            assert "--tail" in called_cmd
            assert "50" in called_cmd
            assert "--timestamps" in called_cmd
            assert "--until" in called_cmd
            assert "2024-12-31" in called_cmd
