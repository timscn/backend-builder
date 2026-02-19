"""
Tests for shared utilities
"""
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_repo_root, resolve_path, ensure_output_dir


def test_get_repo_root():
    """Test getting repo root."""
    root = get_repo_root()
    assert isinstance(root, Path)
    assert root.exists()
    assert root.is_dir()


def test_resolve_path_absolute():
    """Test resolving an absolute path."""
    abs_path = Path("/tmp/test")
    result = resolve_path(str(abs_path))
    assert result == abs_path


def test_resolve_path_relative():
    """Test resolving a relative path."""
    result = resolve_path("output")
    assert isinstance(result, Path)
    assert result.is_absolute()


def test_ensure_output_dir():
    """Test ensuring output directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "subdir" / "file.txt"
        ensure_output_dir(test_file)
        
        assert test_file.parent.exists()
        assert test_file.parent.is_dir()
