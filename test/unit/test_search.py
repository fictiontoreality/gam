"""Tests for search command."""

from unittest.mock import MagicMock

from gam.commands.search import cmd_search


class TestSearchCommand:
    """Test cases for the search command."""

    def test_search_finds_stacks(self, mock_manager, mock_args, capsys):
        """Test searching for stacks."""
        mock_args.term = "test"
        mock_manager.search = MagicMock(
            return_value=[mock_manager.stacks["test-stack"]]
        )

        cmd_search(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Found 1 stack(s)" in captured.out
        assert "test-stack" in captured.out
        assert "Test stack" in captured.out

    def test_search_no_results(self, mock_manager, mock_args, capsys):
        """Test search with no results."""
        mock_args.term = "nonexistent"
        mock_manager.search = MagicMock(return_value=[])

        cmd_search(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "No stacks found matching 'nonexistent'" in captured.out

    def test_search_multiple_results(self, mock_manager, mock_args, capsys):
        """Test search with multiple results."""
        mock_args.term = "stack"
        mock_manager.search = MagicMock(
            return_value=list(mock_manager.stacks.values())
        )

        cmd_search(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Found 3 stack(s)" in captured.out
        assert "test-stack" in captured.out
        assert "autostart-stack" in captured.out
        assert "dependent-stack" in captured.out
