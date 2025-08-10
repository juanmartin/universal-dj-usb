"""Test configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def sample_usb_path():
    """Sample USB path for testing."""
    return Path("test_data/sample_usb")


@pytest.fixture
def sample_pdb_path():
    """Sample PDB file path for testing."""
    return Path("test_data/sample_export.pdb")
