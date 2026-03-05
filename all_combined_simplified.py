import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.utils import resolve_path
from utils.raw_log import RawLog


class AllCombined:



    def __init__(self, input_file: str):
        self.input_file = input_file
        self.valid_features =["map", "chat", "settings", "profile"]
        self.valid_actions = ["start", "end"]
        self.required_fields = ["user_id", "feature", "timestamp", "action"]

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO format timestamp string to datetime object, handling 'Z'."""
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

    def parse_log_line(self, line: str, line_number: int) -> Tuple[Optional[Dict], Optional[str]]:
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


    def validate_log_structure(self, log: Dict, line_number: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that the log has the required structure.
        Returns: (is_valid, error_message)
        """
        missing_fields = [field for field in self.required_fields if field not in log]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate timestamp format
        try:
            self.parse_timestamp(log["timestamp"])
        except (ValueError, AttributeError):
            return False, f"Invalid timestamp format: {log.get('timestamp', 'N/A')}"
        
        # Validate action values
        if log["action"] not in self.VALID_ACTIONS:
            return False, f"Invalid action value: {log.get('action', 'N/A')}"
        
        # Validate feature values
        if log["feature"] not in self.VALID_FEATURES:
            return False, f"Invalid feature value: {log.get('feature', 'N/A')}"
        
        return True, None

    def parse_logs_file(self) -> Dict:
        """
        Parse the logs.jsonl file and return structured data.
        Returns a dictionary with:
        - valid_logs: List of valid log entries
        - errors: List of error information
        - stats: Statistics about the parsing
        """
        full_input_path = resolve_path(self.input_file, __file__)
        
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
                log, parse_error = self.parse_log_line(line, line_number)
                
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
                is_valid, validation_error = self.validate_log_structure(log, line_number)
                
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
    def group_logs_by_user_and_feature(self,valid_logs: List[RawLog]) -> Dict:
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

    def create_summary(self, parsed_data: Dict) -> Dict:
        """
        Create a clean summary from the parsed data.
        """
        valid_logs: List[RawLog] = parsed_data["valid_logs"]
        grouped = self.group_logs_by_user_and_feature(valid_logs)
        
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
    def main(self):
        print(f"Parsing logs from: {self.input_file}")
        parsed_data = self.parse_logs_file()
        summary = self.create_summary(parsed_data)
       # Print overview
        print("\n📊 PARSING SUMMARY")
        print("=" * 60)
        print(f"Total lines processed: {summary['parsing_stats']['total_lines']}")
        print(f"Valid logs: {summary['parsing_stats']['valid_logs']}")
        print(f"Parse errors: {summary['parsing_stats']['parse_errors']}")
        print(f"Validation errors: {summary['parsing_stats']['validation_errors']}")

if __name__ == "__main__":
    # 1. Initialize the class
    processor = AllCombined("backend-builder/output/logs.jsonl")
    
    # 2. Trigger the logic
    processor.main()