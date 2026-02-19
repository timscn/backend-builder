import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import sys
# Add parent directory to path to allow importing utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.utils import resolve_path, parse_timestamp, VALID_FEATURES, VALID_ACTIONS
from utils.raw_log import RawLog

def parse_log_line(line: str, line_number: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse a single line from the JSONL file.
    Returns: (parsed_log_dict, error_message)
    """
    line = line.strip()
    if not line:
        return None, "Empty line"
    
    try:
        log = json.loads(line)
        return log, None
    except json.JSONDecodeError as e:
        return None, f"Malformed JSON: {str(e)}"


def validate_log_structure(log: Dict, line_number: int) -> Tuple[bool, Optional[str]]:
    """
    Validate that the log has the required structure.
    Returns: (is_valid, error_message)
    """
    required_fields = ["user_id", "feature", "timestamp", "action"]
    missing_fields = [field for field in required_fields if field not in log]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate timestamp format
    try:
        parse_timestamp(log["timestamp"])
    except (ValueError, AttributeError):
        return False, f"Invalid timestamp format: {log.get('timestamp', 'N/A')}"
    
    # Validate action values
    if log["action"] not in VALID_ACTIONS:
        return False, f"Invalid action value: {log.get('action', 'N/A')}"
    
    # Validate feature values
    if log["feature"] not in VALID_FEATURES:
        return False, f"Invalid feature value: {log.get('feature', 'N/A')}"
    
    return True, None


def parse_logs_file(input_path: str) -> Dict:
    """
    Parse the logs.jsonl file and return structured data.
    Returns a dictionary with:
    - valid_logs: List of valid log entries
    - errors: List of error information
    - stats: Statistics about the parsing
    """
    full_input_path = resolve_path(input_path, __file__)
    
    if not full_input_path.exists():
        raise FileNotFoundError(f"Input file not found: {full_input_path}")
    
    valid_logs = []
    errors = []
    stats = {
        "total_lines": 0,
        "valid_logs": 0,
        "parse_errors": 0,
        "validation_errors": 0,
    }
    
    with open(full_input_path, "r") as f:
        for line_number, line in enumerate(f, start=1):
            stats["total_lines"] += 1
            
            # Try to parse the JSON
            log, parse_error = parse_log_line(line, line_number)
            
            if parse_error:
                errors.append({
                    "line_number": line_number,
                    "type": "parse_error",
                    "message": parse_error,
                    "raw_line": line.strip()[:100]  # First 100 chars
                })
                stats["parse_errors"] += 1
                continue
            
            # Validate the structure
            is_valid, validation_error = validate_log_structure(log, line_number)
            
            if not is_valid:
                errors.append({
                    "line_number": line_number,
                    "type": "validation_error",
                    "message": validation_error,
                    "log": log
                })
                stats["validation_errors"] += 1
                continue
            
            # Log is valid
            valid_logs.append({
                **log,
                "line_number": line_number
            })
            stats["valid_logs"] += 1
    
    return {
        "valid_logs": valid_logs,
        "errors": errors,
        "stats": stats
    }


def group_logs_by_user_and_feature(valid_logs: List[RawLog]) -> Dict:
    """
    Group logs by user_id and feature.
    Returns a nested dictionary: {user_id: {feature: [logs]}}
    """
    grouped = defaultdict(lambda: defaultdict(list))
    
    for log in valid_logs:
        user_id = log["user_id"]
        feature = log["feature"]
        grouped[user_id][feature].append(log)
    
    # Convert defaultdict to regular dict for cleaner output
    return {user_id: dict(features) for user_id, features in grouped.items()}


def create_summary(parsed_data: Dict) -> Dict:
    """
    Create a clean summary from the parsed data.
    """
    valid_logs: List[RawLog] = parsed_data["valid_logs"]
    grouped = group_logs_by_user_and_feature(valid_logs)
    
    # Calculate statistics
    user_stats = {}
    feature_stats = defaultdict(int)
    action_stats = defaultdict(int)
    
    for log in valid_logs:
        user_id = log["user_id"]
        feature = log["feature"]
        action = log["action"]
        
        if user_id not in user_stats:
            user_stats[user_id] = {
                "total_actions": 0,
                "features_used": set(),
                "actions": {"start": 0, "end": 0}
            }
        
        user_stats[user_id]["total_actions"] += 1
        user_stats[user_id]["features_used"].add(feature)
        user_stats[user_id]["actions"][action] += 1
        feature_stats[feature] += 1
        action_stats[action] += 1
    
    # Convert sets to lists for JSON serialization
    for user_id in user_stats:
        user_stats[user_id]["features_used"] = sorted(list(user_stats[user_id]["features_used"]))
    
    summary = {
        "overview": {
            "total_valid_logs": len(valid_logs),
            "total_errors": len(parsed_data["errors"]),
            "unique_users": len(user_stats),
            "unique_features": len(feature_stats)
        },
        "parsing_stats": parsed_data["stats"],
        "user_statistics": user_stats,
        "feature_statistics": dict(feature_stats),
        "action_statistics": dict(action_stats),
        "grouped_data": grouped
    }
    
    return summary


def main():
    """
    Main function to parse logs and generate summary.
    """
    input_file = "output/logs.jsonl"
    
    print(f"Parsing logs from: {input_file}")
    print("-" * 60)
    
    # Parse the logs
    parsed_data = parse_logs_file(input_file)
    
    # Create summary
    summary = create_summary(parsed_data)
    
    # Print overview
    print("\n📊 PARSING SUMMARY")
    print("=" * 60)
    print(f"Total lines processed: {summary['parsing_stats']['total_lines']}")
    print(f"Valid logs: {summary['parsing_stats']['valid_logs']}")
    print(f"Parse errors: {summary['parsing_stats']['parse_errors']}")
    print(f"Validation errors: {summary['parsing_stats']['validation_errors']}")
    
    print("\n👥 USER STATISTICS")
    print("=" * 60)
    for user_id, stats in sorted(summary["user_statistics"].items()):
        print(f"User {user_id}:")
        print(f"  Total actions: {stats['total_actions']}")
        print(f"  Features used: {', '.join(stats['features_used'])}")
        print(f"  Starts: {stats['actions']['start']}, Ends: {stats['actions']['end']}")
    
    print("\n🎯 FEATURE STATISTICS")
    print("=" * 60)
    for feature, count in sorted(summary["feature_statistics"].items()):
        print(f"  {feature}: {count} actions")
    
    print("\n⚡ ACTION STATISTICS")
    print("=" * 60)
    for action, count in sorted(summary["action_statistics"].items()):
        print(f"  {action}: {count} occurrences")
    
    # Save summary to JSON file
    output_path = resolve_path("output/parsed_summary.json", __file__)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Summary saved to: {output_path}")
    
    # Print sample errors if any
    if parsed_data["errors"]:
        print("\n❌ SAMPLE ERRORS (first 5)")
        print("=" * 60)
        for error in parsed_data["errors"][:5]:
            print(f"Line {error['line_number']} ({error['type']}): {error['message']}")


if __name__ == "__main__":
    main()
