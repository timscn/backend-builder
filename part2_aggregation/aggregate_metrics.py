import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import sys
# Add parent directory to path to allow importing utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.utils import resolve_path, parse_timestamp


def load_parsed_data(summary_path: str = "output/parsed_summary.json") -> Dict:
    """
    Load the parsed data from Part 1.
    
    Raises:
        FileNotFoundError: If the summary file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    full_path = resolve_path(summary_path, __file__)
    
    if not full_path.exists():
        raise FileNotFoundError(f"Summary file not found: {full_path}")
    
    with open(full_path, "r") as f:
        return json.load(f)


def calculate_session_durations(grouped_data: Dict) -> Dict:
    """
    Calculate session durations by matching start/end actions for each user-feature pair.
    Returns a dictionary with session information.
    """
    sessions = []
    incomplete_sessions = defaultdict(list)  # Track unmatched starts
    
    for user_id, features in grouped_data.items():
        for feature, logs in features.items():
            # Sort logs by timestamp
            sorted_logs = sorted(logs, key=lambda x: parse_timestamp(x["timestamp"]))
            
            for log in sorted_logs:
                if log["action"] == "start":
                    # Store start time for this user-feature combination
                    key = (user_id, feature)
                    incomplete_sessions[key].append({
                        "start_time": parse_timestamp(log["timestamp"]),
                        "start_log": log
                    })
                elif log["action"] == "end":
                    # Try to match with the most recent start
                    key = (user_id, feature)
                    if key in incomplete_sessions and incomplete_sessions[key]:
                        start_info = incomplete_sessions[key].pop(0)
                        end_time = parse_timestamp(log["timestamp"])
                        duration = end_time - start_info["start_time"]
                        duration_seconds = duration.total_seconds()
                        
                        # Edge case: Validate duration is non-negative
                        if duration_seconds < 0:
                            # End before start - log as error but don't add to sessions
                            continue
                        
                        # Edge case: Flag unrealistic durations (> 24 hours)
                        max_duration_hours = 24
                        if duration_seconds > max_duration_hours * 3600:
                            # Still add but could be flagged in summary
                            pass
                        
                        sessions.append({
                            "user_id": user_id,
                            "feature": feature,
                            "start_time": start_info["start_time"],
                            "end_time": end_time,
                            "duration_seconds": duration_seconds,
                            "duration_formatted": str(duration),
                            "start_log": start_info["start_log"],
                            "end_log": log
                        })
                    # If no matching start, we can't calculate duration
    
    return {
        "sessions": sessions,
        "incomplete_sessions": {
            str(k): len(v) for k, v in incomplete_sessions.items() if v
        }
    }


def aggregate_by_time_intervals(sessions: List[Dict], interval_minutes: int = 60) -> Dict:
    """
    Group sessions by time intervals (e.g., hourly).
    """
    interval_data = defaultdict(lambda: {
        "sessions": [],
        "total_duration_seconds": 0,
        "session_count": 0
    })
    
    for session in sessions:
        start_time = session["start_time"]
        # Round down to the nearest interval
        interval_start = start_time.replace(
            minute=(start_time.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        interval_key = interval_start.isoformat()
        
        interval_data[interval_key]["sessions"].append(session)
        interval_data[interval_key]["total_duration_seconds"] += session["duration_seconds"]
        interval_data[interval_key]["session_count"] += 1
    
    # Calculate averages
    for interval_key in interval_data:
        count = interval_data[interval_key]["session_count"]
        if count > 0:
            interval_data[interval_key]["average_duration_seconds"] = (
                interval_data[interval_key]["total_duration_seconds"] / count
            )
    
    return dict(interval_data)


def aggregate_by_feature(sessions: List[Dict]) -> Dict:
    """
    Aggregate session metrics by feature (higher level grouping).
    """
    feature_stats = defaultdict(lambda: {
        "total_sessions": 0,
        "total_duration_seconds": 0,
        "average_duration_seconds": 0,
        "min_duration_seconds": float("inf"),
        "max_duration_seconds": 0,
        "unique_users": set()
    })
    
    for session in sessions:
        feature = session["feature"]
        duration = session["duration_seconds"]
        
        feature_stats[feature]["total_sessions"] += 1
        feature_stats[feature]["total_duration_seconds"] += duration
        feature_stats[feature]["unique_users"].add(session["user_id"])
        
        if duration < feature_stats[feature]["min_duration_seconds"]:
            feature_stats[feature]["min_duration_seconds"] = duration
        if duration > feature_stats[feature]["max_duration_seconds"]:
            feature_stats[feature]["max_duration_seconds"] = duration
    
    # Calculate averages and convert sets to counts
    result = {}
    for feature, stats in feature_stats.items():
        count = stats["total_sessions"]
        result[feature] = {
            "total_sessions": count,
            "total_duration_seconds": stats["total_duration_seconds"],
            "average_duration_seconds": (
                stats["total_duration_seconds"] / count if count > 0 else 0
            ),
            "min_duration_seconds": (
                stats["min_duration_seconds"] if stats["min_duration_seconds"] != float("inf") else 0
            ),
            "max_duration_seconds": stats["max_duration_seconds"],
            "unique_users_count": len(stats["unique_users"]),
            "unique_users": sorted(list(stats["unique_users"]))
        }
    
    return result


def aggregate_by_user(sessions: List[Dict]) -> Dict:
    """
    Aggregate session metrics by user (higher level grouping).
    """
    user_stats = defaultdict(lambda: {
        "total_sessions": 0,
        "total_duration_seconds": 0,
        "average_duration_seconds": 0,
        "features_used": set(),
        "sessions_by_feature": defaultdict(int)
    })
    
    for session in sessions:
        user_id = session["user_id"]
        feature = session["feature"]
        duration = session["duration_seconds"]
        
        user_stats[user_id]["total_sessions"] += 1
        user_stats[user_id]["total_duration_seconds"] += duration
        user_stats[user_id]["features_used"].add(feature)
        user_stats[user_id]["sessions_by_feature"][feature] += 1
    
    # Calculate averages and convert sets
    result = {}
    for user_id, stats in user_stats.items():
        count = stats["total_sessions"]
        result[str(user_id)] = {
            "total_sessions": count,
            "total_duration_seconds": stats["total_duration_seconds"],
            "average_duration_seconds": (
                stats["total_duration_seconds"] / count if count > 0 else 0
            ),
            "features_used_count": len(stats["features_used"]),
            "features_used": sorted(list(stats["features_used"])),
            "sessions_by_feature": dict(stats["sessions_by_feature"])
        }
    
    return result


def create_final_summary(parsed_data: Dict, session_data: Dict) -> Dict:
    """
    Create the final aggregated summary combining Part 1 and Part 2 metrics.
    """
    sessions = session_data["sessions"]
    
    # Calculate overall statistics
    total_duration = sum(s["duration_seconds"] for s in sessions)
    avg_duration = total_duration / len(sessions) if sessions else 0
    
    final_summary = {
        "metadata": {
            "total_sessions": len(sessions),
            "total_duration_seconds": total_duration,
            "average_session_duration_seconds": avg_duration,
            "incomplete_sessions": session_data["incomplete_sessions"]
        },
        "aggregated_by_feature": aggregate_by_feature(sessions),
        "aggregated_by_user": aggregate_by_user(sessions),
        "aggregated_by_time_intervals": aggregate_by_time_intervals(sessions, interval_minutes=60),
        "part1_summary": {
            "overview": parsed_data["overview"],
            "parsing_stats": parsed_data["parsing_stats"]
        }
    }
    
    return final_summary


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to a human-readable string.
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


def main():
    """
    Main function to aggregate metrics from Part 1 and produce final summary.
    """
    print("Loading parsed data from Part 1...")
    parsed_data = load_parsed_data()
    
    print("Calculating session durations...")
    session_data = calculate_session_durations(parsed_data["grouped_data"])
    
    print(f"Found {len(session_data['sessions'])} complete sessions")
    if session_data["incomplete_sessions"]:
        print(f"Incomplete sessions: {len(session_data['incomplete_sessions'])} unmatched starts")
    
    print("\nCreating final aggregated summary...")
    final_summary = create_final_summary(parsed_data, session_data)
    
    # Print summary to console
    print("\n" + "=" * 70)
    print("📊 FINAL AGGREGATED SUMMARY")
    print("=" * 70)
    
    print(f"\n🎯 OVERALL METRICS")
    print("-" * 70)
    print(f"Total sessions: {final_summary['metadata']['total_sessions']}")
    print(f"Total duration: {format_duration(final_summary['metadata']['total_duration_seconds'])}")
    print(f"Average session duration: {format_duration(final_summary['metadata']['average_session_duration_seconds'])}")
    
    print(f"\n📈 AGGREGATED BY FEATURE (Higher Level Grouping)")
    print("-" * 70)
    for feature, stats in sorted(final_summary["aggregated_by_feature"].items()):
        print(f"\n{feature.upper()}:")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Total duration: {format_duration(stats['total_duration_seconds'])}")
        print(f"  Average duration: {format_duration(stats['average_duration_seconds'])}")
        print(f"  Min duration: {format_duration(stats['min_duration_seconds'])}")
        print(f"  Max duration: {format_duration(stats['max_duration_seconds'])}")
        print(f"  Unique users: {stats['unique_users_count']}")
    
    print(f"\n👥 AGGREGATED BY USER (Higher Level Grouping)")
    print("-" * 70)
    for user_id, stats in sorted(final_summary["aggregated_by_user"].items(), key=lambda x: int(x[0])):
        print(f"\nUser {user_id}:")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Total duration: {format_duration(stats['total_duration_seconds'])}")
        print(f"  Average duration: {format_duration(stats['average_duration_seconds'])}")
        print(f"  Features used: {', '.join(stats['features_used'])}")
        print(f"  Sessions by feature: {stats['sessions_by_feature']}")
    
    print(f"\n⏰ AGGREGATED BY TIME INTERVALS (Hourly)")
    print("-" * 70)
    for interval, stats in sorted(final_summary["aggregated_by_time_intervals"].items()):
        interval_time = datetime.fromisoformat(interval)
        print(f"\n{interval_time.strftime('%Y-%m-%d %H:%M')}:")
        print(f"  Sessions: {stats['session_count']}")
        print(f"  Total duration: {format_duration(stats['total_duration_seconds'])}")
        if stats['session_count'] > 0:
            print(f"  Average duration: {format_duration(stats['average_duration_seconds'])}")
    
    # Save final summary
    output_path = resolve_path("output/final_summary.json", __file__)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(final_summary, f, indent=2, default=str)
    
    print(f"\n💾 Final summary saved to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
