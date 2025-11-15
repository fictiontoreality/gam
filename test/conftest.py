"""Pytest configuration and fixtures for composer tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from composer.stack import Stack
from composer.stack_manager import StackManager


@pytest.fixture
def mock_stack():
    """Create a mock stack for testing."""
    stack = Stack(
        name="test-stack",
        path=Path("/fake/path/test-stack"),
        category="test",
        tags=["dev", "testing"],
        description="Test stack",
        auto_start=False,
        priority=3,
    )
    return stack


@pytest.fixture
def mock_stack_autostart():
    """Create a mock stack with auto-start enabled."""
    stack = Stack(
        name="autostart-stack",
        path=Path("/fake/path/autostart-stack"),
        category="production",
        tags=["prod"],
        description="Auto-start stack",
        auto_start=True,
        priority=1,
    )
    return stack


@pytest.fixture
def mock_stack_with_deps():
    """Create a mock stack with dependencies."""
    stack = Stack(
        name="dependent-stack",
        path=Path("/fake/path/dependent-stack"),
        category="app",
        tags=["backend"],
        description="Stack with dependencies",
        depends_on=["test-stack"],
        priority=2,
    )
    return stack


@pytest.fixture
def mock_manager(mock_stack, mock_stack_autostart, mock_stack_with_deps):
    """Create a mock StackManager with test stacks."""
    manager = StackManager.__new__(StackManager)
    manager.root_dir = Path("/fake/path")
    manager.stacks = {
        "test-stack": mock_stack,
        "autostart-stack": mock_stack_autostart,
        "dependent-stack": mock_stack_with_deps,
    }
    return manager


@pytest.fixture
def mock_args():
    """Create a mock args object."""
    args = MagicMock()
    args.category = None
    args.tag = None
    args.all = False
    args.priority = False
    args.with_deps = False
    args.target = None
    return args
