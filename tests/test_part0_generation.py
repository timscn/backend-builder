"""
Tests for Part 0: Log Generation
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from part0_generation.generate_practice_file import generate_practice_file


def test_generate_practice_file_creates_file():
    """Test that generate_practice_file creates a file with 100 lines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_logs.jsonl"
        result_path = generate_practice_file(output_path=str(output_path))
        
        assert Path(result_path).exists()
        assert Path(result_path) == output_path
        
        # Count lines
        with open(output_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 100


def test_generate_practice_file_has_valid_and_invalid_logs():
    """Test that the generated file contains both valid and invalid logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_logs.jsonl"
        generate_practice_file(output_path=str(output_path))
        
        valid_count = 0
        invalid_count = 0
        
        with open(output_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Check for malformed JSON (error type 1)
                if "-- BROKEN" in line:
                    invalid_count += 1
                    continue
                
                try:
                    log = json.loads(line)
                    # Check for missing feature (error type 2)
                    if "feature" not in log:
                        invalid_count += 1
                    # Check for bad timestamp (error type 3)
                    elif log.get("timestamp") == "NOT-A-DATE":
                        invalid_count += 1
                    else:
                        valid_count += 1
                except json.JSONDecodeError:
                    invalid_count += 1
        
        # Should have both valid and invalid logs
        assert valid_count > 0
        assert invalid_count > 0


def test_generate_practice_file_valid_logs_have_required_fields():
    """Test that valid logs have all required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_logs.jsonl"
        generate_practice_file(output_path=str(output_path))
        
        required_fields = ["user_id", "feature", "timestamp", "action"]
        
        with open(output_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "-- BROKEN" in line:
                    continue
                
                try:
                    log = json.loads(line)
                    # Skip known error cases
                    if "feature" not in log or log.get("timestamp") == "NOT-A-DATE":
                        continue
                    
                    # Valid logs should have all fields
                    for field in required_fields:
                        assert field in log, f"Missing field: {field} in {log}"
                except json.JSONDecodeError:
                    continue
