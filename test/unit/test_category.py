"""Tests for category command."""

from unittest.mock import MagicMock

import pytest

from gam.commands.category import cmd_category


class TestCategoryCommand:
    """Test cases for the category command."""

    def test_category_list(self, mock_manager, mock_args, capsys):
        """Test listing all categories."""
        mock_args.category_action = 'list'
        mock_manager.get_all_categories = MagicMock(
            return_value=[('test', ''), ('production', ''), ('app', '')]
        )

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Found 3 unique categories" in captured.out
        assert "test" in captured.out
        assert "production" in captured.out
        assert "app" in captured.out

    def test_category_list_empty(self, mock_manager, mock_args, capsys):
        """Test listing categories when none exist."""
        mock_args.category_action = 'list'
        mock_manager.get_all_categories = MagicMock(return_value=[])

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "No categories found" in captured.out

    def test_category_list_with_subcategories(
        self, mock_manager, mock_args, capsys
    ):
        """Test listing categories with subcategories."""
        mock_args.category_action = 'list'
        mock_manager.get_all_categories = MagicMock(
            return_value=[('test', 'unit'), ('test', 'integration')]
        )

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "test/unit" in captured.out
        assert "test/integration" in captured.out

    def test_category_ls_alias(self, mock_manager, mock_args, capsys):
        """Test that 'ls' works as alias for 'list'."""
        mock_args.category_action = 'ls'
        mock_manager.get_all_categories = MagicMock(
            return_value=[('production', ''), ('development', '')]
        )

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Found 2 unique categor" in captured.out
        assert "production" in captured.out
        assert "development" in captured.out

    def test_category_set(self, mock_manager, mock_args, capsys):
        """Test setting category for a stack."""
        mock_args.category_action = 'set'
        mock_args.stack = 'test-stack'
        mock_args.new_category = 'production'
        mock_args.subcategory = None
        stack = mock_manager.stacks['test-stack']
        stack.save_metadata = MagicMock()

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Changed category for test-stack" in captured.out
        assert "test → production" in captured.out
        assert stack.category == 'production'
        stack.save_metadata.assert_called_once()

    def test_category_set_with_subcategory(
        self, mock_manager, mock_args, capsys
    ):
        """Test setting category with subcategory."""
        mock_args.category_action = 'set'
        mock_args.stack = 'test-stack'
        mock_args.new_category = 'services'
        mock_args.subcategory = 'backend'
        stack = mock_manager.stacks['test-stack']
        stack.save_metadata = MagicMock()

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Changed category for test-stack" in captured.out
        assert "services/backend" in captured.out

    def test_category_set_stack_not_found(self, mock_manager, mock_args):
        """Test setting category for non-existent stack."""
        mock_args.category_action = 'set'
        mock_args.stack = 'nonexistent'
        mock_args.new_category = 'test'
        mock_args.subcategory = None

        with pytest.raises(SystemExit):
            cmd_category(mock_manager, mock_args)

    def test_category_rename(self, mock_manager, mock_args, capsys):
        """Test renaming a category across all stacks."""
        mock_args.category_action = 'rename'
        mock_args.old_category = 'test'
        mock_args.new_category = 'testing'
        mock_manager.rename_category = MagicMock(return_value=1)

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Renamed category 'test' to 'testing'" in captured.out
        assert "across 1 stack" in captured.out

    def test_category_rename_not_found(
        self, mock_manager, mock_args, capsys
    ):
        """Test renaming a category that doesn't exist."""
        mock_args.category_action = 'rename'
        mock_args.old_category = 'nonexistent'
        mock_args.new_category = 'new'
        mock_manager.rename_category = MagicMock(return_value=0)

        cmd_category(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "Category 'nonexistent' not found" in captured.out
