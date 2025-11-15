"""Tests for tag command."""

from unittest.mock import MagicMock

import pytest

from composer.commands.tag import cmd_tag


class TestTagCommand:
    """Test cases for the tag command."""

    def test_tag_list(self, mock_manager, mock_args, capsys):
        """Test listing all tags."""
        mock_args.tag_action = 'list'
        mock_manager.get_all_tags = MagicMock(
            return_value=['dev', 'prod', 'testing']
        )

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Found 3 unique tag(s)" in captured.out
        assert "dev" in captured.out
        assert "prod" in captured.out
        assert "testing" in captured.out

    def test_tag_list_empty(self, mock_manager, mock_args, capsys):
        """Test listing tags when none exist."""
        mock_args.tag_action = 'list'
        mock_manager.get_all_tags = MagicMock(return_value=[])

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "No tags found" in captured.out

    def test_tag_add(self, mock_manager, mock_args, capsys):
        """Test adding tags to a stack."""
        mock_args.tag_action = 'add'
        mock_args.stack = 'test-stack'
        mock_args.tags = ['new-tag', 'another-tag']
        stack = mock_manager.stacks['test-stack']
        stack.save_metadata = MagicMock()

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Added tag(s) to test-stack" in captured.out
        assert "new-tag" in captured.out
        assert 'new-tag' in stack.tags
        assert 'another-tag' in stack.tags
        stack.save_metadata.assert_called_once()

    def test_tag_add_duplicate(self, mock_manager, mock_args, capsys):
        """Test adding duplicate tags."""
        mock_args.tag_action = 'add'
        mock_args.stack = 'test-stack'
        mock_args.tags = ['dev']  # Already exists
        stack = mock_manager.stacks['test-stack']

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "All specified tags already exist" in captured.out

    def test_tag_add_stack_not_found(self, mock_manager, mock_args):
        """Test adding tags to non-existent stack."""
        mock_args.tag_action = 'add'
        mock_args.stack = 'nonexistent'
        mock_args.tags = ['tag']

        with pytest.raises(SystemExit):
            cmd_tag(mock_manager, mock_args)

    def test_tag_remove(self, mock_manager, mock_args, capsys):
        """Test removing tags from a stack."""
        mock_args.tag_action = 'remove'
        mock_args.stack = 'test-stack'
        mock_args.tags = ['dev']
        stack = mock_manager.stacks['test-stack']
        stack.save_metadata = MagicMock()

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Removed tag(s) from test-stack" in captured.out
        assert 'dev' not in stack.tags
        stack.save_metadata.assert_called_once()

    def test_tag_remove_nonexistent(self, mock_manager, mock_args, capsys):
        """Test removing tags that don't exist."""
        mock_args.tag_action = 'remove'
        mock_args.stack = 'test-stack'
        mock_args.tags = ['nonexistent-tag']

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "None of the specified tags were found" in captured.out

    def test_tag_rename(self, mock_manager, mock_args, capsys):
        """Test renaming a tag across all stacks."""
        mock_args.tag_action = 'rename'
        mock_args.old_tag = 'dev'
        mock_args.new_tag = 'development'
        mock_manager.rename_tag = MagicMock(return_value=2)

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Renamed 'dev' to 'development'" in captured.out
        assert "across 2 stacks" in captured.out

    def test_tag_rename_not_found(self, mock_manager, mock_args, capsys):
        """Test renaming a tag that doesn't exist."""
        mock_args.tag_action = 'rename'
        mock_args.old_tag = 'nonexistent'
        mock_args.new_tag = 'new'
        mock_manager.rename_tag = MagicMock(return_value=0)

        cmd_tag(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Tag 'nonexistent' not found on any stacks" in captured.out
