"""Fixtures for integration tests."""

import shutil
import subprocess
from pathlib import Path

import pytest

from gam.stack_manager import StackManager


@pytest.fixture(scope="session")
def test_stacks_dir():
    """Return the path to test stacks directory."""
    return Path(__file__).parent.parent / "stacks"


@pytest.fixture(scope="session")
def original_metadata(test_stacks_dir):
    """Save original metadata before tests and restore after."""
    # Save original metadata
    metadata_backups = {}
    for meta_file in test_stacks_dir.rglob(".stack-meta.yaml"):
        backup_path = meta_file.parent / ".stack-meta.yaml.backup"
        shutil.copy2(meta_file, backup_path)
        metadata_backups[meta_file] = backup_path

    yield metadata_backups

    # Restore original metadata
    for original, backup in metadata_backups.items():
        if backup.exists():
            shutil.copy2(backup, original)
            backup.unlink()


@pytest.fixture(autouse=True, scope="session")
def cleanup_docker(original_metadata):
    """Clean up all test stacks before and after test session."""
    test_dir = Path(__file__).parent.parent / "stacks"

    def cleanup_all():
        """Stop and remove all containers from test stacks."""
        for stack_dir in test_dir.iterdir():
            if stack_dir.is_dir() and (
                stack_dir / "docker-compose.yml"
            ).exists():
                # Change to stack directory and run docker compose down
                subprocess.run(
                    ["docker", "compose", "down", "-v", "--remove-orphans"],
                    cwd=stack_dir,
                    capture_output=True,
                )

    # Cleanup before tests
    cleanup_all()

    yield

    # Cleanup after tests
    cleanup_all()


@pytest.fixture
def manager(test_stacks_dir):
    """Create a StackManager for the test stacks directory."""
    manager = StackManager(root_dir=test_stacks_dir)

    yield manager


@pytest.fixture
def clean_stacks(test_stacks_dir):
    """Ensure all stacks are stopped and metadata restored each test."""
    manager = StackManager(root_dir=test_stacks_dir)

    # Stop all stacks
    for stack in manager.stacks.values():
        stack.down()

    # Save metadata before test
    metadata_backups = {}
    for meta_file in test_stacks_dir.rglob(".stack-meta.yaml"):
        if ".backup" not in str(meta_file) and ".testbackup" not in str(
            meta_file
        ):
            backup_path = meta_file.parent / ".stack-meta.yaml.testbackup"
            shutil.copy2(meta_file, backup_path)
            metadata_backups[meta_file] = backup_path

    yield manager

    # Stop all stacks after test
    for stack in manager.stacks.values():
        stack.down()

    # Restore metadata after test
    for original, backup in metadata_backups.items():
        if backup.exists():
            shutil.copy2(backup, original)
            backup.unlink()
