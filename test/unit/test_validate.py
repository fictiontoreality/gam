"""Tests for validate command."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import yaml

from gam.commands.validate import cmd_validate


class TestValidateCommand:
    """Test cases for the validate command."""

    def test_validate_all_valid(self, mock_manager, mock_args, capsys):
        """Test validate when all stacks are valid."""
        with patch.object(Path, 'exists', return_value=True):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "✓ All stacks valid" in captured.out

    def test_validate_single_stack(self, mock_manager, mock_args, capsys):
        """Test validate when a single stack is valid."""
        mock_args.target = "test-stack"

        with patch.object(Path, 'exists', return_value=True):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "✓ All stacks valid" in captured.out

    def test_validate_missing_compose_file(
        self, mock_manager, mock_args, capsys
    ):
        """Test validate detects missing docker-compose.yml."""
        test_compose = (
            mock_manager.stacks["test-stack"].path / "docker-compose.yml"
        )

        def exists_side_effect(path_self):
            # Return False only for test-stack's compose file
            return str(path_self) != str(test_compose)

        with patch.object(Path, 'exists', exists_side_effect):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "docker-compose.yml not found" in captured.out
        assert "test-stack" in captured.out
        assert "1 issue(s) found" in captured.out

    def test_validate_missing_metadata(self, mock_manager, mock_args, capsys):
        """Test validate warns about missing metadata."""
        test_meta = (
            mock_manager.stacks["test-stack"].path / ".stack-meta.yaml"
        )

        def exists_side_effect(path_self):
            # Return False only for test-stack's meta file
            return str(path_self) != str(test_meta)

        with patch.object(Path, 'exists', exists_side_effect):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "no .stack-meta.yaml file" in captured.out
        assert "⚠" in captured.out

    def test_validate_missing_dependency(
        self, mock_manager, mock_args, capsys
    ):
        """Test validate detects missing dependencies."""
        # Make dependent-stack depend on non-existent stack
        stack = mock_manager.stacks["dependent-stack"]
        stack.depends_on = ["nonexistent-stack"]

        # Mock get_stack to return None for nonexistent
        original_get_stack = mock_manager.get_stack
        mock_manager.get_stack = MagicMock(
            side_effect=lambda name: (
                None if name == "nonexistent-stack"
                else original_get_stack(name)
            )
        )

        with patch.object(Path, 'exists', return_value=True):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "dependency 'nonexistent-stack' not found" in captured.out
        assert "dependent-stack" in captured.out

    def test_validate_multiple_issues(
        self, mock_manager, mock_args, capsys
    ):
        """Test validate reports multiple issues."""
        # First stack missing compose file
        test_compose = (
            mock_manager.stacks["test-stack"].path / "docker-compose.yml"
        )

        # Second stack missing metadata
        autostart_meta = (
            mock_manager.stacks["autostart-stack"].path / ".stack-meta.yaml"
        )

        def exists_side_effect(path_self):
            # Return False for test-stack's compose and autostart's meta
            path_str = str(path_self)
            if path_str == str(test_compose):
                return False
            if path_str == str(autostart_meta):
                return False
            return True

        with patch.object(Path, 'exists', exists_side_effect):
            cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "2 issue(s) found" in captured.out
        assert "test-stack" in captured.out
        assert "autostart-stack" in captured.out

    def test_validate_name_field_mismatch(
        self, mock_manager, mock_args, capsys
    ):
        """Test validate detects name field mismatch in metadata."""
        # Create metadata with mismatched name
        metadata_content = yaml.dump({
            'name': 'wrong-name',
            'description': 'Test stack',
            'category': 'test'
        })

        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=metadata_content)):
                cmd_validate(mock_manager, mock_args)

        captured = capsys.readouterr()
        assert "metadata contains 'name' field" in captured.out
        assert "wrong-name" in captured.out
        assert "name is derived from path" in captured.out
        assert "⚠" in captured.out
