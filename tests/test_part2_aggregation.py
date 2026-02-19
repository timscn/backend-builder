"""
Tests for Part 2: Aggregation and Metrics
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from part2_aggregation.aggregate_metrics import (
    parse_timestamp,
    calculate_session_durations,
    aggregate_by_feature,
    aggregate_by_user,
    aggregate_by_time_intervals,
)


def test_parse_timestamp():
    """Test timestamp parsing."""
    timestamp_str = "2024-03-01T10:01:00Z"
    dt = parse_timestamp(timestamp_str)
    
    assert isinstance(dt, datetime)
    assert dt.year == 2024
    assert dt.month == 3
    assert dt.day == 1
    assert dt.hour == 10
    assert dt.minute == 1


def test_calculate_session_durations_complete_sessions():
    """Test calculating durations for complete sessions."""
    grouped_data = {
        1: {
            "map": [
                {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"},
                {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:31:00Z", "action": "end"},
            ]
        }
    }
    
    result = calculate_session_durations(grouped_data)
    
    assert len(result["sessions"]) == 1
    session = result["sessions"][0]
    assert session["user_id"] == 1
    assert session["feature"] == "map"
    assert session["duration_seconds"] == 1800  # 30 minutes


def test_calculate_session_durations_incomplete_sessions():
    """Test handling of incomplete sessions (unmatched starts)."""
    grouped_data = {
        1: {
            "map": [
                {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"},
                # No matching end
            ]
        }
    }
    
    result = calculate_session_durations(grouped_data)
    
    assert len(result["sessions"]) == 0
    assert len(result["incomplete_sessions"]) > 0


def test_calculate_session_durations_multiple_sessions():
    """Test calculating durations for multiple sessions."""
    grouped_data = {
        1: {
            "map": [
                {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:01:00Z", "action": "start"},
                {"user_id": 1, "feature": "map", "timestamp": "2024-03-01T10:11:00Z", "action": "end"},
            ],
            "chat": [
                {"user_id": 1, "feature": "chat", "timestamp": "2024-03-01T10:15:00Z", "action": "start"},
                {"user_id": 1, "feature": "chat", "timestamp": "2024-03-01T10:25:00Z", "action": "end"},
            ]
        }
    }
    
    result = calculate_session_durations(grouped_data)
    
    assert len(result["sessions"]) == 2
    assert result["sessions"][0]["duration_seconds"] == 600  # 10 minutes
    assert result["sessions"][1]["duration_seconds"] == 600  # 10 minutes


def test_aggregate_by_feature():
    """Test aggregation by feature."""
    sessions = [
        {"user_id": 1, "feature": "map", "duration_seconds": 600},
        {"user_id": 1, "feature": "map", "duration_seconds": 1200},
        {"user_id": 2, "feature": "chat", "duration_seconds": 900},
    ]
    
    result = aggregate_by_feature(sessions)
    
    assert "map" in result
    assert "chat" in result
    assert result["map"]["total_sessions"] == 2
    assert result["map"]["total_duration_seconds"] == 1800
    assert result["map"]["average_duration_seconds"] == 900
    assert result["chat"]["total_sessions"] == 1


def test_aggregate_by_user():
    """Test aggregation by user."""
    sessions = [
        {"user_id": 1, "feature": "map", "duration_seconds": 600},
        {"user_id": 1, "feature": "chat", "duration_seconds": 900},
        {"user_id": 2, "feature": "map", "duration_seconds": 1200},
    ]
    
    result = aggregate_by_user(sessions)
    
    assert "1" in result
    assert "2" in result
    assert result["1"]["total_sessions"] == 2
    assert result["1"]["total_duration_seconds"] == 1500
    assert result["1"]["features_used_count"] == 2
    assert result["2"]["total_sessions"] == 1


def test_aggregate_by_time_intervals():
    """Test aggregation by time intervals."""
    sessions = [
        {
            "user_id": 1,
            "feature": "map",
            "start_time": datetime(2024, 3, 1, 10, 5),
            "duration_seconds": 600
        },
        {
            "user_id": 1,
            "feature": "chat",
            "start_time": datetime(2024, 3, 1, 10, 30),
            "duration_seconds": 900
        },
        {
            "user_id": 2,
            "feature": "map",
            "start_time": datetime(2024, 3, 1, 11, 15),
            "duration_seconds": 1200
        },
    ]
    
    result = aggregate_by_time_intervals(sessions, interval_minutes=60)
    
    # Should have two intervals: 10:00 and 11:00
    assert len(result) == 2
    # Check that sessions are grouped correctly
    interval_keys = list(result.keys())
    assert any("10:00" in key for key in interval_keys)
    assert any("11:00" in key for key in interval_keys)
