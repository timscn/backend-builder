"""
Tests for Part 1: Log Parsing
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from part1_parsing.parse_logs import (
    parse_log_line,
    validate_log_structure,
    parse_logs_file,
    group_logs_by_user_and_feature,
)


def test_parse_log_line_valid_json():
    """Test parsing a valid JSON line."""
    line = '{"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"}'
    log, error = parse_log_line(line, 1)
    
    assert error is None
    assert log is not None
    assert log["user_id"] == 1
    assert log["feature"] == "map"


def test_parse_log_line_malformed_json():
    """Test parsing a malformed JSON line."""
    line = '{"user_id": 1, "action": "start" -- BROKEN'
    log, error = parse_log_line(line, 1)
    
    assert log is None
    assert error is not None
    assert "Malformed JSON" in error


def test_parse_log_line_empty_line():
    """Test parsing an empty line."""
    log, error = parse_log_line("", 1)
    
    assert log is None
    assert error == "Empty line"


def test_validate_log_structure_valid():
    """Test validation of a valid log structure."""
    log = {
        "user_id": 1,
        "feature": "map",
        "timestamp": "2024-03-01T10:01:00Z",
        "action": "start"
    }
    is_valid, error = validate_log_structure(log, 1)
    
    assert is_valid is True
    assert error is None


def test_validate_log_structure_missing_field():
    """Test validation with missing required field."""
    log = {
        "user_id": 1,
        "timestamp": "2024-03-01T10:01:00Z",
        "action": "start"
        # Missing "feature"
    }
    is_valid, error = validate_log_structure(log, 1)
    
    assert is_valid is False
    assert "Missing required fields" in error
    assert "feature" in error


def test_validate_log_structure_invalid_timestamp():
    """Test validation with invalid timestamp."""
    log = {
        "user_id": 1,
        "feature": "map",
        "timestamp": "NOT-A-DATE",
        "action": "start"
    }
    is_valid, error = validate_log_structure(log, 1)
    
    assert is_valid is False
    assert "Invalid timestamp format" in error


def test_validate_log_structure_invalid_action():
    """Test validation with invalid action value."""
    log = {
        "user_id": 1,
        "feature": "map",
        "timestamp": "2024-03-01T10:01:00Z",
        "action": "invalid_action"
    }
    is_valid, error = validate_log_structure(log, 1)
    
    assert is_valid is False
    assert "Invalid action value" in error


def test_validate_log_structure_invalid_feature():
    """Test validation with invalid feature value."""
    log = {
        "user_id": 1,
        "feature": "invalid_feature",
        "timestamp": "2024-03-01T10:01:00Z",
        "action": "start"
    }
    is_valid, error = validate_log_structure(log, 1)
    
    assert is_valid is False
    assert "Invalid feature value" in error


def test_parse_logs_file():
    """Test parsing a complete log file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        # Write test data
        f.write('{"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"}\n')
        f.write('{"user_id": 1, "action": "start" -- BROKEN\n')  # Malformed
        f.write('{"user_id": 2, "timestamp": "2024-03-01T10:02:00Z", "action": "end"}\n')  # Missing feature
        f.write('{"user_id": 3, "feature": "chat", "timestamp": "2024-03-01T10:03:00Z", "action": "end"}\n')
        temp_path = f.name
    
    try:
        result = parse_logs_file(temp_path)
        
        assert "valid_logs" in result
        assert "errors" in result
        assert "stats" in result
        
        # Should have 2 valid logs
        assert len(result["valid_logs"]) == 2
        # Should have 2 errors
        assert len(result["errors"]) == 2
        # Stats should reflect this
        assert result["stats"]["valid_logs"] == 2
        assert result["stats"]["parse_errors"] == 1
        assert result["stats"]["validation_errors"] == 1
    finally:
        Path(temp_path).unlink()


def test_group_logs_by_user_and_feature():
    """Test grouping logs by user and feature."""
    valid_logs = [
        {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"},
        {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:02:00Z", "action": "end"},
        {"user_id": 1, "feature": "chat", "timestamp": "2024-03-01T10:03:00Z", "action": "start"},
        {"user_id": 2, "feature": "map", "timestamp": "2024-03-01T10:04:00Z", "action": "start"},
    ]
    
    grouped = group_logs_by_user_and_feature(valid_logs)
    
    assert 1 in grouped
    assert 2 in grouped
    assert "map" in grouped[1]
    assert "chat" in grouped[1]
    assert "map" in grouped[2]
    assert len(grouped[1]["map"]) == 2
    assert len(grouped[1]["chat"]) == 1
    assert len(grouped[2]["map"]) == 1


def test_parse_logs_file_nonexistent_file():
    """Test parsing a non-existent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        parse_logs_file("nonexistent_file.jsonl")
